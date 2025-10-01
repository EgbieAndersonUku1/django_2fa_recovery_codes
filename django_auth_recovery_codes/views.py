import logging
import json
import threading

from django.db import IntegrityError
from django.urls.exceptions import NoReverseMatch
from django.contrib import messages
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from django_q.tasks import async_task
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.conf import settings
from typing import Tuple

from django_auth_recovery_codes.forms.login_form import LoginForm
from django_auth_recovery_codes.utils.converter import SecondsToTime
from django_auth_recovery_codes.models import (RecoveryCodeNotification, 
                                               RecoveryCodesBatch,
                                               RecoveryCode, 
                                               RecoveryCodeSetup, 
                                               LoginRateLimiter)

from django_auth_recovery_codes.utils.cache.safe_cache import delete_cache_with_retry
from django_auth_recovery_codes.views import  (generate_recovery_code_fetch_helper, 
                                              recovery_code_operation_helper,
                                              get_recovery_batches_context, 
                                              set_setup_flag_if_missing_and_add_to_cache
                                             )

from django_auth_recovery_codes.utils.cache.safe_cache import (get_cache_or_set, set_cache, 
                                                                get_cache_with_retry, 
                                                                set_cache_with_retry, 
                                     )

from django_auth_recovery_codes.loggers.loggers import view_logger
from django_auth_recovery_codes.tasks import send_recovery_codes_email
from django_auth_recovery_codes.utils.exporters.file_converters import to_csv, to_pdf, to_text
from django_auth_recovery_codes.utils.notification import NOTIFICATION_CACHE_KEY


CACHE_KEY            = 'recovery_codes_generated_{}'
MINUTES_IN_SECONDS   = 600


TTL = getattr(settings, 'DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL', MINUTES_IN_SECONDS)
TTL = TTL if isinstance(TTL, int) else MINUTES_IN_SECONDS

SENDER_EMAIL =  settings.DJANGO_AUTH_RECOVERY_CODES_ADMIN_SENDER_EMAIL


# Create your views here.

logger = logging.getLogger("app.views")
User   = get_user_model()



@require_http_methods(['POST'])
@csrf_protect
@login_required
def recovery_codes_regenerate(request):
    """
    Regenerates the authenticated user's recovery codes and invalidates previous codes.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements. When called (e.g., via the Fetch API), it issues a new set of 
    recovery codes for the user and invalidates any existing codes to prevent reuse.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of the 
        regeneration operation. Typically includes updated recovery code state 
        for the frontend
    
    """
    request.session["is_downloaded"] = False
    request.session["is_emailed"]    = False
    request.session["force_update"]  = True
    return generate_recovery_code_fetch_helper(request, CACHE_KEY, regenerate_code = True)
   




@require_http_methods(['POST'])
@csrf_protect
@login_required
def delete_recovery_code(request):
    """
    Deletes a recovery code for the currently logged-in user.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements which means only a logged can access the function. 

    This view expects a POST request containing a JSON body with a 'code' key.
    It uses a generic helper (`recovery_code_operation_helper`) to handle the
    operation, including JSON parsing, error handling, and response formatting.

    The internal function `delete_code` defines the operation logic:
        - Retrieves the recovery code using `RecoveryCode.get_by_code_and_user`.
        - If the code exists, it delets the code and updates the batch.
        - Returns a tuple (success: bool, response_data: dict) indicating the result.

   **Note**  
    - Recovery codes are not deleted immediately. Instead, they are marked for deletion 
      and processed by a background task.  
    - This approach provides a smoother user experience by avoiding delays in the UI.  
    - It also reduces the risk of database contention or performance issues if many users
      attempt to delete codes at the same time.  


    The `operation_name` attribute is set to "Delete" so the helper can
    automatically generate meaningful success or failure messages if the internal
    function does not provide one.

    Returns:
        JsonResponse: JSON response indicating whether the code was successfully
        deactivated. The response contains 'SUCCESS' and may include additional
        messages or errors.
    """

    def delete_code(recovery_code: RecoveryCode) -> Tuple[bool, dict]:

        if not recovery_code:
            raise TypeError("The reocvery code instance must not be none")
        
        if not isinstance(recovery_code, RecoveryCode):
            raise TypeError(f"The recovery code must be an instance of the Recovery Model",
                            f"Expected a recovery model instance but got object with type: {type(recovery_code.__name__)}"
                            )
        
        recovery_code.delete_code()
        recovery_code_batch = recovery_code.batch
        recovery_code_batch.update_delete_code_count(save=True)

        
        response_data = {
            "SUCCESS": True,
            "OPERATION_SUCCESS": True,
            "TITLE": "Code deleted",
            "MESSAGE": "The code has been successfully deleted.",
            "ALERT_TEXT": "Code successfully deleted"
        }

        cache_key = f"attempts:recovery_code:{request.user.id}"
        delete_cache_with_retry(cache_key)

        return response_data
        
    
    delete_code.operation_name = "delete"  # Assign a custom attribute to the function for the helper to use
    return recovery_code_operation_helper(request, delete_code)


