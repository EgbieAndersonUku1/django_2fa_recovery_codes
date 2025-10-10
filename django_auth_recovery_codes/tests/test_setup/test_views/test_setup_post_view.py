import json

from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from django_auth_recovery_codes.tests.fixtures.fixtures import create_user


class TestRecoveryCodeOneTimeSetupVerificationPostView(TestCase):
    """Tests the one time verification setup"""

    def setUp(self):

        self.user = create_user(username="test_user", email="test_email@example.com", password="123456")
        self.url  = reverse("recovery_codes_verify") # url name from the django_auth_recovery_codes/urls.py
     
    
    def test_logged_in_user_when_no_code_is_sent(self):
        """
        GIVEN that user is authenticated
        WHEN but the user sends a empty string for the code
        THEN the app should respond with a JSON message stating the code is missing
        """
        self.client.force_login(self.user)
        INVALID_CODE = ""
        INVALID_STATUS_CODE = 400

        response = self.client.post(self.url,
                                    data=json.dumps({"code": INVALID_CODE}),
                                    content_type="application/json"
                                    )
        
        self.assertEqual(response.status_code, INVALID_STATUS_CODE)
        self.assertJSONEqual(response.content, {
                "MESSAGE": "No code provided.",
                "ERROR": "The JSON body did not include a 'code' field.",
                "SUCCESS": False,
            }      
                             )

    def test_logged_in_user_first_time_setup(self):
        """
        Test if the user can log into the dashboard if there are authenticated.
        Since is this is a unit test and not an integration test, the view creates
        a patch for the `RecoveryCodesBatch.verify_setup` model.
        
        GIVEN that a user is authenticated
        WHEN  they try to go to the 2FA authenticated dashboard page
        THEN  there should be redirected to that page after posting a valid code
        AND   they should be able to see the recovery 2FA dashboard
        
        """
        SUCCESS_CODE = 200
        valid_code   = "123456-789745"

        self.client.force_login(self.user)

        with patch("django_auth_recovery_codes.views.RecoveryCodesBatch.verify_setup",
                  return_value={"SUCCESS": True,  "MESSAGE": "", "ERROR": ""}
                  ):
            response = self.client.post(
                self.url,
                data=json.dumps({"code": valid_code}),
                content_type="application/json",
                
            )


        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertJSONEqual(
            response.content,
            {"SUCCESS": True, "MESSAGE": "", "ERROR": ""}
        )
