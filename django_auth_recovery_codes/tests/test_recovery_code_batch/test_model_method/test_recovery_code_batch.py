from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model


from django_auth_recovery_codes.models                  import RecoveryCodesBatch
from django_auth_recovery_codes.models_choices          import Status
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.security.hash     import is_already_hashed, make_lookup_hash
from django_auth_recovery_codes.utils.utils             import schedule_future_date


User = get_user_model()

# ----------------------------------------
# Generation Helpers
# ----------------------------------------
def _recovery_codes_generate(user, use_with_expiry_days: bool = False, days_to_expire: int = None):
    """
    Generates a batch of recovery codes for a given user.

    Args:
        user: The user for whom the recovery codes will be generated.
        use_with_expiry_days (bool, optional): If True, sets an expiry date for the codes.
        days_to_expire (int, optional): Number of days until the codes expire. Required if use_with_expiry_days is True.

    Returns:
        tuple: (raw_codes, batch_instance) where raw_codes is the list of generated codes
               and batch_instance is the RecoveryCodesBatch object.
    """
    if use_with_expiry_days and days_to_expire is not None and isinstance(days_to_expire, int):
        return RecoveryCodesBatch.create_recovery_batch(user, days_to_expire=days_to_expire)
    return RecoveryCodesBatch.create_recovery_batch(user)


# ----------------------------------------
# Assertion Helpers
# ----------------------------------------
def _recovery_codes_assert_batch(
    test_case: TestCase,
    batch_instance: RecoveryCodesBatch,
    days_to_expire: int = None,
    test_with_expiry_days: bool = True
):
    """
    Asserts properties of a RecoveryCodesBatch, including optional expiry date checks.

    Args:
        test_case: The TestCase instance calling this helper.
        batch_instance: The RecoveryCodesBatch object to validate.
        days_to_expire (int, optional): Expected number of days until expiry.
        test_with_expiry_days (bool, optional): Whether to check expiry date.
    """
    if test_with_expiry_days:
        test_case.assertIsNotNone(batch_instance.expiry_date, msg=f"Expected expiry date for {days_to_expire} days")
        
        expected_expiry = schedule_future_date(days=days_to_expire)
        tolerance = timedelta(seconds=20)
        
        test_case.assertTrue(
            abs(batch_instance.expiry_date - expected_expiry) < tolerance,
            f"Expected expiry ≈ {expected_expiry}, got {batch_instance.expiry_date}"
        )
    else:
        test_case.assertIsNone(batch_instance.expiry_date)


def _recovery_codes_assert_plain(test_case: TestCase, raw_codes: list):
    """
    Asserts that the first code in raw_codes is in plain text (not hashed).

    Args:
        test_case: The TestCase instance calling this helper.
        raw_codes: The list of generated recovery codes (tuple of index, code string).
    """
    valid_code = raw_codes[0][1]
    test_case.assertFalse(
        is_already_hashed(valid_code),
        f"Expected code to be plain text, but it appears hashed: {valid_code}"
    )


def _recovery_codes_assert_hashed(test_case: TestCase, user):
    """
    Asserts that all recovery codes in the user's latest batch are hashed.

    Prefetches related codes to avoid N+1 query problem.

    Args:
        test_case: The TestCase instance calling this helper.
        user: The user whose recovery codes batch should be checked.
    """
    batch = RecoveryCodesBatch.objects.prefetch_related("recovery_codes").get(user=user)
    
    for code in batch.recovery_codes.all():
        hashed_code = code.hash_code
        test_case.assertTrue(
            is_already_hashed(hashed_code),
            f"Batch {batch.id} code id {code.id} is not hashed, got {hashed_code}"
        )


