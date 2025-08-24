import threading

from logging import getLogger
from django_q.tasks import async_task
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.conf import settings

from .models import RecoveryCodesBatch, RecoveryCodeEmailLog, Status
from .views_helper import  generate_recovery_code_fetch_helper
from .utils.cache.safe_cache import get_cache_or_set, set_cache, get_with_retry, set_cache_with_retry
from .tasks import send_recovery_codes_email
from .utils.exporters.file_converters import to_csv, to_pdf, to_text


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
def download_code(request):
    """
    Return the user recovery codes as a downloadable file (TXT, CSV, or PDF).
    The filename is set dynamically based on backend logic, so the frontend
    can extract it from the Content-Disposition header.
    """
    user = request.user

    cache = get_cache_or_set(CACHE_KEY.format(user.id), 
                             value_or_func=lambda: RecoveryCodesBatch.get_by_user(user=user).get_cache_values(),
                              ttl=TTL
                            )
    if cache and cache.get("downloaded"):

        request.session["is_downloaded"] = True     # set to the session to be able to hide download button in the UI
        response = HttpResponse(content=b"", content_type="application/octet-stream")
        response["X-Success"] = True

      
        return response
    
    raw_codes = request.session.get("recovery_codes_state", {}).get("codes", [])

    if raw_codes:
        # request.session.get("recovery_codes_state").pop("codes")
        request.session["is_downloaded"] = True     # set to the session to be able to hide download button in the UI

    recovery_batch = RecoveryCodesBatch.get_by_user(user)
    recovery_batch.mark_as_downloaded()

    set_cache(CACHE_KEY,  recovery_batch.get_cache_values(), TTL)

    # Determine desired format (default to TXT)
    format_to_save = getattr(settings, 'DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT', 'txt')
    file_name      = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME", "recovery_codes")

    # Default filename and content
    defaault_file_name = "recovery_codes.txt"
    response_content   = b""
    content_type       = "text/plain"

    match format_to_save:

        case "txt":
            response_content = to_text(raw_codes).encode("utf-8")

        case "csv":

            file_name        = "recovery_codes.csv"
            response_content = to_csv(raw_codes).encode("utf-8")
            content_type     = "text/csv"

        case "pdf":
            file_name        = "recovery_codes.pdf"
            response_content = to_pdf(raw_codes)
            content_type     = "application/pdf"
   

    if not file_name:
        file_name = defaault_file_name
        
    response = HttpResponse(response_content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    response["X-Success"]           = "true"

    return response


@require_http_methods(['POST'])
@csrf_protect
@login_required
def mark_all_recovery_codes_as_pending_delete(request):
    

    recovery_batch  = RecoveryCodesBatch.delete_recovery_batch(request.user)
    status          = None
    data   = { "SUCCESS": False, "MESSAGE": ""}
    
    # reset the cache values
    if recovery_batch:

        recovery_batch.reset_cache_values()
        recovery_batch.save()
        request.session["is_downloaded"] = False
        request.session["is_emailed"]    = False

        set_cache(CACHE_KEY.format(request.user.id), recovery_batch.get_cache_values(), TTL)

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
   
    user       = request.user
    raw_codes  =  request.session.get("recovery_codes_state", {}).get("codes")
    resp       = {"SUCCESS": False, "MESSAGE": ""}

    try:
        cache_data = get_cache_or_set(CACHE_KEY.format(user.id), lambda: RecoveryCodesBatch.get_by_user(user).get_cache_values())
        
        if cache_data and cache_data.get("emailed"):

            if not "is_emailed" in request.session:
                request.session["is_emailed"] = True
            
            resp.update({"MESSAGE": "You have already email a copy of the code. Only one copy per batch", "SUCCESS": True})
            return JsonResponse(resp, status=200)
           
    except Exception:
        pass

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

    set_cache_with_retry(CACHE_KEY.format(user.id), recovery_batch.get_cache_values(), TTL)
   
    request.session["is_emailed"] = True  # needed to hide the page in the UI
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
           
            set_cache(CACHE_KEY.format(user.id),
                    value=recovery_batch.get_cache_values()
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

    user_data = get_with_retry(cache_key,
                            fetch_func=lambda: RecoveryCodesBatch.get_by_user(user=user).get_cache_values(),
                            ttl=TTL
                        )
    
  
    if user_data:
        data = user_data
        context.update({
            "is_generated": data.get("generated"),
            "is_email": data.get("emailed"),
            "is_viewed": data.get("viewed"),
            "is_downloaded": data.get("downloaded")
        })
    
    return render(request, "django_auth_recovery_codes/dashboard.html", context)
