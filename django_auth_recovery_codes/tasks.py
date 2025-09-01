import logging

from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import LoggerType

from django.utils import timezone
from django_auth_recovery_codes import notify_user
from django_auth_recovery_codes.models import RecoveryCodePurgeHistory, RecoveryCodesBatch, RecoveryCodeAudit
from django_auth_recovery_codes.app_settings import app_settings


logger = logging.getLogger("email_sender")
audit_logger = logging.getLogger("audits")

def send_recovery_codes_email(sender_email, user, codes, subject= "Your account recovery codes"):
    email_sender_logger = EmailSenderLogger.create() 
    try:
        ( 
        
            email_sender_logger.create() 
                .add_email_sender_instance(EmailSender.create()) 
                .start_logging_session()
                .config_logger(logger, log_level=LoggerType.INFO)
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
        logger.error(f"Failed to send recovery codes: {e}")
        notify_user(user.id, f"Failed to send recovery codes: {e}")

        raise 

DJANGO_AUTH_RETENTION_DAYS = 0

def purge_all_expired_batches(retention_days=DJANGO_AUTH_RETENTION_DAYS, bulk_delete=True, log_per_code=False, delete_empty_batch=True):
    """
    Scheduled task to purge all expired recovery codes in all batches.
    Returns a summary of totals removed.
    """
    total_batches  = 0
    total_purged   = 0

    batches = RecoveryCodesBatch.objects.all()
    for batch in batches:
        purged_count, _ = batch.purge_expired_codes(
            bulk_delete=bulk_delete,
            log_per_code=log_per_code,
            retention_days=retention_days,
            delete_empty_batch=delete_empty_batch
        )
        if purged_count >= 0:
            total_purged += purged_count
            total_batches += 1
        
    
    RecoveryCodePurgeHistory.objects.create(
        total_codes_purged=total_purged,
        total_batches_purged=total_batches,
        retention_days=retention_days
    )

    print(f"[{timezone.now()}] Purged {total_purged} codes from {total_batches} batches")
    return {
        "total_batches_processed": total_batches,
        "total_codes_removed": total_purged
    }


def clean_up_old_audits_tasks():
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
    
