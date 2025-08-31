from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler
from django_q.tasks import schedule
from datetime import timedelta
from django.core.exceptions import ValidationError


@receiver(post_save, sender=RecoveryCodeCleanUpScheduler)
def update_recovery_code_scheduler(sender, instance, **kwargs):
    if instance.enable_scheduler:
        schedule(
            "django_auth_recovery_codes.tasks.purge_all_expired_batches",
            retention_days=instance.retention_days,
            bulk_delete=instance.bulk_delete,
            log_per_code=instance.log_per_code,
            delete_empty_batch=instance.delete_empty_batch,
            schedule_type=instance.schedule_type,
            run_at=instance.run_at
        )



@receiver(pre_save, sender=RecoveryCodeCleanUpScheduler)
def validate_next_run_scheduler_value(sender, instance, **kwargs):
    if instance.enable_scheduler:
        
        if not instance.next_run:
            instance.next_run = instance.next_run_schedule()
        
        if instance.next_run and instance.next_run < instance.run_at:
            raise ValidationError("The run data cannot be greater than the next run")

    

