# """
# view_helpers.py

# This file contains helper functions specific to the views.

# Purpose:
# - Keep views.py clean and uncluttered.
# - Provide functionality that is specific to the view logic.

# Notes:
# - Not a general-purpose utilities module.
# - Functions here are intended to work only with the views.
# - Can be expanded in the future with more view-specific helpers.
# """


import json
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpRequest 
from typing import Callable,  Dict, Any, Tuple, List
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from typing import TypedDict


from django_auth_recovery_codes.utils.converter import SecondsToTime

from .models import RecoveryCode, RecoveryCodeSetup, RecoveryCodesBatch, Status
from .utils.cache.safe_cache import set_cache_with_retry, get_cache_with_retry, delete_cache_with_retry
from .loggers.loggers import view_logger, purge_code_logger


User = get_user_model()

CACHE_KEY                        = 'recovery_codes_generated_{}'
RECOVERY_CODES_BATCH_HISTORY_KEY = 'recovery_codes_batch_history_{}'

 
class ResponseDict(TypedDict):
    SUCCESS: bool
    OPERATION_SUCCESS: bool
    TITLE: str
    MESSAGE: str
    ALERT_TEXT: str


def _can_codes_be_generated_yet(user):
    """
    Determines whether a given user is allowed to generate a new set of recovery codes.

    The function calls `RecoveryCodesBatch.can_generate_new_code` to check if enough time has 
    passed since the last generation. 

    Args:
        user (User): The user object for which to check code generation eligibility.

    Returns:
        tuple:
            - can_generate_code (bool): True if the user can generate new codes, False otherwise.
            - wait_time (int): Time in seconds the user must wait before generating new codes.

    Notes:
        - If `RecoveryCodesBatch.can_generate_new_code` raises a ValueError, the function
          defaults to allowing code generation with zero wait time.
        - Logs both successful checks (debug) and handled exceptions (warning) for audit purposes.
    """
    try:
        can_generate_code, wait_time = RecoveryCodesBatch.can_generate_new_code(user)
        view_logger.debug(f"[RecoveryCodes] User={user.id} can_generate={can_generate_code}, wait_time={SecondsToTime(wait_time).format_to_human_readable()}")
    except ValueError:
        can_generate_code, wait_time = True, 0
        view_logger.warning(f"[RecoveryCodes] ValueError handled for user={user.id}, defaulting can_generate=True")
    return can_generate_code, wait_time


def _generate_recovery_codes_with_expiry_date_helper(
    request: HttpRequest,
    user: "User"
) -> Tuple[List[str], "RecoveryCodesBatch"]:
    """
    Generate a batch of 2FA recovery codes for a user, with an expiry date.

    Abstract:
        Takes an HttpRequest containing JSON data and a User instance, 
        generates a batch of 2FA raw recovery codes with an expiry date, 
        and assigns it to the user. Returns the raw codes and the batch instance.

    Request JSON must contain:
        - `daysToExpiry` (int): Number of days until the codes expire.

    Args:
        request (HttpRequest): Contains JSON information needed to create the 2FA codes.
        user (User): The user object for whom the codes are generated.

    Raises:
        TypeError: If `request` is not an HttpRequest instance.
        ValueError: If the request JSON is invalid.
        TypeError / ValueError: Raised by the model if:
            - `user` is not a valid User instance.
            - `daysToExpiry` is not an integer or <= 0.

    Returns:
        Tuple[List[str], RecoveryCodesBatch]:
            - raw_codes: List of raw recovery codes.
            - recovery_batch_instance: The batch instance model that created the codes.
    """
    if not isinstance(request, HttpRequest):
        raise TypeError(
            f"Expected the request to be an HttpRequest instance, got {type(request).__name__}"
        )

    try:
        data                      = json.loads(request.body.decode("utf-8"))
        days_to_expire            = int(data.get("daysToExpiry", 0))
        raw_codes, batch_instance = RecoveryCodesBatch.create_recovery_batch(user=user, days_to_expire=days_to_expire)
        
    except IntegrityError as e:
        raise ValueError(f"[RecoveryCodes] IntegrityError for user={request.user.id}: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in request body: {str(e)}")
    except TypeError as e:
        raise TypeError(str(e))

    return raw_codes, batch_instance


