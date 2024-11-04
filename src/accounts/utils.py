# accounts/utils.py

from .models import CustomUser


def get_axes_username(request, credentials):
    """
    Custom callable to extract the username (email) from the login attempt.
    """
    # Try to get the email from the credentials
    email = credentials.get("email")
    if email:
        return email
    # If not in credentials, try to get it from the POST data
    email = request.POST.get("email")
    if email:
        return email
    # Username not found
    return None


def axes_lockout_callable(request, credentials):
    username = credentials.get("username") or credentials.get("email")
    if username:
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=username)
            except CustomUser.DoesNotExist:
                return True  # Lockout applies to unknown users

        if user.user_type == "service_provider":
            return False  # Do not lock out service providers
    return True  # Lockout applies to other users
