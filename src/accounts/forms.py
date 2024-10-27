# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from accounts.models import CustomUser, ServiceSeeker


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2", "user_type"]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class ServiceProviderLoginForm(AuthenticationForm):
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        UserModel = CustomUser
        try:
            user = UserModel.objects.get(email=email)
            if not user.check_password(password):
                raise forms.ValidationError("Invalid email or password")
            if user.user_type != "service_provider":
                raise forms.ValidationError("This page is for service providers only.")
        except UserModel.DoesNotExist:
            raise forms.ValidationError("Invalid email or password")
        return cleaned_data


class ServiceSeekerForm(forms.ModelForm):
    class Meta:
        model = ServiceSeeker
        fields = ["username", "email", "location_preference", "bookmarked_services"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                    "readonly": "readonly",  # Make username non-editable
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                    "readonly": "readonly",  # Make email non-editable
                }
            ),
            "location_preference": forms.TextInput(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                }
            ),
            "bookmarked_services": forms.SelectMultiple(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                }
            ),
        }
