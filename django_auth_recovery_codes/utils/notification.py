from django_auth_recovery_codes.utils.cache.safe_cache import get_cache_with_retry, set_cache_with_retry
from django_auth_recovery_codes.models import RecoveryCodeNotification


NOTIFICATION_CACHE_KEY =  "sse_user_{}"



def notify_user(user: int, message: str):
    """
    Create a notification for a user and push it to cache for SSE.

    Stores the notification in the database and also caches it under a
    key specific to the user for real-time updates via SSE.
    """
    if not message:
        return

    # Save notification in the database
    notification = RecoveryCodeNotification.objects.create(
        user=user,
        message=message,
        
    )

    save_notification_in_cache(user, notification, message)



def save_notification_in_cache(user, notification, notification_msg):
    """"""
    cache_key        = NOTIFICATION_CACHE_KEY.format(user.id)
    messages         = get_cache_with_retry(cache_key, default=[])
    HOURS_IN_SECONDS = 3600

    messages.append({"id": notification.id, "message": notification_msg})
    set_cache_with_retry(cache_key, messages, ttl=HOURS_IN_SECONDS)