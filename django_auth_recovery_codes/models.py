from __future__ import annotations 

import logging
import uuid



from typing                      import Any, Optional, Self, Tuple
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


from django_auth_recovery_codes.models_choices import Status
from django_auth_recovery_codes.app_settings import default_max_login_attempts
from django_auth_recovery_codes.base_models import (
    AbstractBaseModel,
    AbstractCleanUpScheduler,
    AbstractCooldownPeriod,
    AbstractRecoveryCodesBatch,
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
from django_auth_recovery_codes.loggers.loggers        import default_logger, purge_code_logger
from django_auth_recovery_codes.utils.cache.safe_cache import (
    delete_cache_with_retry,
    get_cache_with_retry,
    set_cache_with_retry,
)
from django_auth_recovery_codes.utils.cooldown_period    import RecoveryCooldownManager
from django_auth_recovery_codes.utils.security.generator import generate_2fa_secure_recovery_code
from django_auth_recovery_codes.utils.security.hash      import is_already_hashed, make_lookup_hash
from django_auth_recovery_codes.utils.utils              import (
    create_json_from_attrs,
    create_unique_string,
    schedule_future_date,
)

from django_auth_recovery_codes.utils.attempt_guard          import AttemptGuard
from django_auth_recovery_codes.utils.errors.error_messages  import construct_raised_error_msg
from django_auth_recovery_codes.utils.errors.enforcer        import enforce_types
from django_auth_recovery_codes.loggers.loggers              import default_logger

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

    def __str__(self):
        return f"User has run first time setup: {self.success}"
    
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
        cls.is_user_valid(user)
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
    def log_action(
        cls,
        user_issued_to: Optional[User] = None,
        action: "RecoveryCodeAudit.Action" = None,
        deleted_by: Optional[User] = None,
        batch: Optional[RecoveryCodesBatch] = None,
        number_deleted: int = 0,
        number_issued: int = 0,
        reason: Optional[str] = None,
        ):
        """
        Create a new RecoveryCodeAudit entry to log an action performed on recovery codes.

        This method validates input parameters (via the decorator) and records
        a new audit log entry, including the action type, the user affected,
        the user performing the action, any related batch, and optional counts and reason.

        Args:
            user_issued_to (User | None): The user to whom the recovery code was issued.
            action (RecoveryCodeAudit.Action): The action performed. Must be one of the RecoveryCodeAudit.Action choices.
            deleted_by (User | None): The user who performed the action.
            batch (RecoveryCodesBatch | None): The batch related to the action, if any.
            number_deleted (int): Number of recovery codes deleted.
            number_issued (int): Number of recovery codes issued.
            reason (str | None): Optional explanation or context for the action.

        Raises:
            ValueError: If `action` is not provided.
            TypeError: Raised automatically by `enforce_types` if any argument is of the wrong type.

        Returns:
            RecoveryCodeAudit: The newly created audit log entry.
        """

        if action is None:
            raise ValueError("Action is required.")

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
    @enforce_types()
    def clean_up_audit_records(cls, retention_days: int = 0):
        """Delete RecoveryCodeAudit rows older than retention period, if configured."""

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




class RecoveryCodesBatchHistory(AbstractRecoveryCodesBatch):
    """
    Immutable audit log for recovery code batches.
    Unlike RecoveryCodesBatch, this is never deleted during cleanup.
    It provides a historical record for user-facing history and admin audits.
    """
    batch_id            = models.UUIDField()  
    deleted_by_username = models.CharField(max_length=60, blank=True)
    user                = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="recovery_batches_history")
    
    class Status(models.TextChoices):
        CREATE = "C", "CREATE"
        UPDATE = "U", "UPDATE"
        DELETE = "D", "DELETE"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recovery Code Batch History"
        verbose_name_plural = "Recovery Code Batch Histories"

    def __str__(self):
        """Returns a string representation of the class"""
        return f"History for batch {self.batch_id} (user={self.user})"
    
    
    @classmethod
    @enforce_types()
    def get_by_batch_id(cls, batch_id: uuid.UUID) -> Optional["cls"]:
        """
        Returns a batch record for the given batch_id.

        Args:
            batch_id (uuid.UUID): The UUID of the batch to retrieve.
        
        Returns:
            Optional[cls]: The batch record if found, else None.

        Raises:
            TypeError: If batch_id is not a uuid.UUID (enforced by @enforce_types).
        """
        try:
            return cls.objects.get(batch_id=batch_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def _create_batch_history(cls, batch: RecoveryCodesBatch):
        """
        Creates a new batch history record from a given RecoveryCodesBatch instance.

        Args:
            batch (RecoveryCodesBatch): The RecoveryCodesBatch object from which
                the history record will be created.

        Returns:
            cls: The newly created batch history model instance.
        
        Notes:
            - This method copies all relevant fields from the provided batch.
            - The method is intended for internal use (hence the leading underscore).
            
        """
        return  cls.objects.create(
                    batch_id=batch.id,
                    number_issued=batch.number_issued,
                    number_removed=batch.number_removed,
                    number_used=batch.number_used,
                    status=batch.status,
                    deleted_at=batch.deleted_at,
                    deleted_by=batch.deleted_by,
                    viewed=batch.viewed,
                    downloaded=batch.downloaded,
                    emailed=batch.emailed,
                    expiry_date=batch.expiry_date,
                    generated=batch.generated,
                    deleted_by_username=batch.user.username,
                    user=batch.user,
                    
            )
    
    @classmethod
    def _update_batch_history(cls, batch: RecoveryCodesBatch):
        """
        Updates an existing batch history record with data from a given RecoveryCodesBatch.

        Args:
            batch (RecoveryCodesBatch): The RecoveryCodesBatch instance containing
                updated information.

        Returns:
            None

        Notes:
            - This method looks up the existing batch history by `batch.id`.
            - If a matching record is found, all relevant fields are updated and saved.
            - If no matching record exists, nothing happens.
            - Intended for internal use (leading underscore).
            - Since the argument (batch) is passed into `get_by_batch_id` and the
              method checks the parameter using @enforce_types, there is no need
              to check if the batch is a valid instance again.
        """
        recovery_batch_history = cls.get_by_batch_id(batch.id)

        if recovery_batch_history:
            
            recovery_batch_history.number_issued       = batch.number_issued,
            recovery_batch_history.number_removed      = batch.number_removed,
            recovery_batch_history.number_used         = batch.number_used,
            recovery_batch_history.status              = batch.status,
            recovery_batch_history.deleted_at          = batch.deleted_at,
            recovery_batch_history.deleted_by          = batch.deleted_by,
            recovery_batch_history.viewed              = batch.viewed,
            recovery_batch_history.downloaded          = batch.downloaded,
            recovery_batch_history.emailed             = batch.emailed,
            recovery_batch_history.generated           = batch.generated
            recovery_batch_history.deleted_by_username = batch.user.username
            recovery_batch_history.user                = batch.user
            recovery_batch_history.save()

    @classmethod
    def log_action(cls, batch: RecoveryCodesBatch, action: str = Status.CREATE):
        """Logs an action (CREATE, UPDATE, or DELETE) in the batch history."""
        match action:
            case cls.Status.CREATE:
                return cls._create_batch_history(batch)
            case cls.Status.UPDATE:
                return cls._update_batch_history(batch)
            case _:
                default_logger.warning(f"Unknown action '{action}' for batch {batch.id}")
                return None

    @classmethod
    @enforce_types()
    def update_viewed(cls, batch: RecoveryCodesBatch):
        """
        Marks the given batch as viewed.

        Args:
            batch (RecoveryCodesBatch): The batch instance to update.

        Notes:
            - Updates the `VIEWED_FLAG` and `MODIFIED_AT_FIELD` using `_update_field`.
            - Intended for internal use; batch type is enforced by @enforce_types.
        """
        cls._update_field(batch, fields_list=[cls.VIEWED_FLAG, cls.MODIFIED_AT_FIELD], action_tag=cls.VIEWED_FLAG)


    @classmethod
    @enforce_types()
    def update_download(cls, batch: RecoveryCodesBatch):
        """
        Marks the given batch as downloaded.

        Args:
            batch (RecoveryCodesBatch): The batch instance to update.

        Notes:
            - Updates the `DOWNLOADED_FLAG` and `MODIFIED_AT_FIELD` using `_update_field`.
            - Intended for internal use; batch type is enforced by @enforce_types.
        """
        cls._update_field(batch, fields_list=[cls.DOWNLOADED_FLAG, cls.MODIFIED_AT_FIELD], action_tag=cls.DOWNLOADED_FLAG)

    @classmethod
    @enforce_types()
    def update_email(cls, batch: RecoveryCodesBatch):
        """
        Marks the given batch as emailed.

        Args:
            batch (RecoveryCodesBatch): The batch instance to update.

        Notes:
            - Updates the `EMAILED_FLAG` and `MODIFIED_AT_FIELD` using `_update_field`.
            - Intended for internal use; batch type is enforced by @enforce_types.
        """
        cls._update_field(batch, fields_list=[cls.EMAILED_FLAG, cls.MODIFIED_AT_FIELD], action_tag=cls.EMAILED_FLAG)

    @classmethod
    @enforce_types()
    def update_generated(cls, batch: RecoveryCodesBatch):
        """
        Marks the given batch as generated.

        Args:
            batch (RecoveryCodesBatch): The batch instance to update.

        Notes:
            - Updates the `GENERATED_FLAG` and `MODIFIED_AT_FIELD` using `_update_field`.
            - Intended for internal use; batch type is enforced by @enforce_types.
        """
        cls._update_field(batch, fields_list=[cls.GENERATED_FLAG, cls.MODIFIED_AT_FIELD], action_tag=cls.GENERATED_FLAG)

    @classmethod
    def _update_field(cls, batch: RecoveryCodesBatch, fields_list: list, action_tag: str):
        """
        Updates a specific flag on a batch history record and saves the specified fields.

        Args:
            batch (RecoveryCodesBatch): The batch instance whose history record is to be updated.
            fields_list (list): List of field names to update in the database.
            action_tag (str): The name of the boolean field to set to True.
                              Since the method is quite abstract it tells the 
                              RecoveryCodeBatchHistory which field to set.
                              Without this class would have no idea which field
                              to update.

        Returns:
            bool: True if the batch record was found and updated, False if no record exists.

        Notes:
            - Retrieves the batch history using `get_by_batch_id`.
            - Sets the `action_tag` attribute to True and saves only the fields in `fields_list`.
            - Intended for internal use (leading underscore).
            - The method assumes `batch` is a valid RecoveryCodesBatch instance; type checking can be
            handled externally if using @enforce_types.
        """
        batch  = cls.get_by_batch_id(batch.id)
       
        if batch:
            setattr(batch, action_tag, True)
            batch.save(update_fields=fields_list)
            return True 
        return False
    
        

class RecoveryCodesBatch(AbstractCooldownPeriod, AbstractRecoveryCodesBatch):
    """
    Represents a batch of recovery codes associated with a user.

    This model tracks the lifecycle of a recovery code batch, including 
    generation, download, email distribution, usage, and deletion. It also
    supports automatic removal of expired or deleted batches.

    """

    CACHE_KEYS = ["generated", "downloaded", "emailed", "viewed", "number_used"]
    JSON_KEYS  = ["id", "number_issued", "number_removed", "number_invalidated", "number_used", "created_at",
                  "modified_at", "expiry_date", "deleted_at", "deleted_by", "viewed", "downloaded",
                  "emailed", "generated", 
                  ]
    
    automatic_removal  = models.BooleanField(default=True)
    requested_attempt  = models.PositiveSmallIntegerField(default=0)
    user               = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="recovery_batches")

    # constant field
    STATUS_FIELD             = "status"
    MARK_FOR_DELETION_FIELD  = "mark_for_deletion"
    DELETED_AT_FIELD         = "deleted_at"
    DELETED_BY_FIELD         = "deleted_by"
    REQUEST_ATTEMPT_FIELD    = "requested_attempt"
    NUMBER_USED_FIELD        = "number_used"
    
    class Meta:
        ordering             = ["-created_at"]
        verbose_name         = "RecoveryCodesBatch"
        verbose_name_plural  = "RecoveryCodeBatches"

    def __str__(self):
        """A string representation of the model"""

        return f"Batch {self.id} for {self.user or 'Deleted User'}"

    @property
    def status_css_class(self):
        """
        Returns a CSS class string corresponding to the current status of the batch.

        Maps the batch's `status` field to a CSS class for frontend display.

        Returns:
            str: The CSS class representing the batch status. Defaults to "text-gray-500"
                if the status is unrecognized.

        Example:
            - Status.ACTIVE -> "text-green"
            - Status.INVALIDATE -> "text-red"
            - Status.PENDING_DELETE -> "text-yellow-600"
        """
        return {
            Status.ACTIVE: "text-green",
            Status.INVALIDATE: "text-red",
            Status.PENDING_DELETE: "text-yellow-600",
        }.get(self.status, "text-gray-500")
    
    @property
    def active_codes_remaining(self):
        """Returns the active code still remaining"""
        return self.number_issued - self.number_used   
        
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
        cls.is_user_valid(user)
        attempt_guard = AttemptGuard[RecoveryCodesBatch](instance=cls, instance_attempt_field_name=cls.REQUEST_ATTEMPT_FIELD)
        return attempt_guard.can_proceed(user=user, action="recovery_code")

    @enforce_types()
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
        
            TypeError: Raised by `enforce_types` if `retention_days` is not an int or None.


        Returns:
        QuerySet[RecoveryCode]: The filtered recovery codes queryset.

        """
        qs = self.recovery_codes.filter(
            automatic_removal=True,
            status__in=self.terminal_statuses()
        )
        if retention_days > 0:
            qs = qs.filter(modified_at__lt=self.get_expiry_threshold(retention_days))
        return qs

    def _bulk_delete_expired_codes_by_scheduler_helper(self, 
                                                       expired_codes: object,
                                                        batch_size : int= None, 
                                                        retention_days: int = None):
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

        if not isinstance(expired_codes, (RecoveryCodesBatch, QuerySet)):
            raise TypeError(
                construct_raised_error_msg("expired_codes", 
                                           expected_types=(RecoveryCodesBatch, QuerySet), 
                                           value=expired_codes)
                
            )

        max_deletions    = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN", None)
        number_to_delete = expired_codes.count()

        purge_code_logger.debug(f"Using bulk deleted mode. Batch {self.id} has {number_to_delete} to delete, Maximum delete flag cap {max_deletions}")
      
        deleted_count = 0
        if number_to_delete > 0:

            if batch_size and isinstance(batch_size, int):

                while expired_codes.exists():

                    batch_ids = list(expired_codes.values_list('id', flat=True)[:batch_size])
                    if not batch_ids:
                        break

                    batch_deleted_count, _ = expired_codes.filter(id__in=batch_ids).delete()
                    deleted_count += batch_deleted_count

                    if max_deletions != -1 and deleted_count >= max_deletions:
                        purge_code_logger.info(f"Reached max deletions ({max_deletions}) for this run.")
                        break
                    
                    expired_codes  = self._get_expired_recovery_codes_qs(retention_days)
                          
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

    @enforce_types()
    def purge_expired_codes(self, retention_days: int = 1, delete_empty_batch: bool = True, batch_size: int = 500):
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
       
        expired_codes      = self._get_expired_recovery_codes_qs(retention_days)
        batch_id           = self.id
        default_batch_size = 500

        if not expired_codes.exists():
            purge_code_logger.info(f"No codes to purge for batch {self.id} at {timezone.now()}")
            return 0, True

        if batch_size is None:
             batch_size  = settings.DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE or default_batch_size
             
        deleted_count            = self._bulk_delete_expired_codes_by_scheduler_helper(expired_codes, 
                                                                                       batch_size = batch_size, 
                                                                                       retention_days = retention_days)
        active_codes_remaining   = (self.number_issued - deleted_count)
        is_empty                 = active_codes_remaining == 0

        purge_code_logger.debug(
                f"[Batch {self.id} Purge Summary]\n"
                f"  Number deleted   : {deleted_count}\n"
                f"  Number issued    : {self.number_issued}\n"
                f"  Codes remaining  : {active_codes_remaining}\n"
                f"  Is batch empty   : {is_empty}"
                f"  Batch size       : {batch_size}"
        )

        if delete_empty_batch and is_empty:
            purge_code_logger.info(f"Batch {self.id} is now empty and will be deleted at {timezone.now()}")
            self.delete()
        else:
            purge_code_logger.info(f"Batch {self.id} contains {active_codes_remaining} codes")

        return deleted_count, is_empty, batch_id

    @staticmethod
    @enforce_types()
    def get_expiry_threshold(days: int = 30) -> datetime:
        """
        Uses a days as a parameteer to calculate the datetime representing the 
        expiry threshold `days` ago from now.

        Args:
            days (int): Uses the days to calcuate the expiry threshold (days ago from now)

        Raises:
            TypeError: Raised automatically by the `enforce_types` decorator
                if `fields_list` is not a list or `save` is not a boolean.
            
        """
        if not (days, int):
            raise ValueError(f"Days must be an int. Expected an int got {type(int).__name__}")
        
        return timezone.now() - timedelta(days=days) 
    
    @staticmethod
    def terminal_statuses():
        """Statuses meaning the batch is no longer valid."""
        return [Status.PENDING_DELETE, Status.INVALIDATE]

    def update_used_code_count(self, save = False) -> RecoveryCode:
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
    
    def update_invalidate_code_count(self, save = False) -> RecoveryCode:
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
    
    def update_delete_code_count(self, save: bool = False) -> RecoveryCode:
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
            If `save` is not a boolean enforce by the `update_field_counter`.

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
       
    @enforce_types()
    def _update_field_counter(self, field_name: str, save: bool = False, atomic: bool = True) -> RecoveryCodesBatch:
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

        Raises:
            TypeError: Raised automatically by the `enforce_types()` decorator
                if `fields_list` is not a list or `save` is not a boolean.

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
            RecoveryCodesBatchHistory.objects.filter(batch_id=self.id).update(**{field_name: F(field_name) + 1})
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
            TypeError if the save is not a boolean raised through the update_field_helper
        """
        self.viewed = True
        return self._update_field_helper(action_flag=self.VIEWED_FLAG, fields_list=[self.VIEWED_FLAG, self.MODIFIED_AT_FIELD], save=save)

    def mark_as_downloaded(self, save : bool = True):
        """
        Mark the object as downloaded and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean raised through the `_update_field_helper`
        """
        self.downloaded = True
        return self._update_field_helper(action_flag=self.DOWNLOADED_FLAG, fields_list=[self.DOWNLOADED_FLAG, self.MODIFIED_AT_FIELD], save=save)

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
        return self._update_field_helper(action_flag=self.EMAILED_FLAG, fields_list=[self.EMAILED_FLAG, self.MODIFIED_AT_FIELD], save=save)
    
    def mark_as_generated(self, save: bool = True):
        """
        Mark the object as generated and optionally save it.
        
        Takes a bool value of true which can be used to defer
        the save or to save it right away.

        Args:
           save (bool): Saves the value straight away if true or 
                         defers it for later
        Raises:
            TypeError if the save is not a boolean raised through the update_field_helper
        """
        self.generated = True
        self._update_field_helper(action_flag=self.GENERATED_FLAG, fields_list=[self.GENERATED_FLAG, self.MODIFIED_AT_FIELD], save=save)
    
    @enforce_types()
    def _update_field_helper(self, action_flag: str,  fields_list: list, save : bool = True) -> Any:
        """
        Update specified fields of the model instance and optionally save it.

        This helper method also updates the corresponding record history
        entry based on the provided action flag (e.g., viewed, downloaded).

        Args:
            action_flag (str): The name of the action flag indicating which
                record history update should be triggered.
            fields_list (list): A list of field names to update.
            save (bool, optional): Whether to save the instance after updating.
                Defaults to True.

        Returns:
            self | bool: Returns the updated instance if saved successfully,
            otherwise False.

        Raises:
            TypeError: Automatically raised by the `enforce_types()` decorator
                if `fields_list` or `save` have invalid types.

        Notes:
            This helper is intended for internal use and relies on the 
            `enforce_types()` decorator to perform runtime type checking.
        """
        if save:
            
            with transaction.atomic():
                self.save(update_fields=fields_list)

                match action_flag:
                    case self.VIEWED_FLAG:
                        RecoveryCodesBatchHistory.update_viewed(batch=self)
                    case self.DOWNLOADED_FLAG:
                        RecoveryCodesBatchHistory.update_download(batch=self)
                    case self.GENERATED_FLAG:
                        RecoveryCodesBatchHistory.update_generated(batch=self)
                    case self.EMAILED_FLAG:
                        RecoveryCodesBatchHistory.update_email(batch=self)

            return self
        return False
    
    @classmethod
    def _if_async_supported_async_bulk_create_or_use_sync_bulk_create(cls, batch: list):
        """
        Bulk-create RecoveryCode instances using asynchronous support if available,
        otherwise fallback to synchronous bulk creation.

        This method checks whether the current database connection supports async operations.
        If async is supported, it uses `RecoveryCode.objects.abulk_create` within an asyncio event loop.
        Otherwise, it falls back to `RecoveryCode.objects.bulk_create`.

        Args:
            batch (list): A list of `RecoveryCode` instances to be created in bulk.

        Raises:
            TypeError: Raised by the `enforce_types` decorator if `batch` is not a list.
        
        Notes:
            - This is an internal helper method intended for bulk operations.
            - Async creation is only attempted if the database backend supports it.
        """
        async_supported = getattr(connections['default'], 'supports_async', False)
        if async_supported:
            import asyncio
            async def async_create():
                await RecoveryCode.objects.abulk_create(batch)  
            asyncio.run(async_create())
        else:
            RecoveryCode.objects.bulk_create(batch)

    @classmethod
    def _ensure_setup_for_user(cls, user: User):
        """Ensures that RecoveryCodeSetup for a user is set, creating it if it doesn't exist."""
    
        recovery_code_setup = RecoveryCodeSetup.get_by_user(user)
        if recovery_code_setup is None:
            RecoveryCodeSetup.create_for_user(user)

    @classmethod
    @enforce_types()
    def create_recovery_batch(cls, user: User, days_to_expire: int = 0, batch_number: int = 10):
        """
        Creates a batch of recovery codes for a user, efficiently handling large batches.
        Uses async bulk_create if supported by the database.

        Returns a list of raw recovery codes.
        """

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

            RecoveryCodesBatchHistory.log_action(batch_instance, RecoveryCodesBatchHistory.Status.CREATE)

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
        response_data = {
                "SUCCESS": False,
                "CREATED": CreatedStatus.NOT_CREATED.value,
                "BACKEND_CONFIGURATION": BackendConfigStatus.NOT_CONFIGURED.value,
                "SETUP_COMPLETE": SetupCompleteStatus.NOT_COMPLETE.value,
                "IS_VALID": ValidityStatus.INVALID.value,
                "USAGE": UsageStatus.FAILURE.value,
                "FAILURE": False,
                "MESSAGE": "",
                "ERROR": "",
            }
        cls.is_user_valid(user)
        
        if not isinstance(plaintext_code, str):
            raise TypeError(construct_raised_error_msg("plaintext_code", expected_types=str, value=plaintext_code))
        
        response_data.update({
                "SUCCESS": True,
            })
        recovery_code_setup = RecoveryCodeSetup.get_by_user(user)

        if recovery_code_setup is not None and recovery_code_setup.is_setup():
            response_data.update({
                "SUCCESS": True,
                "CREATED": CreatedStatus.ALREADY_CREATED.value,
                "BACKEND_CONFIGURATION": BackendConfigStatus.ALREADY_CONFIGURED.value,
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
            

            with transaction.atomic():
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
        """
        Retrieve a single instance of the model for a given user and status.

        Args:
            user (User): The user associated with the model instance.
            status (Status, optional): The status to filter by. 
                Defaults to `Status.ACTIVE`.

        Returns:
            cls | None: The matching model instance if found, otherwise None.

        Raises:
            MultipleObjectsReturned: If more than one object matches the query.

        Notes:
            This is a convenience method that wraps `cls.objects.get(...)`.
            If no matching object exists, it returns None instead of raising
            a `DoesNotExist` exception.
        """
        try:
            return cls.objects.get(user=user, status=status)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    @enforce_types()
    def _deactivate_all_batches_except_current(cls, current_batch: RecoveryCodesBatch):
        """
        Deactivates all active batches for the given user except the current one.
        """
        with transaction.atomic():

            cls.objects.filter(
                user=current_batch.user,
                status=Status.ACTIVE,
            ).exclude(id=current_batch.id).update(status=Status.PENDING_DELETE)

            RecoveryCodesBatchHistory.objects.filter(
                user=current_batch.user,
                status=Status.ACTIVE
            ).exclude(batch_id=current_batch.id).update(status=Status.DELETED)

            RecoveryCode.objects.filter(
                user=current_batch.user,
                status=Status.ACTIVE
            ).update(
                status=Status.PENDING_DELETE,
                mark_for_deletion=True,
                is_deactivated=True
            ) 
       
  

class RecoveryCode(models.Model):
    """
    Represents a single recovery code associated with a user.

    Recovery codes are generated as part of the authentication and 
    account recovery process. Each code is stored securely as a hash 
    and linked to a user and a batch for organisational purposes.

    Key Fields:
        id (UUIDField): Unique identifier for the recovery code.
        hash_code (CharField): Hashed value of the recovery code. Indexed for fast lookups and never editable.
        look_up_hash (CharField): Secondary hash used for code lookup. Must be unique.
        mark_for_deletion (BooleanField): Indicates if the code has been flagged for removal in a cleanup process.
        created_at (DateTimeField): Timestamp when the code was created.
        modified_at (DateTimeField): Timestamp when the code was last updated.
        status (CharField): Current status of the recovery code (e.g., active, inactive).
        user (ForeignKey): The user who owns this recovery code.
        batch (ForeignKey): Reference to the batch this code belongs to, allowing grouped management.
        automatic_removal (BooleanField): Whether the code should be automatically removed once used or expired.
        days_to_expire (PositiveSmallIntegerField): Number of days before the code expires. Default is 0 (no expiration).
        is_used (BooleanField): Whether this code has already been used.
        is_deactivated (BooleanField): Whether the code has been manually deactivated.
        deleted_at (DateTimeField): When the code was deleted (if applicable).
        deleted_by (ForeignKey): Reference to the user who deleted the code (if it was deleted manually).
    """
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
    
    @enforce_types()
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
            with transaction.atomic():
                self.save(update_fields=[
                    self.MARK_FOR_DELETION_FIELD,
                    self.IS_USED_FIELD,
                    self.MODIFIED_AT_FIELD,
                    self.STATUS_FIELD,
                    self.IS_DEACTIVATED_FIELD,
                ])

              
          
        return True

    @enforce_types()
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
            with transaction.atomic():
                self.save(update_fields=[self.MARK_FOR_DELETION_FIELD, self.MODIFIED_AT_FIELD])
               
                                                            
        return True

    @enforce_types()
    def invalidate_code(self, save: bool = True) -> RecoveryCode:
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
        

        if save:
           
            with transaction.atomic():
                self.save(update_fields=[self.STATUS_FIELD, 
                                     self.IS_DEACTIVATED_FIELD, 
                                     self.DELETED_BY_FIELD, 
                                     self.DELETED_AT_FIELD,
                                     self.USER_FIELD
                                     ])
                
                RecoveryCodeAudit.log_action(user_issued_to=self.user,
                                            action=RecoveryCodeAudit.Action.BATCH_PURGED,
                                            deleted_by=self.user,
                                            batch=self.batch,
                                            number_deleted=1,
                                            number_issued=self.batch.number_issued,
                                            reason="The code has been invalidated by the user",
                                            )

          
        return True

    def delete_code(self, save: bool = True) -> RecoveryCode:
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
           
            with transaction.atomic():

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
              

        return True
    
    @enforce_types()
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
    @enforce_types()
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
        
        Raises:
            Raises an error if parameter has incorrect type.
            Raised through the decorators `enforce_types()`
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

        plaintext_code = plaintext_code.replace("-", "").strip()
        lookup         = make_lookup_hash(plaintext_code.strip())

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

    @enforce_types()
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
    """
    Stores logs of recovery code emails sent to users.

    This model records the user's email when they request a recovery code
    to be sent. Whether the log is saved in the database depends on the
    setting `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG`:
        - True: store the log in the database.
        - False: do not store the log.

    Inherits from:
        EmailBaseLog: Provides basic email logging functionality.
    """
    pass


class LoginRateLimterAudit(AbstractBaseModel):
    """
    Tracks and audits user login attempts for rate-limiting purposes.

    The `LoginRateLimiter` is a single record associated to a
    given user that logs the number of failed attempts. If the attempts
    are greater than max attempts they are locked out.

    However, once they are logged backed the `LoginRateLimiter`
    reset the attempts back to `0`, This class acts as an audit
    that records the attempt before it is wiped.

    This model can be used to monitor repeated failed login attempts 

    """

    user           = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    modified_at    = models.DateTimeField(auto_now=True)
    login_attempts = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        """A string representaton of the model"""
        return f"{self.user} with {self.login_attempts} login attempt(s)"

    @classmethod
    def create_record_login_audit(cls, user: User, login_attempts: int):
        """
        Create a login audit record for a user if none exists.

        This method checks if the given user already has an associated
        LoginRateLimterAudit record. If not, it creates one with the
        specified number of login attempts.

        Args:
            user (User): The user for whom to create the audit record.
            login_attempts (int): Initial number of login attempts to record.

        Raises:
            ValueError: If the user is invalid according to `cls.is_user_valid`.
        """
        cls.is_user_valid(user)
        if not cls.objects.filter(user=user).exists():
            return cls.objects.get_or_create(user=user, login_attempts=login_attempts)




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
        """A string representation of the model"""
        return f"User {self.user}, login attempts {self.login_attempts}"

    def record_failed_attempt(self):
        """
        Records a failed attempt to use a recovery code.

        The method chooses the storage mechanism based on the
        `DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE` setting:
            - If True, failed attempts are recorded using the cache first.
            - If False, failed attempts are recorded directly in the database.

        What this means?

        If the database is used all failed attempts are checked and pulled from
        the database, and if the cache is used computes the failed attempts within
        the cache first before going to the database.

        Notes:
            - Delegates to `_record_failed_attempts_using_cache_first` or
            `_record_failed_attempts_db_only` depending on configuration.
            `Record the failed attempts in a model for historical record
        """
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
    def _is_login_rate_limiter_valid(cls, login_rate_limiter: LoginRateLimiter)-> bool:
        """
        Validate whether the given object is a valid instance of the LoginRateLimiter class.

        Args:
            login_rate_limiter (LoginRateLimiter):
                The object to be validated.

        Returns:
            bool:
                True if the provided object is a valid instance of LoginRateLimiter.

        Raises:
            ValueError:
                If the provided object is not an instance of LoginRateLimiter.
        """
        if not isinstance(login_rate_limiter, cls):
            raise ValueError(f"The login_limiter is not an instance of LoginRateLimiter class." 
                             f"Expected a class instance got {type(LoginRateLimiter).__name__}")
        return True
    
    @classmethod
    def _get_login_rate_limiter(cls, user: User, cache_key: str, ttl = 3600) -> Self:
        """
        Takes a user object and returns the login rate limiter belong to the user

        Args:
            user (User): The user instance
        """
        cls.is_user_valid(user)
       
        cache_key            = f"login_rate_limiter_{user.id}"
        login_rate_limiter   = get_cache_with_retry(cache_key, default=None)
      
        if login_rate_limiter is None:
            login_rate_limiter = LoginRateLimiter.get_by_user_or_create(user)

            default_logger.debug(f"[DATBABASE_RETRIEVAL] Getting the value from the database using 'LoginRateLimiter.get_by_user()'")
            set_cache_with_retry(cache_key, value=login_rate_limiter, ttl=ttl)
    
        return login_rate_limiter

    @classmethod
    def _is_under_max_attempt(cls, login_rate_limiter: "LoginRateLimiter") -> bool:
        """
        Check whether the user has not yet exceeded the maximum allowed login attempts.

        Args:
            login_rate_limiter (LoginRateLimiter): 
                The rate limiter instance object that tracks the number of login attempts 
                and the maximum allowed attempts.

        Returns:
            bool: 
                True if the current login attempts are below the maximum allowed, 
                False otherwise.

        Raises:
            AttributeError: 
                If `login_rate_limiter` does not have the required attributes 
                (`login_attempts`, `max_login_attempts`).
        """
        if not login_rate_limiter:
            raise ValueError("Expected a login limiter got None")
        return login_rate_limiter.login_attempts < login_rate_limiter.max_login_attempts
        
  
    @classmethod
    def _check_temporary_lockout(cls, user: "User") -> Tuple[bool, int]:
        """
        Verify whether the user is currently under a temporary lockout due to failed login attempts.

        Args:
            user (User): 
                The user object whose login attempts are being validated.

        Returns:
            tuple:
                - bool: True if the user can attempt login, False if locked out.
                - int: Remaining wait time (in seconds) before login is allowed again.

        Raises:
            Exception:
                If the underlying `AttemptGuard` or its `can_proceed` method fails.
        """
        attempt_guard        = AttemptGuard[LoginRateLimiter](instance=cls, 
                                                              instance_attempt_field_name=cls.LOGIN_ATTEMPT_FIELD
                                                             )
        can_login, wait_time = attempt_guard.can_proceed(user=user, action="Login_rate_limiter")
        return can_login, wait_time

    @classmethod
    def _unlock_user(cls, login_rate_limiter: "LoginRateLimiter", user: "User", cache_key: str) -> Tuple[bool, int]:
        """
        Unlock a user by resetting their login attempts, creating an audit record, 
        and clearing any related cache entry.

        Args:
            login_rate_limiter (LoginRateLimiter): 
                The rate limiter object tracking login attempts.
            user (User): 
                The user being unlocked.
            cache_key (str): 
                The cache key used for storing login attempt state.

        Returns:
            tuple:
                - bool: Always True once unlock succeeds.
                - int: Always 0 (indicating no wait time after unlock).

        Raises:
            Exception:
                If resetting attempts, audit logging, or cache deletion fails.
        """
      
        LoginRateLimterAudit.create_record_login_audit(
            user=user, 
            login_attempts=login_rate_limiter.login_attempts
        )    
        
        login_rate_limiter.reset_attempts()
        delete_cache_with_retry(cache_key)
        return True, 0
    
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
        login_rate_limiter   = cls._get_login_rate_limiter(user, cache_key, HOUR_IN_SECONDS)

        if cls._is_under_max_attempt(login_rate_limiter):
            login_rate_limiter.record_failed_attempt()
            set_cache_with_retry(cache_key, login_rate_limiter, ttl=HOUR_IN_SECONDS)
            return True, 0

        can_login, wait_time = cls._check_temporary_lockout(user)
   
        if not can_login:
            return can_login, wait_time   
        
        return cls._unlock_user(login_rate_limiter, user, cache_key)

    @classmethod
    def has_login_rate_limiter(cls, user: User) -> bool:
        """
        Returns True if the user already has a login rate limiter, else False.
        """
        cls.is_user_valid(user)
        return cls.objects.filter(user=user).exists()
    
    @classmethod
    @enforce_types()
    def ensure_exists_or_create_and_cache(cls, user: User, cache_key: str, ttl: int = 86400) -> bool:
        """
        Ensure a LoginRateLimiter exists for a user, creating and caching it if necessary 
        to prevent repeated database queries on page refresh.

        This method creates a LoginRateLimiter for a user if one doesn't already exist,
        and caches a `True` value indicating it has been created. This avoids repeated
        database queries within the TTL and prevents unnecessary database checks.

        Why caching is necessary:

        In Django, a view function (or class-based view) is executed **every time
        a page is requested**. In simpler terms, you can think of a view as a page. 
        Without caching, even if a LoginRateLimiter already exists, the database would 
        be queried on every page load or refresh just to check its existence.

        Standard projects often create a User and a related Profile (or similar
        model) at the same time, either in the registration view or using a
        signal (`post_save` on User). In those cases, the related model is always
        available immediately after the user is created, and no extra checks are
        needed.

        This app, however, is designed as a reusable, plug-and-play component.
        We cannot assume control over user creation, nor can we create the
        LoginRateLimiter at the same time as the User. All we know is that the User 
        already exists, since you must be authenticated to use the app. The app may 
        be installed in a project without any custom signals or registration logic, 
        and we cannot force the user of the app to create a `LoginRateLimiter`.
        Therefore, the LoginRateLimiter must be created within
        the view context, but only **once**.

        The problem with creating it within a view (dashboard page) is that we 
        need to do a few things first:

        1. Check if it exists.
        2. If it doesn't exist, create it.

        This process is repeated every time the user refreshes the page. Even if step 2 
        is never executed because the limiter already exists, we still hit the database 
        on each refresh just to check existence, and this is where caching becomes crucial.

        The caching strategy works as follows:

            Cache Key: login_rate_limiter_user_<id>
            TTL: 24 hours (default)

            On page refresh:
                       |
                ┌──────────────────┐_
                │ Check cache      │
                └────────┬─────────┘
                         │ Exists -> skip DB, limiter already present
                        │
                        
                Cache missing -> Check database
                        │
            ┌──────────┴──────────┐
            │ Limiter exists?      │
            └───────┬─────────────┘
                    │ Yes -> do nothing, store True in cache
                    │ No  -> create limiter, store True in cache

        Args:
            user (User): The user to check.
            cache_key (str): Cache key for the login rate limiter.
            ttl (int): Time-to-live for the cache in seconds. Default is 24 hours.

        Returns:
            bool: True if a new limiter was created, False otherwise.

        Note:
            Without a LoginRateLimiter already available, the app will crash when
            the user tries to log in.
        """

        is_created = get_cache_with_retry(cache_key)  

        if not is_created: 
           cls._ensure_exists_or_create_helper(user, cache_key, ttl)
        else:
            default_logger.debug(f"Cache hit for user {user.email}, skipping DB check entirely")

    @classmethod
    def _ensure_exists_or_create_helper(cls, user: User, cache_key: str, ttl: int):
        """
        A helper method to help the `ensure_exists_or_create_and_cache` method create
        tbe cache and the LoginRateLimiter model. This advoids a nested if-statement
        inside the `ensure_exists_or_create_and_cache` method.

        Note the method is only intended to be used with `ensure_exists_or_create_and_cache`.
        
        Args:
            user (User): The user to check.
            cache_key (str): Cache key for the login rate limiter.
            ttl (int): Time-to-live for the cache in seconds. Default is 24 hours.

        Returns:
            bool: True if a new limiter was created, False otherwise.
        """
        default_logger.debug(f"Cache miss for user {user.email}, checking DB")

        if not LoginRateLimiter.has_login_rate_limiter(user):  
              
            login_rate_limiter = LoginRateLimiter.get_by_user_or_create(user)  
            set_cache_with_retry(cache_key, login_rate_limiter, ttl=ttl)  
            default_logger.debug(f"LoginRateLimiter created and cached for user {user.email}")
        else:
                
            default_logger.debug(f"Limiter exists in DB for user {user.email}, no creation needed")
        return True

    