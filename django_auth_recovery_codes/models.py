from __future__ import annotations 

import uuid

from django.db import models, connections
from django.db.models import F
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django_email_sender.models import EmailBaseLog


from django_auth_recovery_codes.utils.security.generator import generate_2fa_secure_recovery_code
from django_auth_recovery_codes.utils.security.hash import is_already_hashed, make_lookup_hash
from django_auth_recovery_codes.utils.utils import schedule_future_date, create_json_from_attrs


User = get_user_model()


class RecoveryCodePurgeHistory(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    total_codes_purged = models.PositiveIntegerField(default=0)
    total_batches_purged = models.PositiveIntegerField(default=0)
    retention_days = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"Purge on {self.timestamp}: {self.total_codes_purged} codes from {self.total_batches_purged} batches"
    

class Status(models.TextChoices):
    ACTIVE         = "a", "Active"
    INVALIDATE     = "i", "Invalidate"
    USED           = "u", "Used"
    PENDING_DELETE = "p", "Pending Delete"


class RecoveryCodeCleanUpScheduler(models.Model):
    class Status(models.TextChoices):
        SUCCESS        = "s", "Success"
        FAILURE        = "f", "Failure"
        DELETED        = "d", "Deleted"
    
    class Schedule(models.TextChoices):
        ONCE    = "O", "Once"
        MINUTES = "T", "Minutes"
        HOURLY  = "H", "Hourly"
        DAILY   = "D", "Daily"
        WEEKLY  = "W", "Weekly"
        QUARTERLY = "Q", "Quarterly"
        YEARLY  = "Y", "Yearly"

    run_at           = models.DateTimeField()
    deleted_count    = models.PositiveIntegerField(default=0)
    enable_scheduler = models.BooleanField(default=True)
    status           = models.CharField(max_length=1, choices=Status)
    error_message    = models.TextField()

    class Meta:
        ordering = ['-run_at']

    def __str__(self):
        return f"{self.run_at} - {self.status} - Deleted {self.deleted_count}"




class RecoveryCodesBatch(models.Model):
    CACHE_KEYS = ["generated", "downloaded", "emailed", "viewed"]
    JSON_KEYS  = ["id", "number_issued", "number_removed", "number_invalidated", "number_used", "created_at",
                  "modified_at", "expiry_date", "deleted_at", "deleted_by", "viewed", "downloaded",
                  "emailed", "generated", 
                  ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    number_issued      = models.PositiveSmallIntegerField(default=10)
    number_removed     = models.PositiveSmallIntegerField(default=0)
    number_invalidated = models.PositiveSmallIntegerField(default=0)
    number_used        = models.PositiveSmallIntegerField(default=0)
    user               = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="recovery_batches")
    created_at         = models.DateTimeField(auto_now_add=True)
    modified_at        = models.DateTimeField(auto_now=True)
    status             = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE)
    automatic_removal  = models.BooleanField(default=True)
    expiry_date        = models.DateTimeField(blank=True, null=True)
    deleted_at         = models.DateTimeField(null=True, blank=True)
    deleted_by         = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="deleted_batches")

     # Action tracking
    viewed            = models.BooleanField(default=False)
    downloaded        = models.BooleanField(default=False)
    emailed           = models.BooleanField(default=False)
    generated         = models.BooleanField(default=False)

    # constant field
    STATUS_FIELD             = "status"
    MARK_FOR_DELETION_FIELD  = "mark_for_deletion"
    MODIFIED_AT_FIELD        = "modified_at"
    DELETED_AT_FIELD         = "deleted_at"
    DELETED_BY_FIELD         = "deleted_by"
    
    # constant flags
    VIEWED_FLAG              = "viewed"
    DOWNLOADED_FLAG          = "downloaded"
    EMAILED_FLAG             = "emailed"
    GENERATED_FLAG           = "generated"

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Batch {self.id} for {self.user or 'Deleted User'}"
    
    def purge_expired_codes(self, bulk_delete=True, log_per_code=False, retention_days=1, delete_empty_batch=False):
        """
        Hard-delete all recovery codes in this batch that have been marked for deletion or invalidated
        and are older than the retention period. Logs the purge action.

        Args:
            retention_days (int): Number of days to keep a soft-deleted code before purging.
            bulk_delete (bool): Whether to delete codes in bulk or individually.
            log_per_code (bool): If True, log each code deletion individually.
            delete_empty_batch (bool): If True, delete the batch after purging all its codes.

        Returns:
            int: Number of recovery codes deleted.
        """
        
        purge_after_date = self.get_expiry_threshold(retention_days)
        expired_codes = self.recovery_codes.filter(
            automatic_removal=True, 
            status__in=self.terminal_statuses(),
            modified_at__lt=purge_after_date
        )

        deleted_count = 0

        if log_per_code and not bulk_delete:
            for code in expired_codes:
                RecoveryCodeAudit.log_action(
                    user=self.user,
                    deleted_by=None,
                    action=RecoveryCodeAudit.Action.DELETED,
                    batch=self,
                    number_deleted=1
                )
                code.delete()
                deleted_count += 1
        else:
            number_to_delete = expired_codes.count()
            if number_to_delete > 0:
                expired_codes.delete()
                RecoveryCodeAudit.log_action(
                    user=None,
                    deleted_by=None,
                    action=RecoveryCodeAudit.Action.BATCH_PURGED,
                    number_deleted=number_to_delete,
                    batch=self
                )
                deleted_count = number_to_delete

        # Optionally delete the batch if empty
        if delete_empty_batch and not self.recovery_codes.exists():
            self.delete()

        return deleted_count

    @staticmethod
    def get_expiry_threshold(days=30):
        return timezone.now() - timedelta(days=days) 
    
    @classmethod
    def terminal_statuses(cls):
        """Statuses meaning the batch is no longer valid."""
        return [cls.Status.PENDING_DELETE, cls.Status.INVALIDATED]

    @property
    def frontend_status(self):
        """
        Returns a human-readable status for frontend display.

        Overrides certain internal statuses with custom labels for clarity.
        For example:
        - Status.PENDING_DELETE is shown as "Deleted"

        All other statuses use their default TextChoices label.
        """
        overrides = {Status.PENDING_DELETE: "Deleted"}
        return overrides.get(Status(self.status), Status(self.status).label)
 
            
    def update_invalidate_code_count(self, save = False) -> "RecoveryCode":
        """
        Increment the count of invalidated codes by 1.

        This method ensures consistent updates to the invalidated code count.
        Optionally, it can save the instance immediately if `save` is True; 
        otherwise, the update is deferred, allowing additional operations before saving.

        Parameters
        ----------
        save (bool), default=False
            If True, saves the instance immediately after incrementing.  
            If False, the update is performed in memory and can be saved later.

        Raises

        TypeError
            If `save` is not a boolean.

        Returns
       
        RecoveryCode
            Returns self to allow method chaining.

        Notes
        -----
        This can also be done in the views like this:

            # views.py

            >>> recovery_code_batch = RecoveryCodeBatch.get_by_user(user='eu')
            >>> recovery_code_batch.number_invalidated += 1
            >>> recovery_code.save()

        However this can also introduce errors because anyone working in the views can introduce errors e.g
            >>> recovery_code.number_invalidated += 2  # mistake
            >>> recovery_code.save()

        - Using this method prevents accidental mis-increments in views (e.g., adding 2 instead of 1).  
        - Encourages encapsulation of business logic in the model rather than in views.

        Example
        -------
        >>> recovery_code.update_invalidate_code_count(save=True)  # increments by 1 safely
        >>> recovery_code.update_invalidate_code_count().save()   # deferred save, also increments by 1 and not increase accidently
        """
       
        self.status = Status.INVALIDATE
        
        # Increment counter safely (atomic by default)
        self._update_field_counter("number_invalidated", save=save, atomic=True)
        return self
    
    def update_delete_code_count(self, save: bool = False) -> "RecoveryCode":
        """
        Increment the count of deleted (removed) codes by 1.

        This method ensures consistent updates to the `number_removed` field.
        Optionally, it can save the instance immediately if `save` is True; 
        otherwise, the update is deferred, allowing additional operations before saving.

        Parameters
        ----------
        save : bool, default=False
            If True, saves the instance immediately after incrementing.  
            If False, the update is performed in memory and can be saved later.

        Raises
        ------
        TypeError
            If `save` is not a boolean.

        Returns
        -------
        RecoveryCode
            Returns self to allow method chaining.

        Notes
        -----
        This could also be done manually in views, for example:

            # views.py

            >>> recovery_code_batch = RecoveryCodeBatch.get_by_user(user="eu")
            >>> recovery_code_batch.number_removed += 1
            >>> recovery_code_batch.save()

        However, this risks mistakes (e.g., incrementing by 2 instead of 1).
        By using this method, increments remain consistent and the logic
        is encapsulated within the model instead of spread across views.

        Example
        -------
        >>> recovery_code.update_delete_code_count(save=True)   # increments by 1 safely
        >>> recovery_code.update_delete_code_count().save()     # deferred save, still increments by 1
        """
       
        self.status = Status.INVALIDATE
        
        # Increment counter safely (atomic by default)
        self._update_field_counter("number_removed", save=save, atomic=True)
        return self
       
    def _update_field_counter(self, field_name: str, save: bool = False, atomic: bool = True):
        """
        Internal helper to increment a numeric counter field safely.

        Intended for use **only** by the public methods:
        - `update_invalidate_code_count`
        - `update_delete_code_count`

        Parameters
        ----------
        field_name : str
            The name of the field to increment. Must exist on the model.
        save : bool, default=False
            If True, saves the instance immediately after incrementing. 
            If False, the update is performed in memory and can be saved later.
        atomic : bool, default=True
            If True, performs a DB-level atomic increment using F() to prevent lost updates
            in concurrent scenarios. If False, increments in memory (faster but not safe under concurrency).

        Returns
        -------
        self : Model instance
            The updated instance for method chaining.

        Notes
        -----
        - This method is private and should **not** be called directly outside the model.
        - Use `atomic=True` for production or concurrent updates; `atomic=False` is safe for single-user scripts or tests.
        - Encapsulating the increment logic ensures consistent counter updates and prevents misuse.
        """
      
        if not hasattr(self, field_name):
            raise AttributeError(f"{self.__class__.__name__} has no field '{field_name}'")

        if atomic:

            # DB-level increment (avoids race conditions)
            self.__class__.objects.filter(pk=self.pk).update(**{field_name: F(field_name) + 1})

            # Refresh this instance from DB so it's up to date
            return self.refresh_from_db()

        # In-memory increment (not concurrency-safe) especially if the user tries to update the valuse using multiple tabs
        # at the same time or right after another
        current_val = getattr(self, field_name, None)
        if current_val is None:
            raise ValueError(f"Field '{field_name}' is None, cannot increment.")
        setattr(self, field_name, current_val + 1)

        if save:
            self.save()

        return self
    
    def get_cache_values(self) -> dict:
        """
        Returns the current state of this batch for caching.
        """
        return create_json_from_attrs(self, self.CACHE_KEYS)
    
    def get_json_values(self):
        """
        Returns the attribrutes/field name for the model class
        """
        json_cache = create_json_from_attrs(self, keys=self.JSON_KEYS, capitalise_keys=True)
        if json_cache:
            json_cache["STATUS"]    = self.frontend_status
            json_cache["USERNAME"]  = self.user.username
            return json_cache
        return {}
    
    def reset_cache_values(self):
        """
        Resets all cache-related values to False.
        """
        for key in self.CACHE_KEYS:
            setattr(self, key, False)

    def mark_as_viewed(self, save : bool = True):
        self.viewed = True
        return self._update_field_helper(fields_list=[self.VIEWED_FLAG], save=save)

    def mark_as_downloaded(self, save : bool = True):
        self.downloaded = True
        return self._update_field_helper(fields_list=[self.DOWNLOADED_FLAG], save=save)

    def mark_as_emailed(self, save: bool = True):
        self.emailed = True
        return self._update_field_helper(fields_list=[self.EMAILED_FLAG], save=save)
    
    def mark_as_generated(self, save: bool = True):
        self.generated = True
        self._update_field_helper(fields_list=[self.GENERATED_FLAG], save=save)
    
    def _update_field_helper(self, fields_list: list, save : bool = True):

        if not isinstance(fields_list, list):
            raise TypeError(f"Expected a list of fields but got {type(fields_list).__name__}")
        if not isinstance(save, bool):
            raise TypeError(f"Expected a bool object for save but got {type(save).__name__}")
        
        if save:
            self.save(update_fields=fields_list)
            return self
        return False
    
    @classmethod
    def _if_async_supported_async_bulk_create_or_use_sync_bulk_crate(cls, batch: list):
        async_supported = getattr(connections['default'], 'supports_async', False)
        if async_supported:
            import asyncio
            async def async_create():
                await RecoveryCode.objects.abulk_create(batch)  
            asyncio.run(async_create())
        else:
            RecoveryCode.objects.bulk_create(batch)

    @classmethod
    def create_recovery_batch(cls, user, days_to_expire: int = 0, batch_number: int = 10):
        """
        Creates a batch of recovery codes for a user, efficiently handling large batches.
        Uses async bulk_create if supported by the database.

        Returns a list of raw recovery codes.
        """

        if not isinstance(user, User):
            raise TypeError(f"Expected User instance, got {type(user).__name__}")
        if not isinstance(batch_number, int):
            raise TypeError(f"Expected int for batch_number, got {type(batch_number).__name__}")
        if days_to_expire and not isinstance(days_to_expire, int):
            raise TypeError(f"Expected int for days_to_expire, got {type(days_to_expire).__name__}")
        if days_to_expire and days_to_expire < 0:
            raise ValueError("daysToExpiry must be a positive integer")

        raw_codes = []
        batch     = []
       
        CHUNK_SIZE = 50

         # Everything inside here is atomic
         # this means that if creating one model fails it won't create the other
         # Since the RecoveryCodeBatch and RecoveryCode models must be created.
         # if one fails The changes will be rolled back
        with transaction.atomic(): 
        
            batch_instance = cls(user=user, number_issued=batch_number)
            if days_to_expire:
                batch_instance.expiry_date = schedule_future_date(days=days_to_expire)
            batch_instance.mark_as_generated()

            cls._deactivate_all_batches_except_current(batch_instance)

            for _ in range(batch_number):
                raw_code = generate_2fa_secure_recovery_code()
                recovery_code = RecoveryCode(user=user, batch=batch_instance)
                recovery_code.hash_raw_code(raw_code)
                if days_to_expire:
                    recovery_code.days_to_expire = days_to_expire

                raw_codes.append(["unused", raw_code])
                batch.append(recovery_code)

                if len(batch) >= CHUNK_SIZE:
                    cls._if_async_supported_async_bulk_create_or_use_sync_bulk_crate(batch)
                    batch.clear()

            # Insert any remaining codes
            if batch:
                cls._if_async_supported_async_bulk_create_or_use_sync_bulk_crate(batch)

            return raw_codes, batch_instance
        
    @classmethod
    def delete_recovery_batch(cls, user: "User"):
        """
        Marks all active recovery codes for the user's batch(es) as pending delete.
        Returns True if at least one batch was updated, False otherwise.

        Parameters:
        user (User): The user associated with the recovery codes.

        Notes:
            This does not delete the recovery codes immediately.
            They are marked for deletion and will be removed in batches
            by a background task handled by django-q if needed.
        """
        
        try:
          
            recovery_batch = (
                cls.objects
                .select_related('user')  
                .prefetch_related('recovery_codes')   
                .get(user=user, status=Status.ACTIVE)
            )
        except cls.DoesNotExist:
            return False

        # Wrap in a transaction to ensure consistency and only update if both models
        # are saved
        with transaction.atomic():

            # Update all related recovery codes
            recovery_batch.recovery_codes.update(status=Status.PENDING_DELETE)

            # Update the batch itself
            recovery_batch.status = Status.PENDING_DELETE
            recovery_batch.deleted_at = timezone.now()
            recovery_batch.deleted_by = user
            recovery_batch.number_removed = recovery_batch.recovery_codes.count()
            recovery_batch.save()


            # log the action
            RecoveryCodeAudit.log_action(user, 
                                         RecoveryCodeAudit.Action.DELETED,
                                         deleted_by=user,
                                         batch=recovery_batch
                                         )
                                                
        return recovery_batch
    
    @classmethod
    def get_by_user(cls, user, status=Status.ACTIVE):
        try:
            return cls.objects.get(user=user, status=status)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def _deactivate_all_batches_except_current(cls, current_batch):
        """
        Deactivates all active batches for the given user except the current one.
        """
        if not isinstance(current_batch, cls):
            raise TypeError(
                f"Expected a {cls.__name__} instance, got {type(current_batch).__name__}"
            )

        cls.objects.filter(
            user=current_batch.user, 
            status=Status.ACTIVE
        ).exclude(id=current_batch.id).update(status=Status.PENDING_DELETE)


