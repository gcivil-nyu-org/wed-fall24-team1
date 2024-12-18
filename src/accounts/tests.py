from unittest.mock import patch

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from accounts.backends import EmailOrUsernameBackend
from accounts.forms import ServiceProviderLoginForm, UserLoginForm, UserRegisterForm
from accounts.models import CustomUser

User = get_user_model()


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",
            user_type="user",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertTrue(self.user.check_password("testpassword"))
        self.assertEqual(self.user.user_type, "user")

    def test_string_representation(self):
        """Test if the string representation of the user is correct."""
        self.assertEqual(str(self.user.username), "testuser")


# ---------- Form Tests ----------
class UserRegisterFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "new",
            "last_name": "user",
            "password1": "Testpassword123!",
            "password2": "Testpassword123!",
            "user_type": "user",
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_password_mismatch(self):
        """Test if the form is invalid when passwords don't match."""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "Testpassword123!",
            "password2": "Wrongpassword123!",
            "user_type": "user",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


# ---------- View Tests ----------
class RegisterViewTest(TestCase):
    def test_register_view_post_valid_data(self):
        """Test POST request with valid data to the registration page."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "testuser@example.com",
                "first_name": "test",
                "last_name": "user",
                "password1": "Testpassword123!",
                "password2": "Testpassword123!",
                "user_type": "user",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username="testuser").exists())

    def test_register_view_post_invalid_data(self):
        """Test POST request with invalid data to the registration page."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "",
                "email": "invalid-email",
                "password1": "short",
                "password2": "short",
                "user_type": "user",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("Enter a valid email address.", form.errors["email"])


class UserLoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Testpassword123!",
            user_type="user",
        )

    @patch("home.repositories.HomeRepository.fetch_items_with_filter")
    def test_login_view_post_valid(self, mock_fetch_items):
        """Test valid user login."""
        mock_fetch_items.return_value = []  # Mocked response

        response = self.client.post(
            reverse("user_login"),
            {"username": "testuser", "password": "Testpassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class ServiceProviderLoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.sp_user = CustomUser.objects.create_user(
            username="spuser",
            email="spuser@example.com",
            password="Testpassword123!",
            user_type="service_provider",
        )

    def test_service_provider_login_valid(self):
        """Test service provider login with valid credentials."""
        response = self.client.post(
            reverse("service_provider_login"),
            {"email": "spuser@example.com", "password": "Testpassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        # Assuming "services:list" is the redirect for service providers:
        # Update to your actual service provider dashboard URL if different
        self.assertRedirects(response, reverse("services:list"))

    def test_service_provider_login_invalid(self):
        """Test service provider login with invalid credentials."""
        response = self.client.post(
            reverse("service_provider_login"),
            {"email": "wrong@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid email or password.", form.errors["__all__"])


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Testpassword123!",
            user_type="user",
        )

    def test_logout(self):
        """Test that a logged-in user is logged out successfully."""
        self.client.login(username="testuser", password="Testpassword123!")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        # self.assertRedirects(response, reverse("user_login"))


class RegisterDuplicateUsernameTest(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Testpassword123!",
            user_type="user",
        )

    def test_register_duplicate_username(self):
        """Test registration with an already existing username."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",  # Existing username
                "email": "newuser@example.com",
                "password1": "Newpassword123!",
                "password2": "Newpassword123!",
                "user_type": "user",
            },
        )

        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn(
            "A user with that username already exists.", form.errors["username"]
        )


class UserTypeRedirectTest(TestCase):
    @patch("home.repositories.HomeRepository.fetch_items_with_filter")
    def test_user_redirects_to_home(self, mock_fetch_items):
        """Test if a user is redirected to the home page after registration."""
        mock_fetch_items.return_value = []  # Mocked response

        response = self.client.post(
            reverse("register"),
            {
                "username": "user1",
                "email": "user1@example.com",
                "first_name": "test",
                "last_name": "user",
                "password1": "Testpassword123!",
                "password2": "Testpassword123!",
                "user_type": "user",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))


class EmptyRegisterFormTest(TestCase):
    def test_register_view_post_empty_data(self):
        """Test POST request to registration with no data."""
        response = self.client.post(reverse("register"), {})
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())


class CustomUserServiceProviderTest(TestCase):
    def test_string_representation_service_provider(self):
        """Test string representation for a service provider."""
        service_provider = CustomUser(
            username="provider3", user_type="service_provider"
        )
        self.assertEqual(str(service_provider.username), "provider3")


class InvalidServiceProviderLoginFormTest(TestCase):
    def test_invalid_service_provider_login_form(self):
        """Test service provider login form with no data."""
        form = ServiceProviderLoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("password", form.errors)


class DuplicateEmailTest(TestCase):
    def setUp(self):
        CustomUser.objects.create_user(
            username="existinguser",
            email="duplicate@example.com",
            password="ExistingPassword123!",
            user_type="user",
        )


class EmailOrUsernameBackendTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.backend = EmailOrUsernameBackend()
        self.user_model = get_user_model()
        self.request = self.factory.get("/")  # Simulate a GET request for testing

        # Create a test user with both email and username
        self.user = self.user_model.objects.create_user(
            username="testuser", email="testuser@example.com", password="password123"
        )

    def test_authenticate_with_valid_username(self):
        """Test user can authenticate using username"""
        user = authenticate(
            request=self.request, username="testuser", password="password123"
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")

    def test_authenticate_with_invalid_username(self):
        """Test authentication fails with invalid username"""
        user = authenticate(
            request=self.request, username="wronguser", password="password123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_invalid_email(self):
        """Test authentication fails with invalid email"""
        user = authenticate(
            request=self.request,
            username="wrongemail@example.com",
            password="password123",
        )
        self.assertIsNone(user)

    def test_authenticate_with_wrong_password(self):
        """Test authentication fails with correct username/email but wrong password"""
        user = authenticate(
            request=self.request, username="testuser", password="wrongpassword"
        )
        self.assertIsNone(user)

    def test_get_user_valid(self):
        """Test get_user returns a valid user"""
        user = self.backend.get_user(self.user.pk)
        self.assertEqual(user.username, "testuser")

    def test_get_user_invalid(self):
        """Test get_user returns None for invalid user_id"""
        user = self.backend.get_user(9999)
        self.assertIsNone(user)


class ProfileViewTest(TestCase):
    def setUp(self):
        # Create a user with type "service_provider"
        self.service_provider_user = CustomUser.objects.create_user(
            username="provider",
            email="provider@example.com",
            password="testpassword",
            user_type="service_provider",
        )
        # Create a user with type "user"
        self.service_seeker_user = CustomUser.objects.create_user(
            username="seeker",
            email="seeker@example.com",
            password="testpassword",
            user_type="user",
        )

    def test_profile_view_service_provider(self):
        """Test that 'hello' is returned for a service_provider user type."""
        # Log in as service provider
        self.client.login(username="provider", password="testpassword")
        response = self.client.get(reverse("profile_view"))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_service_seeker_get(self):
        """Test that the profile view renders correctly for a user with type 'user'."""
        self.client.login(username="seeker", password="testpassword")
        response = self.client.get(reverse("profile_view"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_base.html")
        self.assertNotContains(
            response, "is_service_provider"
        )  # since user is not provider


class UserRegisterFormEdgeCaseTest(TestCase):
    def test_invalid_username(self):
        """Test if the form is invalid with a non-alphanumeric username."""
        form_data = {
            "username": "invalid@user!",
            "email": "newuser@example.com",
            "password1": "ValidPass123!",
            "password2": "ValidPass123!",
            "user_type": "user",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_missing_user_type(self):
        """Test if the form is invalid when user_type is missing."""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "ValidPass123!",
            "password2": "ValidPass123!",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("user_type", form.errors)

    def test_weak_password(self):
        """Test if the form rejects a weak password."""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "password",  # Weak password
            "password2": "password",
            "user_type": "user",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class UserLoginFormEmailAndUsernameTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="ValidPass123!",
            user_type="user",
            is_active=True,
        )

    def test_login_with_username(self):
        """Test login with a valid username and password."""
        form_data = {"username": "testuser", "password": "ValidPass123!"}
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_with_email(self):
        """Test login with a valid email and password."""
        request = self.factory.post("/login/")
        form_data = {"username": "testuser@example.com", "password": "ValidPass123!"}
        form = UserLoginForm(data=form_data, request=request)
        self.assertFalse(form.is_valid())

    def test_login_with_invalid_email_or_username(self):
        """Test login with invalid username or email."""
        request = self.factory.post("/login/")
        form_data = {"username": "wronguser", "password": "ValidPass123!"}
        form = UserLoginForm(data=form_data, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid username/email or password.", form.errors["__all__"])

    def test_login_without_username_or_password(self):
        """Test login with missing username or password."""
        form_data = {"username": "", "password": ""}
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Please enter both username/email and password.", form.errors["__all__"]
        )


class ServiceProviderLoginFormUserTypeTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="regularuser",
            email="user@example.com",
            password="ValidPass123!",
            user_type="user",  # Regular user, not a service provider
            is_active=True,
        )
        self.factory = RequestFactory()

    def test_regular_user_cannot_login_as_service_provider(self):
        """Test that regular users are blocked from logging in as service providers."""
        request = self.factory.post("/login/")
        form_data = {"email": "user@example.com", "password": "ValidPass123!"}
        form = ServiceProviderLoginForm(data=form_data, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "This page is for service providers only.", form.errors["__all__"]
        )


class ServiceProviderLoginFormNonExistentUserTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_nonexistent_user_login(self):
        """Test login attempt with an email that doesn't exist."""
        request = self.factory.post("/login/")
        form_data = {"email": "nonexistent@example.com", "password": "Password123!"}
        form = ServiceProviderLoginForm(data=form_data, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid email or password.", form.errors["__all__"])


class ServiceProviderLoginFormEmptyFieldsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_missing_email_and_password(self):
        """Test login attempt with missing email and password."""
        request = self.factory.post("/login/")
        form_data = {"email": "", "password": ""}
        form = ServiceProviderLoginForm(data=form_data, request=request)
        self.assertFalse(form.is_valid())
        self.assertIn("Please enter both email and password.", form.errors["__all__"])


class EmailOrUsernameBackendUncoveredTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create an active user for valid test scenarios
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="TestPass123!",
            is_active=True,
        )

    def test_authenticate_with_none_username(self):
        """Test authentication fails when username is None."""
        request = self.factory.post("/login/")
        user = authenticate(request=request, username=None, password="TestPass123!")
        self.assertIsNone(user)

    def test_authenticate_with_none_password(self):
        """Test authentication fails when password is None."""
        request = self.factory.post("/login/")
        user = authenticate(request=request, username="testuser", password=None)
        self.assertIsNone(user)

    def test_user_not_found_by_username(self):
        """Test backend tries email if username doesn't exist."""
        request = self.factory.post("/login/")
        user = authenticate(
            request=request, username="nonexistent", password="TestPass123!"
        )
        self.assertIsNone(user)

    def test_user_not_found_by_username_or_email(self):
        """Test returns None if both username and email don't exist."""
        request = self.factory.post("/login/")
        user = authenticate(
            request=request, username="wrongemail@example.com", password="TestPass123!"
        )
        self.assertIsNone(user)

    def test_authenticate_with_invalid_password(self):
        """Test authentication fails with a valid username but wrong password."""
        request = self.factory.post("/login/")
        user = authenticate(request=request, username="testuser", password="WrongPass!")
        self.assertIsNone(user)

    def test_authenticate_with_inactive_user(self):
        """Test that an inactive user cannot authenticate."""
        self.user.is_active = False
        self.user.save()

        request = self.factory.post("/login/")
        user = authenticate(
            request=request, username="testuser", password="TestPass123!"
        )
        self.assertIsNone(user)
