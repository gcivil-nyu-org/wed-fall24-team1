# public_service_finder/views.py

from django.shortcuts import redirect

# from django.contrib.auth.decorators import login_required


def root_redirect_view(request):
    if request.user.is_authenticated:
        return redirect("home")  # Redirect to home if logged in
    else:
        return redirect("user_login")  # Redirect to user login if not logged in