@require_http_methods(['POST'])
@csrf_protect
@login_required
def invalidate_user_code(request):
    """
    Deactivate a recovery code for the currently logged-in user.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements which means only a logged can access the function. 

    This view expects a POST request containing a JSON body with a 'code' key.
    It uses a generic helper (`recovery_code_operation_helper`) to handle the
    operation, including JSON parsing, error handling, and response formatting.

    The internal function `invalidate_code` defines the operation logic:
        - Retrieves the recovery code using `RecoveryCode.get_by_code_and_user`.
        - If the code exists, it invalidates the code and updates the batch.
        - Returns a tuple (success: bool, response_data: dict) indicating the result.

    The `operation_name` attribute is set to "Deactivate" so the helper can
    automatically generate meaningful success or failure messages if the internal
    function does not provide one.

    Returns:
        JsonResponse: JSON response indicating whether the code was successfully
        deactivated. The response contains 'SUCCESS' and may include additional
        messages or errors.
    """

    def invalidate_code(recovery_code: RecoveryCode) -> dict:

        if not recovery_code:
            raise TypeError("The reocvery code instance must not be none")
        
        if not isinstance(recovery_code, RecoveryCode):
            raise TypeError(f"The recovery code must be an instance of the Recovery Model",
                            f"Expected a recovery model instance but got object with type: {type(recovery_code.__name__)}"
                            )
        
        recovery_code.invalidate_code()
        recovery_code_batch = recovery_code.batch
        recovery_code_batch.update_invalidate_code_count(save=True)

        response_data = {
            "SUCCESS": True,
            "OPERATION_SUCCESS": True,
            "TITLE": "Code deactivated",
            "MESSAGE": "The code has been successfully deactivated.",
            "ALERT_TEXT": "Code successfully deactivated"
        }

        return response_data

    invalidate_code.operation_name = "deactivate"  # Assign a custom attribute to the function for the helper to use
    return recovery_code_operation_helper(request, invalidate_code)


@require_http_methods(['POST'])
@csrf_protect
@login_required
def download_code(request):
    """
    Allows the authenticated user to download their recovery codes as a file.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements which means only a logged can access the function. 

    Return the user recovery codes as a downloadable file (TXT, CSV, or PDF).
    The filename is set dynamically based on backend logic, so the frontend
    can extract it from the Content-Disposition header.

    Returns:
        HttpResponse or JsonResponse:
        - HttpResponse: File download response with the appropriate content type and 
          Content-Disposition header.
        - JsonResponse: Returned if the user has already downloaded the codes or if 
          no codes are available, indicating failure.

    Notes:
        - Only allows one download per batch; subsequent attempts return a JSON message.
        - Assumes the user has a valid RecoveryCodesBatch; otherwise JSON response is returned.

    """
    user = request.user

    try:
        cache = get_cache_or_set(CACHE_KEY.format(user.id), 
                                value_or_func=lambda: RecoveryCodesBatch.get_by_user(user=user).get_cache_values(),
                                ttl=TTL
                                )
    except AttributeError:
        cache = {}
        
    if cache and cache.get("downloaded"):
        return JsonResponse({
            "SUCCESS": False,
            "MESSAGE": "You have already downloaded your codes, only one download per batch"
        }, status=200)
      
    raw_codes = request.session.get("recovery_codes_state", {}).get("codes", [])

    if not raw_codes:
        request.session["is_downloaded"] = False
        return JsonResponse({
            "SUCCESS": False,
            "MESSAGE": "You logged or out before downloading the codes or hit the regenerate button, and due to security reasons you can no longer download the codes"
        }, status=200)

    if raw_codes:
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

    response["Content-Disposition"]  = f'attachment; filename="{file_name}"'
    response["X-Success"]            = "true"
    
    request.session["force_update"]  = True

    return response


