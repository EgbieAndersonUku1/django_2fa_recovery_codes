from django.contrib.auth import get_user_model

from django_auth_recovery_codes.utils.errors.enforcer import enforce_types
from django_auth_recovery_codes.utils.errors.error_messages import construct_raised_error_msg


User = get_user_model()

def create_user(username="test_user", email="test@example.com", password="12345"):
    """Create a user for the test"""
    return User.objects.create_user(username=username, email=email, password=password)


@enforce_types()
def if_key_not_in_expected_list_raise_error(expected_keys: list, data:dict):
    for key, value in data.items():
        if key not in expected_keys:
            construct_raised_error_msg(arg_name=key, expected_types=str, value=value)
          
