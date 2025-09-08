import logging

from django.conf import settings
from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import LoggerType
from django.utils import timezone

from django_q.models import Task, Schedule
from django_auth_recovery_codes import notify_user
from django_auth_recovery_codes.models import (RecoveryCodePurgeHistory, 
                                               RecoveryCodesBatch, 
                                               RecoveryCodeAudit, 
                                               RecoveryCodeCleanUpScheduler,
                                               Status
                                               )

from django_auth_recovery_codes.app_settings import app_settings
from django_auth_recovery_codes.loggers.loggers import (email_logger,
                                                         purge_code_logger, 
                                                         audit_logger, 
                                                         purge_email_logger)





def send_recovery_codes_email(sender_email, user, codes, subject= "Your account recovery codes"):
    
    email_sender_logger = EmailSenderLogger.create()
    _store_user_email_log(email_sender_logger)

    try:
        ( 
            email_sender_logger
            .add_email_sender_instance(EmailSender.create()) 
            .start_logging_session()
            .config_logger(email_logger, log_level=LoggerType.INFO)
            .from_address(sender_email) 
            .to(user.username) 
            .with_context({"codes": codes, "username": user.username}) 
            .with_subject(subject) 
            .with_html_template("recovery_codes_email.html", "recovery_codes") 
            .with_text_template("recovery_codes_email.txt", "recovery_codes") 
            .send()
            )
        notify_user(user.id, "Recovery codes email sent successfully!")
  
    except Exception as e:
        email_logger.error(f"Failed to send recovery codes: {e}")
        notify_user(user.id, f"Failed to send recovery codes: {e}")

       

def purge_all_expired_batches(*args, **kwargs):
    """
    Scheduled task to purge all expired recovery codes.
    Uses kwargs to ensure all arguments reach the function reliably.
    """
    retention_days = kwargs.get("retention_days", settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS)

    bulk_delete        = kwargs.get("bulk_delete", True)
    log_per_code       = kwargs.get("log_per_code", False)
    use_with_logger    = kwargs.get("use_with_logger", settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER)
    delete_empty_batch = kwargs.get("delete_empty_batch", True)
    schedule_name      = kwargs.get("schedule_name")

    purge_code_logger.info(
        f"[RecoveryCodes] Starting purge job | retention_days={retention_days}, bulk_delete={bulk_delete}, "
        f"log_per_code={log_per_code}, delete_empty_batch={delete_empty_batch}, use_with_logger={use_with_logger}s, started_at={timezone.now()}",
    )

    total_batches = 0
    total_purged = 0
    total_skipped = 0
    purged_batches_info = []

    batches = RecoveryCodesBatch.objects.select_related("user").all()
    purge_code_logger.debug("[RecoveryCodes] Found %s batches to check", batches.count())

    for batch in batches:
        purged_count, is_empty = batch.purge_expired_codes(
            bulk_delete=bulk_delete,
            log_per_code=log_per_code,
            retention_days=retention_days,
            delete_empty_batch=delete_empty_batch,
        )

        if purged_count > 0:
            total_purged += purged_count
            total_batches += 1
            batch_report = _generate_purged_batch_code_json_report(batch, purged_count, is_empty)
            purged_batches_info.append(batch_report)

            purge_code_logger.info(f"[RecoveryCodes] Batch purged | user_id={batch.user.id}, batch_id={batch.id}, purged_count={purged_count}, is_empty={is_empty}")
        else:
            total_skipped += 1
            purge_code_logger.debug(
                "[RecoveryCodes] Batch skipped | user_id=%s, batch_id=%s, purged_count=%s",
                batch.user.id, batch.id, purged_count
            )

    RecoveryCodePurgeHistory.objects.create(
        total_codes_purged=total_purged,
        total_batches_purged=total_batches,
        retention_days=retention_days,
    )

    purge_code_logger.info(
        "[RecoveryCodes] Purge complete | total_batches_purged=%s, total_codes_purged=%s, "
        "total_batches_skipped=%s, finished_at=%s",
        total_batches, total_purged, total_skipped, timezone.now()
    )

    return {
        "reports": purged_batches_info,
        "use_with_logger": bool(use_with_logger),
        "schedule_name" : schedule_name,
    }



def clean_up_old_audits_task():  
    """Task to clean up old RecoveryCodeAudit records based on retention settings."""

    if not getattr(app_settings, "ENABLE_AUTO_CLEANUP", False):
        audit_logger.info("Auto cleanup disabled. Skipping cleanup task.")
        return

    retention_days = getattr(app_settings, "RETENTION_DAYS", 0)
    if retention_days == 0:
        audit_logger.info("Retention days set to 0. Nothing to delete.")
        return

    cleanup_method = getattr(RecoveryCodeAudit, "clean_up_audit_records", None)
    if not callable(cleanup_method):
        audit_logger.warning("Method 'clean_up_audit_records' not found on RecoveryCodeAudit. Cleanup skipped.")
        return

    deleted, count = cleanup_method(retention_days)
    if deleted:
        audit_logger.info(f"Cleanup task deleted old RecoveryCodeAudit records older than {retention_days} days.")
        audit_logger.info(f"Cleanup task deleted a total of {count} audit{'s' if count > 0 else ''}.")
    else:
        audit_logger.info("Cleanup task ran but no records needed deletion.")
    return deleted


