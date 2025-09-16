from django.conf import settings
from django.core.checks import register, Error, Warning

from django_auth_recovery_codes.conf import FLAG_VALIDATORS

from typing import Any, Dict, List, Optional
from django.apps import AppConfig
from django.core.checks import CheckMessage, Warning, Error
from django.conf import settings



@register()
def check_app_settings(
    app_configs: Optional[List[AppConfig]], **kwargs: Any
) -> List[CheckMessage]:
    """
    System check to validate all application settings flags defined in
    FLAG_VALIDATORS.

    Iterates through each flag in FLAG_VALIDATORS, ensuring it exists
    in Django settings and is of the correct type. Missing or invalid
    flags are collected as warnings or errors.

    Args:
        app_configs (list[AppConfig] | None): The list of installed app
            configurations (unused in this check).
        **kwargs: Arbitrary keyword arguments passed by the Django
            system check framework.

    Returns:
        list[CheckMessage]:
            A list of warnings or errors generated during the check.
    """
    errors: List[CheckMessage] = []

    for flag_name, config in FLAG_VALIDATORS.items():
        _check_flag(flag_name, config, errors)

    return errors


@register
def check_app_format_setting(
    app_configs: Optional[List[AppConfig]], **kwargs: Any
) -> List[CheckMessage]:
    """
    System check to validate the recovery codes default format setting.

    Ensures that the value of the setting
    `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT` (if defined) is one of
    the allowed formats: 'txt', 'pdf', or 'csv'.

    Args:
        app_configs (list[AppConfig] | None): The list of installed app
            configurations (unused in this check).
        **kwargs: Arbitrary keyword arguments passed by the Django
            system check framework.

    Returns:
        list[CheckMessage]:
            A list containing a warning if the format is invalid,
            otherwise an empty list.
    """
    errors: List[CheckMessage] = []
    
    value: Optional[str] = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT", None)
    if value:
        ext = value.strip()
        if ext not in ("txt", "pdf", "csv"):
            errors.append(
                Warning(
                    "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT",
                    f"The format must be either pdf, txt or csv but got {ext}"
                )
            )
    return errors


def _check_flag(flag_name: str, config: Dict[str, Any], errors: List[CheckMessage]) -> None:
    """
    Helper function to validate a single settings flag.

    Checks whether the flag is present in Django settings and matches
    the expected type as defined in its config dictionary.

    Args:
        flag_name (str): The name of the setting flag to validate.
        config (dict): The validation configuration for the flag,
            containing:
              - "type": The expected Python type.
              - "warning_if_missing": Message if the flag is missing.
              - "warning_id": System check ID for the missing warning.
              - "error_if_wrong_type": Message if the type is invalid.
              - "error_id": System check ID for the type error.
        errors (list[CheckMessage]): A mutable list to which warnings or
            errors will be appended.

    Returns:
        None
    """
    if not hasattr(settings, flag_name):
        errors.append(Warning(config["warning_if_missing"], id=config["warning_id"]))
        return

    value: Any = getattr(settings, flag_name)
    expected_type: type = config["type"]

    if not isinstance(value, expected_type):
        errors.append(Error(config["error_if_wrong_type"], id=config["error_id"]))

