from django.conf import settings

# Default app settings
DEFAULTS = {
    "RETENTION_DAYS": None,         
    "ENABLE_AUTO_CLEANUP": False,   

}



class AppConfigSettings:
    """
    Provides easy access to app-specific settings with:
    - Defaults if not overridden in project settings
    - Error checking for invalid attributes
    - Optional dict-like access
    """
    def __getattr__(self, attr):
        if attr not in DEFAULTS:
            raise AttributeError(f"Invalid app setting: {attr}")
        return getattr(settings, "DJANGO_AUTH_RECOVERY_CODE_AUDIT_" + attr, DEFAULTS[attr])




# Singleton-like instance (just like django.conf.settings)
app_settings = AppConfigSettings()


def default_cooldown_seconds():
    base       = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN", 15)
    multiplier = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER", 2)
    return base * multiplier


def default_multiplier():
    return getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER", 1)


def default_max_login_attempts():
    return getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS", 3)