from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("service_provider", "Service Provider"),
        ("user", "User"),
    )

    email = models.EmailField(unique=True)

    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="user"
    )

    def __str__(self):
        return self.username
