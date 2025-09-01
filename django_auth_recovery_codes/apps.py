import logging
from django.apps import AppConfig
from django.apps import AppConfig
from django.utils import timezone



logger = logging.getLogger(__name__)



class DjangoAuthRecoveryCodesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "django_auth_recovery_codes"

    def ready(self):

        import django_auth_recovery_codes.signals
        from django_auth_recovery_codes.utils.schedulers import schedule_recovery_code_cleanup, schedule_cleanup_audit

        from django.conf import settings
        from django.template import context_processors
            
        from django_auth_recovery_codes.models import RecoveryCodeCleanUpScheduler
        from django_auth_recovery_codes.tasks import purge_all_expired_batches
        from django_q.tasks import schedule
       


        if hasattr(settings, 'TEMPLATES'):
            for template_config in settings.TEMPLATES:
                if 'OPTIONS' in template_config and 'context_processors' in template_config['OPTIONS']:
                    context_processors = template_config['OPTIONS']['context_processors']

                    if 'django_auth_recovery_codes.context_processors.request' not in context_processors:
                        context_processors.append('django_auth_recovery_codes.context_processors.request')
        

        # Schedule cleanup tasks
        schedule_recovery_code_cleanup()
        schedule_cleanup_audit()