def _generate_code_batch(request, generate_with_expiry_date):
    user = request.user
    if generate_with_expiry_date:
        raw_codes, batch_instance = _generate_recovery_codes_with_expiry_date_helper(request, user)
    else:
        raw_codes, batch_instance = RecoveryCodesBatch.create_recovery_batch(user)
    return raw_codes, batch_instance


def set_setup_flag_if_missing_and_add_to_cache(cache_data, user, flag_name):
    """
    Ensures the HAS_SET_UP_FLAG is present in cache_data.
    If missing, computes its value and updates the cache.
    """
    
    if not isinstance(user, User):
        raise ValueError(f"Expected a user instance but got {type(user).__name__}")
    
    if not isinstance(flag_name, str):
        raise ValueError(f"Expected a string instance but got {type(flag_name).__name__}")
    
    try:
        if flag_name not in cache_data:
            view_logger.debug(
                f"Flag not found in cache, setting '{flag_name}' to the cache"
            )
            cache_data[flag_name] = (
                RecoveryCodeSetup.has_first_time_setup_occurred(user) or False
            )
            return True
           
    except Exception as e:
        view_logger.debug(str(e))
        raise 
    return False


def generate_recovery_code_fetch_helper(request: HttpRequest, cache_key: str,  generate_with_expiry_date: bool = False, regenerate_code = False):
    """
    Generate recovery codes for a user, optionally with an expiry date.

    If `generate_with_expiry_date` is True, the number of days until expiry is 
    extracted from `request.body` (JSON) as `daysToExpiry`. Otherwise, the codes 
    are generated indefinitely.

    The generated codes are saved in the user's session and also updated in the cache.

    Args:
        request (HttpRequest): The Django request object containing user information.
        generate_with_expiry_date (bool, optional): Flag indicating whether to generate codes 
            with an expiry date. Defaults to False.
        
        cache_key (str): A string to be used for the cache

    Raises:
        ValueError: If `daysToExpiry` from the frontend is less than or equal to 0.
        TypeError: If `daysToExpiry` is not an integer, or `generate_with_expiry_date` is not a bool.

    Returns:
        JsonResponse: A JSON response containing the status, issued codes, and any error messages.
    """
    if generate_with_expiry_date and not isinstance(generate_with_expiry_date, bool):
        raise TypeError(
            f"Expected `generate_with_expiry_date` flag to be a bool but got object with type {type(generate_with_expiry_date).__name__} "
        )

    if not isinstance(cache_key, str):
        raise TypeError(
            f"Expected the cache parameter to be a string but got object with type {type(cache_key).__name__} "
        )

    cache_key   = CACHE_KEY.format(request.user.id)
    cache_data  = get_cache_with_retry(cache_key, default={})    
   
    view_logger.debug(f"Retrieving the cache in order to check if the user has already run test setup. Cache data: {cache_data}")

    HAS_SET_UP_FLAG = "user_has_done_setup"

    set_setup_flag_if_missing_and_add_to_cache(cache_data, request.user, HAS_SET_UP_FLAG)
    set_cache_with_retry(cache_key, cache_data)

    resp = {
            "TOTAL_ISSUED": 0,
            "SUCCESS": False,
            "ERROR": "",
            "codes": [],
            "MESSAGE": "",
            "CAN_GENERATE": False,
            "HAS_COMPLETED_SETUP": cache_data.get(HAS_SET_UP_FLAG),
            }

    try:
        user       = request.user
        raw_codes  = []

        if not regenerate_code:
             can_generate_code, wait_time = True, 0
        else:
             can_generate_code, wait_time = _can_codes_be_generated_yet(user)
            
        time_to_wait = SecondsToTime(wait_time).format_to_human_readable() or None
        purge_code_logger.debug(f"[GENERATE NEW CODE] Can generate code = {can_generate_code}, wait_time = {time_to_wait}")

        if can_generate_code and time_to_wait is None:

            raw_codes, batch_instance = _generate_code_batch(request, generate_with_expiry_date)

            resp.update(
                {

                    "SUCCESS": True,
                    "CODES": raw_codes,
                    "BATCH": batch_instance.get_json_values(),
                    "ITEM_PER_PAGE": settings.DJANGO_AUTH_RECOVERY_CODE_PER_PAGE,
                    "CAN_GENERATE": True,
                    "MESSAGE": "Your recovery code has been generated",
                }
            )
            view_logger.info(f"[RecoveryCodes] Generated new codes for user={user.id}, batch_id={batch_instance.id}")

        elif wait_time:
     
            resp.update(
                {
                    "MESSAGE": f"You have to wait {time_to_wait} before you can request a new code",
                    "SUCCESS": True,
                    "CAN_GENERATE": False,
                }
            )
            view_logger.info(f"[RecoveryCodes] User={user.id} must wait {time_to_wait} before generating a new code")
    
        # session state
        request.session["recovery_codes_state"] = {"codes": raw_codes}
     
        # update the cache
        values_to_save_in_cache = {
            "generated": True,
            "downloaded": False,
            "emailed": False,
            "viewed": False,
            "user_has_done_setup": cache_data.get(HAS_SET_UP_FLAG, False)
        }

        set_cache_with_retry(cache_key.format(user.id), value=values_to_save_in_cache)
        view_logger.debug(f"[RecoveryCodes] Updated cache for user={user.id}, key={cache_key}")

        # request flags
        data = json.loads(request.body.decode("utf-8"))
        request.session["force_update"] = data.get("forceUpdate", False)

    except IntegrityError as e:
        resp["ERROR"] = str(e)
        view_logger.error(f"[RecoveryCodes] IntegrityError for user={request.user.id}: {e}")
    except json.JSONDecodeError:
        resp["ERROR"] = "Invalid JSON body"
        view_logger.error(f"[RecoveryCodes] Invalid JSON body for user={request.user.id}")
    except Exception as e:
        resp["ERROR"] = "Exception error " + str(e)
        view_logger.exception(f"[RecoveryCodes] Unexpected error for user={request.user.id}")

    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)


