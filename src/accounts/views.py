from decimal import Decimal
import json
from urllib.parse import quote

from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse as parse_date
import uuid
import boto3
from botocore.exceptions import ClientError
from django.contrib.auth import login

from accounts.models import CustomUser
from forum.models import Post
from home.repositories import HomeRepository

from .forms import (
    ServiceSeekerForm,
    UserRegisterForm,
    UserLoginForm,
    ServiceProviderLoginForm,
    ServiceProviderForm,
)

ITEMS_PER_PAGE = 10


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to DB yet
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            profile_image = form.cleaned_data.get("profile_image")
            if profile_image:
                # Generate a unique filename
                image_extension = profile_image.name.split(".")[-1]
                unique_filename = f"{uuid.uuid4()}.{image_extension}"
                s3_key = f"images/{unique_filename}"

                # Upload to S3
                s3_client = boto3.client("s3", region_name=settings.AWS_S3_REGION_NAME)

                try:
                    s3_client.upload_fileobj(
                        profile_image,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        s3_key,
                        ExtraArgs={"ContentType": profile_image.content_type},
                    )
                    # Construct the image URL
                    image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                    user.profile_image_url = image_url
                except ClientError as e:
                    print(f"Failed to upload image to S3: {e}")
                    # Optionally, add an error message to the form
                    form.add_error(
                        "profile_image", "Failed to upload image. Please try again."
                    )
                    return render(request, "register.html", {"form": form})

            user.save()  # Now save to DB            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            if user.user_type == "service_provider":
                return redirect("services:list")
            else:
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
    user = request.user

    if user.user_type == "service_provider":
        service_provider = get_object_or_404(CustomUser, email=user.email)
        user_posts = Post.objects.filter(author=user).order_by("-created_at")

        if request.method == "POST":
            form = ServiceProviderForm(
                request.POST, request.FILES, instance=service_provider
            )
            if form.is_valid():
                profile_image = form.cleaned_data.get("profile_image")
                remove_image = form.cleaned_data.get("remove_profile_image")
                if remove_image:
                    service_provider.profile_image_url = None
                if profile_image:
                    # Generate a unique filename
                    image_extension = profile_image.name.split(".")[-1]
                    unique_filename = f"{uuid.uuid4()}.{image_extension}"
                    s3_key = f"images/{unique_filename}"

                    # Upload to S3
                    s3_client = boto3.client(
                        "s3",
                        region_name=settings.AWS_S3_REGION_NAME,
                    )

                    try:
                        s3_client.upload_fileobj(
                            profile_image,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            s3_key,
                            ExtraArgs={"ContentType": profile_image.content_type},
                        )
                        # Construct the image URL
                        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                        service_provider.profile_image_url = image_url
                    except ClientError as e:
                        print(f"Failed to upload image to S3: {e}")

                form.save()
                return redirect("profile_view")
        else:
            form = ServiceProviderForm(instance=service_provider)

        return render(
            request,
            "profile_base.html",
            {
                "profile": service_provider,
                "form": form,
                "is_service_provider": True,
                "user_posts": user_posts,
            },
        )

    elif user.user_type == "user":
        service_seeker = get_object_or_404(CustomUser, email=user.email)

        # Fetch user's bookmarks
        repo = HomeRepository()
        bookmarks = repo.get_user_bookmarks(str(user.id))
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
                "Description": convert_decimals(item.get("Description", {})),
                "IsBookmarked": True,
                "Announcement": item.get("Announcement", ""),
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

        # Fetch user's posts
        user_posts = Post.objects.filter(author=user).order_by("-created_at")

        # Get active tab
        active_tab = "posts"
        if request.method == "POST":
            form = ServiceSeekerForm(
                request.POST, request.FILES, instance=service_seeker
            )
            if form.is_valid():
                profile_image = form.cleaned_data.get("profile_image")
                remove_image = form.cleaned_data.get("remove_profile_image")
                print(remove_image, profile_image)
                if remove_image:
                    service_seeker.profile_image_url = None
                if profile_image:
                    # Generate a unique filename
                    image_extension = profile_image.name.split(".")[-1]
                    unique_filename = f"{uuid.uuid4()}.{image_extension}"
                    s3_key = f"images/{unique_filename}"
                    # Upload to S3
                    s3_client = boto3.client(
                        "s3",
                        region_name=settings.AWS_S3_REGION_NAME,
                    )

                    try:
                        s3_client.upload_fileobj(
                            profile_image,
                            settings.AWS_STORAGE_BUCKET_NAME,
                            s3_key,
                            ExtraArgs={"ContentType": profile_image.content_type},
                        )
                        # Construct the image URL
                        image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
                        service_seeker.profile_image_url = image_url
                    except ClientError as e:
                        print(f"Failed to upload image to S3: {e}")
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
                "user_posts": user_posts,
                "is_service_provider": False,
                "active_tab": active_tab,
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


class CustomLogoutView(LogoutView):
    def get_next_page(self):
        # Get the default next page
        next_page = super().get_next_page()
        user = self.request.user

        # Check if the user is authenticated
        if user.is_authenticated:
            if user.user_type == "service_provider":
                # Redirect service providers to the service provider login page
                next_page = reverse_lazy("service_provider_login")
            else:
                # Redirect normal users to the home page
                next_page = reverse_lazy("home")
        else:
            # If the user is not authenticated, default to home page
            next_page = reverse_lazy("home")

        return next_page


# Login selection page view
def login_selection(request):
    return render(request, "login_selection.html")
