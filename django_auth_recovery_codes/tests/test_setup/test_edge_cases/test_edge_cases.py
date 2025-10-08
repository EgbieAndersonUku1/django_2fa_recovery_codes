from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError, transaction

from django_auth_recovery_codes.models import RecoveryCodeSetup
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user


class RecoveryCodeSetupEdgeCaseTest(TestCase):
    """Edge case tests for RecoveryCodeSetup model."""

    def setUp(self):
        
        self.user = create_user()

        # Ensure no pre-existing RecoveryCodeSetup exists for this user
        RecoveryCodeSetup.objects.filter(user=self.user).delete()
        self.recovery_setup = RecoveryCodeSetup.objects.create(user=self.user)

    def test_prevent_duplicate_recovery_setups_for_same_user(self):
        """
        GIVEN a user with an existing RecoveryCodeSetup
        WHEN attempting to create another RecoveryCodeSetup for the same user
        THEN it should raise an IntegrityError, but not break the transaction
        """
    
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                RecoveryCodeSetup.objects.create(user=self.user)

    def test_verified_at_updates_on_verification(self):
        """
        GIVEN a RecoveryCodeSetup instance
        WHEN marking it as verified
        THEN the verified_at timestamp should update to the current time
        """
        before_verification = timezone.now()
    
        self.recovery_setup.mark_as_verified()
        self.recovery_setup.refresh_from_db()

        self.assertIsNotNone(self.recovery_setup.verified_at)
        self.assertLessEqual(self.recovery_setup.verified_at, before_verification)
        self.assertLessEqual(self.recovery_setup.verified_at, timezone.now())

    def test_success_flag_changes_correctly(self):
        """
        GIVEN a RecoveryCodeSetup instance
        WHEN the setup is completed
        THEN the success flag should be set to True
        """
        self.assertFalse(self.recovery_setup.success)

        self.recovery_setup.mark_as_verified()
        
        is_setup = RecoveryCodeSetup.has_first_time_setup_occurred(user=self.user)

        self.assertTrue(is_setup)

    def tearDown(self):
        """
        Tear down the test safely.
        Use filter().delete() to avoid TransactionManagementError if
        the transaction is broken due to IntegrityError in any test.
        """
        RecoveryCodeSetup.objects.filter(user=self.user).delete()
