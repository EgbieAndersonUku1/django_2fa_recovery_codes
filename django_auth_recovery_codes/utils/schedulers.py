import logging




logger = logging.getLogger(__name__)


def schedule_recovery_code_cleanup():
    """
    Schedule the periodic cleanup task for recovery codes.

    Iterates through all configured RecoveryCodeCleanUpScheduler instances 
    and schedules the `purge_all_expired_batches` task according to each scheduler's settings.
    Logs any errors encountered during scheduling.
    """
    try:
        from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler
        from django_q.tasks import schedule, Schedule
    
        for scheduler in RecoveryCodeCleanUpScheduler.get_schedulers():
            unique_task_name = f"purge_codes_{scheduler.id}"

            # Check if a schedule with this name already exists
            if not Schedule.objects.filter(name=unique_task_name).exists():
                        schedule(
                            'django_auth_recovery_codes.tasks.purge_all_expired_batches',
                            schedule_type=scheduler.schedule_type,
                            next_run=scheduler.run_at,
                            retention_days=scheduler.retention_days,
                            bulk_delete=scheduler.bulk_delete,
                            log_per_code=scheduler.log_per_code,
                            delete_empty_batch=scheduler.delete_empty_batch,
                            name=unique_task_name,
                        )
    except Exception as e:
        logger.error(f"Error scheduling purge_all_expired_batches: {e}")


def schedule_cleanup_audit():
    """"""
    try:
        
        from django_q.models import Schedule

        schedule_name = "Clean up recovery codes audit"

        if not Schedule.objects.filter(name=schedule_name).exists():
            
            from django_q.tasks import schedule

            schedule('django_auth_recovery_codes.tasks.clean_up_old_audits_task',
                    name="RecoveryCodeAudit cleanup",
                    )
       
    except Exception as e:
        logger.error(f"Error scheduling purge_all_expired_batches: {e}")


    