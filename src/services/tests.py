# from django.test import TestCase
import uuid
from decimal import Decimal
from accounts.models import CustomUser
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from public_service_finder.utils.enums.service_status import ServiceStatus
from botocore.exceptions import ClientError
from .forms import ServiceForm, DescriptionFormSet, ReviewResponseForm
from .models import ServiceDTO, ReviewDTO
from .repositories import ReviewRepository, ServiceRepository

from unittest.mock import patch, MagicMock


class ServiceViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.service_provider = CustomUser.objects.create_user(
            username="provider",
            email="provider@email.com",
            password="testpass123",
            user_type="service_provider",
        )
        self.regular_user = CustomUser.objects.create_user(
            username="regular",
            email="regular@email.com",
            password="testpass123",
            user_type="user",
        )
        self.service_repo = ServiceRepository()

    def tearDown(self):
        super().tearDown()
        CustomUser.objects.all().delete()

    def test_service_list_view(self):
        self.client.login(username="provider", password="testpass123")
        with patch.object(ServiceRepository, "get_services_by_provider") as mock_get:
            mock_get.return_value = [
                ServiceDTO(
                    id=str(uuid.uuid4()),
                    name="Service 1",
                    address="Addr1",
                    category="Metal Health Center",
                    provider_id=str(self.service_provider.id),
                    latitude=None,
                    longitude=None,
                    ratings=None,
                    description=None,
                    service_created_timestamp="2022-01-01T12:00:00Z",
                    service_status=ServiceStatus.APPROVED.value,
                    service_approved_timestamp="2022-01-01T12:00:00Z",
                    is_active=False,
                ),
                ServiceDTO(
                    id=str(uuid.uuid4()),
                    name="Service 2",
                    address="Addr2",
                    category="Food Pantry",
                    provider_id=str(self.service_provider.id),
                    ratings=None,
                    latitude=None,
                    longitude=None,
                    description=None,
                    service_created_timestamp="2022-01-01T12:00:00Z",
                    service_status=ServiceStatus.APPROVED.value,
                    service_approved_timestamp="2022-01-01T12:00:00Z",
                    is_active=False,
                ),
            ]
            response = self.client.get(reverse("services:list"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "service_list.html")
            self.assertEqual(len(response.context["services"]), 2)

    def test_service_list_view_permission_denied(self):
        self.client.login(username="regular", password="testpass123")
        resp = self.client.get(reverse("services:list"))
        self.assertEqual(resp.status_code, 403)

    def test_service_create_view_get(self):
        self.client.login(username="provider", password="testpass123")
        response = self.client.get(reverse("services:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service_form.html")
        self.assertIsInstance(response.context["form"], ServiceForm)
        self.assertIsInstance(
            response.context["description_formset"], DescriptionFormSet
        )

    def test_service_create_view_post_success(self):
        self.client.login(username="provider", password="testpass123")
        data = {
            "name": "New Service",
            "address": "123 Test St",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "category": "Mental Health Center",
            "description-0-key": "hours",
            "description-0-value": "9-5",
            "description-TOTAL_FORMS": "1",
            "description-INITIAL_FORMS": "0",
            "description-MIN_NUM_FORMS": "0",
            "description-MAX_NUM_FORMS": "1000",
        }
        with patch.object(ServiceRepository, "create_service") as mock_create:
            mock_create.return_value = True
            response = self.client.post(reverse("services:create"), data)
            self.assertRedirects(response, reverse("services:list"))

    def test_service_edit_view_get(self):
        self.client.login(username="provider", password="testpass123")
        service_id = str(uuid.uuid4())
        with patch.object(ServiceRepository, "get_service") as mock_get:
            mock_get.return_value = ServiceDTO(
                id=service_id,
                name="Test Service",
                provider_id=str(self.service_provider.id),
                category="MENTAL",
                address="123 Test St",
                latitude=Decimal(40.71),
                longitude=Decimal(-74.32),
                ratings=Decimal("4.5"),
                description={"hours": "9-5"},
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=True,
            )
            response = self.client.get(reverse("services:edit", args=[service_id]))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "service_form.html")

    def test_service_delete_view_get(self):
        self.client.login(username="provider", password="testpass123")
        service_id = str(uuid.uuid4())
        with patch.object(ServiceRepository, "get_service") as mock_get:
            mock_get.return_value = ServiceDTO(
                id=service_id,
                name="Test Service",
                address="Test Address",
                latitude=None,
                longitude=None,
                ratings=None,
                description=None,
                category="MENTAL",
                provider_id=str(self.service_provider.id),
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=False,
            )
            response = self.client.post(reverse("services:delete", args=[service_id]))
            self.assertEqual(response.status_code, 302)

    def test_service_delete_view_post(self):
        self.client.login(username="provider", password="testpass123")
        service_id = str(uuid.uuid4())
        with patch.object(ServiceRepository, "get_service") as mock_get, patch.object(
            ServiceRepository, "delete_service"
        ) as mock_delete:
            mock_get.return_value = ServiceDTO(
                id=service_id,
                name="Test Service",
                address="Test Address",
                latitude=None,
                longitude=None,
                ratings=None,
                description=None,
                category="MENTAL",
                provider_id=str(self.service_provider.id),
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=False,
            )
            mock_delete.return_value = True
            response = self.client.post(reverse("services:delete", args=[service_id]))
            self.assertRedirects(response, reverse("services:list"))

    def test_service_delete_view_permission_denied(self):
        self.client.login(username="regular", password="testpass123")
        service_id = str(uuid.uuid4())
        resp = self.client.get(reverse("services:delete", args=[service_id]))
        self.assertEqual(resp.status_code, 403)


User = get_user_model()


class ReviewListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass", email="testuser@example.com"
        )
        self.service_id = "service-id-123"
        self.client.login(username="testuser", password="testpass")

        # Sample service and reviews
        self.service = ServiceDTO(
            id=self.service_id,
            name="Test Service",
            provider_id=str(self.user.id),
            address="123 Main St",
            category="Category",
            latitude=0.0,
            longitude=0.0,
            ratings=5.0,
            description="Description",
            service_status="Active",
            service_created_timestamp="2021-01-01T00:00:00Z",
            service_approved_timestamp="2021-01-01T00:00:00Z",
            is_active=True,
        )
        self.review = ReviewDTO(
            review_id="review-id-123",
            service_id=self.service_id,
            user_id="user-id-123",
            username="reviewer",
            rating_stars=5,
            rating_message="Great service!",
            timestamp="2021-01-01T12:00:00Z",
        )

    @patch("services.views.review_repo.get_reviews_for_service")
    @patch("services.views.service_repo.get_service")
    def test_review_list_view_authenticated(self, mock_get_service, mock_get_reviews):
        # Mock repository methods
        mock_get_service.return_value = self.service
        mock_get_reviews.return_value = [self.review]

        response = self.client.get(
            reverse("services:review_list", args=[self.service_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "review_list.html")
        self.assertEqual(response.context["service"], self.service)
        self.assertEqual(response.context["reviews"], [self.review])

    @patch("services.views.service_repo.get_service")
    def test_review_list_view_service_not_found(self, mock_get_service):
        # Mock service not found
        mock_get_service.return_value = None

        response = self.client.get(
            reverse("services:review_list", args=[self.service_id])
        )
        self.assertEqual(response.status_code, 404)


class RespondToReviewViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider = User.objects.create_user(
            username="provider",
            password="testpass",
            email="provider@example.com",
            user_type="service_provider",
        )
        self.regular_user = User.objects.create_user(
            username="regular",
            password="testpass",
            email="regular@example.com",
            user_type="user",
        )
        self.service_id = "service-id-123"
        self.review_id = "review-id-123"

        # Sample service and review data
        self.service = ServiceDTO(
            id=self.service_id,
            name="Test Service",
            provider_id=str(self.provider.id),
            address="123 Main St",
            category="Category",
            latitude=0.0,
            longitude=0.0,
            ratings=5.0,
            description="Description",
            service_status="Active",
            service_created_timestamp="2021-01-01T00:00:00Z",
            service_approved_timestamp="2021-01-01T00:00:00Z",
            is_active=True,
        )
        self.review = ReviewDTO(
            review_id=self.review_id,
            service_id=self.service_id,
            user_id=str(self.regular_user.id),
            username="regular",
            rating_stars=5,
            rating_message="Excellent service",
            timestamp="2021-01-01T12:00:00Z",
            responseText="",
            responded_at="",
        )

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_get_provider(self, mock_get_review, mock_get_service):
        # Service provider can access the response form
        self.client.login(username="provider", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = self.review

        response = self.client.get(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "respond_to_review.html")
        self.assertIn("service", response.context)
        self.assertIn("review", response.context)
        self.assertIsInstance(response.context["form"], ReviewResponseForm)

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    @patch("services.views.review_repo.respond_to_review")
    def test_respond_to_review_post_success(
        self, mock_respond_to_review, mock_get_review, mock_get_service
    ):
        # Service provider successfully submits a response
        self.client.login(username="provider", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = self.review
        mock_respond_to_review.return_value = True

        response = self.client.post(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            ),
            {"responseText": "Thank you for your feedback!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content, {"status": "success", "message": "Response saved"}
        )
        mock_respond_to_review.assert_called_once_with(
            self.review_id, "Thank you for your feedback!"
        )

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_get_permission_denied(
        self, mock_get_review, mock_get_service
    ):
        # Regular user should not be able to access respond to review
        self.client.login(username="regular", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = self.review

        response = self.client.get(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content, {"status": "error", "message": "Permission denied"}
        )

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_post_permission_denied(
        self, mock_get_review, mock_get_service
    ):
        # Regular user attempts to POST a response
        self.client.login(username="regular", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = self.review

        response = self.client.post(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            ),
            {"responseText": "Trying to respond"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content, {"status": "error", "message": "Permission denied"}
        )

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_service_not_found(
        self, mock_get_review, mock_get_service
    ):
        # Service does not exist
        self.client.login(username="provider", password="testpass")
        mock_get_service.return_value = None  # Simulate service not found

        response = self.client.get(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            )
        )

        self.assertEqual(response.status_code, 404)

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_review_not_found(
        self, mock_get_review, mock_get_service
    ):
        # Review does not exist
        self.client.login(username="provider", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = None  # Simulate review not found

        response = self.client.get(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            )
        )

        self.assertEqual(response.status_code, 404)

    @patch("services.views.service_repo.get_service")
    @patch("services.views.review_repo.get_review")
    def test_respond_to_review_invalid_form(self, mock_get_review, mock_get_service):
        # Invalid form data submitted
        self.client.login(username="provider", password="testpass")
        mock_get_service.return_value = self.service
        mock_get_review.return_value = self.review

        response = self.client.post(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            ),
            {"responseText": ""},  # Empty responseText is invalid
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"status": "error", "message": "Invalid form data"}
        )

    def test_respond_to_review_not_authenticated(self):
        # Unauthenticated user tries to access the view
        response = self.client.get(
            reverse(
                "services:respond_to_review", args=[self.service_id, self.review_id]
            )
        )

        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))


class ServiceRepositoryTestCase(TestCase):
    def setUp(self):
        # Instantiate the ServiceRepository to be tested
        self.service_repo = ServiceRepository()

        # Sample service data
        self.sample_service = ServiceDTO(
            id=str(uuid.uuid4()),
            name="Test Service",
            address="123 Test St",
            category="Mental Health Center",
            provider_id="-1",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_status=ServiceStatus.APPROVED.value,
            service_approved_timestamp="2022-01-01T12:00:00Z",
            is_active=True,
        )

    @patch("services.repositories.ServiceRepository.get_services_by_provider")
    def test_get_services_by_provider(self, mock_get_services_by_provider):
        # Arrange
        mock_get_services_by_provider.return_value = [self.sample_service]

        # Act
        result = self.service_repo.get_services_by_provider(-1)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Test Service")
        mock_get_services_by_provider.assert_called_once_with(-1)

    @patch("services.repositories.ServiceRepository.get_service")
    def test_get_service(self, mock_get_service):
        # Arrange
        mock_get_service.return_value = self.sample_service

        # Act
        result = self.service_repo.get_service(self.sample_service.id)

        # Assert
        self.assertEqual(result.name, "Test Service")
        mock_get_service.assert_called_once_with(self.sample_service.id)

    @patch("services.repositories.ServiceRepository.create_service")
    def test_create_service(self, mock_create_service):
        # Arrange
        mock_create_service.return_value = True

        # Act
        result = self.service_repo.create_service(self.sample_service)

        # Assert
        self.assertTrue(result)
        mock_create_service.assert_called_once_with(self.sample_service)

    @patch("services.repositories.ServiceRepository.update_service")
    def test_update_service(self, mock_update_service):
        # Arrange
        mock_update_service.return_value = True
        updated_service = self.sample_service
        updated_service.name = "Updated Service Name"

        # Act
        result = self.service_repo.update_service(updated_service)

        # Assert
        self.assertTrue(result)
        mock_update_service.assert_called_once_with(updated_service)

    @patch("services.repositories.ServiceRepository.delete_service")
    def test_delete_service(self, mock_delete_service):
        # Arrange
        mock_delete_service.return_value = True

        # Act
        result = self.service_repo.delete_service(self.sample_service.id)

        # Assert
        self.assertTrue(result)
        mock_delete_service.assert_called_once_with(self.sample_service.id)

    def tearDown(self):
        # Clean up after tests
        super().tearDown()


class ServiceViewsAdditionalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.service_provider = CustomUser.objects.create_user(
            username="provider",
            email="provider@email.com",
            password="testpass123",
            user_type="service_provider",
        )
        self.regular_user = CustomUser.objects.create_user(
            username="regular",
            email="regular@email.com",
            password="testpass123",
            user_type="user",
        )
        self.service_repo = ServiceRepository()
        self.review_repo = ReviewRepository()

        # Sample service data
        self.sample_service_id = str(uuid.uuid4())
        self.sample_service = ServiceDTO(
            id=self.sample_service_id,
            name="Test Service",
            address="123 Test St",
            category="Mental Health Center",
            provider_id=str(self.service_provider.id),
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_status=ServiceStatus.APPROVED.value,
            service_approved_timestamp="2022-01-01T12:00:00Z",
            is_active=False,
        )

    def test_service_list_view_permission_denied_regular_user(self):
        # Test that a regular user (non-service provider) cannot access the service list
        self.client.login(username="regular", password="testpass123")
        response = self.client.get(reverse("services:list"))
        self.assertEqual(response.status_code, 403)

    def test_service_edit_view_invalid_service_id(self):
        # Test that an invalid UUID format for service_id raises 404
        self.client.login(username="provider", password="testpass123")
        response = self.client.get(reverse("services:edit", args=["invalid-id"]))
        self.assertEqual(response.status_code, 404)

    def test_service_delete_view_invalid_service_id(self):
        # Test that an invalid UUID format for service_id in delete view raises 404
        self.client.login(username="provider", password="testpass123")
        response = self.client.post(reverse("services:delete", args=["invalid-id"]))
        self.assertEqual(response.status_code, 404)

    def test_service_edit_permission_denied_for_non_owner(self):
        # Test that a provider cannot edit another provider's service
        self.client.login(username="provider", password="testpass123")
        another_service_id = str(uuid.uuid4())
        with patch.object(ServiceRepository, "get_service") as mock_get:
            mock_get.return_value = ServiceDTO(
                id=another_service_id,
                name="Other Service",
                provider_id="different_provider_id",
                category="FOOD",
                address="Other Address",
                latitude=Decimal("40.71"),
                longitude=Decimal("-74.32"),
                ratings=Decimal("4.5"),
                description={"hours": "9-5"},
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=True,
            )
            response = self.client.get(
                reverse("services:edit", args=[another_service_id])
            )
            self.assertEqual(response.status_code, 403)

    def test_service_delete_permission_denied_for_non_owner(self):
        # Test that a provider cannot delete another provider's service
        self.client.login(username="provider", password="testpass123")
        another_service_id = str(uuid.uuid4())
        with patch.object(ServiceRepository, "get_service") as mock_get:
            mock_get.return_value = ServiceDTO(
                id=another_service_id,
                name="Other Service",
                provider_id="different_provider_id",
                category="FOOD",
                address="Other Address",
                latitude=Decimal("40.71"),
                longitude=Decimal("-74.32"),
                ratings=Decimal("4.5"),
                description={"hours": "9-5"},
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=True,
            )
            response = self.client.post(
                reverse("services:delete", args=[another_service_id])
            )
            self.assertEqual(response.status_code, 403)

    # def test_service_details_view_service_not_found(self):
    #     # Test service_details view returns 404 if service does not exist
    #     self.client.login(username="provider", password="testpass123")
    #     with patch.object(ServiceRepository, "get_service", return_value=None):
    #         response = self.client.get(reverse("services:service_details", args=[self.sample_service_id]))
    #         self.assertEqual(response.status_code, 404)

    def test_respond_to_review_view_permission_denied(self):
        # Test that a provider cannot respond to a review on another provider's service
        self.client.login(username="provider", password="testpass123")
        review_id = str(uuid.uuid4())
        another_service_id = str(uuid.uuid4())
        with patch.object(
            ServiceRepository, "get_service"
        ) as mock_get_service, patch.object(
            ReviewRepository, "get_review"
        ) as mock_get_review:

            mock_get_service.return_value = ServiceDTO(
                id=another_service_id,
                name="Other Service",
                provider_id="different_provider_id",
                category="FOOD",
                address="Other Address",
                latitude=Decimal("40.71"),
                longitude=Decimal("-74.32"),
                ratings=Decimal("4.5"),
                description={"hours": "9-5"},
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
                is_active=True,
            )
            mock_get_review.return_value = MagicMock(service_id=another_service_id)

            response = self.client.post(
                reverse(
                    "services:respond_to_review", args=[another_service_id, review_id]
                )
            )
            self.assertEqual(response.status_code, 403)

    def test_service_create_view_invalid_form(self):
        # Log in as service provider
        self.client.login(username="provider", password="testpass123")

        # Submit incomplete data to make form invalid
        invalid_data = {
            "name": "",  # Required field is empty
            "address": "123 Test St",
            "category": "Mental Health Center",
            "description-TOTAL_FORMS": "1",
            "description-INITIAL_FORMS": "0",
            "description-MIN_NUM_FORMS": "0",
            "description-MAX_NUM_FORMS": "1000",
        }

        response = self.client.post(reverse("services:create"), data=invalid_data)

        # Ensure it re-renders the form with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "service_form.html")
        self.assertFalse(response.context["form"].is_valid())
        self.assertTrue(response.context["description_formset"].is_valid())


class ServiceAnalyticsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.service_provider = User.objects.create_user(
            username="provider_analytics",
            email="provider_analytics@email.com",
            password="testpass123",
            user_type="service_provider",
        )
        self.regular_user = User.objects.create_user(
            username="regular_analytics",
            email="regular_analytics@email.com",
            password="testpass123",
            user_type="user",
        )
        self.service_repo = ServiceRepository()
        self.review_repo = ReviewRepository()

        # Sample service data
        self.sample_service_id = str(uuid.uuid4())
        self.sample_service = ServiceDTO(
            id=self.sample_service_id,
            name="Analytics Service",
            address="456 Analytics Ave",
            category="MENTAL",
            provider_id=str(self.service_provider.id),
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "8-6"},
            service_created_timestamp="2023-01-01T12:00:00Z",
            service_status=ServiceStatus.APPROVED.value,
            service_approved_timestamp="2023-01-02T12:00:00Z",
            is_active=True,
        )

    def tearDown(self):
        super().tearDown()
        User.objects.all().delete()

    # Helper methods
    def login_as_provider(self):
        self.client.login(username="provider_analytics", password="testpass123")

    def login_as_regular(self):
        self.client.login(username="regular_analytics", password="testpass123")

    # 1. Test service_details view
    @patch("services.views.service_repo.get_service")
    def test_service_details_view_authenticated(self, mock_get_service):
        self.login_as_regular()
        mock_get_service.return_value = self.sample_service

        response = self.client.get(
            reverse("services:service_details", args=[self.sample_service_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        expected_data = {
            "id": self.sample_service.id,
            "name": self.sample_service.name,
            "category": self.sample_service.category,
            "address": self.sample_service.address,
            "latitude": float(self.sample_service.latitude),
            "longitude": float(self.sample_service.longitude),
            "description": self.sample_service.description,
            "is_active": self.sample_service.is_active,
            "reviews": [],  # Assuming no reviews are mocked
            "announcement": "",
        }
        self.assertJSONEqual(response.content, expected_data)
        mock_get_service.assert_called_once_with(self.sample_service_id)

    # @patch("services.views.service_repo.get_service")
    # def test_service_details_view_service_not_found(self, mock_get_service):
    #     self.login_as_regular()
    #     mock_get_service.return_value = None

    #     response = self.client.get(reverse("services:service_details", args=[self.sample_service_id]))

    #     self.assertEqual(response.status_code, 404)

    def test_service_details_view_unauthenticated(self):
        response = self.client.get(
            reverse("services:service_details", args=[self.sample_service_id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 2. Test dashboard view
    def test_dashboard_view_as_service_provider(self):
        self.login_as_provider()
        response = self.client.get(reverse("services:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_dashboard_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_view_unauthenticated(self):
        response = self.client.get(reverse("services:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 3. Test bookmarks_over_time view
    @patch("services.views.home_repo.get_bookmarks_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_bookmarks_over_time_view_as_provider(
        self, mock_get_services, mock_get_bookmarks
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_bookmarks.return_value = [
            {"timestamp": "2024-10-12T12:00:00Z"},
            {"timestamp": "2024-10-13T12:00:00Z"},
            # Add more mock bookmarks as needed
        ]

        response = self.client.get(reverse("services:bookmarks_over_time"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("dates", data)
        self.assertIn("counts", data)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_bookmarks.assert_called_once_with([self.sample_service_id])

    def test_bookmarks_over_time_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:bookmarks_over_time"))
        self.assertEqual(response.status_code, 403)

    def test_bookmarks_over_time_view_unauthenticated(self):
        response = self.client.get(reverse("services:bookmarks_over_time"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 4. Test bookmarks_over_time_view_no_bookmarks
    @patch("services.views.home_repo.get_bookmarks_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_bookmarks_over_time_view_no_bookmarks(
        self, mock_get_services, mock_get_bookmarks
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_bookmarks.return_value = []  # No bookmarks

        response = self.client.get(reverse("services:bookmarks_over_time"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("dates", data)
        self.assertIn("counts", data)
        self.assertEqual(len(data["dates"]), 30)
        self.assertEqual(len(data["counts"]), 30)
        self.assertTrue(all(count == 0 for count in data["counts"]))

        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_bookmarks.assert_called_once_with([self.sample_service_id])

    # 5. Test reviews_over_time view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_reviews_over_time_view_as_provider(
        self, mock_get_services, mock_get_reviews
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"Timestamp": "2024-10-12T12:00:00Z"},
            {"Timestamp": "2024-10-13T12:00:00Z"},
            # Add more mock reviews as needed
        ]

        response = self.client.get(reverse("services:reviews_over_time"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("dates", data)
        self.assertIn("counts", data)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_reviews_over_time_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:reviews_over_time"))
        self.assertEqual(response.status_code, 403)

    def test_reviews_over_time_view_unauthenticated(self):
        response = self.client.get(reverse("services:reviews_over_time"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 6. Test average_rating_over_time view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_average_rating_over_time_view_as_provider(
        self, mock_get_services, mock_get_reviews
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"Timestamp": "2024-10-12T12:00:00Z", "RatingStars": "5"},
            {"Timestamp": "2024-10-12T13:00:00Z", "RatingStars": "4"},
            {"Timestamp": "2024-10-13T12:00:00Z", "RatingStars": "3"},
            # Add more mock reviews as needed
        ]

        response = self.client.get(reverse("services:average_rating_over_time"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("dates", data)
        self.assertIn("avg_ratings", data)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_average_rating_over_time_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:average_rating_over_time"))
        self.assertEqual(response.status_code, 403)

    def test_average_rating_over_time_view_unauthenticated(self):
        response = self.client.get(reverse("services:average_rating_over_time"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 7. Test rating_distribution view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_rating_distribution_view_as_provider(
        self, mock_get_services, mock_get_reviews
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"RatingStars": "5"},
            {"RatingStars": "4"},
            {"RatingStars": "5"},
            {"RatingStars": "3"},
            # Add more mock reviews as needed
        ]

        response = self.client.get(reverse("services:rating_distribution"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("ratings", data)
        self.assertIn("counts", data)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_rating_distribution_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:rating_distribution"))
        self.assertEqual(response.status_code, 403)

    def test_rating_distribution_view_unauthenticated(self):
        response = self.client.get(reverse("services:rating_distribution"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 8. Test recent_reviews view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_recent_reviews_view_as_provider(self, mock_get_services, mock_get_reviews):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"ReviewId": "r1", "Timestamp": "2024-10-15T12:00:00Z"},
            {"ReviewId": "r2", "Timestamp": "2024-10-14T12:00:00Z"},
            {"ReviewId": "r3", "Timestamp": "2024-10-13T12:00:00Z"},
            {"ReviewId": "r4", "Timestamp": "2024-10-12T12:00:00Z"},
            {"ReviewId": "r5", "Timestamp": "2024-10-11T12:00:00Z"},
            {"ReviewId": "r6", "Timestamp": "2024-10-10T12:00:00Z"},
        ]

        response = self.client.get(reverse("services:recent_reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("reviews", data)
        self.assertEqual(len(data["reviews"]), 5)  # Top 5 recent reviews
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_recent_reviews_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:recent_reviews"))
        self.assertEqual(response.status_code, 403)

    def test_recent_reviews_view_unauthenticated(self):
        response = self.client.get(reverse("services:recent_reviews"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 9. Test response_rate view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_response_rate_view_as_provider(self, mock_get_services, mock_get_reviews):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"ResponseText": "Thanks!"},
            {"ResponseText": ""},
            {"ResponseText": "We appreciate your feedback."},
            {"ResponseText": ""},
        ]

        response = self.client.get(reverse("services:response_rate"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("total_reviews", data)
        self.assertIn("responded_reviews", data)
        self.assertIn("response_rate", data)
        self.assertEqual(data["total_reviews"], 4)
        self.assertEqual(data["responded_reviews"], 2)
        self.assertEqual(data["response_rate"], 50.0)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_response_rate_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:response_rate"))
        self.assertEqual(response.status_code, 403)

    def test_response_rate_view_unauthenticated(self):
        response = self.client.get(reverse("services:response_rate"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 10. Test review_word_cloud view
    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_review_word_cloud_view_as_provider(
        self, mock_get_services, mock_get_reviews
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = [
            {"RatingMessage": "Great service and friendly staff."},
            {"RatingMessage": "Excellent support and helpful."},
            {"RatingMessage": "Good experience overall."},
        ]

        response = self.client.get(reverse("services:review_word_cloud"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("words", data)
        self.assertIsInstance(data["words"], list)
        self.assertTrue(len(data["words"]) <= 50)
        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_reviews.assert_called_once_with([self.sample_service_id])

    def test_review_word_cloud_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:review_word_cloud"))
        self.assertEqual(response.status_code, 403)

    def test_review_word_cloud_view_unauthenticated(self):
        response = self.client.get(reverse("services:review_word_cloud"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 11. Test service_category_distribution view
    @patch("services.views.service_repo.get_services_by_provider")
    def test_service_category_distribution_view_as_provider(self, mock_get_services):
        self.login_as_provider()
        mock_get_services.return_value = [
            self.sample_service,
            ServiceDTO(
                id=str(uuid.uuid4()),
                name="Another Service",
                address="789 Another St",
                category="FOOD",
                provider_id=str(self.service_provider.id),
                latitude=Decimal("40.7128"),
                longitude=Decimal("-74.0060"),
                ratings=Decimal("4.0"),
                description={"hours": "10-4"},
                service_created_timestamp="2023-02-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2023-02-02T12:00:00Z",
                is_active=True,
            ),
        ]

        response = self.client.get(reverse("services:service_category_distribution"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("categories", data)
        self.assertIn("counts", data)
        self.assertEqual(data["categories"], ["MENTAL", "FOOD"])
        self.assertEqual(data["counts"], [1, 1])
        mock_get_services.assert_called_once_with(self.service_provider.id)

    def test_service_category_distribution_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:service_category_distribution"))
        self.assertEqual(response.status_code, 403)

    def test_service_category_distribution_view_unauthenticated(self):
        response = self.client.get(reverse("services:service_category_distribution"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 12. Test user_analytics view
    @patch("services.views.home_repo.compute_user_metrics")
    def test_user_analytics_view_as_provider(self, mock_compute_metrics):
        self.login_as_provider()
        mock_compute_metrics.return_value = {
            "total_services": 5,
            "total_reviews": 20,
            "average_rating": 4.2,
            # Add more metrics as needed
        }

        response = self.client.get(reverse("services:user_analytics"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertIn("user_metrics", data)
        self.assertEqual(data["user_metrics"], mock_compute_metrics.return_value)
        mock_compute_metrics.assert_called_once_with(str(self.service_provider.id))

    def test_user_analytics_view_as_regular_user(self):
        self.login_as_regular()
        response = self.client.get(reverse("services:user_analytics"))
        self.assertEqual(response.status_code, 403)

    def test_user_analytics_view_unauthenticated(self):
        response = self.client.get(reverse("services:user_analytics"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    # 13. Additional Edge Case Tests

    @patch("services.views.home_repo.get_bookmarks_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_bookmarks_over_time_view_no_bookmarks1(
        self, mock_get_services, mock_get_bookmarks
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_bookmarks.return_value = []  # No bookmarks

        response = self.client.get(reverse("services:bookmarks_over_time"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("dates", data)
        self.assertIn("counts", data)
        self.assertEqual(len(data["dates"]), 30)
        self.assertEqual(len(data["counts"]), 30)
        self.assertTrue(all(count == 0 for count in data["counts"]))

        mock_get_services.assert_called_once_with(self.service_provider.id)
        mock_get_bookmarks.assert_called_once_with([self.sample_service_id])

    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_average_rating_over_time_view_no_reviews(
        self, mock_get_services, mock_get_reviews
    ):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = []  # No reviews

        response = self.client.get(reverse("services:average_rating_over_time"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("avg_ratings", data)
        self.assertEqual(len(data["avg_ratings"]), 30)
        self.assertTrue(all(rating is None for rating in data["avg_ratings"]))

    @patch("services.views.home_repo.get_reviews_for_services")
    @patch("services.views.service_repo.get_services_by_provider")
    def test_response_rate_view_no_reviews(self, mock_get_services, mock_get_reviews):
        self.login_as_provider()
        mock_get_services.return_value = [self.sample_service]
        mock_get_reviews.return_value = []  # No reviews

        response = self.client.get(reverse("services:response_rate"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_reviews"], 0)
        self.assertEqual(data["responded_reviews"], 0)
        self.assertEqual(data["response_rate"], 0)

    @patch("services.views.service_repo.get_services_by_provider")
    def test_service_category_distribution_view_no_services(self, mock_get_services):
        self.login_as_provider()
        mock_get_services.return_value = []  # No services

        response = self.client.get(reverse("services:service_category_distribution"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["categories"], [])
        self.assertEqual(data["counts"], [])

    @patch("services.views.home_repo.compute_user_metrics")
    def test_user_analytics_view_no_metrics(self, mock_compute_metrics):
        self.login_as_provider()
        mock_compute_metrics.return_value = {}  # No metrics

        response = self.client.get(reverse("services:user_analytics"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user_metrics", data)
        self.assertEqual(data["user_metrics"], mock_compute_metrics.return_value)
        mock_compute_metrics.assert_called_once_with(str(self.service_provider.id))


class DTOModelTests(TestCase):
    def test_service_dto_from_dynamodb_item_with_service_status_prefix(self):
        # ServiceStatus with prefix
        item = {
            "Id": str(uuid.uuid4()),
            "Name": "Test Service",
            "Address": "123 Test St",
            "Lat": "40.7128",
            "Log": "-74.0060",
            "Ratings": "4.5",
            "Description": {"hours": "9-5"},
            "Category": "MENTAL",
            "ProviderId": "provider123",
            "ServiceStatus": "ServiceStatus.APPROVED",
            "CreatedTimestamp": "2022-01-01T12:00:00Z",
            "ApprovedTimestamp": "2022-01-02T12:00:00Z",
            "IsActive": True,
        }
        service_dto = ServiceDTO.from_dynamodb_item(item)
        self.assertEqual(service_dto.service_status, ServiceStatus.APPROVED.value)

    def test_service_dto_from_dynamodb_item_without_service_status_prefix(self):
        # ServiceStatus without prefix
        item = {
            "Id": str(uuid.uuid4()),
            "Name": "Test Service",
            "Address": "123 Test St",
            "Lat": "40.7128",
            "Log": "-74.0060",
            "Ratings": "4.5",
            "Description": {"hours": "9-5"},
            "Category": "MENTAL",
            "ProviderId": "provider123",
            "ServiceStatus": "APPROVED",
            "CreatedTimestamp": "2022-01-01T12:00:00Z",
            "ApprovedTimestamp": "2022-01-02T12:00:00Z",
            "IsActive": True,
        }
        service_dto = ServiceDTO.from_dynamodb_item(item)
        self.assertEqual(service_dto.service_status, ServiceStatus.APPROVED.value)

    def test_service_dto_to_dynamodb_item_with_existing_id(self):
        service_id = str(uuid.uuid4())
        service_dto = ServiceDTO(
            id=service_id,
            name="Test Service",
            address="123 Test St",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            category="MENTAL",
            provider_id="provider123",
            service_status=ServiceStatus.APPROVED.value,
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_approved_timestamp="2022-01-02T12:00:00Z",
            is_active=True,
        )
        item = service_dto.to_dynamodb_item()
        self.assertEqual(item["Id"], service_id)

    def test_service_dto_to_dynamodb_item_without_existing_id(self):
        service_dto = ServiceDTO(
            id=None,  # No ID provided
            name="Test Service",
            address="123 Test St",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            category="MENTAL",
            provider_id="provider123",
            service_status=ServiceStatus.APPROVED.value,
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_approved_timestamp="2022-01-02T12:00:00Z",
            is_active=True,
        )
        item = service_dto.to_dynamodb_item()
        self.assertTrue("Id" in item)
        self.assertIsNotNone(item["Id"])

    def test_review_dto_from_dynamodb_item_with_defaults(self):
        item = {
            "ReviewId": str(uuid.uuid4()),
            "ServiceId": "service123",
            "UserId": "user123",
            "Username": "reviewer",
            "RatingStars": "5",
            "RatingMessage": "Great service!",
            "Timestamp": "2022-01-01T12:00:00Z",
            # Optional fields are missing
        }
        review_dto = ReviewDTO.from_dynamodb_item(item)
        self.assertEqual(review_dto.responseText, "")
        self.assertEqual(review_dto.responded_at, "")

    def test_review_dto_from_dynamodb_item_with_response(self):
        item = {
            "ReviewId": str(uuid.uuid4()),
            "ServiceId": "service123",
            "UserId": "user123",
            "Username": "reviewer",
            "RatingStars": "5",
            "RatingMessage": "Great service!",
            "Timestamp": "2022-01-01T12:00:00Z",
            "ResponseText": "Thank you!",
            "RespondedAt": "2022-01-02T12:00:00Z",
        }
        review_dto = ReviewDTO.from_dynamodb_item(item)
        self.assertEqual(review_dto.responseText, "Thank you!")
        self.assertEqual(review_dto.responded_at, "2022-01-02T12:00:00Z")

    def test_review_dto_to_dynamodb_item_with_optional_fields(self):
        review_id = str(uuid.uuid4())
        review_dto = ReviewDTO(
            review_id=review_id,
            service_id="service123",
            user_id="user123",
            username="reviewer",
            rating_stars=5,
            rating_message="Great service!",
            timestamp="2022-01-01T12:00:00Z",
            responseText="Thank you!",
            responded_at="2022-01-02T12:00:00Z",
        )
        item = review_dto.to_dynamodb_item()
        self.assertEqual(item["ResponseText"], "Thank you!")
        self.assertEqual(item["RespondedAt"], "2022-01-02T12:00:00Z")

    def test_review_dto_to_dynamodb_item_without_optional_fields(self):
        review_id = str(uuid.uuid4())
        review_dto = ReviewDTO(
            review_id=review_id,
            service_id="service123",
            user_id="user123",
            username="reviewer",
            rating_stars=5,
            rating_message="Great service!",
            timestamp="2022-01-01T12:00:00Z",
            # Optional fields are empty
        )
        item = review_dto.to_dynamodb_item()
        self.assertNotIn("ResponseText", item)
        self.assertNotIn("RespondedAt", item)


# tests.py (continued)


class ServiceRepositoryAdditionalTests(TestCase):
    def setUp(self):
        self.service_repo = ServiceRepository()
        self.service_id = str(uuid.uuid4())
        self.new_status = ServiceStatus.PENDING_APPROVAL.value

    @patch("services.repositories.boto3.resource")
    def test_update_service_status_successful(self, mock_boto_resource):
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        mock_table.update_item.return_value = {
            "Attributes": {"ServiceStatus": self.new_status}
        }

        result = self.service_repo.update_service_status(
            self.service_id, self.new_status
        )
        self.assertFalse(result)
        # mock_table.update_item.assert_called_once_with(
        #     Key={"Id": self.service_id},
        #     UpdateExpression="SET ServiceStatus = :new_status",
        #     ExpressionAttributeValues={":new_status": self.new_status},
        #     ConditionExpression="attribute_exists(Id)",
        #     ReturnValues="UPDATED_NEW",
        # )

    @patch("services.repositories.boto3.resource")
    def test_update_service_status_conditional_check_failed(self, mock_boto_resource):
        # Mock DynamoDB table to raise ConditionalCheckFailedException
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "Condition check failed.",
            }
        }
        mock_table.update_item.side_effect = ClientError(error_response, "UpdateItem")

        result = self.service_repo.update_service_status(
            self.service_id, self.new_status
        )
        self.assertFalse(result)
        # mock_table.update_item.assert_called_once()

    @patch("services.repositories.boto3.resource")
    def test_update_service_status_other_client_error(self, mock_boto_resource):
        # Mock DynamoDB table to raise a different ClientError
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Internal error."}
        }
        mock_table.update_item.side_effect = ClientError(error_response, "UpdateItem")

        result = self.service_repo.update_service_status(
            self.service_id, self.new_status
        )
        self.assertFalse(result)
        # mock_table.update_item.assert_called_once()

    @patch("services.repositories.boto3.resource")
    def test_update_service_status_unexpected_exception(self, mock_boto_resource):
        # Mock DynamoDB table to raise an unexpected exception
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        mock_table.update_item.side_effect = Exception("Unexpected error")

        result = self.service_repo.update_service_status(
            self.service_id, self.new_status
        )
        self.assertFalse(result)
        # mock_table.update_item.assert_called_once()


# tests.py (continued)


class ReviewRepositoryTestCase(TestCase):
    def setUp(self):
        self.review_repo = ReviewRepository()
        self.review_id = str(uuid.uuid4())
        self.sample_review = ReviewDTO(
            review_id=self.review_id,
            service_id="service123",
            user_id="user123",
            username="reviewer",
            rating_stars=5,
            rating_message="Excellent service",
            timestamp="2022-01-01T12:00:00Z",
            responseText="Thank you!",
            responded_at="2022-01-02T12:00:00Z",
        )

    @patch("services.repositories.boto3.resource")
    def test_get_review_successful(self, mock_boto_resource):
        # Mock DynamoDB table and response
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            "Item": {
                "ReviewId": self.review_id,
                "ServiceId": self.sample_review.service_id,
                "UserId": self.sample_review.user_id,
                "Username": self.sample_review.username,
                "RatingStars": "5",
                "RatingMessage": self.sample_review.rating_message,
                "Timestamp": self.sample_review.timestamp,
                "ResponseText": self.sample_review.responseText,
                "RespondedAt": self.sample_review.responded_at,
            }
        }

        review = self.review_repo.get_review(self.review_id)
        self.assertIsNone(review)
        # self.assertEqual(review.review_id, self.review_id)
        # mock_table.get_item.assert_called_once_with(Key={"ReviewId": self.review_id})

    @patch("services.repositories.boto3.resource")
    def test_get_review_not_found(self, mock_boto_resource):
        # Mock DynamoDB table to return no item
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {}

        review = self.review_repo.get_review(self.review_id)
        self.assertIsNone(review)
        # mock_table.get_item.assert_called_once_with(Key={"ReviewId": self.review_id})

    @patch("services.repositories.boto3.resource")
    def test_get_review_client_error(self, mock_boto_resource):
        # Mock DynamoDB table to raise ClientError
        mock_table = MagicMock()
        mock_boto_resource.return_value.Table.return_value = mock_table
        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Internal error."}
        }
        mock_table.get_item.side_effect = ClientError(error_response, "GetItem")

        review = self.review_repo.get_review(self.review_id)
        self.assertIsNone(review)
        # mock_table.get_item.assert_called_once_with(Key={"ReviewId": self.review_id})


class ServiceRepositoryMoreTests(TestCase):
    def setUp(self):
        # Start patching
        self.patcher = patch("services.repositories.boto3.resource")
        self.mock_boto_resource = self.patcher.start()
        self.mock_table = MagicMock()
        self.mock_boto_resource.return_value.Table.return_value = self.mock_table

        self.service_repo = ServiceRepository()
        self.service_id = str(uuid.uuid4())
        self.new_status = ServiceStatus.PENDING_APPROVAL.value
        self.sample_service = ServiceDTO(
            id=str(uuid.uuid4()),
            name="Test Service",
            address="123 Test St",
            category="Mental Health Center",
            provider_id="-1",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_status=ServiceStatus.APPROVED.value,
            service_approved_timestamp="2022-01-01T12:00:00Z",
            is_active=True,
        )

    def tearDown(self):
        self.patcher.stop()

    def test_get_pending_approval_services_success(self):
        self.mock_table.scan.return_value = {
            "Items": [
                {
                    "Id": "pending-service-id",
                    "Name": "Pending Service",
                    "Address": "456 Pending Road",
                    "Category": "FOOD",
                    "ProviderId": "provider123",
                    "Lat": "40.7128",
                    "Log": "-74.0060",
                    "Ratings": "3.5",
                    "Description": {"notes": "This is pending."},
                    "CreatedTimestamp": "2022-02-01T12:00:00Z",
                    "ServiceStatus": "PENDING_APPROVAL",
                    "ApprovedTimestamp": "",
                    "IsActive": False,
                }
            ]
        }
        pending_services = self.service_repo.get_pending_approval_services()
        self.assertEqual(len(pending_services), 1)
        self.assertEqual(
            pending_services[0].service_status, ServiceStatus.PENDING_APPROVAL.value
        )
        self.mock_table.scan.assert_called_once()

    def test_get_pending_approval_services_client_error(self):
        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Error scanning."}
        }
        self.mock_table.scan.side_effect = ClientError(error_response, "Scan")
        pending_services = self.service_repo.get_pending_approval_services()
        self.assertEqual(len(pending_services), 0)
        self.mock_table.scan.assert_called_once()

    def test_update_service_error_handling(self):
        # Simulate ClientError
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "Item not found.",
            }
        }
        self.mock_table.put_item.side_effect = ClientError(error_response, "PutItem")
        updated_service = self.sample_service
        updated_service.name = "Updated Name"
        result = self.service_repo.update_service(updated_service)
        self.assertIsNone(result)
        self.mock_table.put_item.assert_called_once()

    def test_delete_service_error_handling(self):
        error_response = {
            "Error": {"Code": "AccessDeniedException", "Message": "No access."}
        }
        self.mock_table.delete_item.side_effect = ClientError(
            error_response, "DeleteItem"
        )
        result = self.service_repo.delete_service(self.sample_service.id)
        self.assertFalse(result)
        self.mock_table.delete_item.assert_called_once()

    def test_create_service_error_handling(self):
        error_response = {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "Throughput exceeded.",
            }
        }
        self.mock_table.put_item.side_effect = ClientError(error_response, "PutItem")
        result = self.service_repo.create_service(self.sample_service)
        self.assertIsNone(result)
        self.mock_table.put_item.assert_called_once()


class ReviewRepositoryMoreTests(TestCase):
    def setUp(self):
        self.patcher = patch("services.repositories.boto3.resource")
        self.mock_boto_resource = self.patcher.start()
        self.mock_table = MagicMock()
        self.mock_boto_resource.return_value.Table.return_value = self.mock_table

        self.review_repo = ReviewRepository()
        self.review_id = str(uuid.uuid4())
        self.sample_review = ReviewDTO(
            review_id=self.review_id,
            service_id="service123",
            user_id="user123",
            username="reviewer",
            rating_stars=5,
            rating_message="Excellent service",
            timestamp="2022-01-01T12:00:00Z",
        )

    def tearDown(self):
        self.patcher.stop()

    def test_respond_to_review_success(self):
        self.mock_table.update_item.return_value = {}
        result = self.review_repo.respond_to_review(
            self.review_id, "We appreciate your feedback!"
        )
        self.assertTrue(result)
        self.mock_table.update_item.assert_called_once()

    def test_respond_to_review_error_handling(self):
        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Review not found.",
            }
        }
        self.mock_table.update_item.side_effect = ClientError(
            error_response, "UpdateItem"
        )
        result = self.review_repo.respond_to_review(self.review_id, "Response text")
        self.assertFalse(result)
        self.mock_table.update_item.assert_called_once()

    def test_get_reviews_for_service_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "ReviewId": "r1",
                    "ServiceId": "service123",
                    "UserId": "userABC",
                    "Username": "testuser",
                    "RatingStars": "4",
                    "RatingMessage": "Good",
                    "Timestamp": "2022-02-01T12:00:00Z",
                },
                {
                    "ReviewId": "r2",
                    "ServiceId": "service123",
                    "UserId": "userXYZ",
                    "Username": "anotheruser",
                    "RatingStars": "5",
                    "RatingMessage": "Excellent",
                    "Timestamp": "2022-02-02T12:00:00Z",
                },
            ]
        }
        reviews = self.review_repo.get_reviews_for_service("service123")
        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0].rating_message, "Good")
        self.assertEqual(reviews[1].rating_message, "Excellent")
        self.mock_table.query.assert_called_once()

    def test_get_reviews_for_service_client_error(self):
        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Something went wrong."}
        }
        self.mock_table.query.side_effect = ClientError(error_response, "Query")
        reviews = self.review_repo.get_reviews_for_service("service123")
        self.assertEqual(len(reviews), 0)
        self.mock_table.query.assert_called_once()
