from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from django_auth_recovery_codes.models import Status
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg
from django_auth_recovery_codes.utils.utils import schedule_future_date


def _assert_required_keys_in_return_response(test_case: TestCase, data: dict, required_keys: dict = None):
    """
    Assert that the JSON response contains all required keys.

    This helper verifies that the response dictionary includes every key expected in a valid
    recovery code generation response. It also has the  option to accept a custom set of required keys
    for flexibility when testing different response structures.

    Args:
        test_case (TestCase): The test case instance used to perform assertions.
        data (dict): The JSON response returned by the backend.
        required_keys (dict, optional): A custom dictionary of expected keys.
            If not provided, a default set of required keys for a recovery code response is used.

    Raises:
        TypeError: If `data` is not a dictionary.

    Behaviour:
        - Validates that `data` is a dictionary.
        - Uses the provided `required_keys` or a default schema of expected fields.
        - Asserts that each key in `data` exists within the expected key set.
    """

    if not isinstance(data, dict):
        raise TypeError(construct_raised_error_msg(arg_name="data", expected_types=dict, value=data))
    
    expected_required_keys = {
        "TOTAL_ISSUED": True,
        "SUCCESS": True,
        "ERROR": True,
        "codes": True,
        "MESSAGE": True,
        "CAN_GENERATE": True,
        "HAS_COMPLETED_SETUP": True,
        "CODES": True,
        "BATCH": True,
        "ITEM_PER_PAGE": True,
        "ID": True,
        "NUMBER_ISSUED": True,
        "NUMBER_REMOVED": True,
        "NUMBER_INVALIDATED": True,
        "NUMBER_USED": True,
        "CREATED_AT": True,
        "MODIFIED_AT": True,
        "EXPIRY_DATE": True,
        "DELETED_AT": True,
        "DELETED_BY": True,
        "VIEWED": True,
        "DOWNLOADED": True,
        "EMAILED": True,
        "GENERATED": True,
        "STATUS": True,
        "USERNAME": True
    }

    required_keys = required_keys is not None and  isinstance(required_keys, dict) or expected_required_keys

    for key in data:
        test_case.assertIn(key, required_keys, f"Expected {key} in required keys. Not found.")


def _assert_codes_matches_expected_output(test_case: TestCase, data: dict, expected_count: int = 10):
    """
    Assert that the number of generated recovery codes matches the expected output.

    This helper verifies that:
    - The total number of codes in the 'CODES' list equals the expected count.
    - The 'TOTAL_ISSUED' value in the response matches the expected count.

    Args:
        test_case (TestCase): The test case instance used to perform assertions.
        data (dict): The JSON response data returned by the backend.
        expected_count (int, optional): The expected number of generated recovery codes.
            Defaults to 10.
    """
    test_case.assertEqual(len(data["CODES"]), expected_count)
    test_case.assertEqual(data["TOTAL_ISSUED"], expected_count)


def _assert_expected_date_meets_expectation(test_case: TestCase, 
                                            date_to_test: datetime, 
                                            date_to_test_against: datetime = None,
                                            msg: str = None,
                                            ):   
    """
    Assert that a given date value falls within the expected time window.

    This helper validates that the provided `date_to_test` (usually from a backend response)
    is not later than the current time or the optional `date_to_test_against` value.

    Args:
        test_case (TestCase): The test case instance used to perform assertions.
        date_to_test (datetime): The date string or object returned by the backend to validate.
        date_to_test_against (datetime, optional): The reference datetime to compare against.
            If not provided, the current system time is used.
        msg (str, optional): Custom message to display on assertion failure.

    Test Behaviour:
        - Converts the ISO 8601 date string to a timezone-aware datetime object.
        - Uses the current time (or `date_to_test_against`) as the comparison baseline.
        - Asserts that the tested date is less than or equal to the reference date.
    """
     
    new_date = datetime.fromisoformat(date_to_test.replace("Z", "+00:00"))
    default_msg = "The date returned by the backend exceeds the expected data window"

    if msg and isinstance(msg, str):
        default_msg = msg

    if date_to_test_against and isinstance(date_to_test_against, datetime):
        current_time_now = date_to_test_against
    else:
        current_time_now = timezone.now()

    test_case.assertLessEqual(
            new_date.date(),
            current_time_now.date(),
            msg=default_msg
        )


