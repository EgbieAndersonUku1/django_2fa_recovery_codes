import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django_auth_recovery_codes.utils.cache.safe_cache import (get_cache_with_retry,
                                                              delete_cache_with_retry)

@login_required
def sse_notifications(request):
    """
    SSE endpoint that streams messages to the authenticated user only when they exist.
    """
    user_id = request.user.id
    cache_key = f"sse_user_{user_id}"

    def event_stream():
        while True:
            messages = get_cache_with_retry(cache_key, default=[])
            if messages:
                for notification in messages:
                    yield f"data: {notification.message}"
                delete_cache_with_retry(cache_key)
            time.sleep(1)

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
