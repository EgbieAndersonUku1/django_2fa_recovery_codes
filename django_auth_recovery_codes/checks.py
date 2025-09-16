from django.conf import settings
from django.core.checks import register, Error, Warning

from django_auth_recovery_codes.conf import FLAG_VALIDATORS



@register()
def check_app_settings(app_configs, **kwargs):
    """
    Validate all app settings flags.
    """
    errors = []

    for flag_name, config in FLAG_VALIDATORS.items():
        _check_flag(flag_name, config, errors)

    return errors


def _check_flag(flag_name, config, errors):
    """
    Helper to check a single flag.
    """
    if not hasattr(settings, flag_name):
        errors.append( Warning(config["warning_if_missing"], id=config["warning_id"]))
        return

    value         = getattr(settings, flag_name)
    expected_type = config["type"]

    if not isinstance(value, expected_type):
        errors.append(Error(config["error_if_wrong_type"], id=config["error_id"]))