def recovery_code_operation_helper(
    request: HttpRequest,
    func: Callable[[RecoveryCode], Dict[str, Any]]
) -> JsonResponse:
    """
    Execute a recovery code operation on a RecoveryCode instance and return
    a standardized JSON response.

    Abstract:
        Wraps a callable that performs an operation (e.g., deactivate or delete)
        on a RecoveryCode and returns a ResponseDict. Ensures frontend receives
        consistent success flags and messages.

    Args:
        request (HttpRequest): The incoming HTTP request.
        recovery_code (RecoveryCode): The recovery code instance to operate on.
        func (Callable[[RecoveryCode], ResponseDict]): Function performing the operation.
            Must accept a RecoveryCode and return a ResponseDict.

    Returns:
        JsonResponse: JSON response containing keys:
            - "SUCCESS"
            - "OPERATION_SUCCESS"
            - "TITLE"
            - "MESSAGE"
            - "ALERT_TEXT"

    Notes:
        The `success` value in the ResponseDict is typically True. Returning False
        indicates an actual error, but situations like a code already being `used`,
        `deleted`, or `invalidated` are considered non-errors and still pass `success=True`.
        This allows the frontend to display the appropriate message consistently.


    Examples:
        >>> # Example 1: Deactivate a recovery code using recovery_code_operation_helper
        >>>
        >>> def deactivate_code(recovery_code):
        ...     recovery_code.invalidate_code()
        ...     recovery_code.invalidate_code()
        ...     recovery_code_batch = recovery_code.batch
        ...     recovery_code_batch.update_invalidate_code_count(save=True)
        ...
        ...     return {
        ...         "SUCCESS": True,
        ...         "OPERATION_SUCCESS": True,
        ...         "TITLE": "Code deactivated",
        ...         "MESSAGE": "The code has been successfully deactivated.",
        ...         "ALERT_TEXT": "Code deactivated"
        ...     }
        >>>
        >>> deactivate_code.operation_name = "deactivate"
        >>> response = recovery_code_operation_helper(request, deactivate_code)
        >>> print(response.status_code)
        200

        >>> # Example 2: Delete a recovery code using `recovery_code_operation_helper`
        >>> def delete_code(recovery_code):
        ...
        ...     
        ...     recovery_code.delete_code()
        ...     recovery_batch = recovery_code.batch
        ...     recovery_batch.update_delete_code_count()
        ...
        ...     return {
        ...         "SUCCESS": True,
        ...         "OPERATION_SUCCESS": True,
        ...         "TITLE": "Code deleted",
        ...         "MESSAGE": "The code has been successfully deleted.",
        ...         "ALERT_TEXT": "Code deleted"
        ...     }
        >>> delete_code.operation_name = "delete"
        >>> response = recovery_code_operation_helper(request, delete_code)
        >>> print(response.status_code)
        200
    """

    response_data = {'SUCCESS': False, "OPERATION_SUCCESS": False, "MESSAGE": ""}

    try:
        data = json.loads(request.body.decode("utf-8"))
    
    except json.JSONDecodeError:
        response_data["ERROR"] = "Invalid JSON body"
        return JsonResponse(response_data, status=400)

    plaintext_code = data.get("code")

    if not plaintext_code:
        response_data["MESSAGE"] = "The plaintext code wasn't found in the JSON body"
        return JsonResponse(response_data, status=400)

    if not callable(func):
        raise ValueError("The function must be callable and take one parameter: (str)")
    
    try:
        response_data = _process_recovery_code_response(plaintext_code, request, func)
      
    except IntegrityError as e:
        response_data["ERROR"] = str(e)
        response_data["SUCCESS"] = 400
    except Exception as e:
        response_data["ERROR"] = str(e)
        response_data["SUCCESS"] = 400
    

    return JsonResponse(response_data, status=201 if response_data["SUCCESS"] else 400)


