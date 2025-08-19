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
from .views_helper import fetch_recovery_codes, generate_recovery_code_fetch_helper
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
def marked_code_as_viewed(request):
    """
    Marks the code as viewed. This enables the frontend to hide
    the code after the user refreshes the page.
    """
    user           = request.user
    recovery_batch = RecoveryCodesBatch.get_by_user(user)
    resp           = {'SUCCESS': False, 'ERROR': ''}

    print(recovery_batch)
    if recovery_batch:
        is_marked = recovery_batch.mark_as_viewed()
        print(is_marked)
        if is_marked:
            set_cache(CACHE_KEY.format(user.id),
                    value=fetch_recovery_codes(user)[0]
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
