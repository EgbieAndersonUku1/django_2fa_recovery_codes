# """
# view_helpers.py

# This file contains helper functions specific to the views in specific dashboard.

# Purpose:
# - Keep views.py clean and uncluttered.
# - Provide functionality that is specific to the view logic.

# Notes:
# - Not a general-purpose utilities module.
# - Functions here are intended to work only with the views.
# - Can be expanded in the future with more view-specific helpers.
# """

from django.conf import settings

from django.core.paginator                             import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth                               import get_user_model
from django_auth_recovery_codes.models                 import RecoveryCodesBatch, Status
from django_auth_recovery_codes.utils.cache.safe_cache import set_cache_with_retry, get_cache_with_retry, delete_cache_with_retry


User = get_user_model()

RECOVERY_CODES_BATCH_HISTORY_KEY = 'recovery_codes_batch_history_{}'

 
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

