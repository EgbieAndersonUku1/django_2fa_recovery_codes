from __future__ import annotations 

import logging
import uuid

from datetime                    import datetime
from datetime                    import timedelta
from django.contrib.auth         import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.db                   import connections, models, transaction
from django.db.models            import F
from django.db.models.query      import QuerySet
from django.conf                 import settings
from django.utils                import timezone
from django_email_sender.models  import EmailBaseLog
from typing                      import Tuple

from django_auth_recovery_codes.app_settings import default_max_login_attempts
from django_auth_recovery_codes.base_models import (
    AbstractBaseModel,
    AbstractCleanUpScheduler,
    AbstractCooldownPeriod,
    flush_cache_and_write_attempts_to_db,
)
from django_auth_recovery_codes.enums import (
    BackendConfigStatus,
    CreatedStatus,
    SetupCompleteStatus,
    TestSetupStatus,
    UsageStatus,
    ValidityStatus,
)
from django_auth_recovery_codes.loggers.loggers import default_logger, purge_code_logger
from django_auth_recovery_codes.utils.cache.safe_cache import (
    delete_cache_with_retry,
    get_cache_with_retry,
    set_cache_with_retry,
)
from django_auth_recovery_codes.utils.cooldown_period import RecoveryCooldownManager
from django_auth_recovery_codes.utils.security.generator import generate_2fa_secure_recovery_code
from django_auth_recovery_codes.utils.security.hash import is_already_hashed, make_lookup_hash
from django_auth_recovery_codes.utils.utils import (
    create_json_from_attrs,
    create_unique_string,
    schedule_future_date,
)

from .utils.attempt_guard import AttemptGuard

User   = get_user_model()
logger = logging.getLogger("auth_recovery_codes")


MULTIPLIER                  = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER", 2)
CUTOFF                      = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT", 3600)
CAN_GENERATE_CODE_CACHE_KEY = "can_generate_code:{}"
CAN_LOGIN_CACHE_KEY         = "can_login_{}"


cooldown_manager = RecoveryCooldownManager(multiplier=MULTIPLIER, cutoff=CUTOFF, logger=default_logger)



