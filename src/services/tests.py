# from django.test import TestCase
import uuid
from decimal import Decimal
from unittest.mock import patch

from accounts.models import CustomUser
from django.test import TestCase, Client
from django.urls import reverse

from public_service_finder.utils.enums.service_status import ServiceStatus

from .forms import ServiceForm, DescriptionFormSet
from .models import ServiceDTO
from .repositories import ServiceRepository


# Create your tests here.


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
            )
            response = self.client.get(reverse("services:edit", args=[service_id]))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "service_form.html")

    def test_service_edit_view_post_success(self):
        self.client.login(username="provider", password="testpass123")
        service_id = str(uuid.uuid4())
        data = {
            "name": "Updated Service",
            "address": "456 New St",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "category": "Mental Health Center",
            "description-0-key": "hours",
            "description-0-value": "24/7",
            "description-TOTAL_FORMS": "1",
            "description-INITIAL_FORMS": "1",
            "description-MIN_NUM_FORMS": "0",
            "description-MAX_NUM_FORMS": "1000",
        }
        with patch.object(ServiceRepository, "get_service") as mock_get, patch.object(
            ServiceRepository, "update_service"
        ) as mock_update:
            mock_get.return_value = ServiceDTO(
                id=service_id,
                name="Test Service",
                provider_id=str(self.service_provider.id),
                category="FOOD",
                ratings=Decimal("4.5"),
                description={"hours": "9-5"},
                address="5 Metrotech Center, Brooklyn, NY",
                latitude=Decimal(40.32),
                longitude=Decimal(-74.001),
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status=ServiceStatus.APPROVED.value,
                service_approved_timestamp="2022-01-01T12:00:00Z",
            )
            mock_update.return_value = True
            response = self.client.post(
                reverse("services:edit", args=[service_id]), data
            )
            self.assertRedirects(response, reverse("services:list"))

    # def test_service_details_view(self):
    #     self.client.login(username='provider', password='testpass123')
    #     service_id = str(uuid.uuid4())
    #     with patch.object(ServiceRepository, 'get_service') as mock_get, \
    #             patch('src.home.repositories.HomeRepository.fetch_reviews_for_service') as mock_reviews:
    #         mock_get.return_value = ServiceDTO(
    #             id=service_id,
    #             name='Test Service',
    #             category='MENTAL',
    #             address='123 Test St',
    #             latitude=Decimal('40.7128'),
    #             longitude=Decimal('-74.0060'),
    #             ratings=None,
    #             description={'hours': '9-5'},
    #             provider_id=self.service_provider.id
    #         )
    #         mock_reviews.return_value = [{'id': 1, 'content': 'Great service'}]
    #         response = self.client.get(reverse('services:details', args=[service_id]))
    #         self.assertEqual(response.status_code, 200)
    #         self.assertJSONEqual(response.content, {
    #             'id': service_id,
    #             'name': 'Test Service',
    #             'category': 'MENTAL',
    #             'address': '123 Test St',
    #             'latitude': 40.7128,
    #             'longitude': -74.0060,
    #             'description': {'hours': '9-5'},
    #             'reviews': [{'id': 1, 'content': 'Great service'}]
    #         })

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

    @patch.object(ServiceRepository, 'get_pending_approval_services')
    def test_get_pending_approval_services(self, mock_get_pending_approval_services):
        # Mock the response to simulate services in "PENDING_APPROVAL" status
        mock_get_pending_approval_services.return_value = [
            ServiceDTO(
                id=str(uuid.uuid4()),
                name="Pending Service 1",
                address="Address 1",
                category="Category 1",
                provider_id=str(uuid.uuid4()),
                latitude=None,
                longitude=None,
                ratings=None,
                description=None,
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status="PENDING_APPROVAL",
                service_approved_timestamp=None,
            ),
            ServiceDTO(
                id=str(uuid.uuid4()),
                name="Pending Service 2",
                address="Address 2",
                category="Category 2",
                provider_id=str(uuid.uuid4()),
                latitude=None,
                longitude=None,
                ratings=None,
                description=None,
                service_created_timestamp="2022-01-01T12:00:00Z",
                service_status="PENDING_APPROVAL",
                service_approved_timestamp=None,
            ),
        ]

        result = self.service_repo.get_pending_approval_services()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].service_status, "PENDING_APPROVAL")
        self.assertEqual(result[1].service_status, "PENDING_APPROVAL")

    @patch.object(ServiceRepository, 'update_service_status')
    def test_update_service_status(self, mock_update_service_status):
        # Mock the response to simulate successful status update
        mock_update_service_status.return_value = True

        service_id = str(uuid.uuid4())
        new_status = "APPROVED"

        # Call the method
        result = self.service_repo.update_service_status(service_id, new_status)

        # Assertions
        self.assertTrue(result)
        mock_update_service_status.assert_called_once_with(service_id, new_status)