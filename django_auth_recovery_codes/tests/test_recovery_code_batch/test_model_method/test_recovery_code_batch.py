from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

from django_auth_recovery_codes.models                  import RecoveryCodesBatch
from django_auth_recovery_codes.models_choices          import Status
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.security.hash     import is_already_hashed, make_lookup_hash
from django_auth_recovery_codes.utils.utils             import schedule_future_date
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg

User = get_user_model()

# ----------------------------------------
# Generation Helpers
# ----------------------------------------
def _assert_update_code_count(
    test_case,
    batch_instance,
    method_name: str,
    field_name: str
):
    """
    Helper to test batch update count methods.

    - Checks that the count field increments by 1 when `save=True`.
    - Checks that calling the method without `save` increments in-memory but not in the database.

    Args:
        test_case: The test instance (self)
        batch_instance: The RecoveryCodesBatch instance
        method_name: Name of the update method as string (e.g., 'update_used_code_count')
        field_name: Name of the count field as string (e.g., 'number_used')
    """
    initial_value = getattr(batch_instance, field_name)
    test_case.assertEqual(initial_value, 0, msg=f"Initial {field_name} should be 0")

    # Increment and save immediately
    getattr(batch_instance, method_name)(save=True)
    batch_instance.refresh_from_db()
    test_case.assertEqual(getattr(batch_instance, field_name), 1,
                          msg=f"{field_name} should increment to 1 after save=True")

    # Increment without saving (should only update in-memory)
    getattr(batch_instance, method_name)() # increment the method but without saving
    batch_instance.refresh_from_db()
    test_case.assertEqual(getattr(batch_instance, field_name), 2,
                          msg=f"{field_name} should not increment in DB when save=False")


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


def _assert_batch_codes_marked_for_deletion(test_case, batch: RecoveryCodesBatch, should_be_marked: bool = True):
    """
    Assert that all recovery codes in the given batch are correctly marked (or not marked) for deletion.

    If `should_be_marked` is True:
        - Codes should be deactivated (is_deactivated=True)
        - Codes should be marked for deletion (mark_for_deletion=True)
        - Codes should have deleted_at and deleted_by set
        - deleted_by should match the batch's user

    If `should_be_marked` is False:
        - Codes should be active (is_deactivated=False)
        - Codes should NOT be marked for deletion (mark_for_deletion=False)
        - Codes should NOT have deleted_at or deleted_by set
    """
    for code in batch.recovery_codes.all():
        if should_be_marked:
            test_case.assertTrue(code.is_deactivated, msg="Code should be deactivated (is_deactivated=True)")
            test_case.assertTrue(code.mark_for_deletion, msg="Code should be marked for deletion (mark_for_deletion=True)")
            test_case.assertIsNotNone(code.deleted_at, msg="Code should have a deletion timestamp (deleted_at is None)")
            test_case.assertIsNotNone(code.deleted_by, msg="Code should have a user recorded as deleted_by (deleted_by is None)")
            test_case.assertEqual(code.deleted_by, batch.user, msg=f"Code.deleted_by ({code.deleted_by}) should match batch.user ({batch.user})")
        else:
            test_case.assertFalse(code.is_deactivated, msg="Code should be active (is_deactivated=False)")
            test_case.assertFalse(code.mark_for_deletion, msg="Code should NOT be marked for deletion (mark_for_deletion=False)")
            test_case.assertIsNone(code.deleted_at, msg="Code should NOT have a deletion timestamp (deleted_at should be None)")
            test_case.assertIsNone(code.deleted_by, msg="Code should NOT have a deleted_by user (deleted_by should be None)")

       
# ----------------------------------------
# Assertion Helpers
# ----------------------------------------

