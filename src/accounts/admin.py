# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _


# Customize the UserAdmin for CustomUser
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list view
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_staff",
    )

    # Fields to filter by in the list view
    list_filter = ("user_type", "is_staff", "is_superuser", "is_active", "groups")

    # Custom fieldsets for detail view
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Additional info"),
            {"fields": ("user_type",)},
        ),  # Add your custom fields here
    )

    # Add fields for the create user page
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "user_type"),
            },
        ),
    )

    # Fields to search by
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


# Register the CustomUser model with CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
