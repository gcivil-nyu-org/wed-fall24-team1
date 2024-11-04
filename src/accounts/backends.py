# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from accounts.models import CustomUser

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
            try:
                # If user not found by username, try email
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


class ServiceProviderBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate service providers using their email and password.
        """
        try:
            # 'username' here is the email, as defined in the form
            user = CustomUser.objects.get(email=username)
            if user.user_type != 'service_provider':
                return None  # Only authenticate service providers
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        """
        Retrieve the user by ID.
        """
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
