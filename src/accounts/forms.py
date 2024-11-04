# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2", "user_type"]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            # Allow users to log in with either username or email
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                # Try authenticating with email
                user = authenticate(self.request, email=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username/email or password.")
            else:
                self.confirm_login_allowed(user)
                self.user_cache = user
        else:
            raise forms.ValidationError(
                "Please enter both username/email and password."
            )
        return self.cleaned_data


class ServiceProviderLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=True,
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        Override the default initialization to set autofocus and remove unnecessary fields.
        """
        super().__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': True})

    def confirm_login_allowed(self, user):
        """
        Ensure that only active service providers can log in.
        """
        if not user.is_active:
            raise ValidationError(
                _("This account is inactive."),
                code='inactive',
            )
        if user.user_type != "service_provider":
            raise ValidationError(
                _("This page is for service providers only."),
                code='invalid_login',
            )


class ServiceSeekerForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name"]
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
            "first_name": forms.TextInput(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700",
                }
            ),
        }
