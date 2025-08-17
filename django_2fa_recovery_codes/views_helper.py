from django.core.cache import cache
from contextlib import contextmanager

from .models import RecoveryCodesBatch, Status


@contextmanager
def cache_lock(key, timeout=5):
    lock_key = f"lock_{key}"
    lock_acquired = cache.add(lock_key, "1ocked", timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            cache.delete(lock_key)




def fetch_recovery_codes(user):
    """Query database for active recovery codes."""

    return (RecoveryCodesBatch.objects.filter(user=user,   
                                                  status=Status.ACTIVE).values("generated", 
                                                                               "downloaded",
                                                                                "emailed", 
                                                                                 "viewed",))
 