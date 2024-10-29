from unittest.mock import patch

from accounts.backends import EmailOrUsernameBackend
from accounts.forms import ServiceProviderLoginForm, UserRegisterForm
from accounts.models import CustomUser
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse


# ---------- Model Tests ----------
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
        self.assertEqual(str(self.user), "testuser")


# ---------- Form Tests ----------
class UserRegisterFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
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
    # def test_register_view_post_valid_data(self):
    #     response = self.client.post(
    #         reverse("register"),
    #         {
    #             "username": "testuser",
    #             "email": "testuser@example.com",
    #             "password1": "Testpassword123!",
    #             "password2": "Testpassword123!",
    #             "user_type": "user",
    #         },
    #     )
    #     self.assertEqual(response.status_code, 302)
    #     self.assertRedirects(response, reverse("home"))

    def test_register_view_post_valid_data(self):
        """Test POST request with valid data to the registration page."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "testuser@example.com",
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

    # def test_login_view_get(self):
    #     """Test the login page loads correctly with a GET request."""
    #     response = self.client.get(reverse("user_login"))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "user_login.html")
    #     self.assertIsInstance(response.context["form"], UserLoginForm)


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
                "password1": "Testpassword123!",
                "password2": "Testpassword123!",
                "user_type": "user",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    # def test_service_provider_redirects_to_dashboard(self):
    #     """Test if a service provider is redirected to the dashboard after registration."""
    #     response = self.client.post(reverse("register"), {
    #         "username": "provider1",
    #         "email": "provider1@example.com",
    #         "password1": "Testpassword123!",
    #         "password2": "Testpassword123!",
    #         "user_type": "service_provider"
    #     })
    #     self.assertEqual(response.status_code, 302)
    #     self.assertRedirects(response, reverse("service_provider_dashboard"))


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
        self.assertEqual(str(service_provider), "provider3")


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

    # def test_register_duplicate_email(self):
    #     """Test registration with a duplicate email."""
    #     response = self.client.post(
    #         reverse("register"),
    #         {
    #             "username": "newuser",
    #             "email": "duplicate@example.com",
    #             "password1": "NewPassword123!",
    #             "password2": "NewPassword123!",
    #             "user_type": "user",
    #         },
    #     )
    #     form = response.context.get("form")
    #     self.assertIsNotNone(form)
    #     self.assertFalse(form.is_valid())


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