class RecoveryCodeSetup(AbstractBaseModel):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='code_setup')
    verified_at = models.DateTimeField(auto_now_add=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    success     = models.BooleanField(default=False)

    def mark_as_verified(self):
        """Marks the setup as verified (success=True)."""
        self.success = True
        self.save()

    def is_setup(self):
        """Returns True if the setup is verified."""
        return self.success

    @classmethod
    def create_for_user(cls, user: User):
        """
        Explicitly creates a setup for a user.
        Returns the new instance.
        """
        instance = cls.objects.create(user=user)
        return instance
    
    @classmethod
    def has_first_time_setup_occurred(cls, user: User):
        """
        Check if the user has completed the first-time setup.

        Args:
            user (User): The user instance to check.

        Returns:
            bool: True if the user has at least one RecoveryCode with success=True, False otherwise.

        Example:
            >>> RecoveryCode.has_first_time_setup_occurred(user)
            True
        """       
        cls.is_user_valid(user)
        return cls.objects.filter(user=user, success=True).exists()



class RecoveryCodeAudit(models.Model):
    """
    Audit log for tracking actions performed on recovery codes.

    This model records every significant action taken on recovery codes, 
    including deletions, invalidations, and batch operations. Each entry 
    captures who performed the action, who the action was performed on, 
    and contextual information such as batch references, counts, and reasons.

    """
    class Action(models.TextChoices):
        DELETED                   = "deleted", "Deleted"
        INVALIDATED               = "invalidated", "Invalidated"
        ALREADY_DELETED           = "already_deleted", "Already deleted"
        ALREADY_INVALIDATED       = "already_invalidated", "Already invalidated"
        INVALID_CODE              = "invalid_code", "Invalid code entered"
        BATCH_MARKED_FOR_DELETION = "batch_marked_for_deletion", "Batch marked for deletion"
        BATCH_PURGED              = "batch_purged", "Batch purged (async deletion)"

    action         = models.CharField(max_length=50, choices=Action)
    deleted_by     = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True,  related_name="performed_recovery_code_actions")
    user_issued_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="recovery_code_audits")
    batch          = models.ForeignKey("RecoveryCodesBatch", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    number_deleted = models.PositiveSmallIntegerField(default=0)
    number_issued  = models.PositiveSmallIntegerField(default=0)
    reason         = models.TextField(blank=True, null=True)
    timestamp      = models.DateTimeField(auto_now_add=True)   
    updated_at     = models.DateTimeField(auto_now=True)     

    class Meta:
        indexes = [
            models.Index(fields=["-timestamp"], name="recoverycodeaudit_ts_idx"),
            models.Index(fields=["action"], name="recoverycodeaudit_action_idx"),
            models.Index(fields=["user_issued_to"], name="recoverycodeaudit_user_idx"),
            models.Index(fields=["batch"], name="recoverycodeaudit_batch_idx"),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        """Render a string representation of the model"""
        return f"{self.get_action_display()} for {self.user_issued_to or 'Unknown User'} at {self.timestamp:%Y-%m-%d %H:%M:%S}"

    @classmethod
    def log_action(cls, user_issued_to=None, action=None, deleted_by=None, batch=None, number_deleted=0, number_issued=0, reason=None):
        """
        Create a new RecoveryCodeAudit entry to log an action performed on recovery codes.

        This method validates input parameters and records a new audit log entry,
        including the action type, the user affected, the user performing the action,
        any related batch, and optional counts and reason.

        Args:
            user_issued_to (User, optional): The user to whom the recovery code was issued.
            action (RecoveryCodeAudit.Action): The action performed. Must be one of the RecoveryCodeAudit.Action choices.
            deleted_by (User, optional): The user who performed the action. Can be None if the action was automatic.
            batch (RecoveryCodesBatch, optional): The batch related to the action, if any.
            number_deleted (int, optional): Number of recovery codes deleted. Defaults to 0.
            number_issued (int, optional): Number of recovery codes issued. Defaults to 0.
            reason (str, optional): Optional explanation or context for the action.

        Raises:
            ValueError: If `action` is not provided or not a valid RecoveryCodeAudit.Action.
            TypeError: If `user_issued_to`, `deleted_by`, or `batch` are not model instances or None.

        Returns:
            RecoveryCodeAudit: The newly created audit log entry.
        """
    
        if action is None:
            raise ValueError("Action is required.")

        if not isinstance(action, cls.Action):
            raise ValueError(f"Invalid action '{action}'. Use RecoveryCodeAudit.Action constants.")

        if user_issued_to is not None and not isinstance(user_issued_to, models.Model):
            raise TypeError(f"user_issued_to must be a User instance or None. Expect instance but got {type(user_issued_to).__name__}")

        if deleted_by is not None and not isinstance(deleted_by, models.Model):
            raise TypeError(f"deleted_by must be a User instance or None. Expect instance but got {type(deleted_by).__name__}")

        if batch is not None and not isinstance(batch, models.Model):
            raise TypeError(f"batch must be a RecoveryCodesBatch instance or None. Expect instance but got {type(batch).__name__}")

        return cls.objects.create(
            user_issued_to=user_issued_to,
            action=action,
            deleted_by=deleted_by,
            batch=batch,
            number_deleted=number_deleted,
            number_issued=number_issued,
            reason=reason,
        )
    
    @classmethod
    def clean_up_audit_records(cls, retention_days = 0):
        """Delete RecoveryCodeAudit rows older than retention period, if configured."""

        if retention_days != 0 and retention_days and not isinstance(retention_days, int):
            raise TypeError(f"Expected the retention days to be int but got object with type ({type(retention_days).__name__})")
        
        if retention_days == 0:
            num_deleted, _ = cls.objects.all().delete()  
            return  True, num_deleted
        
        cut_of_date       = timezone.now() - timedelta(days=retention_days)
        old_recovery_audit_qs = cls.objects.filter(updated_at__lt=cut_of_date)

        if old_recovery_audit_qs:
            count = old_recovery_audit_qs.count()

            old_recovery_audit_qs.delete()
            return True, count
        return False, 0


class RecoveryCodePurgeHistory(models.Model):
    """Audit log for actions performed on recovery codes."""

    name                 = models.CharField(max_length=128, default="Recovery code purged history log")
    timestamp            = models.DateTimeField(auto_now_add=True)
    total_codes_purged   = models.PositiveIntegerField(default=0)
    total_batches_purged = models.PositiveIntegerField(default=0)
    retention_days       = models.PositiveIntegerField(default=30)

    class Meta:
        verbose_name         = "RecoveryCodePurgeHistory"
        verbose_name_plural  = "RecoveryCodePurgeHistories"

    def __str__(self):
        """Creates a string representation of the model"""
        return f"Purge on {self.timestamp}: {self.total_codes_purged} codes from {self.total_batches_purged} batches"
    

class Status(models.TextChoices):
    """Choices representing the status of a recovery code."""

    ACTIVE         = "a", "Active"
    INVALIDATE     = "i", "Invalidate"
    PENDING_DELETE = "p", "Pending Delete"


class RecoveryCodeCleanUpScheduler(AbstractCleanUpScheduler):
    """Schedules cleanup tasks for expired recovery codes, including bulk deletion and empty batch removal."""

    name               = models.CharField(max_length=180, default=create_unique_string("Purge Expired Recovery Codes"), unique=True)
    bulk_delete        = models.BooleanField(default=True)
    delete_empty_batch = models.BooleanField(default=True)
    next_run           = models.DateTimeField(blank=True, null=True)
    deleted_count      = models.PositiveIntegerField(default=0, editable=False)
  
    
class RecoveryCodeAuditScheduler(AbstractCleanUpScheduler):
     DEFAULT_NAME = "Clean up recovery codes audit"
     name         = models.CharField(max_length=180, default=create_unique_string("Remove Recovery code audit"), unique=True)


class RecoveryCodesBatch(AbstractCooldownPeriod, AbstractBaseModel):
    """Schedules cleanup tasks for recovery code audit logs."""

    CACHE_KEYS = ["generated", "downloaded", "emailed", "viewed", "number_used"]
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
    status             = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE, db_index=True)
    automatic_removal  = models.BooleanField(default=True)
    expiry_date        = models.DateTimeField(blank=True, null=True, db_index=True)
    deleted_at         = models.DateTimeField(null=True, blank=True)
    deleted_by         = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="deleted_batches")
    requested_attempt  = models.PositiveSmallIntegerField(default=0)

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
    REQUEST_ATTEMPT_FIELD    = "requested_attempt"
    NUMBER_USED_FIELD        = "number_used"

    # constant flags
    VIEWED_FLAG              = "viewed"
    DOWNLOADED_FLAG          = "downloaded"
    EMAILED_FLAG             = "emailed"
    GENERATED_FLAG           = "generated"
    
    class Meta:
        ordering             = ["-created_at"]
        verbose_name         = "RecoveryCodesBatch"
        verbose_name_plural  = "RecoveryCodeBatches"

    def __str__(self):
        """A string representation of the model"""

        return f"Batch {self.id} for {self.user or 'Deleted User'}"
       
    @classmethod
    def can_generate_new_code(cls, user: User) -> tuple[bool, int]:
        """
        Decide if the user can generate a new recovery code.

        Returns:
            (bool, int):
                - bool: True if allowed, False otherwise
                - int:  Remaining cooldown (0 if allowed)

        ⚠️ Note:

        This method may *look simple*, but it orchestrates a mini-engine done with AttemptGuard class:

        - checks the cache
        - increments attempts
        - updates TTLs with progressive back-off
        - may write to the DB if necessary otherwise cache is used avoiding hiting the db

        Helpers used to navigate the mini-engine:
        -  update_cooldown
        - _start_recovery_cooldown
        - flush_cache_and_write_attempts_to_db

        Without the helper functions the can_generate_new_code` is doing:

        - Checking cache
        - Reading TTL
        - Multiplying cooldown
        - Incrementing DB field
        - Setting cache keys

        That’s a lot of moving parts hidden behind a simple-sounding method name.
        By pulling those steps into helpers it enables `can_generate_new_code` to 
        stay true to its name (returns yes/no + wait time) because it delegates 
        the heavy lifting to the functions 

        Example usage:

        >>> user = User.objects.get(username="eu") # assume that you already have a user model
        >>> can_generate_new_codes = Recovery.can_generate_new_code(user)
        >>> True
        >>>
        """
        attempt_guard = AttemptGuard[RecoveryCodesBatch](instance=cls, instance_attempt_field_name=cls.REQUEST_ATTEMPT_FIELD)
        return attempt_guard.can_proceed(user=user, action="recovery_code")
    
    def _get_expired_recovery_codes_qs(self, retention_days: int = None) -> QuerySet[RecoveryCode]:
        """
        Return a queryset of recovery codes eligible for automatic removal with two extra conditions.

        The queryset returned is filtered based on two conditions:

        1. If `retention_days` is None or less than 0, the queryset returns all codes
        that are invalidated or marked for deletion, regardless of age.

        2. If `retention_days` is a positive number, only codes older than or equal to the
        retention period are returned.

        Example:
        If a code is marked for deletion or invalidation on 30th August 2025 and
        `retention_days` is set to 30, the code will not be returned before 29th September 2025.

        Args:
            retention_days (int): The number of days for the codes to stay in the database
                                  before it is removed
        
        Raises:
            TypeError: Raised if the retention days is not an integer. Note an error is not
            raised if the number is a negative number since the method assumes that the 
            user wants all expired codes regrdless of age.

        Returns:
        QuerySet[RecoveryCode]: The filtered recovery codes queryset.

        """

        if retention_days is not None and not isinstance(retention_days, int):
            raise TypeError(f"Expected a int for retention_days parameter but got object with type f{type(retention_days).__name__}")
        
        qs = self.recovery_codes.filter(
            automatic_removal=True,
            status__in=self.terminal_statuses()
        )
        if retention_days > 0:
            qs = qs.filter(modified_at__lt=self.get_expiry_threshold(retention_days))
        return qs
 
    def _bulk_delete_expired_codes_by_scheduler_helper(self, expired_codes: RecoveryCodesBatch, batch_size : int= None, retention_days: int = None):
        """
        Delete expired recovery codes in bulk, with optional batching and throttling.

        This method is designed for use by a scheduler or background worker.

        It deletes expired recovery codes in batches until either all are removed
        or an optional maximum per run is reached. This makes it safe for both
        small deployments and large, high-traffic systems.

        Behaviour can be controlled via Django settings:

            RECOVERY_CODES_BATCH_SIZE (int, optional):
                Number of codes deleted in each database operation.
                Defaults to None (delete all at once).

            RECOVERY_CODES_MAX_DELETIONS_PER_RUN (int, optional):
                Maximum number of codes to delete in a single scheduler run.
                Defaults to -1 (delete all expired codes in one run).

        Args:
            expired_codes (QuerySet):
                Queryset of expired recovery codes for this batch.
            batch_size (int, optional):
                Number of codes to delete in one batch. Overrides the setting
                if provided. Defaults to None.
            retention_days (int, optional):
                Retention period used to refresh the queryset between batches.

        Returns:
            int: The total number of codes deleted during this run.

        Notes:
            - If ``batch_size`` is provided, deletion occurs in a loop,
            fetching IDs in chunks to avoid the SQL ``LIMIT/OFFSET`` restriction.

            - If ``DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN`` is set, deletion will stop
            once the threshold is reached, even if expired codes remain. 


            - An audit log entry is created after deletions complete.
        """
        max_deletions    = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN", None)
        number_to_delete = expired_codes.count()

        purge_code_logger.debug(f"Using bulk deleted mode. Batch {self.id} has {number_to_delete} to delete, Maximum delete flag cap {max_deletions}")
      
        deleted_count = 0
        if number_to_delete > 0:

            if batch_size and isinstance(batch_size, int):

                deleted_counts = []  # track individual deletion counts; avoids rebinding immutable integers on each increment which is more memory efficient
                                     # than deleted_count += deleted_count. Calls sum at the end to get the result

                while expired_codes.exists():

                    batch_ids = list(expired_codes.values_list('id', flat=True)[:batch_size])
                    if not batch_ids:
                        break

                    batch_deleted_count, _ = expired_codes.filter(id__in=batch_ids).delete()

                    if max_deletions != -1 and deleted_count >= max_deletions:
                        purge_code_logger.info(f"Reached max deletions ({max_deletions}) for this run.")
                        break
                    
                    expired_codes  = self._get_expired_recovery_codes_qs(retention_days)
                    deleted_counts.append(batch_deleted_count)

                deleted_count = sum(deleted_counts)

        
            RecoveryCodeAudit.log_action(
                    user_issued_to=self.user,
                    action=RecoveryCodeAudit.Action.BATCH_PURGED,
                    deleted_by=self.deleted_by,
                    batch=self,
                    number_deleted=deleted_count,
                    number_issued=self.number_issued,
                    reason="Batch of expired or invalidated codes removed by scheduler",
                )
        else:
            purge_code_logger.debug(f"There is nothing to delete in the batch. Batch has {number_to_delete} to delete")
        return deleted_count

    def purge_expired_codes(self, retention_days=1, delete_empty_batch = True, batch_size: int = 500):
        """
        Hard-delete recovery codes in this batch marked for deletion or invalidated,
        optionally logging per code or in bulk. Deletes batch if empty.

        Args:
        
            retention_days (int): Number of days to keep soft-deleted codes.
            batch_size (int): Allows the code to be deleted in smaller chunks instead all at once. 
                              This prevents a database lock if there are million of codes all deleting
                              at once.

                              The batch size comes from the `settings.DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE` flag
                              but it can be overriden by adding a value to this method.
        
        Returns:
            int: Number of codes deleted.
        """
       
        expired_codes = self._get_expired_recovery_codes_qs(retention_days)
      
        if not expired_codes.exists():
            purge_code_logger.info(f"No codes to purge for batch {self.id} at {timezone.now()}")
            return 0, True

        batch_size               = settings.DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE or batch_size
        deleted_count            = self._bulk_delete_expired_codes_by_scheduler_helper(expired_codes, batch_size = batch_size, retention_days = retention_days)
        active_codes_remaining   = (self.number_issued - deleted_count)
        is_empty                 = active_codes_remaining == 0

        purge_code_logger.debug(
                f"[Batch {self.id} Purge Summary]\n"
                f"  Number deleted   : {deleted_count}\n"
                f"  Number issued    : {self.number_issued}\n"
                f"  Codes remaining  : {active_codes_remaining}\n"
                f"  Is batch empty   : {is_empty}"
        )

        if delete_empty_batch and is_empty:
            purge_code_logger.info(f"Batch {self.id} is now empty and will be deleted at {timezone.now()}")
            self.delete()
        else:
            purge_code_logger.info(f"Batch {self.id} contains {active_codes_remaining} codes")

        return deleted_count, is_empty

    @staticmethod
    def get_expiry_threshold(days: int = 30) -> datetime:
        """
        Uses a days as a parameteer to calculate the datetime representing the 
        expiry threshold `days` ago from now.

        Args:
            days (int): Uses the days to calcuate the expiry threshold (days ago from now)

        Raises:
            Raises a valueError if days is not an int
        
        """
        if not (days, int):
            raise ValueError(f"Days must be an int. Expected an int got {type(int).__name__}")
        
        return timezone.now() - timedelta(days=days) 
    
    @staticmethod
    def terminal_statuses():
        """Statuses meaning the batch is no longer valid."""
        return [Status.PENDING_DELETE, Status.INVALIDATE]

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
 
    def update_used_code_count(self, save = False) -> "RecoveryCode":
        """
        Increment the count of used codes by 1.

        This method ensures consistent updates to the used code count.
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
            >>> recovery_code_batch.number_used += 1
            >>> recovery_code.save()

        However this can also introduce errors because anyone working in the views can introduce errors e.g
            >>> recovery_code.number_used += 2  # mistake
            >>> recovery_code.save()

        - Using this method prevents accidental mis-increments in views (e.g., adding 2 instead of 1).  
        - Encourages encapsulation of business logic in the model rather than in views.

        """
       
        self.number_used += 1
        
        # Increment counter safely (atomic by default)
        self._update_field_counter(self.NUMBER_USED_FIELD, save=save, atomic=True)
        return self
    
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
            json_cache["STATUS"]           = self.frontend_status
            json_cache["USERNAME"]         = self.user.username

            return json_cache
        return {}
    
    def reset_cache_values(self):
        """
        Resets all cache-related values to False.
        """
        for key in self.CACHE_KEYS:
            setattr(self, key, False)

    def mark_as_viewed(self, save : bool = True):
        """
        Mark the object as viewed and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean
        """
        self.viewed = True
        return self._update_field_helper(fields_list=[self.VIEWED_FLAG, self.MODIFIED_AT_FIELD], save=save)

    def mark_as_downloaded(self, save : bool = True):
        """
        Mark the object as downloaded and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean
        """
        self.downloaded = True
        return self._update_field_helper(fields_list=[self.DOWNLOADED_FLAG, self.MODIFIED_AT_FIELD], save=save)

    def mark_as_emailed(self, save: bool = True):
        """
         Mark the object as emailed and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean
        """
        self.emailed = True
        return self._update_field_helper(fields_list=[self.EMAILED_FLAG, self.MODIFIED_AT_FIELD], save=save)
    
    def mark_as_generated(self, save: bool = True):
        """
        Mark the object as generated and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean
        """
        self.generated = True
        self._update_field_helper(fields_list=[self.GENERATED_FLAG, self.MODIFIED_AT_FIELD], save=save)
    
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
    def _if_async_supported_async_bulk_create_or_use_sync_bulk_create(cls, batch: list):
        async_supported = getattr(connections['default'], 'supports_async', False)
        if async_supported:
            import asyncio
            async def async_create():
                await RecoveryCode.objects.abulk_create(batch)  
            asyncio.run(async_create())
        else:
            RecoveryCode.objects.bulk_create(batch)

    @classmethod
    def _ensure_setup_for_user(cls, user):
        """Ensures that RecoveryCodeSetup for a user is set, creating it if it doesn't exist."""

        recovery_code_setup = RecoveryCodeSetup.get_by_user(user)
        if recovery_code_setup is None:
            RecoveryCodeSetup.create_for_user(user)

    @classmethod
    def create_recovery_batch(cls, user, days_to_expire: int = 0, batch_number: int = 10):
        """
        Creates a batch of recovery codes for a user, efficiently handling large batches.
        Uses async bulk_create if supported by the database.

        Returns a list of raw recovery codes.
        """
        cls.is_user_valid(user)
        if not isinstance(batch_number, int):
            raise TypeError(f"Expected int for batch_number, got {type(batch_number).__name__}")
        if days_to_expire and not isinstance(days_to_expire, int):
            raise TypeError(f"Expected int for days_to_expire, got {type(days_to_expire).__name__}")
        if days_to_expire and days_to_expire < 0:
            raise ValueError("daysToExpiry must be a positive integer")

        cls._ensure_setup_for_user(user)

        raw_codes = []
        batch     = []
       
        CHUNK_SIZE = 50

         # Everything inside here is atomic
         # this means that if creating one model fails it won't create the other
         # Since the RecoveryCodeBatch and RecoveryCode models must be created, 
         # since it makes no sense for one to be created and not the other.
         # if one fails none is created and the changes are rolled back
        with transaction.atomic(): 
            
            batch_instance = cls(user=user, number_issued=batch_number)

            if days_to_expire:
                batch_instance.expiry_date = schedule_future_date(days=days_to_expire)
            batch_instance.last_attempt = timezone.now()
            batch_instance.mark_as_generated()

            cls._deactivate_all_batches_except_current(batch_instance)
            cache_key = CAN_GENERATE_CODE_CACHE_KEY.format(user.id)
            flush_cache_and_write_attempts_to_db(instance=batch_instance, field_name=cls.REQUEST_ATTEMPT_FIELD, cache_key=cache_key, logger=purge_code_logger)
          
            for _ in range(batch_number):
                raw_code = generate_2fa_secure_recovery_code()
                recovery_code = RecoveryCode(user=user, batch=batch_instance)
                recovery_code.hash_raw_code(raw_code)
                if days_to_expire:
                    recovery_code.days_to_expire = days_to_expire

                raw_codes.append(["unused", raw_code])
                batch.append(recovery_code)

                if len(batch) >= CHUNK_SIZE:
                    cls._if_async_supported_async_bulk_create_or_use_sync_bulk_create(batch)
                    batch.clear()

            # Insert any remaining codes
            if batch:
                cls._if_async_supported_async_bulk_create_or_use_sync_bulk_create(batch)

            return raw_codes, batch_instance
    
    @classmethod
    def verify_setup(cls, user: User, plaintext_code: str) -> dict:
        """
        One-time verification of a user's recovery code setup.

        Args:
            user: User instance
            plaintext_code: str, the recovery code to test

        Returns:
            dict: Status of verification, including success and other flags.
        """
      
        cls.is_user_valid(user)
        
        if not isinstance(plaintext_code, str):
            raise TypeError(f"Expected the plaintext code to be a string but got object with type {type(plaintext_code).__name__}")

        response_data = {
            "SUCCESS": True,
            "CREATED": CreatedStatus.NOT_CREATED.value,
            "BACKEND_CONFIGURATION": BackendConfigStatus.NOT_CONFIGURED.value,
            "SETUP_COMPLETE": SetupCompleteStatus.NOT_COMPLETE.value,
            "IS_VALID": ValidityStatus.INVALID.value,
            "USAGE": UsageStatus.FAILURE.value,
            "FAILURE": True,
        }

        recovery_code_setup = RecoveryCodeSetup.get_by_user(user)

        if recovery_code_setup is not None and recovery_code_setup.is_setup():
            response_data.update({
                "SUCCESS": True,
                "CREATED": CreatedStatus.ALREADY_CREATED.value,
                "BACKEND_CONFIGURATION": BackendConfigStatus.CONFIGURED.value,
                "SETUP_COMPLETE": SetupCompleteStatus.ALREADY_COMPLETE.value,
                "IS_VALID": ValidityStatus.VALID.value,
                "USAGE": UsageStatus.SUCCESS.value,
                "FAILURE": False,
            })
            return response_data

        recovery_code = RecoveryCode.get_by_code_and_user(plaintext_code, user) # returns only the object if plaintext code is valid

        logger.debug(f"The recovery code returned {recovery_code == None}")
        logger.debug("[VERIFY_SETUP] The recovery code returned %s", recovery_code)


        if not recovery_code:
            response_data.update({"SUCCESS": True})
            return response_data
        
        if recovery_code.batch.id:
            response_data.update({
                    "SUCCESS": True,
                    "CREATED": TestSetupStatus.CREATED.value,
                    "BACKEND_CONFIGURATION": TestSetupStatus.BACKEND_CONFIGURATION_SUCCESS.value,
                    "SETUP_COMPLETE": TestSetupStatus.SETUP_COMPLETE.value,
                    "IS_VALID": TestSetupStatus.VALIDATION_COMPLETE.value,
                    "USAGE": UsageStatus.SUCCESS.value,
                    "FAILURE": False,
                })

            # should be created when the batch is first created, however, if for
            # some reason, it wasn't createdin the batch, recreate it.
            if recovery_code_setup is None:
                recovery_code_setup = RecoveryCodeSetup.create_for_user(user)

            recovery_code_setup.mark_as_verified()
   
        return response_data

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
            # Update the batch itself
            recovery_batch.status         = Status.PENDING_DELETE
            recovery_batch.deleted_at     = timezone.now()
            recovery_batch.deleted_by     = user
            recovery_batch.number_removed = recovery_batch.number_issued

            recovery_batch.recovery_codes.update(status=Status.PENDING_DELETE, 
                                                 is_deactivated=True,
                                                 mark_for_deletion=True,
                                                 )
            recovery_batch.save()

            delete_cache_with_retry(CAN_GENERATE_CODE_CACHE_KEY.format(user.id))
        
            RecoveryCodeAudit.log_action(  user_issued_to=recovery_batch.user,
                                            action=RecoveryCodeAudit.Action.BATCH_PURGED,
                                            deleted_by=user,
                                            batch=recovery_batch,
                                            number_deleted=1,
                                            number_issued=recovery_batch.number_issued,
                                            reason="The entire batch is being deleted by the user",
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
            status=Status.ACTIVE,
        ).exclude(id=current_batch.id).update(status=Status.PENDING_DELETE)

        RecoveryCode.objects.filter(
                    user=current_batch.user,
                    status=Status.ACTIVE
                ).update(status=Status.PENDING_DELETE, mark_for_deletion=True, is_deactivated=True)

  


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
    IS_USED_FIELD            = "is_used"
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
  
    def mark_code_as_used(self, save: bool = True):
        """
        Marks the recovery code as used. Once the code has been marked for used 
        it can never be used again.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.mark_code_as_used()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.mark_code_as_used(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """
        self.is_used        = True
        self.status         = Status.PENDING_DELETE
        self.is_deactivated = True
        self.mark_code_for_deletion(save=False)
        self.batch.update_used_code_count()
      
        if save:
            self.save(update_fields=[self.MARK_FOR_DELETION_FIELD, 
                                     self.IS_USED_FIELD,
                                     self.MODIFIED_AT_FIELD,
                                     self.STATUS_FIELD, 
                                     self.IS_DEACTIVATED_FIELD,

                                     ])
        return True

    def mark_code_for_deletion(self, save: bool = True):
        """
        Marks the recovery code for deletion.

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
            self.save(update_fields=[self.MARK_FOR_DELETION_FIELD, self.MODIFIED_AT_FIELD])
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
        # set the various to the model, the save will then save it right away or defer it.
        self.status          = Status.INVALIDATE
        self.is_deactivated  = True
        self.deleted_by      = self.user
        self.deleted_at      = timezone.now()
       
        RecoveryCodeAudit.log_action(user_issued_to=self.user,
                                    action=RecoveryCodeAudit.Action.BATCH_PURGED,
                                    deleted_by=self.user,
                                    batch=self.batch,
                                    number_deleted=1,
                                    number_issued=self.batch.number_issued,
                                    reason="The code has been invalidated by the user",
                                     )
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
        self.is_deactivated    = True
        self.deleted_by        = self.user
        
        if save:
            self.save(update_fields=[self.STATUS_FIELD,
                                     self.MARK_FOR_DELETION_FIELD,
                                     self.IS_DEACTIVATED_FIELD,
                                     self.MODIFIED_AT_FIELD,
                                     self.DELETED_AT_FIELD,
                                     self.DELETED_BY_FIELD
                                      ])
          
        
        RecoveryCodeAudit.log_action( user_issued_to=self.user,
                                    action=RecoveryCodeAudit.Action.BATCH_PURGED,
                                    deleted_by=self.user,
                                    batch=self.batch,
                                    number_deleted=1,
                                    number_issued=self.batch.number_issued,
                                    reason="The code was deleted by the userr"

                                     )
        return self

    def _verify_recovery_code(self, plaintext_code: str) -> bool:
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
        return check_password(plaintext_code.strip(), self.hash_code)

    @classmethod
    def get_by_code_and_user(cls, plaintext_code: str, user: User) -> RecoveryCode | None:
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
        >>> recovery_code = RecoveryCode.get_by_code_and_user("ABCD-1234", user)
        >>> if recovery_code:
        >>>     print("Code verified!", recovery_code.batch)
        """
        if not isinstance(plaintext_code, str):
            raise ValueError(f"The code parameter is not a string. Expected a string but got an object with type {type(code)}")
        
        plaintext_code = plaintext_code.replace("-", "").strip()
        lookup = make_lookup_hash(plaintext_code.strip())

        try:
            # Use lookup_hash to narrow down the correct recovery code.
            # Each user can have multiple codes, so filtering by user alone is insufficient.
            candidate = cls.objects.select_related("batch").get(user=user, 
                                                                look_up_hash=lookup, 
                                                                is_used=False,
                                                                is_deactivated=False,
                                                                mark_for_deletion=False,
                                                                  )
        except cls.DoesNotExist:
            return None
        
        is_valid = candidate._verify_recovery_code(plaintext_code)
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




