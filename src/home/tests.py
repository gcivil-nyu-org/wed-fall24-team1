from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
import json

from accounts.models import CustomUser


class ViewsTest(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        # Sample service data
        self.sample_service = {
            "Id": "123",
            "Name": "Test Service",
            "Address": "123 Test St",
            "Lat": "40.7128",
            "Log": "-74.0060",
            "Ratings": "4.5",
            "rating_count": 10,
            "Category": "Test Category",
            "MapLink": "http://test.map",
            "Description": {"text": "Test description"},
        }
        # Sample review data
        self.sample_review = {
            "service_id": "123",
            "rating": 5,
            "message": "Great service!",
        }
        self.patcher = patch("home.views.HomeRepository")
        self.MockHomeRepository = self.patcher.start()
        self.mock_repo = self.MockHomeRepository.return_value

    def tearDown(self):
        self.patcher.stop()

    def test_home_view_basic(self):
        self.client.login(username="testuser", password="testpass123")

        self.mock_repo.fetch_items_with_filter.return_value = [self.sample_service]
        self.MockHomeRepository.process_items.return_value = [self.sample_service]

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertIn("serialized_items", response.context)
        items = json.loads(response.context["serialized_items"])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["Id"], "123")

        self.mock_repo.fetch_items_with_filter.assert_called_once()
        self.MockHomeRepository.process_items.assert_called_once()

    def test_home_view_with_search(self):
        self.client.login(username="testuser", password="testpass123")

        self.mock_repo.fetch_items_with_filter.return_value = [self.sample_service]
        self.MockHomeRepository.process_items.return_value = [self.sample_service]

        response = self.client.get(
            reverse("home"),
            {
                "search": "test",
                "type": "category",
                "radius": "10",
                "user_lat": "40.7128",
                "user_lon": "-74.0060",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "test")
        self.assertEqual(response.context["service_type_dropdown"], "category")
        self.assertEqual(response.context["radius"], "10")

        self.mock_repo.fetch_items_with_filter.assert_called_once_with(
            "test", "category", "10", "40.7128", "-74.0060"
        )
        self.MockHomeRepository.process_items.assert_called_once()

    def test_submit_review_success(self):
        self.client.login(username="testuser", password="testpass123")

        self.mock_repo.add_review.return_value = None
        self.mock_repo.update_service_rating.return_value = None

        response = self.client.post(
            reverse("submit_review"),
            data=json.dumps(self.sample_review),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["service_id"], "123")
        self.assertEqual(response_data["rating"], 5)
        self.assertEqual(response_data["message"], "Great service!")

        self.mock_repo.add_review.assert_called_once()
        self.mock_repo.update_service_rating.assert_called_once()

    def test_submit_review_missing_data(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("submit_review"),
            data=json.dumps({"service_id": "123"}),  # Missing rating and message
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn("error", response_data)

    def test_get_reviews_success(self):
        mock_reviews = [
            {"id": "1", "rating": 5, "message": "Great!"},
            {"id": "2", "rating": 4, "message": "Good!"},
        ]
        self.mock_repo.fetch_reviews_for_service.return_value = mock_reviews

        response = self.client.get(
            reverse("get_reviews", kwargs={"service_id": "123"}), {"page": "1"}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn("reviews", response_data)
        self.assertIn("has_next", response_data)
        self.assertIn("has_previous", response_data)
        self.assertEqual(response_data["current_page"], 1)

        self.mock_repo.fetch_reviews_for_service.assert_called_once_with("123")

    def test_submit_review_unauthenticated(self):
        response = self.client.post(
            reverse("submit_review"),
            data=json.dumps(self.sample_review),
            content_type="application/json",
        )

        self.assertIn(response.status_code, [302, 403])
