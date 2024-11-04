from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView
from accounts.models import CustomUser

from .forms import (
    ServiceSeekerForm,
    UserRegisterForm,
    UserLoginForm,
    ServiceProviderLoginForm,
)


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if user.user_type == "service_provider":
                return redirect("services:list")
            else:
                # CustomUser.objects.create(
                #     username=user.username, email=user.email,
                #     first_name="John", last_name="Doe"
                # )
                return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


@login_required
def profile_view(request):
    print("In profile view", request.GET)
    user = request.user
    if user.user_type == "service_provider":
        print("user type is service_provider")
        return HttpResponseNotFound("Page not found")
    elif user.user_type == "user":
        service_seeker = get_object_or_404(CustomUser, email=user.email)

        # If it's a POST request, we're updating the profile
        if request.method == "POST":
            form = ServiceSeekerForm(request.POST, instance=service_seeker)
            if form.is_valid():
                form.save()
                return redirect("profile_view")
        else:
            form = ServiceSeekerForm(instance=service_seeker)

        return render(
            request,
            "profile_base.html",
            {
                "profile": service_seeker,
                "form": form,  # Pass the form to the template
            },
        )


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
class ServiceProviderLoginView(FormView):
    form_class = ServiceProviderLoginForm
    template_name = "service_provider_login.html"

    def get_form_kwargs(self):
        """
        Pass the request object to the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """
        Log in the user and redirect to the success URL.
        """
        user = form.get_user()
        login(self.request, user, backend='accounts.backends.ServiceProviderBackend')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("services:list")


# Login selection page view
def login_selection(request):
    return render(request, "login_selection.html")