class RecoveryCodeEmailLog(EmailBaseLog):
    pass



class LoginRateLimterAudit(AbstractBaseModel):

    user           = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    modified_at    = models.DateTimeField(auto_now=True)
    login_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.user} with {self.login_attempts} login attempt"

    @classmethod
    def create_record_login_audit(cls, user: User, login_attempts: int):
        """"""
        cls.is_user_valid(user)
        if not cls.objects.filter(user=user).exists():
            cls.objects.get_or_create(user=user, login_attempts=login_attempts)


class LoginRateLimiter(AbstractCooldownPeriod, AbstractBaseModel):
    """
    Tracks failed login attempts and enforces cooldown periods.

    This model ensures a user cannot exceed a configurable number
    of failed login attempts before being locked out for a set
    duration.

    key Attributes fields:
        user (ForeignKey): The user associated with this limiter.
        login_attempts (int): Number of failed attempts.
        last_attempt (datetime): Timestamp of the last attempt.
        max_login_attemts(int): The maximum login attempts before lockout is initiated
       
    """
    user                     = models.OneToOneField(User, on_delete=models.CASCADE)
    login_attempts           = models.PositiveSmallIntegerField(default=0)
    max_login_attempts       = models.PositiveSmallIntegerField(default=default_max_login_attempts)
    created_at               = models.DateTimeField(auto_now_add=True)
    modified_at              = models.DateTimeField(auto_now=True)
    last_login_attempt       = models.DateTimeField(auto_now=True)

    # constant fields
    LOGIN_ATTEMPT_FIELD      = "login_attempts"
    MODIFIED_AT_FIELD        = "modified_at"
    LAST_ATTEMPT_FIELD       = "last_attempt"

    def __str__(self):
        return f"User {self.user}, login attempts {self.login_attempts}"

    def record_failed_attempt(self):
        """"""
        use_with_cache = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE", False)

        if use_with_cache:
            self._record_failed_attempts_using_cache_first()
        else:
            self._record_failed_attempts_db_only()
       
    
    def _record_failed_attempts_using_cache_first(self):
        """
        Increment failed attempts in cache. 

        Failed attempts are stored in cache to reduce database writes.
        The database is only updated when the user reaches the maximum
        number of allowed attempts (lockout) or when the cooldown expires.
        """

        self._increment_failed_login_attempt_count()
        self.last_attempt   = timezone.now()
        self.modified_at    = timezone.now()

        default_logger.debug(f"Getting cache for user={self.user}: failed_attempts={self.login_attempts} (max={self.max_login_attempts})")

        # only hit and save to the database once the failed attempts matches the maximum login attempts
        if self.login_attempts >= self.max_login_attempts:

            self.last_attempt   = timezone.now()
            self.modified_at    = timezone.now()

            default_logger.debug(f"Saving to database, user={self.user}: failed_attempts={self.login_attempts} (max={self.max_login_attempts})")
            self.save(update_fields=[self.LOGIN_ATTEMPT_FIELD, self.MODIFIED_AT_FIELD, self.LAST_ATTEMPT_FIELD])
     
    def _record_failed_attempts_db_only(self):
        """
        Record a failed attempt directly in the database.

        Increments the login attempt counter and persists changes
        immediately. This is the safest and most consistent mode,
        but under heavy traffic it may generate more database writes.

        Returns:
            None
        """
        self._increment_failed_login_attempt_count()
        self.save(update_fields=[self.LOGIN_ATTEMPT_FIELD, self.MODIFIED_AT_FIELD, self.LAST_ATTEMPT_FIELD])

    def _increment_failed_login_attempt_count(self):
        """
        A safe private method that Increment the login attempt by one.

        """
        self.login_attempts += 1 

    def reset_attempts(self):
        """Reset attempts (e.g. after successful login)."""

        self.login_attempts = 0
        self.save(update_fields=[self.LOGIN_ATTEMPT_FIELD, self.MODIFIED_AT_FIELD])

    @classmethod
    def is_locked_out(cls, user: User) -> Tuple[bool, int]:
        """
        A class method that determines whether a given user can log in or is 
        locked out.

        The method returns a tuple containing two values, a boolean to determine
        whether they can log in or not, and a wait time in seconds to determing how
        long they are locked out for. A wait time value of 0 means they are not locked
        out.

        Args:
            user (instance): The user instance to check

        Returns:
           Can login   : Returns a bool value of true and a wait time of 0
           Cannot login: Returns a bool value of false along with a wait time
        
        Examples:

        from my_app import User

        >>> user = User.objects.get(username="eu")
        >>> LoginRateLimiter.is_locked_out(user)  # assume can login
        (True, 0)

        >>> user = User.objects.get(username="eu")
        >>> LoginRateLimiter.is_locked_out(user)  # assume cannot login
        (False, 140)
        """

        HOUR_IN_SECONDS      = 3600
        cache_key            = f"login_rate_limiter_{user.id}"
        login_rate_limiter   = get_cache_with_retry(cache_key, default=None)
       
        if login_rate_limiter is None:
            login_rate_limiter = LoginRateLimiter.get_by_user(user)

            default_logger.debug(f"[DATBABASE_RETRIEVAL] Getting the value from the database using 'LoginRateLimiter.get_by_user()'")
            set_cache_with_retry(cache_key, value=login_rate_limiter, ttl=HOUR_IN_SECONDS)

        if login_rate_limiter.login_attempts < login_rate_limiter.max_login_attempts:
            login_rate_limiter.record_failed_attempt()
            set_cache_with_retry(cache_key, login_rate_limiter, ttl=HOUR_IN_SECONDS)
            return True, 0

        attempt_guard                = AttemptGuard[LoginRateLimiter](instance=cls, instance_attempt_field_name=cls.LOGIN_ATTEMPT_FIELD)
        is_not_locked_out, wait_time = attempt_guard.can_proceed(user=user, action="Login_rate_limiter")

        if not is_not_locked_out:
            return is_not_locked_out, wait_time   
        
        login_rate_limiter = LoginRateLimiter.get_by_user(user)
        LoginRateLimterAudit.create_record_login_audit(user=user, login_attempts=login_rate_limiter.login_attempts)    
        login_rate_limiter.reset_attempts()
        delete_cache_with_retry(cache_key)

        return is_not_locked_out, wait_time        

     
   