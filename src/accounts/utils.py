# accounts/utils.py


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