def _assert_batch_in_return_json_response_has_correct_data(test_case: TestCase, data: dict):
    """
    Assert that the 'BATCH' object in the JSON response contains valid and correctly typed data.

    This helper verifies that:
    - All required batch keys are present and have values of the correct type.
    - Boolean flags such as 'VIEWED', 'DOWNLOADED', and 'EMAILED' are False by default.
    - The 'GENERATED' flag is True, indicating successful batch creation.
    - The 'STATUS' field matches the expected active state.
    - The 'CREATED_AT' and 'MODIFIED_AT' timestamps are within an acceptable range.
    - 'DELETED_AT' and 'DELETED_BY' fields are None, confirming the batch has not been deleted.
    """

    batch = data["BATCH"]
 
    batch_dict = {
        "ID": {"type": str, "value": batch["ID"]},
        "NUMBER_ISSUED": {"type": int, "value": batch["NUMBER_ISSUED"]},
        "NUMBER_REMOVED": {"type": int, "value": batch["NUMBER_REMOVED"]},
        "NUMBER_INVALIDATED": {"type": int, "value": batch["NUMBER_INVALIDATED"]},
        "NUMBER_USED": {"type": int, "value": batch["NUMBER_USED"]},
        "CREATED_AT": {"type": str, "value": batch["CREATED_AT"]},
        "MODIFIED_AT": {"type": str, "value": batch["MODIFIED_AT"]},
        "DELETED_AT": {"type": (str, type(None)), "value": batch["DELETED_AT"]},
        "DELETED_BY": {"type": (str, type(None)), "value": batch["DELETED_BY"]},
        "VIEWED": {"type": bool, "value": batch["VIEWED"]},
        "DOWNLOADED": {"type": bool, "value": batch["DOWNLOADED"]},
        "EMAILED": {"type": bool, "value": batch["EMAILED"]},
        "GENERATED": {"type": bool, "value": batch["GENERATED"]},
        "STATUS": {"type": str, "value": batch["STATUS"]},
        "USERNAME": {"type": str, "value": batch["USERNAME"]},
    }

    for key, info in batch_dict.items():
        value         = info["value"]
        expected_type = info["type"]
        test_case.assertIsInstance(value, expected_type, msg=f"Key {key} doesn't have the required value types. Type = {type(value).__name__}")
           
    test_case.assertFalse(batch["VIEWED"])
    test_case.assertFalse(batch["DOWNLOADED"])
    test_case.assertFalse(batch["EMAILED"])
    test_case.assertTrue(batch["GENERATED"])

    test_case.assertEqual(batch["STATUS"], Status.ACTIVE.name.capitalize())
    
    # test created at
    _assert_expected_date_meets_expectation(test_case, date_to_test=batch["CREATED_AT"])
    
    # test modified at
    _assert_expected_date_meets_expectation(test_case, date_to_test=batch["MODIFIED_AT"])

    # deleted at and deleteb by
    test_case.assertIsNone(batch["DELETED_AT"])
    test_case.assertIsNone(batch["DELETED_BY"])
  

def _assert_success_json(test_case: TestCase, data: dict):
    """
    Assert that the JSON response indicates a successful recovery code generation.

    This helper verifies that:
    - The 'SUCCESS' flag is True.
    - The 'ERROR' field is empty.
    - The 'MESSAGE' matches the expected success message.
    - The 'CAN_GENERATE' flag is True.
    - The 'HAS_COMPLETED_SETUP' flag is False.
    - The 'ITEM_PER_PAGE' value is at least 1.
    """
    expected_msg = "Your recovery code has been generated"
    test_case.assertTrue(data["SUCCESS"])
    test_case.assertEqual(data["ERROR"], "")
    test_case.assertEqual(data["MESSAGE"], expected_msg)
    test_case.assertTrue(data["CAN_GENERATE"])
    test_case.assertFalse(data["HAS_COMPLETED_SETUP"])
    test_case.assertGreaterEqual(data["ITEM_PER_PAGE"], 1)


