import uuid
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialApp
from django.contrib.contenttypes.models import ContentType

from moderation.models import Flag
from public_service_finder.utils.enums.service_status import ServiceStatus
from services.repositories import ServiceRepository

User = get_user_model()


class RootRedirectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            user_type="normal_user",
            email="testuser@example.com",
        )
        self.service_provider = User.objects.create_user(
            username="serviceuser",
            password="testpass123",
            user_type="service_provider",
            email="serviceuser@example.com",
        )
        patcher = patch("allauth.socialaccount.models.SocialApp.objects.get")
        self.mock_get = patcher.start()
        self.mock_get.return_value = SocialApp(
            provider="google", name="Google", client_id="dummy", secret="dummy"
        )
        self.addCleanup(patcher.stop)

    def test_root_redirect_unauthenticated(self):
        # Unauthenticated user should be redirected to "home"
        response = self.client.get(reverse("root_redirect"))
        self.assertRedirects(response, reverse("home"))

    def test_root_redirect_authenticated_normal_user(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("root_redirect"))
        self.assertRedirects(response, reverse("home"))

    def test_root_redirect_authenticated_service_provider(self):
        self.client.login(username="serviceuser", password="testpass123")
        response = self.client.get(reverse("root_redirect"))
        # For service_provider users, redirect to services:list
        self.assertRedirects(response, reverse("services:list"))


class AdminOnlyViewNewListingsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            password="adminpass123",
            user_type="normal_user",
            email="adminuser@example.com",
        )
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="testpass123",
            user_type="normal_user",
            email="regularuser@example.com",
        )

    def test_admin_only_view_not_logged_in(self):
        # Should redirect to login page due to @login_required
        response = self.client.get(reverse("admin_only_view_new_listings"))
        self.assertNotEqual(response.status_code, 200)
        self.assertIn("/accounts/login/", response.url)

    def test_admin_only_view_non_superuser(self):
        # Logged in as non-superuser should return 403
        self.client.login(username="regularuser", password="testpass123")
        response = self.client.get(reverse("admin_only_view_new_listings"))
        self.assertEqual(response.status_code, 403)

    @patch.object(ServiceRepository, "get_pending_approval_services", return_value=[])
    def test_admin_only_view_superuser_no_flags_no_services(self, mock_services):
        # Logged in as superuser with no pending services and no flags
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(reverse("admin_only_view_new_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_only.html")
        self.assertEqual(len(response.context["pending_services"]), 0)
        self.assertEqual(len(response.context["flags"]), 0)

    @patch.object(
        ServiceRepository,
        "get_pending_approval_services",
        return_value=[{"id": str(uuid.uuid4()), "name": "Test Service"}],
    )
    def test_admin_only_view_superuser_with_services(self, mock_services):
        # Logged in as superuser with some pending services, but no flags
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(reverse("admin_only_view_new_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_only.html")
        self.assertEqual(len(response.context["pending_services"]), 1)
        self.assertEqual(len(response.context["flags"]), 0)

    @patch.object(ServiceRepository, "get_pending_approval_services", return_value=[])
    def test_admin_only_view_superuser_with_flags(self, mock_services):
        # Create some pending flags
        self.client.login(username="adminuser", password="adminpass123")
        flagger = User.objects.create_user(
            username="flagger", password="flagpass", email="flagger@example.com"
        )
        content_type = ContentType.objects.get_for_model(User)

        Flag.objects.create(
            content_type=content_type,
            object_id=flagger.id,
            content_preview="Some preview",
            content_title="Title",
            content_rating=5,
            content_author="Author",
            created_at="2024-01-01T10:00:00Z",
            flagger=flagger,
            reason="Test reason",
            explanation="Test explanation",
            status="PENDING",
        )

        response = self.client.get(reverse("admin_only_view_new_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_only.html")
        self.assertEqual(len(response.context["flags"]), 1)
        flag_group = response.context["flags"][0]
        self.assertEqual(flag_group["content_preview"], "Some preview")
        self.assertEqual(flag_group["flag_count"], 1)
        self.assertEqual(len(flag_group["flags"]), 1)


class AdminUpdateListingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.service_id = uuid.uuid4()  # Use a UUID to match the URL pattern
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            password="adminpass123",
            user_type="normal_user",
            email="adminuser@example.com",
        )
        self.regular_user = User.objects.create_user(
            username="regularuser2",
            password="testpass123",
            user_type="normal_user",
            email="regularuser2@example.com",
        )

    def test_admin_update_not_logged_in(self):
        # Not logged in: should redirect to login
        response = self.client.get(
            reverse("admin_update_listing", args=[self.service_id])
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertIn("/accounts/login/", response.url)

    def test_admin_update_not_superuser(self):
        # Logged in as non-superuser should return 403 on POST and GET
        self.client.login(username="regularuser2", password="testpass123")
        response = self.client.post(
            reverse("admin_update_listing", args=[self.service_id]),
            {"status": "approve"},
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.get(
            reverse("admin_update_listing", args=[self.service_id])
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_update_get_request_superuser(self):
        # GET request should redirect back to listings page
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.get(
            reverse("admin_update_listing", args=[self.service_id])
        )
        self.assertRedirects(response, reverse("admin_only_view_new_listings"))

    @patch.object(ServiceRepository, "update_service_status")
    def test_admin_update_post_approve_superuser(self, mock_update):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.post(
            reverse("admin_update_listing", args=[self.service_id]),
            {"status": "approve"},
        )
        self.assertRedirects(response, reverse("admin_only_view_new_listings"))
        mock_update.assert_called_once_with(
            self.service_id, ServiceStatus.APPROVED.value
        )

    @patch.object(ServiceRepository, "update_service_status")
    def test_admin_update_post_reject_superuser(self, mock_update):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.post(
            reverse("admin_update_listing", args=[self.service_id]),
            {"status": "reject"},
        )
        self.assertRedirects(response, reverse("admin_only_view_new_listings"))
        mock_update.assert_called_once_with(
            self.service_id, ServiceStatus.REJECTED.value
        )

    @patch.object(ServiceRepository, "update_service_status")
    def test_admin_update_post_invalid_status_superuser(self, mock_update):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.post(
            reverse("admin_update_listing", args=[self.service_id]),
            {"status": "invalid"},
        )
        self.assertRedirects(response, reverse("admin_only_view_new_listings"))
        mock_update.assert_not_called()

    @patch.object(
        ServiceRepository,
        "update_service_status",
        side_effect=Exception("Test Exception"),
    )
    def test_admin_update_post_exception_handling(self, mock_update):
        self.client.login(username="adminuser", password="adminpass123")
        response = self.client.post(
            reverse("admin_update_listing", args=[self.service_id]),
            {"status": "approve"},
        )
        self.assertRedirects(response, reverse("admin_only_view_new_listings"))
        mock_update.assert_called_once()
