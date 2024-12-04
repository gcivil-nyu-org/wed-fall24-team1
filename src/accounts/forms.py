# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    SetPasswordForm,
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import PasswordResetForm

from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Username",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Email Address",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "First Name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Last Name",
            }
        ),
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter Password",
            }
        ),
        required=True,
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Confirm Password",
            }
        ),
        required=True,
    )

    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Select User Type",
            }
        ),
    )
    profile_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
            }
        ),
        help_text="Optional. Upload a profile image.",
    )

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "user_type",
            "profile_image",  # Add this field
        ]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter your username",
            }
        ),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter your password",
            }
        ),
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
        widget=forms.EmailInput(
            attrs={
                "class": "form-control w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter your email",
            }
        ),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter your password",
            }
        ),
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
    profile_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
            }
        ),
        help_text="Upload a new profile image or leave blank to keep the current one.",
    )
    remove_profile_image = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove profile image",
        help_text="Check this box to remove your current profile image.",
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "profile_image"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "readonly": "readonly",  # Make username non-editable
                    "placeholder": "Username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "readonly": "readonly",  # Make email non-editable
                    "placeholder": "Email Address",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "placeholder": "First Name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "placeholder": "Last Name",
                }
            ),
        }


# Note: We're maintaining two different forms (even though they're the same) for seekers and providers to future-proof our code.
# We *might* add additional fields for service providers soon.
class ServiceProviderForm(forms.ModelForm):
    profile_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
            }
        ),
        help_text="Upload a new profile image or leave blank to keep the current one.",
    )
    remove_profile_image = forms.BooleanField(
        required=False,
        initial=False,
        label="Remove profile image",
        help_text="Check this box to remove your current profile image.",
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "profile_image"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "readonly": "readonly",  # Make username non-editable
                    "placeholder": "Username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "readonly": "readonly",  # Make email non-editable
                    "placeholder": "Email Address",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "placeholder": "First Name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                    "placeholder": "Last Name",
                }
            ),
        }
        # Add any other basic fields you want to include for service providers


class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the widget attributes for the email field
        self.fields["email"].widget.attrs.update(
            {
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter Email",
                "label": "Enter Email",
            }
        )


class CustomPasswordResetSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update the widget attributes for the email field
        print(self.fields)
        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Enter Password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600",
                "placeholder": "Confirm Password",
            }
        )
