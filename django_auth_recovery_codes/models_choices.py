from django.db import models


class Status(models.TextChoices):
    """Choices representing the status of a recovery code."""

    ACTIVE         = "a", "Active"
    INVALIDATE     = "i", "Invalidate"
    PENDING_DELETE = "p", "Pending Delete"
    DELETED        = "d", "Deleted"
