from decimal import Decimal
import json
from urllib.parse import quote

from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse as parse_date


from accounts.models import CustomUser
from home.repositories import HomeRepository

from .forms import (
    ServiceSeekerForm,
    UserRegisterForm,
    UserLoginForm,
    ServiceProviderLoginForm,
    ServiceProviderForm,
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


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        return obj


@login_required
def profile_view(request):
    print("In profile view", request.GET)
    user = request.user

    if user.user_type == "service_provider":
        # Handle service provider profile
        service_provider = get_object_or_404(CustomUser, email=user.email)

        if request.method == "POST":
            form = ServiceProviderForm(request.POST, instance=service_provider)
            if form.is_valid():
                form.save()
                return redirect("profile_view")
        else:
            form = ServiceProviderForm(instance=service_provider)

        return render(
            request,
            "profile_base.html",
            {"profile": service_provider, "form": form, "is_service_provider": True},
        )

    elif user.user_type == "user":
        # Existing code for regular users
        service_seeker = get_object_or_404(CustomUser, email=user.email)

        # Fetch user's bookmarks
        repo = HomeRepository()
        bookmarks = repo.get_user_bookmarks(str(user.id))

        # Process the bookmarks
        processed_bookmarks = [
            {
                "Id": item.get("Id"),
                "Name": item.get("Name", "No Name"),
                "Address": item.get("Address", "N/A"),
                "Lat": float(item.get("Lat")) if item.get("Lat") else None,
                "Log": float(item.get("Log")) if item.get("Log") else None,
                "Ratings": (
                    "N/A"
                    if item.get("Ratings") in [0, "0", None]
                    else str(item.get("Ratings"))
                ),
                "RatingCount": str(item.get("rating_count", 0)),
                "Category": item.get("Category", "N/A"),
                "MapLink": f"https://www.google.com/maps/dir/?api=1&destination={quote(item.get('Address'))}",
                "Distance": "N/A",  # Since distance may not be available
                "Description": convert_decimals(item.get("Description", {})),
                "IsBookmarked": True,  # These are bookmarks
            }
            for item in bookmarks
        ]

        # Fetch user's reviews
        reviews = repo.fetch_reviews_by_user(str(user.id))
        service_ids = set([review["ServiceId"] for review in reviews])
        service_map = repo.get_services_by_ids(service_ids)

        for review in reviews:
            service = service_map.get(review["ServiceId"], {})
            review["ServiceName"] = service.get("Name", "Unknown Service")
            try:
                review["Timestamp"] = parse_date(review["Timestamp"])
            except Exception:
                pass

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
                "form": form,
                "bookmarks": processed_bookmarks,
                "reviews": reviews,
                "is_service_provider": False,
                "serialized_bookmarks": json.dumps(processed_bookmarks),
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

    def get_success_url(self):
        if self.request.user.user_type == "user":
            return reverse_lazy("home")  # Redirect to user's home page
        else:
            return reverse_lazy("user_login")


# Service provider login view
class ServiceProviderLoginView(CustomLoginView):
    form_class = ServiceProviderLoginForm
    template_name = "service_provider_login.html"

    def get_success_url(self):
        if self.request.user.user_type == "service_provider":
            return reverse_lazy("services:list")
        return reverse_lazy("login")


# Login selection page view
def login_selection(request):
    return render(request, "login_selection.html")
