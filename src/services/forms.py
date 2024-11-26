# services/forms.py
from decimal import Decimal

from better_profanity import profanity
from django import forms
from django.forms import formset_factory
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from django.forms import BaseFormSet


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
    is_active = forms.BooleanField(
        required=False, initial=True, label="Is the service currently available?"
    )
    announcement = forms.CharField(  # Add this field
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Enter your announcement here"}
        ),
        required=False,
        max_length=500,
        help_text="Use this space to inform users about temporary changes or important updates.",
    )

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
        if "announcement" in cleaned_data:
            announcement = cleaned_data["announcement"]
            if announcement:
                profanity.load_censor_words()
                cleaned_data["announcement"] = profanity.censor(announcement)

        return cleaned_data


class DescriptionItemForm(forms.Form):
    key = forms.CharField(max_length=100,
                          widget=forms.TextInput(
                              attrs={
                                  "class": "w-full p-2 rounded bg-gray-600 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                              }
                          ),
                          )
    value = forms.CharField(widget=forms.Textarea(attrs={
        "rows": 3,
        "class": "w-full p-2 rounded bg-gray-600 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600",
    }))


class CustomDescriptionFormSet(BaseFormSet):
    def clean(self):
        """
        Adds validation to check for duplicate keys in the formset.
        """
        if any(self.errors):
            return

        keys = []
        duplicate_keys = set()

        # First pass: collect all keys and identify duplicates
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            if form.cleaned_data:
                key = form.cleaned_data.get("key")
                if key:
                    print(f"Processing key: {key}")  # Debug print
                    if key in keys:
                        duplicate_keys.add(key)
                    keys.append(key)

        # Second pass: add errors to all forms with duplicate keys
        if duplicate_keys:
            for form in self.forms:
                if self.can_delete and self._should_delete_form(form):
                    continue

                if form.cleaned_data:
                    key = form.cleaned_data.get("key")
                    if key in duplicate_keys:
                        form.add_error(
                            "key",
                            f"Duplicate key detected: '{key}'. Each key must be unique.",
                        )

            # Raise the validation error with all duplicate keys listed
            raise forms.ValidationError(
                f"Duplicate keys found: {', '.join(duplicate_keys)}. Each key must be unique."
            )

        print(f"All keys found: {keys}")  # Debug print for all keys
        return self.cleaned_data


DescriptionFormSet = formset_factory(
    DescriptionItemForm,
    formset=CustomDescriptionFormSet,
    extra=0,
    can_delete=True,
)


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
