import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django_auth_recovery_codes.utils.cache.safe_cache import (get_cache_or_set, 
                                                               cache_lock, 
                                                               get_cache_with_retry,
                                                              delete_cache_with_retry)



@login_required
def sse_notifications(request):
    user_id = request.user.id

    def event_stream():
        cache_key = f"sse_user_{user_id}"
        messages = get_cache_or_set(cache_key, lambda: [])
       
        while messages:
            
            with cache_lock(cache_key) as locked:
                if locked:
                   
                    messages = get_cache_with_retry(cache_key)
                    if messages:
                        delete_cache_with_retry(cache_key)
            for msg in messages:
                yield f"data: {msg}\n\n"
        time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response
