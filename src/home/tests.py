from django.test import TestCase, Client
from django.urls import reverse
import json

from accounts.models import CustomUser
from unittest.mock import patch, MagicMock
from decimal import Decimal
from botocore.exceptions import ClientError
import uuid

from home.repositories import HomeRepository


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
            "test", "category", "10", 40.7128, -74.0060
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

    def test_home_view_invalid_page(self):
        self.client.login(username="testuser", password="testpass123")

        self.mock_repo.fetch_items_with_filter.return_value = [self.sample_service]
        self.MockHomeRepository.process_items.return_value = [self.sample_service]

        response = self.client.get(reverse("home"), {"page": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_get_reviews_no_reviews(self):
        self.mock_repo.fetch_reviews_for_service.return_value = []

        response = self.client.get(
            reverse("get_reviews", kwargs={"service_id": "123"}), {"page": "1"}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data["reviews"]), 0)
        self.assertFalse(response_data["has_next"])
        self.assertFalse(response_data["has_previous"])

    def test_submit_review_invalid_json(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("submit_review"),
            data="invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertIn("error", response_data)

    def test_home_view_no_location(self):
        self.client.login(username="testuser", password="testpass123")

        service_no_distance = self.sample_service.copy()
        self.mock_repo.fetch_items_with_filter.return_value = [service_no_distance]
        self.MockHomeRepository.process_items.return_value = [service_no_distance]

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        items = json.loads(response.context["serialized_items"])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["Distance"], "N/A")


class HomeRepositoryTests(TestCase):
    @patch("home.repositories.boto3.resource")
    def setUp(self, mock_boto_resource):
        # Mock DynamoDB and tables
        self.repo = HomeRepository()
        self.mock_dynamodb = mock_boto_resource.return_value
        self.mock_services_table = MagicMock()
        self.mock_reviews_table = MagicMock()
        self.mock_bookmarks_table = MagicMock()

        # Assign mocks to the repository's table attributes
        self.repo.services_table = self.mock_services_table
        self.repo.reviews_table = self.mock_reviews_table
        self.repo.bookmarks_table = self.mock_bookmarks_table

        # Sample data
        self.sample_service_id = str(uuid.uuid4())
        self.sample_user_id = str(uuid.uuid4())

    def test_fetch_items_with_filter_name_only(self):
        self.mock_services_table.scan.return_value = {
            "Items": [{"Name": "Test Service"}]
        }

        result = self.repo.fetch_items_with_filter("Test", None, None, None, None)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Name"], "Test Service")
        self.mock_services_table.scan.assert_called_once()

    def test_add_review_success(self):
        self.mock_reviews_table.put_item.return_value = {}

        self.repo.add_review(
            review_id=str(uuid.uuid4()),
            service_id=self.sample_service_id,
            user_id=self.sample_user_id,
            rating_stars=5,
            rating_message="Great service!",
            username="testuser",
        )

        self.mock_reviews_table.put_item.assert_called_once()

    def test_add_review_client_error(self):
        self.mock_reviews_table.put_item.side_effect = ClientError(
            error_response={"Error": {"Message": "DynamoDB Error"}},
            operation_name="PutItem",
        )

        with self.assertRaises(ClientError):
            self.repo.add_review(
                review_id=str(uuid.uuid4()),
                service_id=self.sample_service_id,
                user_id=self.sample_user_id,
                rating_stars=5,
                rating_message="Great service!",
                username="testuser",
            )

    def test_update_service_rating_success(self):
        self.mock_services_table.get_item.return_value = {
            "Item": {"Ratings": Decimal("4.5"), "rating_count": 10}
        }

        self.repo.update_service_rating(service_id=self.sample_service_id, new_rating=5)

        self.mock_services_table.get_item.assert_called_once()
        self.mock_services_table.update_item.assert_called_once()

    def test_update_service_rating_client_error(self):
        self.mock_services_table.get_item.side_effect = ClientError(
            error_response={"Error": {"Message": "DynamoDB Error"}},
            operation_name="GetItem",
        )

        with self.assertRaises(ClientError):
            self.repo.update_service_rating(
                service_id=self.sample_service_id, new_rating=5
            )

    def test_process_items_with_decimal(self):
        # Test the process_items with decimal conversion
        items = [{"Ratings": Decimal("4.5"), "Address": "123 Test St"}]
        result = self.repo.process_items(items)

        # Assert the Decimal is converted to string in result
        self.assertEqual(str(result[0]["Ratings"]), "4.5")
        self.assertEqual(result[0]["Address"], "123 Test St")

    def test_fetch_reviews_for_service_success(self):
        # Mock the reviews table scan response
        self.mock_reviews_table.scan.return_value = {
            "Items": [
                {
                    "ReviewId": "1",
                    "ServiceId": self.sample_service_id,
                    "RatingStars": 5,
                    "Timestamp": "2022-01-01T12:00:00Z",
                }
            ]
        }

        result = self.repo.fetch_reviews_for_service(self.sample_service_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ReviewId"], "1")
        self.mock_reviews_table.scan.assert_called_once()

    def test_fetch_reviews_for_service_client_error(self):
        self.mock_reviews_table.scan.side_effect = ClientError(
            error_response={"Error": {"Message": "DynamoDB Error"}},
            operation_name="Scan",
        )

        result = self.repo.fetch_reviews_for_service(self.sample_service_id)

        self.assertEqual(result, [])
        self.mock_reviews_table.scan.assert_called_once()

    def test_add_bookmark_success(self):
        self.mock_bookmarks_table.put_item.return_value = {}

        bookmark_id = str(uuid.uuid4())
        self.repo.add_bookmark(
            bookmark_id=bookmark_id,
            user_id=self.sample_user_id,
            service_id=self.sample_service_id,
        )

        self.mock_bookmarks_table.put_item.assert_called_once()

    def test_remove_bookmark_success(self):
        self.mock_bookmarks_table.query.return_value = {
            "Items": [{"BookmarkId": "bookmark-123"}]
        }

        self.repo.remove_bookmark(
            user_id=self.sample_user_id, service_id=self.sample_service_id
        )

        self.mock_bookmarks_table.query.assert_called_once()
        self.mock_bookmarks_table.delete_item.assert_called_once()

    def test_is_bookmarked_true(self):
        self.mock_bookmarks_table.query.return_value = {
            "Items": [{"BookmarkId": "bookmark-123"}]
        }

        result = self.repo.is_bookmarked(
            user_id=self.sample_user_id, service_id=self.sample_service_id
        )

        self.assertTrue(result)
        self.mock_bookmarks_table.query.assert_called_once()

    def test_get_user_bookmarks_success(self):
        self.mock_bookmarks_table.query.return_value = {
            "Items": [{"ServiceId": self.sample_service_id}]
        }
        self.mock_services_table.get_item.return_value = {
            "Item": {"Id": self.sample_service_id}
        }

        result = self.repo.get_user_bookmarks(user_id=self.sample_user_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Id"], self.sample_service_id)
        self.mock_bookmarks_table.query.assert_called_once()
        self.mock_services_table.get_item.assert_called_once()
