from django.contrib.auth import get_user_model

User = get_user_model()

def create_user(username="test_user", email="test@example.com"):
    """Create a user for the test"""
    return User.objects.create(username=username, email=email)