from django.core.cache import cache
from contextlib import contextmanager

from .models import RecoveryCodesBatch, Status


def fetch_recovery_codes(user):
    """Query database for active recovery codes."""

    return (RecoveryCodesBatch.objects.filter(user=user,   
                                                  status=Status.ACTIVE).values("generated", 
                                                                               "downloaded",
                                                                                "emailed", 
                                                                                 "viewed",))
 