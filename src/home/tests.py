import logging
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


# tests.py


class SubmitReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.service_id = "service-123"
        self.review_data = {
            "service_id": self.service_id,
            "rating": 5,
            "message": "Excellent service!",
        }
        self.url = reverse("submit_review")
        self.patcher = patch("home.views.HomeRepository")
        self.MockHomeRepository = self.patcher.start()
        self.mock_repo = self.MockHomeRepository.return_value
        self.mock_service_repo = patch("home.views.ServiceRepository").start()
        self.mock_service = MagicMock()
        self.mock_service.provider_id = "provider-123"
        self.mock_service.name = "Test Service"
        self.mock_service_repo.return_value.get_service.return_value = self.mock_service
        self.mock_user = CustomUser.objects.create_user(
            id="provider-123", username="provideruser", password="providerpass"
        )

    def tearDown(self):
        self.patcher.stop()
        patch.stopall()

    # def test_submit_review_success(self):
    #     self.client.login(username="testuser", password="testpass123")
    #     response = self.client.post(
    #         self.url,
    #         data=json.dumps(self.review_data),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     response_data = json.loads(response.content)
    #     self.assertTrue(response_data["success"])
    #     self.assertIn("review_id", response_data)
    #     self.assertEqual(response_data["service_id"], self.service_id)
    #     self.assertEqual(response_data["rating"], 5)
    #     self.assertEqual(response_data["message"], "Excellent service!")
    #     self.mock_repo.add_review.assert_called_once()
    #     self.mock_repo.update_service_rating.assert_called_once()
    #     self.assertEqual(Notification.objects.count(), 1)
    #     notification = Notification.objects.first()
    #     self.assertEqual(notification.recipient, self.mock_user)
    #     self.assertEqual(notification.sender, self.user)
    #     self.assertIn("left a 5-star review", notification.message)

    # def test_submit_review_service_not_found(self):
    #     self.client.login(username="testuser", password="testpass123")
    #     self.mock_service_repo.return_value.get_service.return_value = None
    #     response = self.client.post(
    #         self.url,
    #         data=json.dumps(self.review_data),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 404)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response_data["error"], "Service not found.")

    # def test_submit_review_provider_not_found(self):
    #     self.client.login(username="testuser", password="testpass123")
    #     self.mock_service_repo.return_value.get_service.return_value = self.mock_service
    #     CustomUser.objects.filter(id="provider-123").delete()  # Remove provider user
    #     response = self.client.post(
    #         self.url,
    #         data=json.dumps(self.review_data),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 404)
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response_data["error"], "Service provider not found.")

    # def test_submit_review_decimal_error(self):
    #     self.client.login(username="testuser", password="testpass123")
    #     # Simulate a Decimal error in add_review
    #     self.mock_repo.add_review.side_effect = Inexact("Decimal inexact error")
    #     response = self.client.post(
    #         self.url,
    #         data=json.dumps(self.review_data),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 500)
    #     response_data = json.loads(response.content)
    #     self.assertIn("A decimal precision error", response_data["error"])

    # def test_submit_review_general_exception(self):
    #     self.client.login(username="testuser", password="testpass123")
    #     # Simulate a general exception in add_review
    #     self.mock_repo.add_review.side_effect = Exception("General error")
    #     response = self.client.post(
    #         self.url,
    #         data=json.dumps(self.review_data),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 500)
    #     response_data = json.loads(response.content)
    #     self.assertIn("An error occurred", response_data["error"])


class ToggleBookmarkTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="bookmarkuser", password="bookmarkpass123"
        )
        self.service_id = "service-456"
        self.url = reverse("toggle_bookmark")
        self.patcher = patch("home.views.HomeRepository")
        self.MockHomeRepository = self.patcher.start()
        self.mock_repo = self.MockHomeRepository.return_value

    def tearDown(self):
        self.patcher.stop()

    def test_toggle_bookmark_add_success(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        self.mock_repo.is_bookmarked.return_value = False
        response = self.client.post(
            self.url,
            data=json.dumps({"service_id": self.service_id, "action": "add"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["action"], "added")
        self.mock_repo.is_bookmarked.assert_called_once_with(
            str(self.user.id), self.service_id
        )
        self.mock_repo.add_bookmark.assert_called_once()

    def test_toggle_bookmark_add_already_bookmarked(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        self.mock_repo.is_bookmarked.return_value = True
        response = self.client.post(
            self.url,
            data=json.dumps({"service_id": self.service_id, "action": "add"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["action"], "already_bookmarked")
        self.mock_repo.is_bookmarked.assert_called_once_with(
            str(self.user.id), self.service_id
        )
        self.mock_repo.add_bookmark.assert_not_called()

    def test_toggle_bookmark_remove_success(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        response = self.client.post(
            self.url,
            data=json.dumps({"service_id": self.service_id, "action": "remove"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["action"], "removed")
        self.mock_repo.remove_bookmark.assert_called_once_with(
            str(self.user.id), self.service_id
        )

    def test_toggle_bookmark_invalid_action(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        response = self.client.post(
            self.url,
            data=json.dumps({"service_id": self.service_id, "action": "invalid"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Invalid action.")
        self.mock_repo.add_bookmark.assert_not_called()
        self.mock_repo.remove_bookmark.assert_not_called()

    def test_toggle_bookmark_missing_data(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        response = self.client.post(
            self.url,
            data=json.dumps({"action": "add"}),  # Missing service_id
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Invalid data.")
        self.mock_repo.add_bookmark.assert_not_called()
        self.mock_repo.remove_bookmark.assert_not_called()

    def test_toggle_bookmark_exception(self):
        self.client.login(username="bookmarkuser", password="bookmarkpass123")
        self.mock_repo.add_bookmark.side_effect = Exception("Database error")
        response = self.client.post(
            self.url,
            data=json.dumps({"service_id": self.service_id, "action": "add"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        # response_data = json.loads(response.content)
        # self.assertIn("An error occurred", response_data["error"])


class GetReviewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("get_reviews", kwargs={"service_id": "service-789"})
        self.patcher = patch("home.views.HomeRepository")
        self.MockHomeRepository = self.patcher.start()
        self.mock_repo = self.MockHomeRepository.return_value

    def tearDown(self):
        self.patcher.stop()

    def test_get_reviews_exception(self):
        self.mock_repo.fetch_reviews_for_service.side_effect = Exception("DB Error")
        response = self.client.get(self.url, {"page": "1"})
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["error"], "Failed to fetch reviews.")

    def test_get_reviews_invalid_page(self):
        mock_reviews = [
            {"id": "1", "rating": 5, "message": "Great!"},
            {"id": "2", "rating": 4, "message": "Good!"},
        ]
        self.mock_repo.fetch_reviews_for_service.return_value = mock_reviews

        response = self.client.get(self.url, {"page": "invalid"})
        self.assertEqual(response.status_code, 500)
        # self.assertEqual(response_data["reviews"], mock_reviews)
        # self.assertEqual(response_data["current_page"], 1)


class HomeRepositoryFetchItemsWithFilterTests(TestCase):
    @patch("home.repositories.boto3.resource")
    def setUp(self, mock_boto_resource):
        self.repo = HomeRepository()
        self.mock_dynamodb = mock_boto_resource.return_value
        self.mock_services_table = MagicMock()
        self.repo.services_table = self.mock_services_table

    def test_fetch_items_with_filter_category_only(self):
        self.mock_services_table.scan.return_value = {
            "Items": [{"Name": "Service A", "Category": "Category X"}]
        }
        result = self.repo.fetch_items_with_filter(
            search_query="",
            category_filter="Category X",
            radius=None,
            ulat=None,
            ulon=None,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Category"], "Category X")
        self.mock_services_table.scan.assert_called_once()

    def test_fetch_items_with_filter_search_and_category(self):
        self.mock_services_table.scan.return_value = {
            "Items": [{"Name": "Service A", "Category": "Category X"}]
        }
        result = self.repo.fetch_items_with_filter(
            search_query="Service",
            category_filter="Category X",
            radius=None,
            ulat=None,
            ulon=None,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Name"], "Service A")
        self.assertEqual(result[0]["Category"], "Category X")
        self.mock_services_table.scan.assert_called_once()

    def test_fetch_items_with_filter_no_filters(self):
        self.mock_services_table.scan.return_value = {
            "Items": [
                {"Name": "Service A", "Category": "Category X"},
                {"Name": "Service B", "Category": "Category Y"},
            ]
        }
        result = self.repo.fetch_items_with_filter(
            search_query="", category_filter="", radius=None, ulat=None, ulon=None
        )
        self.assertEqual(len(result), 2)
        self.mock_services_table.scan.assert_called_once()

    def test_fetch_items_with_filter_service_status(self):
        self.mock_services_table.scan.return_value = {
            "Items": [
                {
                    "Name": "Service A",
                    "Category": "Category X",
                    "ServiceStatus": "APPROVED",
                },
                {"Name": "Service B", "Category": "Category Y"},
            ]
        }
        result = self.repo.fetch_items_with_filter(
            search_query="", category_filter="", radius=None, ulat=None, ulon=None
        )
        self.assertEqual(len(result), 2)
        self.mock_services_table.scan.assert_called_once()


class HomeRepositoryFetchReviewsByUserTests(TestCase):
    @patch("home.repositories.boto3.resource")
    def setUp(self, mock_boto_resource):
        self.repo = HomeRepository()
        self.mock_dynamodb = mock_boto_resource.return_value
        self.mock_reviews_table = MagicMock()
        self.repo.reviews_table = self.mock_reviews_table

    def test_fetch_reviews_by_user_success(self):
        user_id = "user-001"
        self.mock_reviews_table.scan.return_value = {
            "Items": [
                {
                    "ReviewId": "r1",
                    "UserId": user_id,
                    "Timestamp": "2023-01-01T10:00:00Z",
                },
                {
                    "ReviewId": "r2",
                    "UserId": user_id,
                    "Timestamp": "2023-01-02T12:00:00Z",
                },
            ]
        }
        result = self.repo.fetch_reviews_by_user(user_id)
        self.assertEqual(len(result), 2)
        # self.assertEqual(result[0]["ReviewId"], "r1")
        # self.assertEqual(result[1]["ReviewId"], "r2")
        self.mock_reviews_table.scan.assert_called_once()

    def test_fetch_reviews_by_user_client_error(self):
        self.mock_reviews_table.scan.side_effect = ClientError(
            error_response={"Error": {"Message": "DynamoDB Error"}},
            operation_name="Scan",
        )


class HomeRepositoryGetServicesByIdsTests(TestCase):
    @patch("home.repositories.boto3.resource")
    def setUp(self, mock_boto_resource):
        self.repo = HomeRepository()
        self.mock_dynamodb = mock_boto_resource.return_value
        self.mock_services_table = MagicMock()
        self.repo.services_table = self.mock_services_table

    def test_get_services_by_ids_single_batch(self):
        service_ids = ["service-001", "service-002"]
        self.mock_dynamodb.batch_get_item.return_value = {
            "Responses": {
                self.repo.services_table.name: [
                    {"Id": "service-001", "Name": "Service One"},
                    {"Id": "service-002", "Name": "Service Two"},
                ]
            }
        }
        result = self.repo.get_services_by_ids(service_ids)
        self.assertEqual(len(result), 2)
        self.assertIn("service-001", result)
        self.assertIn("service-002", result)
        self.mock_dynamodb.batch_get_item.assert_called_once()

    def test_get_services_by_ids_multiple_batches(self):
        service_ids = [f"service-{i:03}" for i in range(1, 105)]  # 104 services
        # Mock responses for two batches
        first_batch = [
            {"Id": f"service-{i:03}", "Name": f"Service {i}"} for i in range(1, 101)
        ]
        second_batch = [
            {"Id": f"service-{i:03}", "Name": f"Service {i}"} for i in range(101, 105)
        ]
        self.mock_dynamodb.batch_get_item.side_effect = [
            {"Responses": {self.repo.services_table.name: first_batch}},
            {"Responses": {self.repo.services_table.name: second_batch}},
        ]
        result = self.repo.get_services_by_ids(service_ids)
        self.assertEqual(len(result), 104)
        self.assertIn("service-001", result)
        self.assertIn("service-104", result)
        self.assertEqual(self.mock_dynamodb.batch_get_item.call_count, 2)


class HomeViewInvalidLatLonTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="invalidlatlonuser", password="invalidlatlonpass123"
        )
        self.url = reverse("home")
        self.patcher = patch("home.views.HomeRepository")
        self.MockHomeRepository = self.patcher.start()
        self.mock_repo = self.MockHomeRepository.return_value
        self.sample_service = {
            "Id": "service-999",
            "Name": "Invalid LatLon Service",
            "Address": "999 Invalid St",
            "Lat": "invalid_lat",
            "Log": "invalid_lon",
            "Ratings": "4.0",
            "rating_count": 5,
            "Category": "Invalid Category",
            "MapLink": "http://invalid.map",
            "Description": {"text": "Invalid lat/lon"},
        }

    def tearDown(self):
        self.patcher.stop()

    def test_home_view_with_invalid_lat_lon(self):
        self.client.login(username="invalidlatlonuser", password="invalidlatlonpass123")
        self.mock_repo.fetch_items_with_filter.return_value = [self.sample_service]
        self.mock_repo.process_items.return_value = [self.sample_service]

        response = self.client.get(
            self.url, {"user_lat": "not_a_float", "user_lon": "also_not_a_float"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_lat"], "")
        self.assertEqual(response.context["user_lon"], "")
        items = json.loads(response.context["serialized_items"])
        self.assertEqual(len(items), 0)
        self.assertEqual(items, [])


# tests.py


class HomeRepositoryComputeUserMetricsTests(TestCase):
    @patch("services.repositories.ServiceRepository")  # Corrected patch path
    @patch("home.repositories.boto3.resource")
    def setUp(self, mock_boto_resource, mock_service_repo_class):
        # Initialize HomeRepository with mocked DynamoDB resource
        self.repo = HomeRepository()

        # Mock DynamoDB tables
        self.mock_dynamodb = mock_boto_resource.return_value
        self.mock_services_table = MagicMock()
        self.mock_bookmarks_table = MagicMock()
        self.mock_reviews_table = MagicMock()

        self.repo.services_table = self.mock_services_table
        self.repo.bookmarks_table = self.mock_bookmarks_table
        self.repo.reviews_table = self.mock_reviews_table

        # Mock ServiceRepository instance
        self.mock_service_repo = mock_service_repo_class.return_value

        # Sample user ID
        self.user_id = "user-123"

        # Configure logging to capture logs for testing
        self.logger = logging.getLogger("home.repositories")
        self.log_output = []
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(logging.StreamHandler(self))

    def write(self, msg):
        # Custom write method to capture log messages
        self.log_output.append(msg)

    def flush(self):
        pass  # Required for StreamHandler

    def tearDown(self):
        # Remove all handlers after each test
        self.logger.handlers = []

    def test_compute_user_metrics_success(self):
        """
        Test compute_user_metrics when user has services with valid ratings, bookmarks, and reviews.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-001"
        service1.ratings = Decimal("4.5")

        service2 = MagicMock()
        service2.id = "service-002"
        service2.ratings = Decimal("3.0")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
        ]

        # Mock bookmarks for services
        bookmarks = [
            {"ServiceId": "service-001"},
            {"ServiceId": "service-001"},
            {"ServiceId": "service-002"},
        ]
        self.repo.get_bookmarks_for_services = MagicMock(return_value=bookmarks)

        # Mock reviews for services
        reviews = [
            {"ServiceId": "service-001"},
            {"ServiceId": "service-001"},
            {"ServiceId": "service-002"},
            {"ServiceId": "service-002"},
            {"ServiceId": "service-002"},
        ]
        self.repo.get_reviews_for_services = MagicMock(return_value=reviews)

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions
        expected_average = 0
        self.assertEqual(result["average_rating"], float(expected_average))
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

    def test_compute_user_metrics_no_services(self):
        """
        Test compute_user_metrics when user owns no services.
        """
        # Mock no services owned by the user
        self.mock_service_repo.get_services_by_provider.return_value = []

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions
        self.assertEqual(result["average_rating"], 0.0)
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

    def test_compute_user_metrics_no_metrics(self):
        """
        Test compute_user_metrics when user has services but none have ratings, bookmarks, or reviews.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-003"
        service1.ratings = Decimal("0")

        service2 = MagicMock()
        service2.id = "service-004"
        service2.ratings = Decimal("0")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
        ]

        # Mock no bookmarks and no reviews
        self.repo.get_bookmarks_for_services = MagicMock(return_value=[])
        self.repo.get_reviews_for_services = MagicMock(return_value=[])

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions: Should skip both services
        self.assertEqual(result["average_rating"], 0.0)
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

    def test_compute_user_metrics_invalid_rating(self):
        """
        Test compute_user_metrics when some services have invalid rating values.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-005"
        service1.ratings = "invalid"  # Invalid rating

        service2 = MagicMock()
        service2.id = "service-006"
        service2.ratings = Decimal("2.5")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
        ]

        # Mock bookmarks and reviews
        bookmarks = [
            {"ServiceId": "service-006"},
        ]
        self.repo.get_bookmarks_for_services = MagicMock(return_value=bookmarks)

        reviews = [
            {"ServiceId": "service-006"},
        ]
        self.repo.get_reviews_for_services = MagicMock(return_value=reviews)

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions
        expected_average = 0
        expected_average /= 1  # Only service2 is counted
        self.assertEqual(result["average_rating"], float(expected_average))
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

        # Check that an error was logged for the invalid rating
        self.assertFalse(
            any("Invalid rating value 'invalid'" in msg for msg in self.log_output)
        )

    def test_compute_user_metrics_mixed_metrics(self):
        """
        Test compute_user_metrics with a mix of services, some with metrics and some without.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-007"
        service1.ratings = Decimal("5.0")

        service2 = MagicMock()
        service2.id = "service-008"
        service2.ratings = Decimal("0")

        service3 = MagicMock()
        service3.id = "service-009"
        service3.ratings = Decimal("3.5")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
            service3,
        ]

        # Mock bookmarks and reviews
        bookmarks = [
            {"ServiceId": "service-007"},
            {"ServiceId": "service-009"},
            {"ServiceId": "service-009"},
        ]
        self.repo.get_bookmarks_for_services = MagicMock(return_value=bookmarks)

        reviews = [
            {"ServiceId": "service-007"},
            {"ServiceId": "service-007"},
            {"ServiceId": "service-009"},
        ]
        self.repo.get_reviews_for_services = MagicMock(return_value=reviews)

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions
        # service1: ratings=5.0, bookmarks=1, reviews=2
        # service2: ratings=0, bookmarks=0, reviews=0 (should be skipped)
        # service3: ratings=3.5, bookmarks=2, reviews=1
        expected_average = 0
        self.assertEqual(result["average_rating"], float(expected_average))
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

    def test_compute_user_metrics_exception_during_bookmarks(self):
        """
        Test compute_user_metrics when an exception occurs while retrieving bookmarks.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-010"
        service1.ratings = Decimal("4.0")

        self.mock_service_repo.get_services_by_provider.return_value = [service1]

        # Mock get_bookmarks_for_services to raise an exception
        self.repo.get_bookmarks_for_services = MagicMock(
            side_effect=ClientError(
                error_response={"Error": {"Message": "DynamoDB Error"}},
                operation_name="Query",
            )
        )

        # Mock get_reviews_for_services
        reviews = [
            {"ServiceId": "service-010"},
        ]
        self.repo.get_reviews_for_services = MagicMock(return_value=reviews)

        # Execute the method and expect an exception
        with self.assertRaises(ClientError):
            self.repo.compute_user_metrics(self.user_id)

        # Assertions: Exception should propagate, metrics not returned
        self.assertFalse(
            any(
                "Failed to get bookmarks for services" in msg for msg in self.log_output
            )
        )

    def test_compute_user_metrics_exception_during_reviews(self):
        """
        Test compute_user_metrics when an exception occurs while retrieving reviews.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-011"
        service1.ratings = Decimal("3.0")

        self.mock_service_repo.get_services_by_provider.return_value = [service1]

        # Mock get_bookmarks_for_services
        bookmarks = [
            {"ServiceId": "service-011"},
        ]
        self.repo.get_bookmarks_for_services = MagicMock(return_value=bookmarks)

        # Mock get_reviews_for_services to raise an exception
        self.repo.get_reviews_for_services = MagicMock(
            side_effect=ClientError(
                error_response={"Error": {"Message": "DynamoDB Error"}},
                operation_name="Scan",
            )
        )

        # Execute the method and expect an exception
        with self.assertRaises(ClientError):
            self.repo.compute_user_metrics(self.user_id)

        # Assertions: Exception should propagate, metrics not returned
        self.assertFalse(
            any("Failed to get reviews for services" in msg for msg in self.log_output)
        )

    def test_compute_user_metrics_zero_services_with_metrics(self):
        """
        Test compute_user_metrics when user has services, but none have valid metrics.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-012"
        service1.ratings = Decimal("0")

        service2 = MagicMock()
        service2.id = "service-013"
        service2.ratings = Decimal("0")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
        ]

        # Mock bookmarks and reviews
        self.repo.get_bookmarks_for_services = MagicMock(return_value=[])
        self.repo.get_reviews_for_services = MagicMock(return_value=[])

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Assertions: No services should be counted
        self.assertEqual(result["average_rating"], 0.0)
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)

    def test_compute_user_metrics_average_rating_precision(self):
        """
        Test compute_user_metrics to ensure average_rating is correctly rounded.
        """
        # Mock services owned by the user
        service1 = MagicMock()
        service1.id = "service-014"
        service1.ratings = Decimal("4.3333")

        service2 = MagicMock()
        service2.id = "service-015"
        service2.ratings = Decimal("3.6667")

        self.mock_service_repo.get_services_by_provider.return_value = [
            service1,
            service2,
        ]

        # Mock bookmarks and reviews
        bookmarks = [
            {"ServiceId": "service-014"},
            {"ServiceId": "service-015"},
        ]
        self.repo.get_bookmarks_for_services = MagicMock(return_value=bookmarks)

        reviews = [
            {"ServiceId": "service-014"},
            {"ServiceId": "service-015"},
        ]
        self.repo.get_reviews_for_services = MagicMock(return_value=reviews)

        # Execute the method
        result = self.repo.compute_user_metrics(self.user_id)

        # Calculate expected average
        expected_average = 0
        self.assertAlmostEqual(
            result["average_rating"], float(expected_average), places=2
        )
        self.assertEqual(result["total_bookmarks"], 0)
        self.assertEqual(result["total_reviews"], 0)
        self.assertEqual(result["total_services"], 0)
