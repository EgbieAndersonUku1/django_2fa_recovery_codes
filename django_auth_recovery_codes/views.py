import threading

from logging import getLogger
from django_q.tasks import async_task, result

from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from django.conf import settings


from .models import RecoveryCodesBatch, RecoveryCodeEmailLog, Status
from .views_helper import fetch_recovery_codes, generate_recovery_code_fetch_helper
from .utils.cache.safe_cache import get_cache, set_cache, delete_cache
from .tasks import send_recovery_codes_email


from django.conf import settings

CACHE_KEY           = 'recovery_codes_generated_{}'
MINUTES_IN_SECONDS  = 300

TTL = getattr(settings, 'DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL', MINUTES_IN_SECONDS)
TTL = TTL if isinstance(TTL, int) else MINUTES_IN_SECONDS

SENDER_EMAIL =  settings.DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL
# Create your views here.

logger = getLogger()



@require_http_methods(['POST'])
@csrf_protect
@login_required
def recovery_codes_regenerate(request):
    """
    When called by the fetch api it issues the user a new set of codes and invalidates their previous codes
    """
    return generate_recovery_code_fetch_helper(request, CACHE_KEY)
   


def recovery_codes_verify(request, code):
    pass


def deactivate_recovery_code(request, code):
    pass





@require_http_methods(['POST'])
@csrf_protect
@login_required
def mark_all_recovery_codes_as_pending_delete(request):
    

    resp   = RecoveryCodesBatch.delete_recovery_batch(request.user)
    status = None
    data   = { "SUCCESS": False, "MESSAGE": ""}
    
    # reset the cache values
    if resp:
        values_to_save_in_cache = {
            "generated": False,
            "downloaded": False,
            "emailed": False,
            "viewed": False,
        }
        
        set_cache(CACHE_KEY, values_to_save_in_cache, TTL)

        data.update({
            "SUCCESS": True,
            "MESSAGE": "Your recovery codes was successfully deleted"
        })
        status = 201
       
    else:
    
        data.update({
            "MESSAGE": "Failed to delete recovery codes"
        })
        status = 400

    return JsonResponse(data, status=status)


@require_http_methods(['POST'])
@csrf_protect
@login_required
def email_recovery_codes(request):
   
    cache_data = get_cache(CACHE_KEY, fetch_func=lambda: fetch_recovery_codes(request.user), ttl=TTL)
    resp       = {"SUCCESS": False, "MESSAGE": ""}

    if cache_data and cache_data.get("emailed"):
        resp.update({
            "MESSAGE": "You have already emailed yourself a copy only copy is allowed by recovery batch",
            "SUCCESS": True,
        })
        return JsonResponse(resp, status=200)

    raw_codes = request.session.get("recovery_codes_state", {}).get("codes")
    resp      = {"SUCCESS": False, "MESSAGE": ""}

    if not raw_codes:
        resp.update({
            "MESSAGE": "Something went wrong and recovery codes weren't generated"
        })
        return JsonResponse(resp, status=400)

    user = request.user

    if settings.DEBUG:
        # Development: uses threading for speed
        threading.Thread(
            target=send_recovery_codes_email,
            args=(SENDER_EMAIL, user, raw_codes)
        ).start()
    else:
        # Production: uses Django Q for reliability
        async_task(
            send_recovery_codes_email,
            SENDER_EMAIL,
            user,
            raw_codes,
        )

    recovery_batch = RecoveryCodesBatch.get_by_user(request.user)
    recovery_batch.mark_as_emailed()

    values_to_save_in_cache = {
        "generated": recovery_batch.generated,
        "downloaded": recovery_batch.downloaded,
        "emailed": recovery_batch.emailed,
        "viewed": recovery_batch.viewed
    }

    set_cache(CACHE_KEY, values_to_save_in_cache, TTL)

    resp.update({
        "MESSAGE": "Recovery codes email has been queued. We will notify you once they have been sent",
        "SUCCESS": True,
    })
    return JsonResponse(resp, status=200)
    


@require_http_methods(['POST'])
@csrf_protect
@login_required
def marked_code_as_viewed(request):
    """
    Marks the code as viewed. This enables the frontend to hide
    the code after the user refreshes the page.
    """
    user           = request.user
    recovery_batch = RecoveryCodesBatch.get_by_user(user)
    resp           = {'SUCCESS': False, 'ERROR': ''}

    if recovery_batch:
        recovery_batch = recovery_batch.mark_as_viewed()
      
        if recovery_batch and recovery_batch.viewed:
            values_to_cache = {
                "viewed": recovery_batch.viewed,
                "downloaded": recovery_batch.downloaded,
                "emailed": recovery_batch.emailed,
                "generated": recovery_batch.generated,
            }
            set_cache(CACHE_KEY.format(user.id),
                    value=values_to_cache
                    )
            resp["SUCCESS"] = True
   
    else:
        resp["ERROR"] = "Failed to set batch to marked because it wasn't found"
    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)

        

@require_http_methods(['POST'])
@csrf_protect
@login_required
def generate_recovery_code_with_expiry(request):
    """
    Generate a batch of recovery codes for the logged-in user with an expiry.
    """
    return generate_recovery_code_fetch_helper(request, CACHE_KEY, generate_with_expiry_date=True)
   

@require_http_methods(['POST'])
@csrf_protect
@login_required
def generate_recovery_code_without_expiry(request):
    """
    Generate a batch of recovery codes for the logged-in user for an indefine period.
    """
    return generate_recovery_code_fetch_helper(request, CACHE_KEY)



@csrf_protect
@login_required
def recovery_dashboard(request):
    user       = request.user
    cache_key  = CACHE_KEY.format(user.id)
    context    = {}
    user_data  = get_cache(cache_key, fetch_func=lambda: fetch_recovery_codes(user), ttl=TTL)

    if user_data:
        data = user_data
        context.update({
            "is_generated": data.get("generated"),
            "is_email": data.get("emailed"),
            "is_viewed": data.get("viewed")
        })
    
  
    return render(request, "django_auth_recovery_codes/dashboard.html", context)
