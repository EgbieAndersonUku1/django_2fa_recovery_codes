import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django_auth_recovery_codes.utils.cache.safe_cache import (get_cache_or_set, 
                                                               cache_lock, 
                                                               get_cache_with_retry,
                                                              delete_cache_with_retry)


@login_required
def sse_notifications(request):
    """
    SSE endpoint that streams messages to the authenticated user only when they exist.
    
    Workflow:
    - Polls the user's cache for messages.
    - If messages exist, locks the cache, retrieves, deletes, and yields them.
    - Does NOT send pings; the client only receives actual messages.
    
    Args:
        request (HttpRequest): Must be from an authenticated user.
    
    Returns:
        StreamingHttpResponse: Event stream with `content_type="text/event-stream"`.
    """
    user_id = request.user.id

    def event_stream():
        cache_key = f"sse_user_{user_id}"

        while True:
            messages = get_cache_or_set(cache_key, lambda: [])

            if messages:
                with cache_lock(cache_key) as locked:
                    if locked:
                        messages = get_cache_with_retry(cache_key)
                        if messages:
                            delete_cache_with_retry(cache_key)

                for msg in messages:
                    yield f"data: {msg}\n\n"

            # Sleep to prevent tight loop
            time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response