def _generate_purged_batch_code_json_report(batch: RecoveryCodesBatch, purged_count: int, is_empty: bool) -> dict:
    """
    Creates a JSON report for a purged batch of 2FA recovery codes.

    Each batch contains recovery codes that may be active or expired.
    After purging, this function compiles a structured JSON report with
    details about the batch state and its metadata.

    JSON fields:
        "id": Batch ID.
        "number_issued": Total number of codes issued to the batch.
        "number_removed": Number of codes removed during purge.
        "is_batch_empty": Whether the batch is now empty.
        "number_used": Number of codes already used.
        "number_remaining_in_batch": Active codes still left in the batch.
        "user_issued_to": Username of the person the batch was issued to.
        "batch_creation_date": When the batch was created.
        "last_modified": When the batch was last modified.
        "expiry_date": Expiry date assigned to the batch codes.
        "deleted_at": When the batch was deleted/purged.
        "deleted_by": Who deleted the batch.
        "was_codes_downloaded": Whether codes were downloaded before purge.
        "was_codes_viewed": Whether codes were viewed before purge.
        "was_code_generated": Whether codes were generated before purge.

    Args:
        batch (RecoveryCodesBatch): The purged batch instance.
        purged_count (int): Number of codes deleted during purge.
        is_empty (bool): Whether the batch is now empty after deletion.

    Raises:
        TypeError:
            - If `batch` is not a RecoveryCodesBatch instance.
            - If `purged_count` is not an integer.
            - If `is_empty` is not a boolean.

    Example 1:
        >>> batch = RecoveryCodesBatch.get_by_user(request.user)
        >>> batch.purge_expired_codes()
        >>> report = _generate_purged_batch_code_json_report(batch, purged_count=5, is_empty=True)
        >>> report["number_removed"]
    
    Example Out:
        
        {
            "id": 42,
            "number_issued": 10,
            "number_removed": 8,
            "is_batch_empty": False,
            "number_used": 3,
            "number_remaining_in_batch": 2,
            "user_issued_to": "alice",
            "batch_creation_date": "2025-08-01T09:00:00Z",
            "last_modified": "2025-09-01T12:00:00Z",
            "expiry_date": "2025-09-30T00:00:00Z",
            "deleted_at": "2025-09-01T12:34:56Z",
            "deleted_by": "admin",
            "was_codes_downloaded": True,
            "was_codes_viewed": False,
            "was_code_generated": True,
        }
    """

    if not isinstance(batch, RecoveryCodesBatch):
        raise TypeError(f"Expected the instance of the batch to be  of RecoveryCodesBatch",
                        f"But got a batch instance with type {type(batch).__name__}"
                        )
    
    if  not isinstance(purged_count, int):
        raise TypeError(f"The `purged_count` parameter is not an integer. Expected an integer but got an object with type {type(purged_count).__name__}")
    
    if not isinstance(is_empty, bool):
        raise TypeError(f"The `is_empty` parameter is not a boolean. Expected a boolean object but got an object with type {type(is_empty).__name__}")
    
    purged_batch_info = {
                            "id": batch.id,
                            "number_issued": batch.number_issued,
                            "number_removed": purged_count,
                            "is_batch_empty": is_empty,
                            "number_used": batch.number_used,
                            "number_remaining_in_batch": (batch.number_issued - batch.number_used),
                            "user_issued_to": batch.user.username,
                            "batch_creation_date": batch.created_at,
                            "last_modified": batch.modified_at,
                            "expiry_date": batch.expiry_date,
                            "deleted_at": batch.deleted_at,
                            "deleted_by": batch.deleted_by,
                            "was_codes_downloaded": batch.downloaded,
                            "was_codes_viewed": batch.viewed,
                            "was_code_generated": batch.generated,
            }
    return purged_batch_info


def _if_set_to_true_use_logger(use_logger: bool, email_sender_logger: EmailSenderLogger) -> None:
    """
    Decides if a logger should be turned on for a given scheduled action.

    Args:
        use_logger (bool): Flag that determines if the logger should be run.
        email_sender_logger (EmailSenderLogger): The email logger instance.

    Raises:
        TypeError: If `use_logger` is not a bool or if `email_sender_logger`
                   is not an instance of EmailSenderLogger.
    """

    if not isinstance(use_logger, bool):
        raise TypeError(
            f"The `use_logger` must be a bool. Got {type(use_logger).__name__}"
        )

    if not isinstance(email_sender_logger, EmailSenderLogger):
        raise TypeError(
            f"The `email_sender_logger` must be an instance of `EmailSenderLogger`. "
            f"Got {type(email_sender_logger).__name__}"
        )

    if use_logger or settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER:
        purge_email_logger.info(
            "Sending email with logger turned on. All actions will be logged."
        )
        email_sender_logger.config_logger(email_logger, log_level=LoggerType.INFO)
        email_sender_logger.start_logging_session()
    else:
        purge_email_logger.info(
            "Sending email with logger turned off. No actions will be logged."
        )