def _assert_cache_values_valid(test_case, cache_values: dict, expect_active=False):
    """
    Assert that all cache values reflect the expected state.

    If expect_active is True:
        - All cache values (except 'number_used') should be True.
        - 'number_used' should be 0.

    If expect_active is False (reset state):
        - All cache values (except 'number_used') should be False.
        - 'number_used' should be 0.
    """
    if not isinstance(cache_values, dict):
        raise TypeError(construct_raised_error_msg("cache_values", expected_types=dict, value=cache_values))

    for key, value in cache_values.items():
        if key == "number_used":
            test_case.assertEqual(value, 0, msg=f"'number_used' should be 0, got {value}")
        elif expect_active:
            test_case.assertTrue(value, msg=f"key = {key}, value = {value} should be True but got {value}")
        else:
            test_case.assertFalse(value, msg=f"key = {key}, value = {value} should be False but got {value}")


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

        # automatically marked as True when generated
        self.assertTrue(self.batch_instance.generated)

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

    def test_create_recovery_batch_code_size(self):
        """
        GIVEN that a developer want to increase the number of codes in a given a batch
        WHEN  the developer sets the batch to a number greater than the default or less
        THEN  the size should increase or decrease based on the number selected by the developer
        AND   an error should be raised if batch size is 0 or -1
        """
        batch_size = 20
        new_user = create_user("new_user", email="new_user@example.com")
        raw_codes, batch_instance = RecoveryCodesBatch.create_recovery_batch(user=new_user, num_of_codes_per_batch=batch_size)

        self.assertTrue(raw_codes)
        self.assertTrue(batch_instance)
        self.assertTrue(batch_instance.id)
        self.assertEqual(len(raw_codes), batch_size)
        self.assertEqual(batch_instance.number_issued, batch_size)
        self.assertEqual(batch_instance.number_removed, 0)
        self.assertEqual(batch_instance.number_invalidated, 0)
        self.assertEqual(batch_instance.number_used, 0)

        # test if an error is raised if 0 attempts
        expected_error_msg = "The batch number(size) cannot be less or equal to 0"
        with self.assertRaises(ValueError) as context:
            RecoveryCodesBatch.create_recovery_batch(user=new_user, num_of_codes_per_batch=0)
        
        self.assertEqual(str(context.exception), expected_error_msg)

        # test if negative batch size can be created
        with self.assertRaises(ValueError) as context:
            RecoveryCodesBatch.create_recovery_batch(user=new_user, num_of_codes_per_batch=-1)
        self.assertEqual(str(context.exception), expected_error_msg)


    def test_delete_recovery_batch_method_marked_codes_and_batch_for_deletion(self):
        """Test that delete_recovery_batch deactivates and marks the batch for deletion."""
        
        # test that the codes and batches are not marked for deletion befoee method is called
        user_batch = RecoveryCodesBatch.objects.prefetch_related("recovery_codes").filter(user=self.user).first()
        _assert_batch_codes_marked_for_deletion(test_case=self, batch=user_batch, should_be_marked=False)

        # Call the method to delete the recovery batch for the user
        RecoveryCodesBatch.delete_recovery_batch(self.user)

        # Get the first batch for the user after it has been marked for deletion
        user_batch = RecoveryCodesBatch.objects.prefetch_related("recovery_codes").filter(user=self.user).first()
        _assert_batch_codes_marked_for_deletion(test_case=self, batch=user_batch, should_be_marked=True)
    def test_mark_as_viewed_method(self):
        """
        GIVEN that the developer sets the model batch method viewed to True
        WHEN  the method is marked e.g set as True
        THEN  the batch should now be marked as True
        """
        self.assertFalse(self.batch_instance.viewed)

        self.batch_instance.mark_as_viewed()
        self.batch_instance.refresh_from_db()

        self.assertTrue(self.batch_instance.viewed)

        # check if the others are not marked as True
        self.assertFalse(self.batch_instance.downloaded)
        self.assertFalse(self.batch_instance.emailed)

        # generated is automatically marked as True when created
        # Check if is not automatically marked as False but still True
        self.assertTrue(self.batch_instance.generated)
    
    def test_mark_as_download_method(self):
        """
        GIVEN that the developer sets the model batch method download to True
        WHEN  the method is marked e.g set as True
        THEN  the batch should now be marked as True
        """
        self.assertFalse(self.batch_instance.downloaded)
        self.batch_instance.mark_as_downloaded()
        self.batch_instance.refresh_from_db()

        self.assertTrue(self.batch_instance.downloaded)

        # check if the others are not marked as True
        self.assertFalse(self.batch_instance.viewed)
        self.assertFalse(self.batch_instance.emailed)

        # generated is automatically marked as True when created
        # Check if is not automatically marked as False but still True
        self.assertTrue(self.batch_instance.generated)
    
    def test_mark_as_emailed_method(self):
        """
        GIVEN that the developer sets the model batch method emailed to True
        WHEN  the method is marked e.g set as True
        THEN  the batch should now be marked as True
        """
        self.assertFalse(self.batch_instance.emailed)
        self.batch_instance.mark_as_emailed()
        self.batch_instance.refresh_from_db()

        self.assertTrue(self.batch_instance.emailed)

        # check if the others are not marked as True
        self.assertFalse(self.batch_instance.viewed)
        self.assertFalse(self.batch_instance.downloaded)

        # generated is automatically marked as True when created
        # Check if is not automatically marked as False but still True
        self.assertTrue(self.batch_instance.generated)

    def test_get_by_user_method(self):
        """
        GIVEN that the developer uses the method `get_by_user`
        WHEN  the developer passes in a valid user
        THEN  the method should return the user object
        AND   if the user doesn't exist the a None should be returned
        """
        non_existance_user = create_user("non_existance_user")
        user_1 = RecoveryCodesBatch.get_by_user(user=non_existance_user)
        self.assertIsNone(user_1)

        existing_user = RecoveryCodesBatch.get_by_user(user=self.user)
        self.assertIsNotNone(existing_user)

        self.assertEqual(existing_user.user, self.user)
    
    def test_get_json_values_method(self):
        """
        GIVEN that developer calls the `get_json_values`
        WHEN it is called
        THEN the method should return JSON attribrutes prepending to the model
        """
        cache_values = self.batch_instance.get_cache_values()
        self.assertTrue(cache_values)

        for key in cache_values:
            self.assertIn(key, cache_values)
        
        is_generated = cache_values.pop("generated")
        self.assertTrue(is_generated)
        _assert_cache_values_valid(self, cache_values)
      
    def test_reset_cache_values_method(self):
        """Test that cache values correctly toggle between active and reset states."""

        cache_values = self.batch_instance.get_cache_values()
        is_generated = cache_values.pop("generated")
        self.assertTrue(is_generated)
    
        # Initially all should be False (reset state)
        _assert_cache_values_valid(self, cache_values, expect_active=False)

        # Simulate actions
        self.batch_instance.mark_as_downloaded()
        self.batch_instance.mark_as_emailed()
        self.batch_instance.mark_as_viewed()
        self.batch_instance.refresh_from_db()

        cache_values = self.batch_instance.get_cache_values()

        # Now all should be True (active state)
        _assert_cache_values_valid(self, cache_values, expect_active=True)

        # # After reset, all should be False again
        self.batch_instance.reset_cache_values()
        cache_values = self.batch_instance.get_cache_values()
        _assert_cache_values_valid(self, cache_values, expect_active=False)

    def test_expiry_threshold_method(self):
        """
        Test the `get_expiry_threshold` method of RecoveryCodesBatch.

        - Ensure TypeError is raised if `days` is not an integer or is None.
        - Ensure the method returns a datetime object representing the threshold in the past.
        
        For example, if `days=30` is passed, the method returns a datetime object
        representing 30 days before the current time. This is used to determine
        which recovery codes have expired based on the threshold.
        """
        expected_error_msg = construct_raised_error_msg("days", expected_types=int, value="one_day")
        expected_non_error_msg = "Argument `days` cannot be None."

        # Type checks
        with self.assertRaises(TypeError) as context:
            self.batch_instance.get_expiry_threshold(days="one_day")
        self.assertEqual(str(context.exception), expected_error_msg)

        with self.assertRaises(TypeError) as context:
            self.batch_instance.get_expiry_threshold(days=None)
        self.assertEqual(str(context.exception), expected_non_error_msg)

        # Valid days value
        one_day_in_the_past = self.batch_instance.get_expiry_threshold(days=1)

        # Check return type
        self.assertIsInstance(one_day_in_the_past, datetime)

        # Check that the returned datetime is approximately 1 day in the past
        expected_datetime = timezone.now() - timedelta(days=1)
        self.assertAlmostEqual(one_day_in_the_past.timestamp(), expected_datetime.timestamp(), delta=2)

    def test_terminal_status_method(self):
        """
        Test whether the method returns `pending delete` and  `invalidate` values. 
        The is used by the class `RecoveryCodesBatch` to check if the code or codes
        been removed have actually been marked as `invalid` or `pending deletion`
        """
        
        EXPECTED_LENGTH = 2
        terminal_status = self.batch_instance.terminal_statuses()
        self.assertIsNotNone(terminal_status, msg="Expected a list but got none")
        self.assertIsInstance(terminal_status, list, construct_raised_error_msg("terminal status", expected_types=list, value=terminal_status))

        self.assertEqual(len(terminal_status), EXPECTED_LENGTH)

        self.assertIn(Status.PENDING_DELETE, terminal_status)
        self.assertIn(Status.INVALIDATE, terminal_status)

    def test_update_used_code_count_method(self):
        """Test updating number_used count."""
        _assert_update_code_count(self, self.batch_instance, "update_used_code_count", "number_used")

    def test_update_deleted_code_count_method(self):
        """Test updating number_removed count."""
        _assert_update_code_count(self, self.batch_instance, "update_delete_code_count", "number_removed")

    def test_update_invalidate_code_count_method(self):
        """Test updating number_invalidated count."""
        _assert_update_code_count(self, self.batch_instance, "update_invalidate_code_count", "number_invalidated")

    def tearDown(self):
        RecoveryCodesBatch.objects.filter(user=self.user).delete()



