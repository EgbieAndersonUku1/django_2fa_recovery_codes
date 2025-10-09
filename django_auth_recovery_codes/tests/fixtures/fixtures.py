from django.contrib.auth import get_user_model

User = get_user_model()

def create_user(username="test_user", email="test@example.com", password="12345"):
    """Create a user for the test"""
    return User.objects.create_user(username=username, email=email, password=password)