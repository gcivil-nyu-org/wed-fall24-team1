# services/forms.py
from decimal import Decimal

import requests
from django import forms
from django.conf import settings
from django.forms import formset_factory


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
            # Perform forward geocoding
            api_key = settings.GEOCODING_API_KEY  # Replace with your actual API key
            url = f"https://api.positionstack.com/v1/forward?access_key={api_key}&query={address}"

            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()["data"]
                if data:
                    # Use the first result
                    result = data[0]
                    cleaned_data["latitude"] = Decimal(str(result["latitude"]))
                    cleaned_data["longitude"] = Decimal(str(result["longitude"]))
                else:
                    # Add error to the address field
                    self.add_error(
                        "address",
                        "Unable to geocode the given address. Please check if the address is correct.",
                    )
            else:
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


class DescriptionItemForm(forms.Form):
    key = forms.CharField(max_length=100)
    value = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))


DescriptionFormSet = formset_factory(DescriptionItemForm, extra=1, can_delete=True)
