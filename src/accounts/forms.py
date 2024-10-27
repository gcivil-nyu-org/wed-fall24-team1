# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2", "user_type"]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username", widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True,
    )


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
                if user.user_type != "service_provider":
                    raise forms.ValidationError(
                        "This page is for service providers only."
                    )

                # Set the username field for authentication
                self.cleaned_data["username"] = user.username
            except UserModel.DoesNotExist:
                raise forms.ValidationError("Invalid email or password")

        return super().clean()

    def get_invalid_login_error(self):
        return forms.ValidationError("Invalid email or password.")
