import json

from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django_auth_recovery_codes.enums import (BackendConfigStatus, 
                                              CreatedStatus, 
                                              SetupCompleteStatus, 
                                              TestSetupStatus, 
                                              UsageStatus, 
                                              ValidityStatus
                                              )
from django_auth_recovery_codes.models import RecoveryCodesBatch, RecoveryCodeSetup, RecoveryCode
from django_auth_recovery_codes.tests.fixtures.fixtures import create_user
from django_auth_recovery_codes.tests.fixtures.fixtures import if_key_not_in_expected_list_raise_error


class TestRecoveryCodeIntegration(TestCase):
    """Integration tests for the recovery code verify view, RecoverycodeBatch and RecoveryCodeSetup."""

    def setUp(self):
        """Create the setup necessary to run the integration"""
        self.CODES_PER_BATCH              = 10
        self.user                         = create_user()
        settings.DJANGO_AUTH_RECOVERY_KEY = "deterministic-recovery-key"
        self.url                          = reverse("recovery_codes_verify")  # from the urls.py file

        # Create a recovery batch for this user
        self.raw_codes, self.batch_instance = RecoveryCodesBatch.create_recovery_batch(user=self.user, num_of_codes_per_batch=self.CODES_PER_BATCH)
        self.recovery_code_setup            = RecoveryCodeSetup.get_by_user(self.user)

        self.assertTrue(self.raw_codes, "No recovery codes created for user")
        self.assertEqual(self.batch_instance.user, self.user, "Batch created for wrong user")
        self.assertTrue(self.recovery_code_setup)

        # check the number of codes in the batch match the expected number of codes for a given batch
        self.assertEqual(self.batch_instance.number_issued, self.CODES_PER_BATCH)

        self.EXPECTED_KEYS =  [
            "SUCCESS",
            "MESSAGE",
            "ERROR",
            "CREATED",
            "BACKEND_CONFIGURATION",
            "SETUP_COMPLETE",
            "IS_VALID",
            "USAGE",
            "FAILURE",
        ]
    
    def test_verify_returns_json_when_already_setup(self):
        """
        GIVEN that a user has already run their setup verification in the froentend form
        WHEN  they post a new request to the backend to verify the setup again
        THEN  the view returns a JSON setup messages stating that no action was taken since it already verified
              along with a list of other messages
        """

        SUCCESSFUL_STATUS_CODE = 200

        self.client.force_login(self.user)
        single_plain_code = self.raw_codes[0][1]
        self.assertTrue(single_plain_code)

        # simulate already setup by setting to True
        self.recovery_code_setup.success = True
        self.recovery_code_setup.save()

        # Post to the view
        response = self.client.post(
            self.url,
            data=json.dumps({"code": single_plain_code}),
            content_type="application/json"
        )

        
        self.assertEqual(response.status_code, SUCCESSFUL_STATUS_CODE)

        data = response.json()

        if_key_not_in_expected_list_raise_error(expected_keys=self.EXPECTED_KEYS, data=data)

        self.assertTrue(data["SUCCESS"])
        self.assertFalse(data["FAILURE"])
        self.assertEqual(data["CREATED"], CreatedStatus.ALREADY_CREATED.value)
        self.assertEqual(data['BACKEND_CONFIGURATION'], BackendConfigStatus.ALREADY_CONFIGURED.value)
        self.assertEqual(data['IS_VALID'], ValidityStatus.VALID.value)
        self.assertEqual(data['SETUP_COMPLETE'], SetupCompleteStatus.ALREADY_COMPLETE.value)
        self.assertEqual(data['USAGE'], UsageStatus.SUCCESS.value)
    
        # Verify the RecoveryCodeSetup instance is marked successful
        self.recovery_code_setup.refresh_from_db()
        self.assertTrue(self.recovery_code_setup.success)

    def test_verify_returns_json_when_successful_setup(self):
        """
        GIVEN a user who has succesfully generated their recovery codes and setup form is shown
        WHEN they POST a request to the verify the setup
        THEN the view returns a JSON response indicating setup has been done
        AND the codes are verified but not marked as used
        """
        self.client.force_login(self.user)

        NUMBER_OF_CODES_USED = 0
        single_plain_code    = self.raw_codes[0][1]
        SUCCESS_STATUS_CODE  = 200

        self.assertTrue(single_plain_code)

        # Post to the view
        response = self.client.post(self.url,
                                    data=json.dumps({"code": single_plain_code}),
                                    content_type="application/json"
                                    )
        data = response.json()

        self.assertEqual(response.status_code, SUCCESS_STATUS_CODE)
       
        if_key_not_in_expected_list_raise_error(self.EXPECTED_KEYS, data=data)
       
        self.assertEqual(data["BACKEND_CONFIGURATION"], TestSetupStatus.BACKEND_CONFIGURATION_SUCCESS.value)
        self.assertEqual(data["SETUP_COMPLETE"], TestSetupStatus.SETUP_COMPLETE.value)
        self.assertEqual(data["IS_VALID"], TestSetupStatus.VALIDATION_COMPLETE.value)
        self.assertEqual(data["USAGE"], UsageStatus.SUCCESS.value)
        self.assertTrue(data["SUCCESS"])
        self.assertEqual(data["MESSAGE"], '')
        self.assertEqual(data["ERROR"], '')
        self.assertEqual(data["CREATED"], TestSetupStatus.CREATED.value)
        self.assertFalse(data["FAILURE"])

        # check that is marked as success after creation
        self.recovery_code_setup.refresh_from_db()

        self.assertTrue(self.recovery_code_setup.success, msg="The setup should be marked as True ")

        # Verify that running a verification test setup does not mark any of the codes 
        # in the batch as used or reduce the active code count.
        self.batch_instance.refresh_from_db()
        self.assertEqual(self.batch_instance.number_used, NUMBER_OF_CODES_USED)
        self.assertEqual(self.batch_instance.active_codes_remaining, self.CODES_PER_BATCH)

        # Ensure the individual recovery code itself remains active and unused.
        recovery_code = RecoveryCode.get_by_code_and_user(single_plain_code, self.user)
        self.assertTrue(recovery_code)

        self.assertFalse(recovery_code.is_deactivated)
        self.assertFalse(recovery_code.is_used)

    def test_verify_returns_error_json_when_invalid_code(self):
        """
        GIVEN a user who submits an invalid recovery code
        WHEN they POST to the verify view
        THEN the view returns a JSON response with an error
        AND SUCCESS is False
        """
        self.client.force_login(self.user)
        INVALID_STATUS_CODE = 400
        invalid_plain_code  = ""

        # Post to the view
        response = self.client.post(self.url,
                                    data=json.dumps({"code": invalid_plain_code}),
                                    content_type="application/json"
                                    )
        data = response.json()
        self.assertTrue(data)

        self.assertEqual(response.status_code, INVALID_STATUS_CODE)

        self.assertIn('SUCCESS', data)
        self.assertIn('MESSAGE', data)
        self.assertIn('ERROR', data)
       
        self.assertFalse(data['SUCCESS'])
        self.assertEqual(data['MESSAGE'], "No code provided.")
        self.assertEqual(data['ERROR'], "The JSON body did not include a 'code' field.")

    def test_verify_returns_json_when_not_setup_and_recovery_code_batch_not_created(self):
        """
        GIVEN a user who has not completed the recovery setup and hasn't created a recovery code batch
        WHEN they POST a request to the verify view
        THEN the view returns a JSON response with the expected keys
        AND the response indicates setup is incomplete but returns True because it is not a failure
        """

        new_user = create_user(username="test_user_2", email="test_user_2@example.com", password="123456")
        self.client.force_login(new_user)
    
        response = self.client.post(self.url,
                                    data=json.dumps({"code": "123456-789"}),
                                    content_type="application/json"
                                    )
        data = response.json()
        if_key_not_in_expected_list_raise_error(expected_keys=self.EXPECTED_KEYS, data=data)

        self.assertTrue(data['SUCCESS'])
        self.assertEqual(data['MESSAGE'], '')
        self.assertEqual(data['ERROR'], '')
        self.assertEqual(data['CREATED'], CreatedStatus.NOT_CREATED.value)
        self.assertEqual(data['BACKEND_CONFIGURATION'], BackendConfigStatus.NOT_CONFIGURED.value)
        self.assertEqual(data['SETUP_COMPLETE'], SetupCompleteStatus.NOT_COMPLETE.value)
        self.assertEqual(data['IS_VALID'], ValidityStatus.INVALID.value)
        self.assertEqual(data['USAGE'], UsageStatus.FAILURE.value)
        self.assertFalse(data['FAILURE'])
       
    def tearDown(self):
        """Tear down the test since we want every test to begin anew and not a share state"""
        RecoveryCodesBatch.get_by_user(self.user).delete()
        RecoveryCodeSetup.get_by_user(self.user).delete()
      