from django.conf import settings
from django_auth_recovery_codes.models_choices import Status

def request(request):
    SITE_NAME = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_SITE_NAME", None)
    return {'request': request,  "site_name": SITE_NAME, "Status": Status}