def hook_email_purge_report(task):
    """
    Hook to send purge summary report by email.
    Marks scheduler as SUCCESS only if everything runs correctly.
    """
    result           = task.result or {}
    reports          = result.get("reports", [])
    use_with_logger  = result.get("use_with_logger")
    schedule_name    = result.get("schedule_name")

    if use_with_logger is None:
        use_with_logger = settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER

    email_sender_logger = EmailSenderLogger.create()

    try:
        _if_set_to_true_use_logger(use_with_logger, email_sender_logger)

        subject, html, text = _get_email_attribrutes(reports)
        email_sender = EmailSender.create()
        if not email_sender:
            raise RuntimeError("EmailSender.create() returned None! Cannot send email.")

        (
            email_sender_logger
            .add_email_sender_instance(email_sender)    
            .from_address(settings.DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER)
            .to(settings.DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL)
            .with_context({"report": reports, "username": settings.DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL})
            .with_subject(subject)
            .with_html_template(html, "recovery_codes_deletion")
            .with_text_template(text, "recovery_codes_deletion")
            .send()
        )

        email_logger.info("Purge summary email sent successfully")

        RecoveryCodeCleanUpScheduler.objects.filter(
            name=schedule_name
        ).update(status=RecoveryCodeCleanUpScheduler.Status.SUCCESS)

    except Exception as e:
        email_logger.error(f"Failed to send purge summary email: {e}", exc_info=True)
        RecoveryCodeCleanUpScheduler.objects.filter(
            name=schedule_name
        ).update(status=RecoveryCodeCleanUpScheduler.Status.FAILED)
        raise

        


def _get_email_attribrutes(reports: list):
    """
    """
    if not reports:
        subject = "Recovery Code Purge: No Expired Codes Found"
        html    = "no_purge.html"
        text    = "no_purge.txt"

    else:
        subject = f"Recovery Code Purge: {len(reports)} Batch(es) Processed"
        html    = "deleted_codes.html"
        text    = "deleted_codes.txt"
    
    return subject, html, text



def unschedule_task(schedule_name):
    """
    Delete all queued tasks and the schedule for a given Django-Q schedule name.
    Returns the number of tasks deleted (0 if none).
    """
    try:
       
        deleted_tasks, _ = clear_queued_tasks(schedule_name)
        Schedule.objects.filter(name=schedule_name).delete()
        return deleted_tasks
        
    except Task.DoesNotExist:
        return False  


def clear_queued_tasks(schedule_name: str):
    """
    Delete all queued tasks for a given Django-Q schedule.

    Why this is necessary?:

    Django-Q does NOT automatically remove old tasks from the queue
    when a schedule is updated. If an admin updates `next_run` or other
    schedule parameters in the admin interface **before the existing task
    has executed**, Django-Q will enqueue a new task **without removing the old one**. 
    This leads to duplicate tasks in the queue.

    Always call this function **before updating a schedule** to ensure
    that only a single task is queued for that schedule.

    Args:
        schedule_name (str): The name of the schedule whose queued tasks
                             should be deleted.

    Returns:
        tuple: Number of deleted tasks and a dictionary with deletion details
               (same as `QuerySet.delete()`).
    """
    return Task.objects.filter(name=schedule_name).delete()


def _store_user_email_log(email_sender_logger: EmailSenderLogger):
    """
    Store user email logs conditionally based on settings.

    This private helper inspects the `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG`
    setting. If the flag is enabled, the user's email (associated with the account
    requesting a recovery code) will be stored in the database. If the flag is 
    disabled, the email will not be stored.

    Args:
        email_sender_logger (EmailSenderLogger): 
            The logger instance responsible for handling email logging behaviour.

    Raises:
        TypeError: If `email_sender_logger` is not an instance of EmailSenderLogger.

    Returns:
        None: This function does not return anything. Its effect is to optionally
              configure the logger to persist email metadata.

    Example:
        # If DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG is True, the logger will be
        # configured to store the email metadata in the database.
        # If False, no database storage occurs.
    """
    if not isinstance(email_sender_logger, EmailSenderLogger):
        raise TypeError(
            f"Expected an instance of EmailSenderLogger, "
            f"but got {type(email_sender_logger).__name__}"
        )

    if settings.DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG:
        from django_auth_recovery_codes.models import RecoveryCodeEmailLog

        email_sender_logger.add_log_model(RecoveryCodeEmailLog)
        email_sender_logger.enable_email_meta_data_save()