class TestUpdateFieldCounter(TestCase):
    """
    Tests for the internal `_update_field_counter` helper method.

    Although this is a private method and normally wouldn't be tested, however, this
    is tested directly because it manages the atomic and in-memory update logic for 
    several public methods:

    - `update_used_code_count`
    - `update_delete_code_count`
    - `update_invalidate_code_count`

    Ensuring its correctness prevents subtle regressions in database-level counter behaviour.
    """

    def setUp(self):
        self.user = create_user("counter_user", email="counter_user@example.com")
        self.batch = RecoveryCodesBatch.objects.create(
            user=self.user,
            number_used=0,
            number_removed=0,
            number_invalidated=0,
        )

    def test_atomic_increment_persists_to_database(self):
        """Ensure `atomic=True` performs a DB-level F() increment."""
        self.batch._update_field_counter("number_removed", atomic=True)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.number_removed, 1, msg="Atomic increment should persist to DB")

    def test_non_atomic_increment_is_in_memory_only(self):
        """Ensure `atomic=False` increments only in memory (not saved)."""

        self.batch._update_field_counter("number_invalidated", atomic=False)
        self.assertEqual(self.batch.number_invalidated, 1, msg="In-memory increment should update instance value")
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.number_invalidated, 0, msg="DB should not update when atomic=False")

    def test_non_atomic_with_save_persists_to_database(self):
        """Ensure `save=True` with `atomic=False` persists the increment to DB."""

        self.batch._update_field_counter("number_used", atomic=False, save=True)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.number_used, 1, msg="Save=True should persist in-memory increment")

    def test_invalid_field_name_raises_attribute_error(self):
        """Ensure AttributeError is raised for invalid or missing fields."""

        with self.assertRaises(AttributeError) as context:
            self.batch._update_field_counter("invalid_field")

        self.assertIn("has no field 'invalid_field'", str(context.exception))

    def test_none_field_value_raises_value_error(self):
        """Ensure ValueError is raised when field value is None."""

        self.batch.number_used = None
        with self.assertRaises(ValueError) as context:
            self.batch._update_field_counter("number_used", atomic=False)

        self.assertIn("Field 'number_used' is None, cannot increment.", str(context.exception))
