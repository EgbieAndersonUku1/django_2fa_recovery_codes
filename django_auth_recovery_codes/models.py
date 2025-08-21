import uuid

from django.db import models, connections
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django_email_sender.models import EmailBaseLog

from django_auth_recovery_codes.utils.security.generator import generate_2fa_secure_recovery_code
from django_auth_recovery_codes.utils.security.security import is_already_hashed
from django_auth_recovery_codes.utils.utils import schedule_future_date


User = get_user_model()




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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, db_index=True)

    number_issued     = models.PositiveBigIntegerField()
    number_removed    = models.PositiveBigIntegerField(default=0)
    user              = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="recovery_batches")
    created_at        = models.DateTimeField(auto_now_add=True)
    modified_at       = models.DateTimeField(auto_now=True)
    status            = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE)
    automatic_removal = models.BooleanField(default=True)
    expiry_date       = models.DateTimeField(blank=True, null=True)
    deleted_at        = models.DateTimeField(null=True, blank=True)
    deleted_by        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_batches")

     # Action tracking
    viewed            = models.BooleanField(default=False)
    downloaded        = models.BooleanField(default=False)
    emailed           = models.BooleanField(default=False)
    generated         = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Batch {self.id} for {self.user or 'Deleted User'}"

    def mark_as_viewed(self, save : bool = True):
        self.viewed = True
        return self._update_field_helper(fields_list=['viewed'], save=save)

    def mark_downloaded(self, save : bool = True):
        self.downloaded = True
        return self._update_field_helper(fields_list=['downloaded'], save=save)

    def mark_emailed(self, save: bool = True):
        self.emailed = True
        return self._update_field_helper(fields_list=['emailed'], save=save)
    
    def mark_as_generated(self, save: bool = True):
        self.generated = True
        self._update_field_helper(fields_list=['generated'], save=save)
    
    def _update_field_helper(self, fields_list: list, save : bool = True):

        if not isinstance(fields_list, list):
            raise TypeError(f"Expected a list of fields but got {type(fields_list).__name__}")
        if not isinstance(save, bool):
            raise TypeError(f"Expected a bool object for save but got {type(save).__name__}")
        
        if save:
            self.save(update_fields=fields_list)
            return True 
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

        # Type validations
        if not isinstance(user, User):
            raise TypeError(f"Expected User instance, got {type(user).__name__}")
        if not isinstance(batch_number, int):
            raise TypeError(f"Expected int for batch_number, got {type(batch_number).__name__}")
        if days_to_expire and not isinstance(days_to_expire, int):
            raise TypeError(f"Expected int for days_to_expire, got {type(days_to_expire).__name__}")

        # Create batch instance
        batch_instance = cls(user=user, number_issued=batch_number)
        if days_to_expire:
            batch_instance.expiry_date = schedule_future_date(days=days_to_expire)
        batch_instance.mark_as_generated(save=False)
        batch_instance.save()

        raw_codes = []
        batch     = []
       
        CHUNK_SIZE = 50

        cls._deactivate_all_batches_except_current(batch_instance)

        for _ in range(batch_number):

            raw_code      = generate_2fa_secure_recovery_code()
            recovery_code = RecoveryCode(user=user, batch=batch_instance)
            recovery_code.hash_raw_code(raw_code)

            if days_to_expire:
                recovery_code.days_to_expire = days_to_expire

            # returns a list of list where each list is a row for a table and the elements
            # inside the rows are the cells or column for table. This allows the frontend
            # to easily render the table
            raw_codes.append(["unused", raw_code]) 
            batch.append(recovery_code)

            if len(batch) >= CHUNK_SIZE:
                cls._if_async_supported_async_bulk_create_or_use_sync_bulk_crate(batch)
                batch.clear()

        # Insert any remaining codes
        if batch:
            cls._if_async_supported_async_bulk_create_or_use_sync_bulk_crate(batch)
           
        return raw_codes


    @classmethod
    def delete_recovery_batch(cls, batch_id):
        """"""
        pass
    
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
    hash_code         = models.CharField(max_length=128, unique=True, db_index=True)
    mark_for_deletion = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)
    modified_at       = models.DateTimeField(auto_now=True)
    status            = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_codes")
    batch             = models.ForeignKey(RecoveryCodesBatch, on_delete=models.CASCADE, related_name="recovery_codes")
    automatic_removal = models.BooleanField(default=True)
    days_to_expire    = models.PositiveSmallIntegerField(default=0)
    code_downloaded   = models.BooleanField(default=False)
    code_emailed      = models.BooleanField(default=False)


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
        self.is_active = True
        if save:
            self.save(update_fields=["is_active"])
        return True

    @classmethod
    def get_by_code(cls, code: str) -> str:
        if not isinstance(code, str):
            raise ValueError(f"The code parameter is not a string. Expected a string but got an object with type {type(code)}")
        return make_password(code)
    
    def hash_raw_code(self, code: str):
        if code:
            self.hash_code = make_password(code)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()

        # ensure that is code is always saved as hash and never as a plaintext
        if self.hash_code and not is_already_hashed(self.hash_code):
            self.hash_code = make_password(self.hash_code)
        super().save(*args, **kwargs)



class RecoveryCodeEmailLog(EmailBaseLog):
    pass