@require_http_methods(['POST'])
@csrf_protect
@login_required
def mark_all_recovery_codes_as_pending_delete(request):
    """
    Marks all recovery codes for the authenticated user as pending deletion.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements, meaning that only authenticated users can perform this action.

    The view uses `soft delete` to delete the user's current recovery codes batch and
    resets session values, and updates the cache to prevent further 
    access to the codes (e.g., downloading  or emailing them).

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of the 
        operation.
        - SUCCESS: True if recovery codes were successfully marked for deletion; False otherwise.
        - MESSAGE: A descriptive message about the result.

    Notes:
        - Resets session values: "is_emailed" is set to False, "force_update" to True.
        - Removes raw codes from the session to prevent reuse on the frontend.
        - Updates the cache with reset values for security.
        - Returns status code 201 on success, 400 on failure.
        - Assumes that the user has existing recovery codes; otherwise returns failure.
    """
    
    recovery_batch  = RecoveryCodesBatch.delete_recovery_batch(request.user)
    status          = None
    data            = { "SUCCESS": False, "MESSAGE": ""}
    
    # reset the cache values
    if recovery_batch:

        request.session["is_emailed"]    = False
        request.session["force_update"]  = True
        
    
        # removes the raw codes from the session to ensure that it can't be downloaded or emailed 
        # when the frontend buttons are clicked
        request.session.get("recovery_codes_state", {}).pop("codes", None)  
        recovery_batch.reset_cache_values()
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
    """
    Sends recovery codes to the authenticated user's email.

    This view only accepts POST requests and is protected by CSRF and login 
    requirements, ensuring that only authenticated users can trigger the email action.

    Args:
        request (HttpRequest): The HTTP request object containing POST data.

    Returns:
        JsonResponse: A JSON response indicating the success or failure of the 
        email sending operation.

    Notes:
        - Only allows one email per batch.
        - Does not validate whether the user's email address is real.
        - Returns "not sent" if the email is invalid or fails to send.
        - This reusable app assumes that the user of the app has already verified that the email address is valid.

    """ 
   
    user       = request.user
    raw_codes  =  request.session.get("recovery_codes_state", {}).get("codes", None)
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
            "MESSAGE": "Backup codes can only be emailed once while you’re logged in. "
                       "Since you logged out or hit the regenerate buttion, they’re no longer available. Please log in to generate new codes."

        })
        return JsonResponse(resp, status=200)

    user = request.user

    if settings.DEBUG:

        # Development: uses threading for speed
        threading.Thread(target=send_recovery_codes_email,args=(SENDER_EMAIL, user, raw_codes) ).start()
    else:

        # Production: uses Django Q for reliability
        async_task(send_recovery_codes_email, SENDER_EMAIL, user, raw_codes)

    recovery_batch = RecoveryCodesBatch.get_by_user(request.user)
    recovery_batch.mark_as_emailed()

    set_cache_with_retry(CACHE_KEY.format(user.id), recovery_batch.get_cache_values(), TTL)
   
    request.session["is_emailed"]   = True  # needed to hide the page in the UI
    request.session["force_update"] = True
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


    This view is protected by CSRF and login requirements,mwhich ensures that only
    authenticated users can access the dashboard. 
    
    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: Returns a json response to fetch object indicating if
        successful or not along with any error messages.
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
            resp["SUCCESS"]                 = True
            request.session["force_update"] = True
   
    else:
        resp["ERROR"] = "Failed to set batch to marked because it wasn't found"
    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)

        

