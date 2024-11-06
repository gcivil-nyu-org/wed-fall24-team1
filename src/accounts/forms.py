# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist

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
                if user.user_type != "user":
                    raise forms.ValidationError("This page is for users only.")
                self.confirm_login_allowed(user)
                self.user_cache = user
        else:
            raise forms.ValidationError(
                "Please enter both username/email and password."
            )
        return self.cleaned_data


class ServiceProviderLoginForm(AuthenticationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields.pop("username")  # Remove the username field

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(email=email)
                self.user_cache = authenticate(
                    self.request, username=user.username, password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError("Invalid email or password.")
                else:
                    if self.user_cache.user_type != "service_provider":
                        raise forms.ValidationError(
                            "This page is for service providers only."
                        )
                    self.confirm_login_allowed(self.user_cache)
            except ObjectDoesNotExist:
                raise forms.ValidationError("Invalid email or password.")
        else:
            raise forms.ValidationError("Please enter both email and password.")
        return self.cleaned_data

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return forms.ValidationError("Invalid email or password.")


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


class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name"]
        # Add any other basic fields you want to include for service providers
