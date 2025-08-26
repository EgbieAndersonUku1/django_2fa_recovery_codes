from django_auth_recovery_codes.utils.cache.safe_cache import get_cache_or_set, set_cache


def notify_user(user_id: int, message: str):
    """
    Add a notification message for a user.
    Stores messages in a queue so multiple notifications are preserved.
    """
    key = f"sse_user_{user_id}"

    # Get existing messages or initialize empty list
    messages = get_cache_or_set(key, lambda: [])

    if message:
        messages.append(message)

    set_cache(key, messages, ttl=60)


default_app_config = "django_auth_recovery_codes.apps.DjangoAuthRecoveryCodesConfig"