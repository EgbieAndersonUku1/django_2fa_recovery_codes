from django.test import TestCase
from django.utils import timezone
from django_auth_recovery_codes.models import RecoveryCodeSetup
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg



class RecoveryCodeMethodTestSetup(TestCase):
    """Test the one-time RecoveryCodeSetup model methods"""

    def setUp(self):
        """Create the basic startup test"""
        self.user           = create_user()
        self.recovery_setup = RecoveryCodeSetup.objects.create(user=self.user)

    def test_is_setup_method(self):
        """Test if the is_setup_method correctly returns a bool value"""
        self.assertFalse(self.recovery_setup.is_setup())
    
    def test_create_for_user_method(self):
        """
        GIVEN that the user wants to create a new recovery setup model
        WHEN `create_for_user()` is called
        THEN à brand new user should be created in the database
        AND the values `verified_at`, `created_at`, `modified_at` should contain time and `success` should be `False`

        """
        new_user       = create_user("new_user", email="new_user@example.com")
        EXPECTED_COUNT = 2  # one created in the setup method plus the one created in this method
        
        RecoveryCodeSetup.create_for_user(new_user)

        recovery_new_user_setup = RecoveryCodeSetup.objects.filter(user=new_user).first()
    
        self.assertTrue(recovery_new_user_setup)
        self.assertTrue(recovery_new_user_setup.user, new_user)

        self.assertEqual(new_user.username, recovery_new_user_setup.user.username)
        self.assertEqual(new_user.email, recovery_new_user_setup.user.email)

        # check count
        self.assertEqual(RecoveryCodeSetup.objects.count(), EXPECTED_COUNT)

    def test_if_recovery_model_can_be_marked_when_setup(self):
        """
        GIVEN that the user has successful verified their code setup
        WHEN `mark_as_verified()` and `has_first_time_setup_occurred()`
        THEN it should return True
        
        """
        self.recovery_setup.refresh_from_db()

        self.assertFalse(self.recovery_setup.success)
        self.recovery_setup.mark_as_verified()

        self.assertTrue(RecoveryCodeSetup.has_first_time_setup_occurred(self.user))


    def test_if_user_instance_is_valid(self):
        """
        GIVEN a valid user instance
        WHEN is_user_valid() is called
        THEN it should return True
        AND raise a TypeError with a proper message when an invalid instance is passed
        """

        self.assertTrue(self.recovery_setup.is_user_valid(self.user))
        from django.contrib.auth import get_user_model

        User = get_user_model()

        invalid_user_instance = RecoveryCodeSetup(user=self.user)
        expected_msg          = construct_raised_error_msg(
            "user",
            expected_types=User,
            value=invalid_user_instance,
        )

        with self.assertRaises(TypeError) as context:
            self.recovery_setup.is_user_valid(invalid_user_instance)

        self.assertEqual(str(context.exception), expected_msg)

    