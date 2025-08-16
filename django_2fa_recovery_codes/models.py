import uuid
import secrets
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

from django_2fa_recovery_codes.utils.security.generator import generate_2fa_recovery_code_batch
from django_2fa_recovery_codes.utils.security.security import identify_hasher
from django_2fa_recovery_codes.utils.utils import schedule_future_date


User = get_user_model()

class Status(models.TextChoices):
    ACTIVE         = "a", "Active"
    INVALIDATE     = "i", "Invalidate"
    USED           = "u", "Used"
    PENDING_DELETE = "p", "Pending Delete"


class RecoveryCodeCleanUpScheduler(models.Model):
    class Status(models.TextChoices):
        SUCCESS        = "s", "Success"
        FAILURE        = "f", "Failure"
        DELETED        = "d", "Deleted"
    
    class Schedule(models.TextChoices):
        ONCE    = "O", "Once"
        MINUTES = "T", "Minutes"
        HOURLY  = "H", "Hourly"
        DAILY   = "D", "Daily"
        WEEKLY  = "W", "Weekly"
        QUARTERLY = "Q", "Quarterly"
        YEARLY  = "Y", "Yearly"

    run_at           = models.DateTimeField()
    deleted_count    = models.PositiveIntegerField(default=0)
    enable_scheduler = models.BooleanField(default=True)
    status           = models.CharField(max_length=1, choices=Status)
    error_message    = models.TextField()

    class Meta:
        ordering = ['-run_at']

    def __str__(self):
        return f"{self.run_at} - {self.status} - Deleted {self.deleted_count}"



class RecoveryCodesBatch(models.Model):
    id                = models.UUIDField(unique=True, db_index=True)
    number_issued     = models.PositiveBigIntegerField()
    number_removed    = models.PositiveBigIntegerField()
    user              = models.ForeignKey(User, on_delete=models.SET_NULL)
    created_at        = models.DateTimeField(auto_now_add=True)
    modified_at       = models.DateTimeField(auto_now=True)
    status            = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE)
    automatic_removal = models.BooleanField(default=True)
    expiry_date       = models.DateTimeField()


    def __str__(self):
        return f"{self.id}"
    
    @classmethod
    def create_recovery_batch(cls, batch_number=10):
        """"""
        pass

    @classmethod
    def delete_recovery_batch(cls, batch_id):
        """"""
        pass

  


class RecoveryCode(models.Model):
    id                = models.UUIDField(unique=True, db_index=True)
    hash_code         = models.CharField(max_length=128, unique=True, db_index=True)
    is_active         = models.BooleanField(default=True)
    mark_for_deletion = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)
    modified_at       = models.DateTimeField(auto_now=True)
    status            = models.CharField(choices=Status, max_length=1, default=Status.ACTIVE)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recovery_codes")
    batch             = models.ForeignKey(RecoveryCodesBatch, on_delete=models.CASCADE, related_name="recovery_codes")
    automatic_removal = models.BooleanField(default=True)
    days_to_expiry    = models.PositiveSmallIntegerField(default=0)


    def __str__(self):
        """Returns a string representation of the class"""

        email = self.user.email
        return f"{email}" if self.user.email else self.id
    
    def mark_code_for_deletion(self, save: bool = True):
        """
        Marks this recovery code for deletion.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.mark_code_for_deletion()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.mark_code_for_deletion(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """
        self.mark_for_deletion = True
        if save:
            self.save(update_fields=["mark_for_deletion"])
        return True

    def invalidate_code(self, save: bool = True):
        """
        Marks this recovery code as in-active.

        If `save` is True (default), the change is immediately persisted to the database.
        If `save` is False, the change is applied in memory and will not be written 
        to the database until you explicitly call `.save()` later. Note if a code
        is set to invalid it is not deleted and can be re-activated. However, if
        the code has been in-active for x-amount of days then it will be 
        automatically deleted. The days to be deleted is determined by the
        flags in the settings.

        Without the optional `save` parameter, making multiple changes in a single 
        operation can result in multiple database writes.

        Example 1 (less efficient):
            # This results in TWO database hits
            code.invalidate_code()  # First hit (inside method)
            code.some_other_field = "new value"
            code.save()                    # Second hit

        Example 2 (optimised):
            # This results in ONE database hit
            code.invalidate_code(save=False)
            code.some_other_field = "new value"
            code.save()  # Both changes persisted together
        """
        self.is_active = True
        if save:
            self.save(update_fields=["is_active"])
        return True

    @classmethod
    def get_by_code(cls, code: str) -> str:
        if not isinstance(code, str):
            raise ValueError(f"The code parameter is not a string. Expected a string but got an object with type {type(code)}")
        return make_password(code)
    
    def hash_code(self, code: str):
        if code:
            self.hash_code = make_password(code)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid4()

        # ensure that is code is always saved as hash and never as a plaintext
        if self.hash_code and not identify_hasher(self.hash_code):
            make_password(self.hash_code)
        super().save(*args, **kwargs)

