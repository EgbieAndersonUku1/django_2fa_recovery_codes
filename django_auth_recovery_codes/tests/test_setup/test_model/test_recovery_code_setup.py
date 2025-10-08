from django.test import TestCase
from django.utils import timezone

from django_auth_recovery_codes.models import RecoveryCodeSetup
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg

class RecoveryCodeSetupTest(TestCase):
    """Tests for the RecoveryCodeSetup model."""

    def setUp(self):
        """Set up a user and associated RecoveryCodeSetup instance."""
        self.user = create_user()
        self.recovery_setup = RecoveryCodeSetup.objects.create(user=self.user)

    def test_created(self):
        """
        GIVEN a RecoveryCodeSetup instance
        WHEN it is created
        THEN it should exist in the database
        AND have correct default field values and timestamps
        """
        recovery_code_setup = RecoveryCodeSetup.objects.get(user=self.user)
        self.assertIsNotNone(recovery_code_setup)
        self.assertFalse(recovery_code_setup.success)

        current_time = timezone.now()

        if recovery_code_setup.verified_at:
            self.assertLessEqual(recovery_code_setup.verified_at, current_time)
        self.assertLessEqual(recovery_code_setup.created_at, current_time)
        self.assertLessEqual(recovery_code_setup.modified_at, current_time)

    def test_count_created_is_one(self):
        """
        GIVEN a single RecoveryCodeSetup instance
        WHEN counting instances for the user
        THEN exactly one should exist
        """
        EXPECTED_COUNT = 1
        count = RecoveryCodeSetup.objects.filter(user=self.user).count()
        self.assertEqual(count, EXPECTED_COUNT, "Expected a single count of 1")

    def test_string_representation(self):
        """
        GIVEN a RecoveryCodeSetup instance
        WHEN converting it to string
        THEN it should return the expected descriptive string
        """
        recovery_code_setup = RecoveryCodeSetup.objects.get(user=self.user)
        EXPECTED_STR = "User has run first time setup: False"
        self.assertEqual(
            EXPECTED_STR,
            str(recovery_code_setup),
            "The string representation does not match the expected string",
        )

    def test_correct_user_association(self):
        """
        GIVEN a RecoveryCodeSetup instance
        WHEN accessing its user field
        THEN it should be associated with the correct user instance
        """
        self.recovery_setup.refresh_from_db()
        self.assertEqual(self.user, self.recovery_setup.user)
        self.assertEqual(self.user.username, self.recovery_setup.user.username)
        self.assertEqual(self.user.email, self.recovery_setup.user.email)

    def test_if_user_instance_is_valid(self):
        """
        GIVEN a valid and invalid user instance
        WHEN calling is_user_valid()
        THEN it should return True for valid instances
        AND raise a TypeError with the correct message for invalid instances
        """

        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Valid instance
        self.assertTrue(self.recovery_setup.is_user_valid(self.user))

        invalid_user_instance = RecoveryCodeSetup(user=self.user)
        
        with self.assertRaises(TypeError) as context:
            RecoveryCodeSetup.is_user_valid(invalid_user_instance)
        
        self.assertEqual(str(context.exception), construct_raised_error_msg("user", expected_types=User, value=invalid_user_instance ))
       