from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler, RecoveryCodeAudit, RecoveryCodeAuditScheduler
from django_q.tasks import schedule, Schedule
from datetime import timedelta
from django.core.exceptions import ValidationError
from django_auth_recovery_codes.utils.utils import create_unique_string



@receiver(post_save, sender=RecoveryCodeCleanUpScheduler)
def update_recovery_code_scheduler(sender, instance, **kwargs):
   
    
    schedule_name = create_unique_string(f"purge_recovery_codes_{instance.pk}")

    if instance.enable_scheduler:
        schedule(
            "django_auth_recovery_codes.tasks.purge_all_expired_batches",
            retention_days=instance.retention_days,
            bulk_delete=instance.bulk_delete,
            log_per_code=instance.log_per_code,
            delete_empty_batch=instance.delete_empty_batch,
            schedule_type=instance.schedule_type,
            run_at=instance.run_at,
            hook="django_auth_recovery_codes.tasks.hook_email_purge_report",
            name=schedule_name, 
            repeats=-1,
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
    if instance.enable_scheduler:
        
        if not instance.next_run:
            instance.next_run = instance.next_run_schedule()
        
        if instance.next_run and instance.next_run < instance.run_at:
            raise ValidationError("The run data cannot be greater than the next run")

    



@receiver(pre_save, sender=RecoveryCodeAuditScheduler)
def recovery_code_audit_scheduler(sender, instance, **kwargs):
     if instance and not instance.pk:
        instance.name = create_unique_string(instance.name or "Recovery Codes Removal Audit Cleanup")