class RecoveryCode(models.Model):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)
    hash_code         = models.CharField(max_length=128, db_index=True, null=False, editable=False)
    look_up_hash      = models.CharField(max_length=128, unique=True, db_index=True, blank=True, editable=False)
    mark_for_deletion = models.BooleanField(default=False, db_index=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    modified_at       = models.DateTimeField(auto_now=True)
    status            = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE, db_index=True)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_codes")
    batch             = models.ForeignKey(RecoveryCodesBatch, on_delete=models.CASCADE, related_name="recovery_codes")
    automatic_removal = models.BooleanField(default=True)
    days_to_expire    = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_used           = models.BooleanField(default=False)
    is_deactivated    = models.BooleanField(default=False)
    deleted_at        = models.DateTimeField(blank=True, null=True)
    deleted_by        = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_code", null=True, blank=True)
    
     # constant field
    STATUS_FIELD             = "status"
    MARK_FOR_DELETION_FIELD  = "mark_for_deletion"
    MODIFIED_AT_FIELD        = "modified_at"
    DELETED_AT_FIELD         = "deleted_at"
    DELETED_BY_FIELD         = "deleted_by"
    IS_DEACTIVATED_FIELD     = "is_deactivated"
    USER_FIELD               = "user"

    class Meta:
        indexes = [
            models.Index(fields=["user", "look_up_hash"], name="user_lookup_idx"),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'look_up_hash'],
                name='unique_user_lookup_hash'
            )
        ]
       

    def __str__(self):
        """Returns a string representation of the class"""

        email = self.user.email
        return f"{email}" if self.user.email else self.id
  
    def mark_code_for_deletion(self, save: bool = True):
        """
        Marks this recovery code for deletion.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.mark_code_for_deletion()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.mark_code_for_deletion(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """
        self.mark_for_deletion = True
        if save:
            self.save(update_fields=["mark_for_deletion"])
        return True

    def invalidate_code(self, save: bool = True):
        """
        Marks this recovery code as in-active.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later. Note if a code
        is set to invalid it is not deleted and can be re-activated. However, if
        the code has been in-active for x-amount of days then it will be 
        automatically deleted. The days to be deleted is determined by the
        flags in the settings.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.invalidate_code()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.invalidate_code(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """
        self.status          = Status.INVALIDATE
        self.is_deactivated  = True
        self.deleted_by      = self.user
        self.deleted_at      = timezone.now()
        self.user            = self.user

        RecoveryCodeAudit.log_action(user=self.user, deleted_by=self.deleted_by, batch=self)
        if save:
            self.save(update_fields=[self.STATUS_FIELD, 
                                     self.IS_DEACTIVATED_FIELD, 
                                     self.DELETED_BY_FIELD, 
                                     self.DELETED_AT_FIELD,
                                     self.USER_FIELD
                                     ])
        return True

    def delete_code(self, save: bool = True) -> "RecoveryCode":
        """
        Marks this recovery code pending to be deleed.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.delete_code()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.delete_code(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """

        self.status            = Status.PENDING_DELETE
        self.mark_for_deletion = True
        self.deleted_by        = self.user
        
        if save:
            self.save(update_fields=[self.STATUS_FIELD,
                                     self.MARK_FOR_DELETION_FIELD,
                                     self.MODIFIED_AT_FIELD,
                                     self.DELETED_AT_FIELD,
                                     self.DELETED_BY_FIELD
                                      ])
          
        
        RecoveryCodeAudit.log_action(user=self.user,
                                     action=RecoveryCodeAudit.Action.DELETED,
                                     batch=self.batch,
                                     deleted_by=self.user

                                     )
        return self

    def verify_recovery_code(self, plaintext_code: str) -> bool:
        """
        Verify a recovery code against its stored Django-hashed value.

        Workflow:
        1. Lookup hash (deterministic HMAC) is used for efficient DB queries.
        This narrows down the candidate code but is not secure on its own.

        2. check_password() is used on the Django-hashed code to securely verify
        the plaintext code entered by the user against their hash password stored
        on record.
        
        Django hashing includes:
        - Salt (randomized per code)
        - Multiple iterations
        - Resistance to brute-force and rainbow attacks

        Parameters
        ----------
        code : str
            The plaintext recovery code entered by the user.

        Returns
        -------
        bool
            True if the code matches the stored hash, False otherwise.

        Notes
        -----
        - Even if the candidate was retrieved using lookup_hash, skipping check_password
        would weaken security. Both steps are necessary.
        """
        return check_password(plaintext_code, self.hash_code)

    @classmethod
    def get_by_code(cls, plaintext_code: str, user: User) -> RecoveryCode | None:
        """
        Retrieve a RecoveryCode instance for a user by plaintext code.

        Workflow:
        1. Compute a deterministic lookup hash (HMAC) for the code to perform a fast
        database query. This narrows down the candidate record but is NOT secure
        on its own.
        2. If a candidate is found, use Django's check_password() on the stored
        hashed code in the model used by `make_password` to verify the plaintext 
        code securely. Django hashing includes salt, multiple iterations, and 
        is resistant to brute-force and rainbow table attacks.

        Args:
            user (User): The user who owns the recovery code.
            code (str):  The plaintext recovery code entered by the user.

        Returns:

        RecoveryCode or None
            Returns the corresponding RecoveryCode instance if found and verified,
            otherwise None.

        Notes
        -----
        - Do NOT attempt to query the DB using make_password(code), as it generates
        a new salted hash every time and will never match the stored hash.

        - Using both lookup_hash (fast query) and check_password (secure verification)
        ensures both efficiency and security.

        - select_related('batch') is used for efficient fetching of the related batch.

        Example
        -------
        >>> recovery_code = RecoveryCode.get_by_code("ABCD-1234", user)
        >>> if recovery_code:
        >>>     print("Code verified!", recovery_code.batch)
        """
        if not isinstance(plaintext_code, str):
            raise ValueError(f"The code parameter is not a string. Expected a string but got an object with type {type(code)}")
        
        plaintext_code = plaintext_code.replace("-", "")
        lookup = make_lookup_hash(plaintext_code.strip())

        try:
            # Use lookup_hash to narrow down the correct recovery code.
            # Each user can have multiple codes, so filtering by user alone is insufficient.
            candidate = cls.objects.select_related("batch").get(user=user, look_up_hash=lookup)
        except cls.DoesNotExist:
            return None
        
        is_valid = candidate.verify_recovery_code(plaintext_code)
        return candidate if is_valid else None

    def hash_raw_code(self, code: str):
        """Hashes a plaintext recovery code and stores it securely in the instance.

        This method uses Django's `make_password` to generate a salted, cryptographically
        secure hash of the provided code. The result is stored in `self.hash_code` and
        can later be verified using `check_password`.

        Args:
            code (str): The plaintext recovery code to be hashed and stored.

        Raises:
            None

        Notes:
            - This method is only for storing or updating the hashed code.
            - Do NOT use this hashed value for database queries; `make_password` generates
            a new salted hash each time and will not match the stored hash.
            - For database lookups, use `make_lookup_hash` to find the candidate record,
            then verify using `check_password`.

        Examples:
            >>> recovery_code = RecoveryCode()
            >>> recovery_code.hash_raw_code("ABCD-1234")
            >>> recovery_code.save()
        """
        if code:
            code = code.replace("-", "").strip()
            self.look_up_hash = make_lookup_hash(code)
            self.hash_code = make_password(code)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()

        # ensure that is code is always saved as hash and never as a plaintext
        if self.hash_code and not is_already_hashed(self.hash_code):
            self.hash_code = self.hash_raw_code(self.hash_code)
        super().save(*args, **kwargs)




