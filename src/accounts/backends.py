# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None or password is None:
            return None
        try:
            # Try to get the user by username
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # If not found, try to get the user by email
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
        # Use user_can_authenticate method from ModelBackend
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
