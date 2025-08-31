import logging
from django.apps import AppConfig
from django.apps import AppConfig
from django.utils import timezone



logger = logging.getLogger(__name__)



class DjangoAuthRecoveryCodesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "django_auth_recovery_codes"

    def ready(self):

        from django.conf import settings
        from django.template import context_processors
            
        from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler
        from django_auth_recovery_codes.tasks import purge_all_expired_batches
        from django_q.tasks import schedule
        import django_auth_recovery_codes.signals


        if hasattr(settings, 'TEMPLATES'):
            for template_config in settings.TEMPLATES:
                if 'OPTIONS' in template_config and 'context_processors' in template_config['OPTIONS']:
                    context_processors = template_config['OPTIONS']['context_processors']

                    if 'django_auth_recovery_codes.context_processors.request' not in context_processors:
                        context_processors.append('django_auth_recovery_codes.context_processors.request')
        

        # Schedule cleanup tasks
        try:
            from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler
        
            from django_q.tasks import schedule

            for scheduler in RecoveryCodeCleanUpScheduler.get_schedulers():
                if scheduler.enable_scheduler:
                    schedule(
                         'django_auth_recovery_codes.tasks.purge_all_expired_batches',
                        schedule_type=scheduler.schedule_type,
                        next_run=scheduler.run_at,
                        retention_days=scheduler.retention_days,
                        bulk_delete=scheduler.bulk_delete,
                        log_per_code=scheduler.log_per_code,
                        delete_empty_batch=scheduler.delete_empty_batch,
                       
                    )
        except Exception as e:
            logger.error(f"Error scheduling purge_all_expired_batches: {e}")