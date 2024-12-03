# accounts/urls.py

from django.contrib.auth import views as auth_views
from django.urls import path, include

from .views import UserLoginView, ServiceProviderLoginView, register, CustomLogoutView
from accounts import views


# app_name = "accounts"  # This line defines the 'accounts' namespace

urlpatterns = [
    path("register/", register, name="register"),
    path("login/user/", UserLoginView.as_view(), name="user_login"),
    path(
        "login/service_provider/",
        ServiceProviderLoginView.as_view(),
        name="service_provider_login",
    ),
    path("profile/", views.profile_view, name="profile_view"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),  # Logout URL
    path("", include("allauth.urls")),  # This allows allauth URLs under /accounts/
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
