import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler, RecoveryCodeAudit, RecoveryCodeAuditScheduler
from django_q.tasks import schedule, Schedule
from datetime import timedelta
from django.core.exceptions import ValidationError
from django_auth_recovery_codes.tasks import unschedule_task, clear_queued_tasks
from django_auth_recovery_codes.utils.utils import create_unique_string

from django.conf import settings

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=RecoveryCodeAuditScheduler)
def recovery_code_audit_scheduler(sender, instance, **kwargs):
     if instance and not instance.pk:
        instance.name = create_unique_string(instance.name or "Recovery Codes Removal Audit Cleanup")



@receiver(post_save, sender=RecoveryCodeCleanUpScheduler)
def update_recovery_code_scheduler(sender, instance, **kwargs):
    schedule_name = f"purge_recovery_codes_{instance.pk}"

    if instance.enable_scheduler:
        first_run = instance.run_at or instance.next_run_schedule()

        deleted_tasks, _ = clear_queued_tasks(schedule_name)

        if deleted_tasks > 0:
            logger.info(f"Removed {deleted_tasks} queued tasks to prevent duplicates for '{schedule_name}'.")

        Schedule.objects.update_or_create(
            name=schedule_name,
            defaults={
                "func": "django_auth_recovery_codes.tasks.purge_all_expired_batches",
                "repeats": -1,
                "schedule_type": instance.schedule_type,
                "next_run": first_run,
                "hook": "django_auth_recovery_codes.tasks.hook_email_purge_report",
                "kwargs": {
                    "retention_days": instance.retention_days,
                    "bulk_delete": instance.bulk_delete,
                    "log_per_code": instance.log_per_code,
                    "delete_empty_batch": instance.delete_empty_batch,
                    "use_with_logger": instance.use_with_logger,
                },
            },
        )
    else:
        deleted_task = unschedule_task(schedule_name)
        logger.info(
            f"Schedule '{schedule_name}' disabled. "
            f"Deleted {deleted_task} queued tasks for this schedule."
        )


@receiver(post_save, sender=RecoveryCodeAuditScheduler)
def update_recovery_code_audit_scheduler(sender, instance, **kwargs):

    schedule_name = create_unique_string(f"cleanup_audit_task{instance.pk}")

    if instance.enable_scheduler:
        schedule(
            "django_auth_recovery_codes.tasks.clean_up_old_audits_task",
            schedule_type=instance.schedule_type,
            run_at=instance.run_at,
            next_run=instance.next_run_schedule(),
            name=schedule_name
        )
 


@receiver(pre_save, sender=RecoveryCodeCleanUpScheduler)
def validate_unique_recovery_code_name_scheduler(sender, instance, **kwargs):

    if instance and instance.enable_scheduler and not instance.pk:
        instance.name = create_unique_string(instance.name or "Purge Expired Recovery Codes")
        


@receiver(pre_save, sender=RecoveryCodeCleanUpScheduler)
def validate_next_run_scheduler_value(sender, instance, **kwargs):

    if instance.pk is not None and instance.enable_scheduler:

        if not instance.next_run:
            instance.next_run = instance.next_run_schedule()

        if instance.next_run and instance.next_run < instance.run_at:
            raise ValidationError("The run date cannot be earlier than the 'run_at' date")

        if instance.use_with_logger is None:
            instance.use_with_logger = settings.DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER
    



