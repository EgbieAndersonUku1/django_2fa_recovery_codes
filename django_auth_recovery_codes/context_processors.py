from django.conf import settings

def request(request):
    SITE_NAME = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_SITE_NAME", None)
    return {'request': request,  "site_name": SITE_NAME}