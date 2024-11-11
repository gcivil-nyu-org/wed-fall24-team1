# from django.test import TestCase
import uuid
from decimal import Decimal
from accounts.models import CustomUser
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from public_service_finder.utils.enums.service_status import ServiceStatus

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

    # def test_service_create_view_post_success(self):
    #     self.client.login(username="provider", password="testpass123")
    #     data = {
    #         "name": "New Service",
    #         "address": "123 Test St",
    #         "latitude": "40.7128",
    #         "longitude": "-74.0060",
    #         "category": "Mental Health Center",
    #         "description-0-key": "hours",
    #         "description-0-value": "9-5",
    #         "description-TOTAL_FORMS": "1",
    #         "description-INITIAL_FORMS": "0",
    #         "description-MIN_NUM_FORMS": "0",
    #         "description-MAX_NUM_FORMS": "1000",
    #     }
    #     with patch.object(ServiceRepository, "create_service") as mock_create:
    #         mock_create.return_value = True
    #         response = self.client.post(reverse("services:create"), data)
    #         self.assertRedirects(response, reverse("services:list"))

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
            provider_id="test_provider_id",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            ratings=Decimal("4.5"),
            description={"hours": "9-5"},
            service_created_timestamp="2022-01-01T12:00:00Z",
            service_status=ServiceStatus.APPROVED.value,
            service_approved_timestamp="2022-01-01T12:00:00Z",
        )

    @patch("services.repositories.ServiceRepository.get_services_by_provider")
    def test_get_services_by_provider(self, mock_get_services_by_provider):
        # Arrange
        mock_get_services_by_provider.return_value = [self.sample_service]

        # Act
        result = self.service_repo.get_services_by_provider("test_provider_id")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Test Service")
        mock_get_services_by_provider.assert_called_once_with("test_provider_id")

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

    # def test_review_list_view(self):
    #     # Log in as service provider
    #     self.client.login(username="provider", password="testpass123")

    #     with patch.object(ServiceRepository, "get_service") as mock_get_service, \
    #         patch.object(ReviewRepository, "get_reviews_for_service") as mock_get_reviews:
    #         # Mock the service and reviews to simulate database response
    #             mock_get_service.return_value = self.sample_service
    #             mock_get_reviews.return_value = [
    #                 MagicMock(review_id="1", responseText="Great service!"),
    #                 MagicMock(review_id="2", responseText="Would recommend!")
    #             ]

    #             # Call the view
    #             response = self.client.get(reverse("services:review_list", args=[self.sample_service_id]))

    #             # Assert correct response and context data
    #             self.assertEqual(response.status_code, 200)
    #             self.assertTemplateUsed(response, "review_html.html")
    #             self.assertIn("reviews", response.context)
    #             self.assertEqual(len(response.context["reviews"]), 2)
