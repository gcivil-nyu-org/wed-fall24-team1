from django.db import models
from accounts.models import CustomUser


class ServiceSeeker(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bookmarked_services = models.JSONField(
        default=list, blank=True, null=True
    )  # Allow null values
    location_preference = models.CharField(
        max_length=255, help_text="Preferred borough or location in NYC"
    )

    def __str__(self):
        return f"Seeker: {self.user.username}"
