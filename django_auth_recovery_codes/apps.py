from django.apps import AppConfig
from django.apps import AppConfig
from django.utils import timezone

from django_q.tasks import schedule

class DjangoAuthRecoveryCodesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "django_auth_recovery_codes"

    def ready(self):

        from django.conf import settings
        from django.template import context_processors

        if hasattr(settings, 'TEMPLATES'):
            for template_config in settings.TEMPLATES:
                if 'OPTIONS' in template_config and 'context_processors' in template_config['OPTIONS']:
                    context_processors = template_config['OPTIONS']['context_processors']

                    if 'django_auth_recovery_codes.context_processors.request' not in context_processors:
                        context_processors.append('django_auth_recovery_codes.context_processors.request')