@require_http_methods(['POST'])
@csrf_protect
@login_required
def generate_recovery_code_with_expiry(request):
    """
    Generate a batch of recovery codes for the logged-in user with an expiry.

    This view is protected by CSRF and login requirements,mwhich ensures that only
    authenticated users can access the dashboard. 
    
    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: Returns a json response to fetch object, and amongs other things
         including the plain code.
    """
    return generate_recovery_code_fetch_helper(request, CACHE_KEY, generate_with_expiry_date=True)
   

@require_http_methods(['POST'])
@csrf_protect
@login_required
def generate_recovery_code_without_expiry(request):
    """
    Generate a batch of recovery codes for the logged-in user for an indefine period.

    This view is protected by CSRF and login requirements,mwhich ensures that only
    authenticated users can access the dashboard. 
    
    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: Returns a json response to fetch object, and amongs other things
         including the plain code.
    """
    return generate_recovery_code_fetch_helper(request, CACHE_KEY)


@csrf_protect
@login_required
def verify_test_code_setup(request):
    """
    Verify a test recovery code setup for the logged-in user.
    """
    response_data = {"SUCCESS": False, "MESSAGE": "", "ERROR": ""}

    try:
        data           = json.loads(request.body.decode("utf-8"))
        plaintext_code = data.get("code")

        if not plaintext_code:
            response_data.update({
                "MESSAGE": "No code provided.",
                "ERROR": "The JSON body did not include a 'code' field."
            })
            return JsonResponse(response_data, status=400)

        result = RecoveryCodesBatch.verify_setup(request.user, plaintext_code)
        if not isinstance(result, dict):
            raise TypeError(f"Expected a dictionary but got object with type ({type(result).__name__})")
        
        response_data.update(result)
        
        if not result.get("FAILURE"):
            cache_key  = CACHE_KEY.format(request.user.id)
            cache_data = get_cache_with_retry(cache_key)

            if cache_data:
                cache_data['user_has_done_setup'] = True
                set_cache_with_retry(cache_key, cache_data)
        return JsonResponse(response_data, status=200 if response_data["SUCCESS"] else 400)

    except IntegrityError as e:
        response_data.update({
            "ERROR": str(e),
            "MESSAGE": "Database integrity error occurred."
        })
        return JsonResponse(response_data, status=400)

    except Exception as e:
        response_data.update({
            "ERROR": str(e),
            "MESSAGE": "An unexpected error occurred."
        })
        return JsonResponse(response_data, status=500)



@csrf_protect
@login_required
def recovery_dashboard(request):
    """
    Renders the recovery dashboard for authenticated users.

    This view is protected by CSRF and login requirements,mwhich ensures that only
    authenticated users can access the dashboard. 

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered recovery dashboard page.
    """
    
    user                   = request.user
    cache_key              = CACHE_KEY.format(user.id)
    user_data              =  get_cache_with_retry(cache_key)
    context                = {}
    recovery_batch_context = get_recovery_batches_context(request)
    HAS_USER_SET_UP_KEY    = "user_has_done_setup"
      
    if user_data is None:

        view_logger.debug("The cache has expired. Pulling data from db and rewriting to the cache")

        # cache has expired, get data and re-add to cache
        recovery_batch = RecoveryCodesBatch.get_by_user(user)
      

        if recovery_batch:
            user_data                        = recovery_batch.get_cache_values()
            user_data[HAS_USER_SET_UP_KEY]   = RecoveryCodeSetup.has_first_time_setup_occurred(user)

            view_logger.debug("Data retrieved are: is_generated=%s, is_email=%s, is_viewed=%s, is_downloaded=%s, user_has_done_setup=%s",
                               user_data.get("generated"), user_data.get("emailed"), user_data.get("viewed"),
                               user_data.get("downloaded"), user_data.get("user_has_done_setup"),
                               user_data.get("number_used")
                    )

            set_cache_with_retry(cache_key, user_data)

    else:
        view_logger.debug("Getting the data from the cache instead of the database")
   
    if user_data:

        if set_setup_flag_if_missing_and_add_to_cache(user_data, request.user, HAS_USER_SET_UP_KEY):
            set_cache_with_retry(cache_key, user_data)

        context.update({
                "is_generated": user_data.get("generated"),
                "is_email": user_data.get("emailed"),
                "is_viewed": user_data.get("viewed"),
                "is_downloaded": user_data.get("downloaded"),
                "user_has_done_setup": user_data.get("user_has_done_setup"),
                "number_used": user_data.get("number_used"),
               
            })
        
    
    if not isinstance(recovery_batch_context, dict):
        raise TypeError(f"Expected a context dictionary but got object with type {type(recovery_batch_context).__name__}")

    context.update(recovery_batch_context)
    
    return render(request, "django_auth_recovery_codes/dashboard.html", context)


