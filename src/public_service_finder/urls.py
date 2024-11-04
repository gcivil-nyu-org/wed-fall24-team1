# public_service_finder/urls.py

from django.contrib import admin
from django.urls import path, include
from .views import (
    admin_only_view_new_listings,
    admin_update_listing,
    root_redirect_view,
)  # Import the redirect view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("home/", include("home.urls")),
    path("", root_redirect_view, name="root_redirect"),  # Use the custom redirect view
    path("services/", include("services.urls", namespace="services")),
    path(
        "admin-only-view-new-listings/",
        admin_only_view_new_listings,
        name="admin_only_view_new_listings",
    ),
    path(
        "admin-listing/update/<uuid:service_id>/",
        admin_update_listing,
        name="admin_update_listing",
    ),  # Changed prefix
]
