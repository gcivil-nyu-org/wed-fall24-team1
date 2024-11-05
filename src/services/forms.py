# services/forms.py
from decimal import Decimal

from django import forms
from django.forms import formset_factory
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class ServiceForm(forms.Form):
    CATEGORY_CHOICES = [
        ("Mental Health Center", "Mental Health Center"),
        ("Homeless Shelter", "Homeless Shelter"),
        ("Food Pantry", "Food Pantry"),
        ("Restroom", "Restroom"),
    ]

    name = forms.CharField(max_length=255)
    address = forms.CharField(widget=forms.Textarea)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        address = cleaned_data.get("address")

        if address:
            geolocator = Nominatim(user_agent="public_service_finder")
            try:
                location = geolocator.geocode(address)
                if location:
                    cleaned_data["latitude"] = Decimal(str(location.latitude))
                    cleaned_data["longitude"] = Decimal(str(location.longitude))
                else:
                    self.add_error(
                        "address",
                        "Unable to geocode the given address. Please check if the address is correct.",
                    )
            except (GeocoderTimedOut, GeocoderServiceError):
                self.add_error(
                    "address",
                    "Error occurred while geocoding the address. Please try again later.",
                )

        # Translate category to backend value
        category_translation = {
            "Mental Health Center": "MENTAL",
            "Homeless Shelter": "SHELTER",
            "Food Pantry": "FOOD",
            "Restroom": "RESTROOM",
        }
        cleaned_data["category"] = category_translation[cleaned_data["category"]]

        return cleaned_data


class DescriptionItemForm(forms.Form):
    key = forms.CharField(max_length=100)
    value = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))


DescriptionFormSet = formset_factory(DescriptionItemForm, extra=1, can_delete=True)


class ReviewResponseForm(forms.Form):
    responseText = forms.CharField(  # Changed from 'response' to 'responseText'
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                "rows": "4",
                "placeholder": "Enter your response to this review...",
            }
        ),
        required=True,
    )
