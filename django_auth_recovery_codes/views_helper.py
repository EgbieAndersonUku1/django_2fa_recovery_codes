import json
from django.http import JsonResponse
from django.db import IntegrityError
from django.http import HttpRequest

from .models import RecoveryCodesBatch, Status
from .utils.cache.safe_cache import set_cache



def fetch_recovery_codes(user):
    """Query database for active recovery codes."""

    return list(RecoveryCodesBatch.objects.filter(user=user,   
                                                  status=Status.ACTIVE).values("generated", 
                                                                               "downloaded",
                                                                                "emailed", 
                                                                                 "viewed",))
 

 
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
    
    resp = {"TOTAL_ISSUED": 0, 
            "SUCCESS": False,
             "ERROR": "", "codes": []
             }

    user = request.user

    if generate_with_expiry_date and not isinstance(generate_with_expiry_date, bool):
        raise TypeError(f"Expected `generate_with_expiry_date` flag to be a bool but got object with type {type(generate_with_expiry_date).__name__} ")
    
    if not isinstance(cache_key, str):
        raise TypeError(f"Expected the cache parameter to be a string but got object with type {type(cache_key).__name__} ")
          
    try:

        if generate_with_expiry_date:
            data           = json.loads(request.body.decode("utf-8"))
            days_to_expire = int(data.get("daysToExpiry", 0))

            if not isinstance(days_to_expire, int):
                raise TypeError(f"Expected an integer from the frontend fetch api but got object with type {type(days_to_expire).__name__} ")
            
            if days_to_expire <= 0:
                raise ValueError("daysToExpiry must be a positive integer")
            
            raw_codes = RecoveryCodesBatch.create_recovery_batch(
                user=user,
                days_to_expire=days_to_expire
            )
        else:
            raw_codes = RecoveryCodesBatch.create_recovery_batch(user)

        resp.update({
            "TOTAL_ISSUED": 1,
            "SUCCESS": True,
            "CODES": raw_codes
        })

        request.session["recovery_codes_state"] = {
                        "codes": raw_codes,
                    }
        
        # update the cache
        set_cache(cache_key.format(user.id),
                  value=fetch_recovery_codes(user)
                  )

    except IntegrityError as e:
        resp["ERROR"] = str(e)
    except json.JSONDecodeError:
        resp["ERROR"] = "Invalid JSON body"
    except Exception as e:
        resp["ERROR"] = str(e)

    return JsonResponse(resp, status=201 if resp["SUCCESS"] else 400)

