# """
# view_helpers.py

# This file contains helper functions specific to the views.
# Generic things that are not specific to any view

# Purpose:
# - Keep views.py clean and uncluttered.
# - Provide functionality that is specific to the view logic.

# Notes:
# - Not a general-purpose utilities module.
# - Functions here are intended to work only with the views.
# - Can be expanded in the future with more view-specific helpers.
# """


from django.contrib.auth import get_user_model


from django_auth_recovery_codes.models                       import RecoveryCodeSetup
from django_auth_recovery_codes.loggers.loggers              import view_logger
from django_auth_recovery_codes.utils.errors.enforcer        import enforce_types

User = get_user_model()


@enforce_types()
def set_setup_flag_if_missing_and_add_to_cache(cache_data: dict, user: User, flag_name: str):
    """
    Ensure a setup flag is present in the cache and add it if missing.

    The `enforce_types` decorator ensures that `cache_data` is a dictionary,
    `user` is a User instance, and `flag_name` is a string. If any argument
    has an incorrect type, a TypeError is raised automatically.

    Args:
        cache_data (dict): The cache dictionary where flags are stored.
        user (User): The user for whom the setup flag is being checked.
        flag_name (str): The key name for the flag in the cache.

    Returns:
        bool: True if the flag was missing and has been added, False otherwise.

    Raises:
        Exception: Re-raises any exception encountered during flag computation.
    """
    
    try:

        if flag_name not in cache_data:
            view_logger.debug(
                f"Flag not found in cache, setting '{flag_name}' to the cache"
            )
            cache_data[flag_name] = (
                RecoveryCodeSetup.has_first_time_setup_occurred(user) or False
            )
            return True
           
    except Exception as e:
        view_logger.debug(str(e))
        raise 
    return False