class TestRecoveryCodeBatcPostView(TestCase):
    """
    Test suite for verifying the behaviour of the recovery code batch generation within the views.
    """

    def setUp(self):
        """Create the necessary startup for the test"""

        self.user                = create_user(username="test_user", email="test_email@example.com", password="123456")
        self.url_without_expiry  = reverse("generate_code_without_expiry") # url name from the django_auth_recovery_codes/urls.py
        self.url_with_expiry     = reverse("generate_code_with_expiry")
    
    def test_code_cannot_be_generated_if_user_is_not_logged_in(self):
        """Test 405 if not logged in and method not allowed"""

        METHOD_NOT_ALLOWED_STATUS_CODE = 405
        response                       = self.client.get(self.url_without_expiry)
        self.assertEqual(response.status_code, METHOD_NOT_ALLOWED_STATUS_CODE)

        # test with expiry url
        response = self.client.get(self.url_with_expiry)
        self.assertEqual(response.status_code, METHOD_NOT_ALLOWED_STATUS_CODE)

    def test_generate_recovery_code_with_expiry_view(self):
        """
        GIVEN a user clicks the frontend 'Generate Recovery Code' button and selects an expiry period of 1 day
        WHEN the user triggers the generation via a fetch POST request
        THEN the server should respond with a 201 status code and a JSON payload containing:
            - The recovery codes and related batch metadata
            - Flags and data fields required by the frontend
            - An expiry date correctly matching the requested duration
        """
        CREATED_STATUS_CODE = 201
        self.client.force_login(self.user)

        num_of_days_to_expire = 1

        response = self.client.post(self.url_with_expiry, 
                         data={"daysToExpiry": num_of_days_to_expire},
                         content_type="application/json",
                         )
        

        self.assertEqual(response.status_code, CREATED_STATUS_CODE)
        self.assertTrue(response.content)

        data = response.json()
        _assert_required_keys_in_return_response(test_case=self, data=data)
        _assert_codes_matches_expected_output(test_case=self, data=data)
        _assert_batch_in_return_json_response_has_correct_data(test_case=self, data=data)
        _assert_success_json(test_case=self, data=data)
        
        # check the username 
        self.assertEqual(data["BATCH"]["USERNAME"], self.user.username)

        # check the expiry date matches the required expired data
        expiry_date = data["BATCH"]["EXPIRY_DATE"]
        self.assertIsNotNone(expiry_date, msg="EXPIRY_DATE should not be None")

        date_till_expiry = schedule_future_date(days=num_of_days_to_expire)

        # Compare only the date part to avoid flaky failures due to small time differences
        _assert_expected_date_meets_expectation(test_case=self, 
                                                date_to_test=expiry_date, 
                                                date_to_test_against=date_till_expiry,
                                                msg="The expiry date returned by the backend exceeds the expected expiry window"
                                                )
        

    def test_generate_recovery_code_without_expiry_view(self):
        """
        GIVEN a user clicks the frontend 'Generate Recovery Code' button without selecting an expiry period
        WHEN the user triggers the generation via a fetch POST request
        THEN the server should respond with a 201 status code and a JSON payload containing:
            - The newly generated recovery codes and related batch metadata
            - Flags and data fields required by the frontend
            - No expiry date set in the batch information
        """
        CREATED_STATUS_CODE = 201
        self.client.force_login(self.user)

        response = self.client.post(self.url_with_expiry, 
                         content_type="application/json",
                         )
        
        self.assertEqual(response.status_code, CREATED_STATUS_CODE)

        data = response.json()
        _assert_required_keys_in_return_response(test_case=self, data=data)
        _assert_codes_matches_expected_output(test_case=self, data=data)
        _assert_batch_in_return_json_response_has_correct_data(test_case=self, data=data)
        _assert_success_json(test_case=self, data=data)

        # check the username 
        self.assertEqual(data["BATCH"]["USERNAME"], self.user.username)

      
      

        
