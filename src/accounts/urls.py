# accounts/urls.py

from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import UserLoginView, ServiceProviderLoginView, profile_view, register

urlpatterns = [
    path("register/", register, name="register"),
    path("login/user/", UserLoginView.as_view(), name="user_login"),
    path(
        "login/service_provider/",
        ServiceProviderLoginView.as_view(),
        name="service_provider_login",
    ),
    path("profile/", profile_view, name="profile_view"),
    path(
        "logout/", auth_views.LogoutView.as_view(next_page="user_login"), name="logout"
    ),  # Logout URL
    path("", include("allauth.urls")),  # This allows allauth URLs under /accounts/
]
