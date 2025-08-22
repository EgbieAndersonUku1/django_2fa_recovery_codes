import time
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django_auth_recovery_codes.utils.cache.safe_cache import get_cache, set_cache


@login_required
def sse_notifications(request):
    user_id = request.user.id

    def event_stream():

        messages = get_cache(f"sse_user_{user_id}", [])
        SECONDS_TO_CACHE = 60
        while messages:
            msg = messages.pop(0)
            if msg:
                yield f"data: {msg}\n\n"
            
            set_cache(f"sse_user_{user_id}", messages, SECONDS_TO_CACHE)
            time.sleep(1)  # small delay to avoid CPU spin

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response
