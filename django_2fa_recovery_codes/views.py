import json

from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db import IntegrityError

from .models import RecoveryCodesBatch, Status
from .views_helper import cache_lock, fetch_recovery_codes
from .utils.cache.safe_cache import get_cache, set_cache, delete_cache


from django.conf import settings

CACHE_KEY           = 'recovery_codes_generated_{}'
MINUTES_IN_SECONDS  = 300

TTL = getattr(settings, 'RECOVERY_CODES_CACHE_TTL', MINUTES_IN_SECONDS)
TTL = TTL if isinstance(TTL, int) else MINUTES_IN_SECONDS


# Create your views here.

def recovery_codes_list(request):
    return HttpRequest("I am here")


def recovery_codes_regenerate(request):
    pass


def recovery_codes_verify(request, code):
    pass


def deactivate_recovery_code(request, code):
    pass


@require_http_methods(['POST'])
@csrf_protect
@login_required
def generate_recovery_code_with_expiry(request):
    """
    Generate a batch of recovery codes for the logged-in user with an expiry.
    """
    resp = {"TOTAL_ISSUED": 0, 
            "SUCCESS": False,
             "ERROR": "", "codes": []}

    try:
        data = json.loads(request.body.decode("utf-8"))
        days_to_expire = int(data.get("daysToExpiry", 0))

        if days_to_expire <= 0:
            raise ValueError("daysToExpiry must be a positive integer")
        
        raw_codes = RecoveryCodesBatch.create_recovery_batch(
            user=request.user,
            days_to_expire=days_to_expire
        )

        resp.update({
            "TOTAL_ISSUED": 1,
            "SUCCESS": True,
            "CODES": raw_codes
        })

        request.session["recovery_codes_state"] = {
                        "codes": raw_codes,
                        "viewed": False,
                        "downloaded": False,
                        "emailed": False,
                        "is_generated": True,
                    }
        
        # update the cache
        set_cache(CACHE_KEY.format(request.user.id),
                  value=fetch_recovery_codes(request.user)
                  )

    except IntegrityError as e:
        resp["ERROR"] = str(e)
    except json.JSONDecodeError:
        resp["ERROR"] = "Invalid JSON body"
    except Exception as e:
        resp["ERROR"] = str(e)

    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)



@csrf_protect
@login_required
def recovery_dashboard(request):
    user                 = request.user
    cache_key            = CACHE_KEY.format(user.id)
    context              = {}

    user_data                 = get_cache(cache_key, fetch_func=lambda: fetch_recovery_codes(user), ttl=TTL)
    recovery_state            = request.session.get("recovery_codes_state", {})
    context["recovery_state"] = recovery_state
   
    # print(user_data)
    # print(len(user_data))
    return render(request, "django_2fa_recovery_codes/dashboard.html", context)
