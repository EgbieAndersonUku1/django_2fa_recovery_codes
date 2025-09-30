from django.conf import settings
from django.core.checks import register, Error, Warning, CheckMessage
from typing import Any, Dict, List, Optional
from django.apps import AppConfig

from django_auth_recovery_codes.conf import FLAG_VALIDATORS


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

    # Fl
    flags_to_skip = ["DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN"]

    for flag_name, config in FLAG_VALIDATORS.items():
        if flag_name not in flags_to_skip:
            _check_flag(flag_name, config, errors)

    return errors


@register
def check_app_format_setting(app_configs: Optional[List[AppConfig]], **kwargs: Any
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
    
    value: Optional[str] = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT")
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


@register()
def check_app_max_deletions_per_run(app_configs: Optional[List[Any]] = None, **kwargs: Any) -> List[CheckMessage]:
    """
    Checks if the `DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN` in the settings is valid.

    A valid value is either an int or None.
    """
    errors: List[CheckMessage] = []

    raw = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN")

    if not isinstance(raw, int):
   
        errors.append(
            Warning(
                f"`DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN` must be an int or None. got type {type(raw).__name__}",
                hint="Set it to a positive integer or 0 for unlimited deletions.",
                id="django_auth_recovery_codes.W001",
            )
        )

    return errors


@register
def check_pagination_settings(app_configs: Optional[List[AppConfig]], **kwargs: Any
) -> List[CheckMessage]:
    """"""
    max_code_visible = settings.DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE 
    codes_per_page   = settings.DJANGO_AUTH_RECOVERY_CODE_PER_PAGE 
    errors           = []

    if (max_code_visible <= 0 and codes_per_page <= 0):
        errors.append(
            Error(
                f"One of more of the flags is 0",
                f"The flags cannot be 0 because they are needed for pagination and to display the number of items per page",
                f'DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE value is {max_code_visible}',
                f'DJANGO_AUTH_RECOVERY_CODE_PER_PAGE value is {codes_per_page}',
            )
        )
        return errors
    
    if codes_per_page > max_code_visible:
        errors.append(
            Error(
                  f'DJANGO_AUTH_RECOVERY_CODE_PER_PAGE cannot be greater than DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE',
                  f'DJANGO_AUTH_RECOVERY_CODE_PER_PAGE value is {codes_per_page}',
                  f'DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE value is {max_code_visible}'
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

@register
def check_ttl_setting(app_configs: Optional[List[AppConfig]], **kwargs: Any) -> List[CheckMessage]:
    """
    Validates the Django settings for recovery code caching.

    This check ensures that the cache configuration is sensible:
    1. CACHE_TTL, CACHE_MIN, and CACHE_MAX must be positive values.
    2. CACHE_MIN cannot exceed CACHE_MAX.
    3. CACHE_TTL must lie within the range defined by CACHE_MIN and CACHE_MAX.

    These checks prevent misconfiguration that could lead to recovery codes
    expiring too quickly or remaining in the cache indefinitely.

    Returns:
        List[CheckMessage]: A list of Django CheckMessages indicating any errors
                            or inconsistencies in the cache settings.
    """
    cache_ttl = settings.DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL
    cache_min = settings.DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN
    cache_max = settings.DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX
    errors: List[CheckMessage] = []

    # Check for zero or negative values
    if cache_min <= 0 or cache_max <= 0 or cache_ttl <= 0:
        errors.append(
            Error(
                "One or more cache settings is zero or negative.",
                hint=(
                    "All cache settings must be positive as they determine how long "
                    "recovery codes remain in the cache. "
                    f"Current values: TTL={cache_ttl}, MIN={cache_min}, MAX={cache_max}. "
                    "Consider setting them to positive integers, e.g., TTL=300, MIN=60, MAX=600."
                ),
                id="django_auth_recovery_codes.E001",
            )
        )
        return errors

    # Ensure min is not greater than max
    if cache_min > cache_max:
        errors.append(
            Error(
                "CACHE_MIN cannot be greater than CACHE_MAX.",
                hint=(
                    f"Current values: MIN={cache_min}, MAX={cache_max}, TTL={cache_ttl}. "
                    "Swap the values or adjust them so that MIN <= MAX."
                ),
                id="django_auth_recovery_codes.E002",
            )
        )

    # Ensure TTL is within min and max range
    if not (cache_min <= cache_ttl <= cache_max):
        errors.append(
            Error(
                "CACHE_TTL is outside the min-max range.",
                hint=(
                    f"Current values: TTL={cache_ttl}, MIN={cache_min}, MAX={cache_max}. "
                    "Adjust TTL to fall within the range defined by MIN and MAX."
                ),
                id="django_auth_recovery_codes.E003",
            )
        )

    return errors
