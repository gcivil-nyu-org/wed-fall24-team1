# public_service_finder/urls.py

from django.contrib import admin
from django.urls import path, include
from .views import root_redirect_view  # Import the redirect view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("home/", include("home.urls")),
    path("", root_redirect_view, name="root_redirect"),  # Use the custom redirect view
    path('profile/', include("profileapp.urls") ),
]
