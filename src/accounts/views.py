from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
                    return redirect("services:list")
                else:
                    return redirect("home")
            else:
                form.add_error(None, "Authentication failed. Please try again.")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


# Custom Login View to handle AxesLockedOut exception
class CustomLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            form = self.get_form()
            form.add_error(
                None,
                "Your account has been locked due to too many failed login attempts. Please try again later.",
            )
            return self.form_invalid(form)

    def form_valid(self, form):
        """
        This method is called when valid form data has been POSTed.
        It should return an HttpResponse.
        """
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            # Extract username from the form
            username_field = getattr(settings, "AXES_USERNAME_FORM_FIELD", "username")
            username = form.cleaned_data.get(username_field)

            # Check if the user is locked out
            if self.is_user_locked_out(username):
                form.add_error(
                    None,
                    _(
                        "Your account has been locked due to too many failed login attempts. Please try again later."
                    ),
                )
                return self.form_invalid(form)
            else:
                # Proceed with authentication
                return super().post(request, *args, **kwargs)
        else:
            return self.form_invalid(form)

    def is_user_locked_out(self, username):
        """
        Check if the user is locked out based on the failure limit and cool-off time.
        """
        failure_limit = getattr(settings, "AXES_FAILURE_LIMIT", 5)
        cool_off_time = getattr(settings, "AXES_COOLOFF_TIME", None)

        # Get all access attempts for the username
        attempts = AccessAttempt.objects.filter(username=username)

        if cool_off_time:
            # Calculate the threshold time
            cool_off_threshold = timezone.now() - cool_off_time

            # Filter attempts within the cool-off period
            attempts = attempts.filter(attempt_time__gte=cool_off_threshold)

        # Calculate the total failures within the cool-off period
        total_failures = (
            attempts.aggregate(total_failures=models.Sum("failures_since_start"))[
                "total_failures"
            ]
            or 0
        )

        # Check if the failure limit is reached
        if total_failures >= failure_limit:
            return True
        return False


# User login view
class UserLoginView(CustomLoginView):
    form_class = UserLoginForm
    template_name = "user_login.html"


# Service provider login view
class ServiceProviderLoginView(CustomLoginView):
    form_class = ServiceProviderLoginForm
    template_name = "service_provider_login.html"

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self):
        if self.request.user.user_type == "service_provider":
            return reverse_lazy("services:list")
        return reverse_lazy("login")


# Login selection page view
def login_selection(request):
    return render(request, "login_selection.html")
