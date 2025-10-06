from django.conf import settings
from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import LoggerType
from django_email_sender.email_sender_constants import EmailSenderConstants
from django.utils import timezone

from django_q.models import Task, Schedule
from django_auth_recovery_codes.models import (RecoveryCodePurgeHistory, 
                                               RecoveryCodesBatch, 
                                               RecoveryCodeAudit, 
                                               RecoveryCodeCleanUpScheduler,
                                               )

from django_auth_recovery_codes.app_settings import app_settings
from django_auth_recovery_codes.loggers.loggers import (email_logger,
                                                         purge_code_logger, 
                                                         audit_logger, 
                                                         purge_email_logger)


from django_auth_recovery_codes.helpers import PurgedStatsCollector
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg


def send_recovery_codes_email(sender_email, user, codes, subject= "Your account recovery codes"):
    
    email_sender_logger = EmailSenderLogger.create()
    use_logger          =  settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER

    _store_user_email_log(email_sender_logger)

    # exclude the context and header from being logged since they contain crucial information
    # e.g recovery raw codes within the context
    _if_set_to_true_use_logger(use_logger, email_sender_logger, log_context_and_header=False)

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
  
    except Exception as e:
        email_logger.error(f"Failed to send recovery codes: {e}")
      


def purge_all_expired_batches(*args, **kwargs):
    """
    Scheduled task to purge all expired recovery codes.
    Uses kwargs to ensure all arguments reach the function reliably.
    """
    retention_days     = kwargs.get("retention_days", settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS)
    bulk_delete        = kwargs.get("bulk_delete", True)
    use_with_logger    = kwargs.get("use_with_logger", settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER)
    delete_empty_batch = kwargs.get("delete_empty_batch", True)
    schedule_name      = kwargs.get("schedule_name")

    purge_code_logger.info( f"[RecoveryCodes] Starting purge job | retention_days={retention_days}, bulk_delete={bulk_delete}, "
                             f"delete_empty_batch={delete_empty_batch}, use_with_logger={use_with_logger}s, started_at={timezone.now()}"
                            )

    stats      = PurgedStatsCollector(logger=purge_code_logger)
    batches    = RecoveryCodesBatch.objects.select_related("user").all()
    MAX_LENGTH = 3

    purge_code_logger.debug("[RecoveryCodes] Found %s batches to check", batches.count())

    for batch in batches:

        try:

            result = batch.purge_expired_codes(retention_days=retention_days, delete_empty_batch=delete_empty_batch)

            if not isinstance(result, tuple) or len(result) != MAX_LENGTH:
                purge_code_logger.error(f"Unexpected return from purge_expired_codes: {result} | skipping batch {batch.id}")
                continue

            purged_count, is_empty, batch_id = result

            purge_code_logger.error(f" purge_expired_codes: {result} | processing batch {batch_id}")
            stats.process_batch(batch, purged_count=purged_count, is_empty=is_empty, batch_id=batch_id, use_with_logger=True)        

        except Exception as e:
            purge_code_logger.error(f"Unexpected error while purging batch {batch.id}: {e}", exc_info=True)
            continue

    if stats.total_batches > 0 or stats.total_purged > 0:
        RecoveryCodePurgeHistory.objects.create(
            total_codes_purged=stats.total_purged,
            total_batches_purged=stats.total_batches,
            retention_days=retention_days,
        )

    purge_code_logger.info(
        "[RecoveryCodes] Purge complete | total_batches_purged=%s, total_codes_purged=%s, "
        "total_batches_skipped=%s, finished_at=%s",
        stats.total_batches, stats.total_purged, stats.total_skipped, timezone.now()
    )

    result = {
        "reports": stats.batches_report,
        "use_with_logger": bool(use_with_logger),
        "schedule_name": schedule_name,
        "total_batches_removed": stats.total_batches,
    }

    purge_code_logger.info(f"[RecoveryCodes] Returning result: {result}")
    return result


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


def _if_set_to_true_use_logger(use_logger: bool, email_sender_logger: EmailSenderLogger, log_context_and_header: bool = True) -> None:
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
        raise TypeError(construct_raised_error_msg("use_logger", bool, use_logger))
      
    if not isinstance(email_sender_logger, EmailSenderLogger):
        raise TypeError(construct_raised_error_msg("email_sender_logger", EmailSenderLogger, email_sender_logger))

    if use_logger or settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER:
        purge_email_logger.info(
            "Sending email with logger turned on. All actions will be logged."
        )
        email_sender_logger.config_logger(email_logger, log_level=LoggerType.INFO)

       
        email_sender_logger.start_logging_session()


        if not log_context_and_header:
            purge_code_logger.debug("The context and headers haven't be logged")
            email_sender_logger.exclude_fields_from_logging(EmailSenderConstants.Fields.CONTEXT.value,
                                                            EmailSenderConstants.Fields.HEADERS.value,
                                                            )
      
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

        # show the ontext and header since they don't include sensitive information
        _if_set_to_true_use_logger(use_with_logger, email_sender_logger)

        subject, html, text = _get_email_attribrutes(reports)
        email_sender = EmailSender.create()
        if not email_sender:
            raise RuntimeError("EmailSender.create() returned None! Cannot send email.")

        admin_email = settings.DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL
        (
            email_sender_logger
            .add_email_sender_instance(email_sender)    
            .from_address(settings.DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER)
            .to(admin_email)
            .with_context({"reports": reports, "username": settings.DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME})
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
        raise TypeError(construct_raised_error_msg("email_sender_logger", EmailSenderLogger, email_sender_logger))
       
    if settings.DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG:
        from django_auth_recovery_codes.models import RecoveryCodeEmailLog

        email_sender_logger.add_log_model(RecoveryCodeEmailLog)
        email_sender_logger.enable_email_meta_data_save()
