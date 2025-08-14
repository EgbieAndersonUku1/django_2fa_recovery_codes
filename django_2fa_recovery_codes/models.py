import uuid
import secrets
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()

class RecoveryCodeIssuedHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    number_issued = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recovery codes batch for {self.user} on {self.created_at}"


class RecoveryCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    issued_batch = models.ForeignKey(RecoveryCodeIssuedHistory, on_delete=models.CASCADE, related_name="codes")
    hashed_code = models.CharField(max_length=128)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    has_been_shown = models.BooleanField(default=False)  # False means *not yet* shown to user
    days_to_expiry = models.PositiveBigIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["user", "used"]),
        ]

    def __str__(self):
        return f"RecoveryCode for {self.user} (used={self.used}, shown={self.has_been_shown})"

    @classmethod
    def generate_recovery_codes_for_user(cls, user, num_codes=10, should_expire=False, days_to_expiry=0):
        """
        Generates recovery codes for the user tied to an issued batch.
        Codes start with has_been_shown=False (not displayed yet).
        """
        if not isinstance(should_expire, bool):
            raise ValueError(f"should_expire must be bool, got {type(should_expire)}")
        if not isinstance(days_to_expiry, int):
            raise ValueError(f"days_to_expiry must be int, got {type(days_to_expiry)}")

        batch = RecoveryCodeIssuedHistory.objects.create(
        user=user,
        number_issued=num_codes,
        created_at=timezone.now(),
        )

        codes = []
        raw_codes = []
        for _ in range(num_codes):
            raw_code = secrets.token_hex(5).upper()  # e.g. 10 char hex code
            raw_codes.append(raw_code)
            hashed_code = make_password(raw_code)
            code_obj = cls(
                user=user,
                issued_batch=batch,
                hashed_code=hashed_code,
                has_been_shown=False,
                days_to_expiry=days_to_expiry if should_expire else 0,
            )
            codes.append(code_obj)

        cls.objects.bulk_create(codes)
        return raw_codes