def _process_recovery_code_response(plaintext_code: str, request: HttpRequest, func: Callable[[RecoveryCode], Dict[str, Any]]):
    """
    Processes a recovery code and return a structured response dictionary.

    This function checks the provided recovery code against several conditions:
      - Whether the code exists
      - Whether the code has already been used
      - Whether the code has been deactivated
      - Whether the code is marked for deletion

    If the code fails any of these checks, a response dictionary with an error
    message is returned. If the code is valid, the given `func` is executed
    and its result is returned as the response.

    Args:
        plaintext_code (str): The recovery code provided by the user.
        user (User): The user associated with the recovery code.
        func (Callable): A callable executed if the code is valid.

    Returns:
        dict: A response dictionary containing keys such as SUCCESS,
              OPERATION_SUCCESS, TITLE, MESSAGE, and ALERT_TEXT.
    """
  
    recovery_code      = RecoveryCode.get_by_code_and_user(plaintext_code, request.user)
    REQUIRED_FUNC_KEYS = {"delete", "deactivate"}

    if recovery_code is None:
        response_data =  _make_response(
            title="Invalid code",
            message="The code is invalid or no longer exists.",
            alert_text="Invalid code"
        )
      
    elif recovery_code.is_used:
        response_data =  _make_response(
            title="Code already used",
            message="The code has already been used.",
            alert_text="This code was already used"
        )
    elif recovery_code.is_deactivated:
        response_data =  _make_response(
            title="Code already deactivated",
            message="The code has already been deactivated.",
            alert_text="Code already deactivated"
        )
    elif recovery_code.mark_for_deletion:
         response_data = _make_response(
            title="Code already deleted",
            message="The code has already been deleted.",
            alert_text="Code already deleted"
        )
    else:
        request.session["force_update"]  = True  # force update to tell app not to use the cache get from db and the update cache
        response_data = func(recovery_code)

    invalid_operation = func.operation_name if func else "None"

    if func is None or invalid_operation.lower() not in REQUIRED_FUNC_KEYS:
        response_data = _make_response(
            title="Invalid operation",
            message=f"The operation '{invalid_operation}' entered is invalid.",
            alert_text="Could not proceed: received an invalid operation"
        )

    return response_data