class RecoveryCodeAudit(models.Model):

    class Action(models.TextChoices):

        DELETED                   = "deleted", "Deleted"
        INVALIDATED               = "invalidated", "Invalidated"
        ALREADY_DELETED           = "already_deleted", "Already deleted"
        ALREADY_INVALIDATED       = "already_invalidated", "Already invalidated"
        INVALID_CODE              = "invalid_code", "Invalid code entered"
        BATCH_MARKED_FOR_DELETION = "batch_marked_for_deletion", "Batch marked for deletion"
        BATCH_PURGED              = "batch_purged", "Batch purged (async deletion)"

    action      = models.CharField(max_length=50, choices=Action)
    deleted_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_recovery_code_actions")
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    number_deleted = models.PositiveBigIntegerField(default=0)
    deleted_at  = models.DateTimeField(auto_now=True)
    batch       = models.ForeignKey("RecoveryCodesBatch", on_delete=models.SET_NULL, null=True, blank=True)
    timestamped = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @classmethod
    def log_action(cls, user, action, deleted_by, batch):
        """
        Logs an action for a recovery code.
        `action` should be one of RecoveryCodeAudit.Action constants.
        """
        if not isinstance(action, cls.Action):
            raise ValueError(f"Invalid action '{action}'. Use RecoveryCodeAudit.Action constants.")
        if user is not None and not isinstance(user, User):
            raise TypeError(f"The user is not an instance of the user model. Expected instance got type ({type(user).__name__})")
        if batch is not None and not isinstance(batch, RecoveryCodesBatch):
            raise TypeError(f"The recovery batch instance is not an instance of the Recovery code batch model."
                            f"Expected instance got type ({type(batch  ).__name__})")
        if deleted_by is not None and not isinstance(deleted_by, User):
            raise TypeError(f"The delete by is not an instance of the user model. Expected instance got type ({type(user).__name__})")
        cls.objects.create(user=user, action=action, deleted_by=deleted_by, batch=batch)

class RecoveryCodeEmailLog(EmailBaseLog):
    pass