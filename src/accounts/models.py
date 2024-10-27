from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("service_provider", "Service Provider"),
        ("user", "User"),
    )

    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="user"
    )

    def __str__(self):
        return self.username


class ServiceSeeker(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    bookmarked_services = models.JSONField(
        default=list, blank=True, null=True
    )  # Allow null values
    location_preference = models.CharField(
        max_length=255, help_text="Preferred borough or location in NYC"
    )

    def __str__(self):
        return f"Seeker: {self.user.username}"