def login_user(request):
    """Logs the user into the given application"""

    form    = LoginForm()
    context = {}

    if request.user.is_authenticated:
        return redirect(reverse("recovery_dashboard"))

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():

            recovery_code = form.cleaned_data["recovery_code"]
            email         = form.cleaned_data["email"].strip()
            can_login, wait_time = None, None

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, "The code and email is invalid")
            else:
            
                user                 = User.objects.get(email=email)
                can_login, wait_time = LoginRateLimiter.is_locked_out(user)
              
                if can_login and wait_time == 0:
                    
                    code  = RecoveryCode.get_by_code_and_user(recovery_code, user)
                    
                    if code:

                        code.mark_code_as_used()
                        request.session["force_update"] = True
                        login(request, user)
                        return redirect(reverse("recovery_dashboard"))
                    else:
                        messages.add_message(request, messages.ERROR, "The code and email is invalid")
                    
                else:
                    wait_text = SecondsToTime(wait_time).format_to_human_readable()
                    
                    messages.error(request, "You have already exceeded the maximum number of login attempts.")
                    messages.error(request, f"You must wait {wait_text} before you can attempt to log in again.")
                    messages.warning(request, "Further attempts during this period will increase the penalty.")
                                    
    context["form"] = form
    return render(request, "django_auth_recovery_codes/login.html", context)


@csrf_protect
@login_required
def fetch_notifications(request):
    cache_key = NOTIFICATION_CACHE_KEY.format(request.user.id)
    HOURS_IN_SECS = 3600
    data = []

    # Try getting notifications from cache
    notifications_list = get_cache_with_retry(cache_key, default=[])

    if not notifications_list:
        # Cache miss → fetch from DB
        notifications_list, notification_instance = RecoveryCodeNotification.get_message_notifications(user=request.user)

        # Cache the fetched notifications
        if notifications_list:

            set_cache_with_retry(cache_key, notifications_list, HOURS_IN_SECS, log_failures=True)

            # Mark as read in DB
            notification_instance.update(is_read=True)

    else:
       
        notification_instance = None  # no DB objects available


    if notifications_list:
        data = [notification.message for notification in notifications_list]
        print(data)

    return JsonResponse({"notifications": data}, status=200)

@csrf_protect
@require_POST
@login_required
def logout_user(request):
    """
    logout_user view

    This view logs out the current user and redirects them afterwards.

    How it works?:

    1. Attempts to redirect to the view defined in the project settings:
    DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT

    2. If the setting is missing or the view does not exist,
    it falls back to the site root ('/') as a universal, safe location.

    Notes for developers:
    - Ensure DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT (in your settings.py)
    points to a valid URL pattern name if you want custom redirect behaviour.

    - Using '/' as the fallback ensures users are never left on an unknown or broken page
    after logout.
    """

    logout(request)
    request.session.flush()

    redirect_view_name = getattr(settings, "DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT", None)

    if redirect_view_name:
        try:
            return redirect(reverse(redirect_view_name))
        except NoReverseMatch:
            view_logger.error(
                f"Redirect view '{redirect_view_name}' does not exist. Falling back to site root.",
               
            )

    return redirect(reverse("login_user"))
    