def _make_response(title: str, message: str, alert_text: str, success: bool = True) -> ResponseDict:
    """
    Generate a standardized response dictionary for frontend alerts.

    Abstract:
        Returns a ResponseDict containing success flags and messages 
        formatted for frontend use (e.g., SweetAlert2) to indicate
        whether an operation succeeded or failed.

    Args:
        title (str): Short title describing the outcome, e.g., "Failed to delete code".
        message (str): A detailed message about the operation.
        alert_text (str): Additional text for frontend alerts or notifications.
        success (bool, optional): Indicates whether the operation succeeded. 
            Defaults to True. Returning False indicates an error, which is not always
            the case. For example, a code may have already been `deleted`, `used`,
            `invalidated`, etc. This value is passed to the frontend to display the 
            appropriate message.

    Returns:
        ResponseDict: Keys include:
            - "SUCCESS" (bool)
            - "OPERATION_SUCCESS" (bool)
            - "TITLE" (str)
            - "MESSAGE" (str)
            - "ALERT_TEXT" (str)

    Examples:
        >>> resp: ResponseDict = _make_response(
        ...     title="Code Deleted",
        ...     message="The code has been successfully deleted.",
        ...     alert_text="Code deleted",
        ...     success=True
        ... )
        >>> resp["SUCCESS"]
        True
        >>> resp["TITLE"]
        'Code Deleted'
    """
    return {
        "SUCCESS": success,
        "OPERATION_SUCCESS": success,
        "TITLE": title,
        "MESSAGE": message,
        "ALERT_TEXT": alert_text,
    }


def get_recovery_batches_context(request):
    """
    Returns a context dict with recovery batches, paginated.
    Automatically refreshes cache if the session flag indicates update.

    Note:

    The data is always pulled from the cache and never from database. If
    an update is made (e.g the batch updated) the new data is added to
    the database and then to the cache before the updated data in the 
    cache is used.
    """
    user               = request.user
    recovery_cache_key = RECOVERY_CODES_BATCH_HISTORY_KEY.format(user.id)
    context            = {}

    PAGE_SIZE = settings.DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE
    PER_PAGE  = settings.DJANGO_AUTH_RECOVERY_CODE_PER_PAGE

    # fetch from cache or DB. When force_update is True fetch from db and when false cache  
    force_update = request.session.get("force_update", False)

    if not force_update:
        recovery_batch_history = get_cache_with_retry(recovery_cache_key)
    else:
        delete_cache_with_retry(recovery_cache_key)
        recovery_batch_history = None
        request.session.pop("force_update")
  
    if recovery_batch_history is None:
        recovery_batch_history = list(
            RecoveryCodesBatch.objects.filter(user=user).order_by("-created_at")[:PAGE_SIZE]
        )
        set_cache_with_retry(recovery_cache_key, value=recovery_batch_history)

    if recovery_batch_history:
        request.session["show_batch"]  = True

    paginator   = Paginator(recovery_batch_history, PER_PAGE)
    page_number = request.GET.get("page", 1)

    try:
        recovery_batches = paginator.page(page_number)
    except PageNotAnInteger:
        recovery_batches = paginator.page(1)
    except EmptyPage:
        recovery_batches = paginator.page(paginator.num_pages)

    context["recovery_batches"] = recovery_batches
    context["Status"]           = Status

    return context

