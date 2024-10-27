# accounts/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView

from accounts.forms import (
    ServiceProviderLoginForm,
    ServiceSeekerForm,
    UserLoginForm,
    UserRegisterForm,
)
from accounts.models import ServiceSeeker


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
                    ServiceSeeker.objects.create(
                        user=user, username=user.username, email=user.email
                    )
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


def profile_view(request):
    user = request.user
    if user.user_type == "service_provider":
        service_provider = ""
        service_provider = get_object_or_404(service_provider, user=user)
        # TODO: Service Provider
        form = None

        # If it's a POST request, we're updating the profile
        # if request.method == "POST":
        #     form = ServiceProviderForm(request.POST, instance=service_provider)
        #     if form.is_valid():
        #         form.save()
        #         return redirect("profile_view")  # Redirect to avoid resubmission
        # else:
        #     form = ServiceProviderForm(instance=service_provider)

        return render(
            request,
            "profile_service_provider.html",
            {
                "profile": service_provider,
                "form": form,  # Pass the form to the template
            },
        )
    elif user.user_type == "user":
        service_seeker = get_object_or_404(ServiceSeeker, user=user)

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
