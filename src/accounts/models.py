from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("service_provider", "Service Provider"),
        ("user", "User"),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)

    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="user"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
