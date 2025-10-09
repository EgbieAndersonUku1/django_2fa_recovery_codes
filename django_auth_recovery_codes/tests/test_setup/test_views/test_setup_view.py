from django.test import TestCase
from django.urls import reverse

from django_auth_recovery_codes.tests.fixtures.fixtures import create_user


class TestRecoveryCodeOneTimeSetupVerificationGetView(TestCase):
    """Tests the one time verification setup"""

    def setUp(self):
        self.test_username = "test_setup_user"
        self.test_email    = "test_setup_email@example.com"
        self.test_password = "123456"
        self.user = create_user(username=self.test_username, email=self.test_email, password=self.test_password)
        self.url  = reverse("recovery_codes_verify") # url name from the django_auth_recovery_codes/urls.py
     
    def test_redirect_if_not_logged_in(self):
        """Test redirect if not logged in

        GIVEN that a user is not logged in
        WHEN  there try to go to the 2FA authenticated dashboard page   
        THEN  there should be redirected
        """
        TEMPORARY_REDIRECTED_STATUS_CODE = 302
        response                         = self.client.get(self.url)
        self.assertEqual(response.status_code, TEMPORARY_REDIRECTED_STATUS_CODE)
 
