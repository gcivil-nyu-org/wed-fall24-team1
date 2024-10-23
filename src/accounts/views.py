# accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from .forms import UserRegisterForm, UserLoginForm, ServiceProviderLoginForm


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Authenticate the user to set the backend
            authenticated_user = authenticate(
                request, username=user.username, password=form.cleaned_data["password1"]
            )

            if authenticated_user is not None:
                login(request, authenticated_user)  # Backend is automatically set

                if user.user_type == "service_provider":
                    return redirect("service_provider_dashboard")
                else:
                    return redirect("home")
            else:
                form.add_error(None, "Authentication failed. Please try again.")
    else:
        form = UserRegisterForm()

    return render(request, "register.html", {"form": form})


# User login view
class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "user_login.html"


# Service provider login view
class ServiceProviderLoginView(LoginView):
    form_class = ServiceProviderLoginForm
    template_name = "service_provider_login.html"


# Login selection page view
def login_selection(request):
    return render(request, "login_selection.html")