def test_create_recovery_batch_method_helper(
    test_case: TestCase, 
    username: str, 
    use_with_expiry_days: bool = False, 
    days_to_expire: int = None
):
    """
    Helper function to test the creation of a RecoveryCodesBatch for a given user.

    This function performs end-to-end checks:
    1. Creates a test user with the given username.
    2. Generates a batch of recovery codes using `_recovery_codes_generate`.
    3. Verifies that raw codes and batch instance are correctly created.
    4. Asserts the batch belongs to the correct user.
    5. Checks expiry date logic, if `use_with_expiry_days` is True.
    6. Asserts that raw codes are in plain text.
    7. Confirms that stored codes are hashed in the database.

    Args:
        test_case (TestCase): The Django TestCase instance.
        username (str): Username for the test user to create.
        use_with_expiry_days (bool, optional): If True, sets an expiry date for the codes.
        days_to_expire (int, optional): Number of days until the codes expire. Defaults to 1.

    Returns:
        None
    """

    test_user                 = create_user(username)
    raw_codes, batch_instance = _recovery_codes_generate(test_user, use_with_expiry_days=use_with_expiry_days, days_to_expire=days_to_expire)
   
    test_case.assertTrue(raw_codes)
    test_case.assertTrue(batch_instance.number_issued, len(raw_codes))

    test_case.assertEqual(batch_instance.user, test_user)

    _recovery_codes_assert_batch(test_case, batch_instance, days_to_expire, test_with_expiry_days=use_with_expiry_days)
    _recovery_codes_assert_plain(test_case=test_case, raw_codes=raw_codes)
    _recovery_codes_assert_hashed(test_case=test_case, user=test_user)
    _recovery_codes_assert_hashed(test_case=test_case, user=test_user)

  

class RecoveryCodesBatchMethodTest(TestCase):
    """Test suite for RecoveryCodesBatch model."""

    # set determinsic key needed to hash the codes
    settings.DJANGO_AUTH_RECOVERY_KEY   = "test-key"

    def setUp(self):
        """"""
        self.user            = create_user()
        self.batch_size      = 10
        self.raw_codes, self.batch_instance  = RecoveryCodesBatch.create_recovery_batch(self.user)

        self.assertTrue(self.raw_codes)
        self.assertTrue(self.batch_instance)

    def test_status_css_class_frontend_settings(self):
        """

        Test frontend css selectors settings view.

        GIVEN that user marks a given batch as either "invalid" or "pending deletion" 
        WHEN the user inspects the frontend record 
        THEN the batch should display the given colour for the selector "active" green and "pending deleted"
             or "invalid" as "red"
        """
        EXPECTED_CSS_SELECTORS = {
            Status.INVALIDATE: "text-red",
            Status.PENDING_DELETE: "text-yellow-600",
        }


        # set the status to invalid
        self.batch_instance.status = Status.INVALIDATE
        self.batch_instance.save()

        self.batch_instance.refresh_from_db()
        self.assertEqual(self.batch_instance.status_css_class, EXPECTED_CSS_SELECTORS[Status.INVALIDATE])

        # set to pending delete
        self.batch_instance.status = Status.PENDING_DELETE
        self.batch_instance.save()

        self.batch_instance.refresh_from_db()
        self.assertEqual(self.batch_instance.status_css_class, EXPECTED_CSS_SELECTORS[Status.PENDING_DELETE])
    
    def test_create_recovery_batch_method_with_expired_codes(self):
        """
        GIVEN a user chooses the option to create recovery codes with expiry
        WHEN the expiry is set to 1 day
        THEN the batch is created with the correct expiry date,
            raw codes are plain, and stored codes are hashed.
        """
        test_create_recovery_batch_method_helper(
            test_case=self,
            username="test_user_with_expiry_codes",
            use_with_expiry_days=True,
            days_to_expire=1
        )


    def test_create_recovery_batch_method_with_unexpired_codes(self):
        """
        GIVEN a user chooses to create recovery codes without expiry
        WHEN no expiry is set
        THEN the batch is created with no expiry date,
            raw codes are plain, and stored codes are hashed.
        """
        test_create_recovery_batch_method_helper(
            test_case=self,
            username="test_user_without_expired_codes",
        )

    def tearDown(self):
        RecoveryCodesBatch.objects.filter(user=self.user).delete()
      