from django import forms

class ServiceProviderForm(forms.Form):
    business_name = forms.CharField(max_length=255)
    business_address = forms.CharField(max_length=255)
    service_description = forms.CharField(widget=forms.Textarea)
    service_categories = forms.CharField(max_length=255)
    service_location = forms.CharField(max_length=255)
    availability = forms.CharField(max_length=255)
    price_range = forms.CharField(max_length=100)
    phone_number = forms.CharField(max_length=20)
    website = forms.URLField(required=False)  # Optional field
