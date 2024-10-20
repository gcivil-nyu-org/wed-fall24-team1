from django import forms

from profileapp.models.service_seeker_model import ServiceSeeker


class ServiceSeekerForm(forms.ModelForm):
    class Meta:
        model = ServiceSeeker
        fields = ['location_preference', 'bookmarked_services']
        widgets = {
            'location_preference': forms.TextInput(attrs={
                'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700',
            }),
            'bookmarked_services': forms.SelectMultiple(attrs={
                'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700',
            }),
        }
