import json
from django.http import JsonResponse
from django.db import IntegrityError
from django.http import HttpRequest 
from typing import Callable, Tuple, Dict, Any
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from .models import RecoveryCodesBatch, Status
from .utils.cache.safe_cache import set_cache_with_retry, get_cache_with_retry, delete_cache_with_retry


RECOVERY_CODES_BATCH_HISTORY_KEY = 'recovery_codes_batch_history_{}'
ITEM_PER_PAGE                   = 5  # This will be taking from teh settings for now constant
 

def _generate_recovery_codes_with_expiry_date_helper(request, user) -> list:
     
    data           = json.loads(request.body.decode("utf-8"))
    days_to_expire = int(data.get("daysToExpiry", 0))

    if not isinstance(days_to_expire, int):
        raise TypeError(f"Expected an integer from the frontend fetch api but got object with type {type(days_to_expire).__name__} ")
            
    if days_to_expire <= 0:
        raise ValueError("daysToExpiry must be a positive integer")
            
    raw_codes, batch = RecoveryCodesBatch.create_recovery_batch(user=user, days_to_expire=days_to_expire)
    return raw_codes, batch


def generate_recovery_code_fetch_helper(request: HttpRequest, cache_key: str,  generate_with_expiry_date: bool = False):
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
        raise TypeError(f"Expected `generate_with_expiry_date` flag to be a bool but got object with type {type(generate_with_expiry_date).__name__} ")
    
    if not isinstance(cache_key, str):
        raise TypeError(f"Expected the cache parameter to be a string but got object with type {type(cache_key).__name__} ")
          
    try:
        resp = {"TOTAL_ISSUED": 0, 
            "SUCCESS": False,
             "ERROR": "", "codes": []
             }

        user  = request.user
        batch = None

        if generate_with_expiry_date:
           
            raw_codes, batch = _generate_recovery_codes_with_expiry_date_helper(request, user)
        else:
            raw_codes, batch = RecoveryCodesBatch.create_recovery_batch(user)

        resp.update({
            "TOTAL_ISSUED": 1,
            "SUCCESS": True,
            "CODES": raw_codes,
            "BATCH": batch.get_json_values(), 
            "ITEM_PER_PAGE": ITEM_PER_PAGE,
        })

        request.session["recovery_codes_state"] = {"codes": raw_codes}
        request.session["is_emailed"]           = False
        request.session["is_downloaded"]        = False


        # update the cache
        values_to_save_in_cache = {
            "generated": True,
            "downloaded": False,
            "emailed": False,
            "viewed": False
        }
        
        set_cache_with_retry(cache_key.format(user.id), value=values_to_save_in_cache)
        
        data                             = json.loads(request.body.decode("utf-8"))   
        request.session["force_update"]  = data.get("forceUpdate", False)

    except IntegrityError as e:
        resp["ERROR"] = str(e)
    except json.JSONDecodeError:
        resp["ERROR"] = "Invalid JSON body"
    except Exception as e:
        resp["ERROR"] = str(e)

    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)




def recovery_code_operation_helper(
                                    request: HttpRequest,
                                    func: Callable[[str], Tuple[bool, Dict[str, Any]]]
                                ) -> JsonResponse:
    """
    Perform a generic operation on a recovery code (e.g., invalidate or remove).
    
    If the internal function does not provide a 'MESSAGE', this helper
    will automatically create a default one using the function's
    'operation_name' attribute (if set) or fallback to 'Code operation'.
    """
    
    resp = {'SUCCESS': False, 'ERROR': '', 'MESSAGE': 'Code operation failed'}

    try:
        data = json.loads(request.body.decode("utf-8"))
        # print(data)
    except json.JSONDecodeError:
        resp["ERROR"] = "Invalid JSON body"
        return JsonResponse(resp, status=400)

    plaintext_code = data.get("code")

      
    if not plaintext_code:
        resp["MESSAGE"] = "The plaintext code wasn't found in the JSON body"
        return JsonResponse(resp, status=400)

    if not callable(func):
        raise ValueError("The function must be callable and take one parameter: (str)")

    operation_name = getattr(func, "operation_name", "Code operation")  # Retrieve the operation name from the function, or use a default
    
  
    try:
        success, response_data = func(plaintext_code)
    
        resp.update(response_data)
        resp["SUCCESS"] = success

        # Auto-generate MESSAGE if not provided
        if "MESSAGE" not in resp or not resp["MESSAGE"]:
            resp["MESSAGE"] =  f"{operation_name} succeeded"  if success else f"{operation_name} failed"
        
     
    except IntegrityError as e:
        resp["ERROR"] = str(e)
    except Exception as e:
        resp["ERROR"] = str(e)

    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)



def get_recovery_batches_context(request):
    """
    Returns a context dict with recovery batches, paginated.
    Automatically refreshes cache if the session flag indicates update.
    """
    user               = request.user
    recovery_cache_key = RECOVERY_CODES_BATCH_HISTORY_KEY.format(user.id)
    context            = {}

    PAGE_SIZE = 20
    PER_PAGE  = 5

    # fetch from cache or DB
   
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
