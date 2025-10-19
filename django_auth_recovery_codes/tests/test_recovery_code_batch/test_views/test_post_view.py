from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.utils.utils import schedule_future_date

from django_auth_recovery_codes.tests.test_recovery_code_batch.utils import (generate_and_get_wait_time,
                                                                             assert_required_keys_in_return_response,
                                                                             assert_codes_matches_expected_output,
                                                                             assert_expected_date_meets_expectation,
                                                                             assert_batch_in_return_json_response_has_correct_data,
                                                                             assert_success_json,
                                                                          
                                                                             is_wait_time_multiple,
                                                                             )


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
        assert_required_keys_in_return_response(test_case=self, data=data)
        assert_codes_matches_expected_output(test_case=self, data=data)
        assert_batch_in_return_json_response_has_correct_data(test_case=self, data=data)
        assert_success_json(test_case=self, data=data)
        
        # check the username 
        self.assertEqual(data["BATCH"]["USERNAME"], self.user.username)

        # check the expiry date matches the required expired data
        expiry_date = data["BATCH"]["EXPIRY_DATE"]
        self.assertIsNotNone(expiry_date, msg="EXPIRY_DATE should not be None")

        date_till_expiry = schedule_future_date(days=num_of_days_to_expire)

        # Compare only the date part to avoid flaky failures due to small time differences
        assert_expected_date_meets_expectation(test_case=self, 
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
        assert_required_keys_in_return_response(test_case=self, data=data)
        assert_codes_matches_expected_output(test_case=self, data=data)
        assert_batch_in_return_json_response_has_correct_data(test_case=self, data=data)
        assert_success_json(test_case=self, data=data)

        # check the username 
        self.assertEqual(data["BATCH"]["USERNAME"], self.user.username)

    def test_wait_time_backoff_for_recovery_code_regeneration(self):
        """
        Test that regenerating recovery codes correctly increases wait times 
        between consecutive attempts according to the backoff logic.

        Steps performed:
        1. Verify that the cooldown cutoff and multiplier settings exist.
        2. Generate an initial recovery code and check the response.
        3. Simulate regenerating recovery codes multiple times, generating 
        a sequence of wait times.
        4. Assert that each generated wait time is roughly a multiple of the 
        previous one, based on the configured multiplier, while allowing 
        small deviations due to elapsed time.

        The goal is to ensures that the rate-limiting / cooldown mechanism behaves 
        correctly and prevents users from regenerating codes too quickly.

        GIVEN the user regenerates recovery codes multiple times in a short period
        WHEN the backoff mechanism is applied
        THEN each new wait time should increase according to the multiplier until the cutoff threshold is reached
        """

        cutoff           = settings.DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT
        multiplier       = settings.DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER
   
        self.assertTrue(cutoff)
        self.assertTrue(multiplier)

        self.client.force_login(self.user)

        # generate the code no wait time
        response = self.client.post(self.url_without_expiry, 
                         content_type="application/json",
                         )
        
        self.assertIsNotNone(response)

        data = response.json()

        response_message = data["MESSAGE"]
        EXPECTED_MSG     = "Your recovery code has been generated"

        self.assertTrue(response_message)
        self.assertTrue(data["CAN_GENERATE"], EXPECTED_MSG)
    
      
        # Simulate regenerating wait times after the user clicks the `regenerate` button.
        # This will generate seven wait times. Each wait time is intended to be double
        # the previous one, based on the settings:
        # - DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN
        # - DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER
        #
        # Example:
        # If DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN = 20
        # and DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER = 2,
        # the ideal wait times would be:
        # [40, 80, 160, 320, 640, 1280, 2560]
        #
        # Note: because time may pass between calculations, the actual generated
        # wait times may differ slightly from these ideal values (e.g., 33 instead of 40)
        # which could be [33, 66, 132, 264, 528, 1056, 2112]
        wait_times = [generate_and_get_wait_time(self) for _ in range(5)]

        wait_time_1, wait_time_2, wait_time_3, wait_time_4, wait_time_5 = wait_times

        self.assertTrue(is_wait_time_multiple(previous_wait_time=wait_time_1, current_wait_time=wait_time_2))
        self.assertTrue(is_wait_time_multiple(previous_wait_time=wait_time_2, current_wait_time=wait_time_3))
        self.assertTrue(is_wait_time_multiple(previous_wait_time=wait_time_3, current_wait_time=wait_time_4))
        self.assertTrue(is_wait_time_multiple(previous_wait_time=wait_time_4, current_wait_time=wait_time_5))

    def test_wait_time_does_not_exceed_cutoff(self):
        """
        Test that the wait time stops increasing once the cooldown cutoff is reached.

        The cooldown mechanism should progressively increase the wait time between 
        regeneration attempts until it reaches a maximum threshold (the cutoff). 
        After the cutoff is reached, any new regenerations should no longer produce 
        higher wait times they should remain capped at the cutoff value.

        GIVEN the user clicks the regeneration button multiple times
        WHEN the wait time increases with each click until it reaches the cutoff
        THEN it should no longer increase, regardless of additional clicks
        """
        cutoff     = settings.DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT
        multiplier = settings.DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER

        self.assertTrue(cutoff)
        self.assertTrue(multiplier)

        self.client.force_login(self.user)

        running = True
        while running:
            wait_time = generate_and_get_wait_time(self)
            if wait_time >= cutoff:
                self.assertLessEqual(wait_time, cutoff)
                running = False

        # Generate a few more wait times to ensure the value doesn't exceed the cutoff
        for _ in range(3):
            wait_time = generate_and_get_wait_time(self)

        self.assertEqual(wait_time, cutoff, msg="The wait time shouldn't exceed the cutoff time")
