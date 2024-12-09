import json
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError

from accounts.models import CustomUser
from services.models import ReviewDTO
from services.repositories import ReviewRepository
from forum.models import Post, Comment, Category, Notification
from home.repositories import HomeRepository  # Added HomeRepository
from moderation.models import Flag  # Adjust if needed based on your app structure


class ModerationViewsTest(TestCase):
    """
    Test suite for moderation views including flag creation, review, and status checking.
    All tests use mocking to avoid database operations.
    """

    def setUp(self):
        """Set up test environment before each test"""
        self.client = Client()

        # Create mock users
        self.regular_user = MagicMock()
        self.regular_user.is_authenticated = True
        self.regular_user.is_superuser = False
        self.regular_user.id = "user123"
        self.regular_user.username = "regular_user"

        self.admin_user = MagicMock()
        self.admin_user.is_authenticated = True
        self.admin_user.is_superuser = True
        self.admin_user.id = "admin456"
        self.admin_user.username = "admin_user"

        # Create mock content objects
        self.mock_post = MagicMock()
        self.mock_post.id = "post789"
        self.mock_post.author = self.regular_user

        self.mock_comment = MagicMock()
        self.mock_comment.id = "comment101"
        self.mock_comment.author = self.regular_user

        # Create mock review with all required fields
        self.mock_review = ReviewDTO(
            review_id="review123",
            service_id="service789",
            user_id="user123",
            username="testuser",
            rating_stars=5,
            rating_message="Great service",
            timestamp=datetime.now().isoformat(),
            responseText="",
            responded_at="",
        )

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        with patch(
            "django.contrib.auth.middleware.get_user", return_value=AnonymousUser()
        ):
            response = self.client.post(reverse("moderation:create_flag"))
            self.assertEqual(response.status_code, 302)  # Should redirect to login
            self.assertTrue("/login/" in response.url)

    @patch("moderation.views.Flag.objects.filter")
    def test_check_flag_status(self, mock_flag_filter):
        """Test checking the status of flags on content"""
        # Setup mock for pending flags
        mock_flag_filter.return_value.exists.return_value = True
        mock_flag_filter.return_value.count.return_value = 2

        with patch(
            "django.contrib.auth.middleware.get_user", return_value=self.regular_user
        ):
            response = self.client.get(
                reverse(
                    "moderation:check_flag_status",
                    kwargs={
                        "content_type": "REVIEW",
                        "object_id": self.mock_review.review_id,
                    },
                )
            )

        data = json.loads(response.content)
        self.assertTrue(data["userHasFlagged"])
        self.assertTrue(data["hasPendingFlags"])
        self.assertEqual(data["pendingFlagsCount"], 2)

    def test_invalid_content_type(self):
        """Test flag creation with invalid content type"""
        with patch(
            "django.contrib.auth.middleware.get_user", return_value=self.regular_user
        ):
            response = self.client.post(
                reverse("moderation:create_flag"),
                {
                    "content_type": "INVALID_TYPE",
                    "object_id": "test123",
                    "reason": "SPAM",
                },
            )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid content type", data["error"])

    @patch("moderation.views.Post.objects.get")
    def test_nonexistent_content(self, mock_post_get):
        """Test flag creation for nonexistent content"""
        mock_post_get.side_effect = Post.DoesNotExist

        with patch(
            "django.contrib.auth.middleware.get_user", return_value=self.regular_user
        ):
            response = self.client.post(
                reverse("moderation:create_flag"),
                {
                    "content_type": "FORUM POST",
                    "object_id": "nonexistent",
                    "reason": "SPAM",
                },
            )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn("not found", data["error"])

    @patch("moderation.views.Flag.objects.get")
    def test_review_flag_unauthorized(self, mock_flag_get):
        """Test that non-admin users cannot review flags"""
        mock_flag_get.return_value = MagicMock()

        with patch(
            "django.contrib.auth.middleware.get_user", return_value=self.regular_user
        ):
            response = self.client.post(
                reverse("moderation:review_flag", args=[1]), {"action": "dismiss"}
            )

        self.assertEqual(response.status_code, 302)  # Should redirect


class FlagModelTest(TestCase):
    """
    Tests for the Flag model to ensure coverage of model logic,
    including get_content_object, save, clean, unique constraints,
    and string representation.
    """

    def setUp(self):
        self.flagger = CustomUser.objects.create_user(
            username='flaggeruser', email='flagger@example.com', password='testpass'
        )
        self.author = CustomUser.objects.create_user(
            username='authoruser', email='author@example.com', password='authorpass'
        )

        self.category = Category.objects.create(name="Test Category")

        self.post = Post.objects.create(
            title="Sample Post",
            content="This is a sample forum post.",
            author=self.author,
            category=self.category
        )

        self.comment = Comment.objects.create(
            content="This is a sample comment.",
            author=self.author,
            post=self.post
        )

        self.review_id = str(uuid.uuid4())

        # Provide all required fields for ReviewDTO.
        self.mock_review_dto = ReviewDTO(
            review_id=self.review_id,
            service_id="test_service",
            user_id=str(self.flagger.id),
            username=self.author.username,
            rating_stars=5,  # Use an int here
            rating_message="Excellent service",
            timestamp=datetime.now().isoformat(),
            responseText="",
            responded_at=""
        )

    @patch('services.repositories.ReviewRepository.get_review')
    def test_flag_for_post(self, mock_get_review):
        # For Posts, no call to ReviewRepository should be made
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.flagger,
            reason="SPAM",
        )
        self.assertEqual(flag.content_title, self.post.title)
        self.assertEqual(flag.content_preview, self.post.content)
        self.assertEqual(flag.content_author, self.author.username)
        self.assertIsNone(flag.content_rating)
        mock_get_review.assert_not_called()

    @patch('services.repositories.ReviewRepository.get_review')
    def test_flag_for_comment(self, mock_get_review):
        # For Comments, no call to ReviewRepository
        flag = Flag.objects.create(
            content_type="FORUM COMMENT",
            object_id=self.comment.id,
            flagger=self.flagger,
            reason="OFFENSIVE",
        )
        self.assertEqual(flag.content_preview, self.comment.content)
        self.assertEqual(flag.content_author, self.author.username)
        self.assertIsNone(flag.content_rating)
        mock_get_review.assert_not_called()

    @patch('services.repositories.ReviewRepository.get_review')
    def test_flag_for_review(self, mock_get_review):
        mock_get_review.return_value = self.mock_review_dto
        flag = Flag.objects.create(
            content_type="REVIEW",
            object_id=self.review_id,
            flagger=self.flagger,
            reason="SPAM",
        )
        self.assertEqual(flag.content_preview, self.mock_review_dto.rating_message)
        self.assertEqual(flag.content_author, self.mock_review_dto.username)
        self.assertEqual(flag.content_rating, self.mock_review_dto.rating_stars)
        mock_get_review.assert_called_once_with(self.review_id)

    def test_get_content_object_post(self):
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.flagger,
            reason="SPAM",
        )
        obj = flag.get_content_object()
        self.assertEqual(obj, self.post)

    def test_get_content_object_comment(self):
        flag = Flag.objects.create(
            content_type="FORUM COMMENT",
            object_id=self.comment.id,
            flagger=self.flagger,
            reason="OFFENSIVE",
        )
        obj = flag.get_content_object()
        self.assertEqual(obj, self.comment)

    @patch('services.repositories.ReviewRepository.get_review')
    def test_get_content_object_review(self, mock_get_review):
        mock_get_review.return_value = self.mock_review_dto
        flag = Flag.objects.create(
            content_type="REVIEW",
            object_id=self.review_id,
            flagger=self.flagger,
            reason="SPAM",
        )
        obj = flag.get_content_object()
        self.assertEqual(obj, self.mock_review_dto)

    def test_get_content_object_nonexistent_post(self):
        flag = Flag(
            content_type="FORUM POST",
            object_id="999999",
            flagger=self.flagger,
            reason="OTHER"
        )
        self.assertIsNone(flag.get_content_object())

    def test_object_id_always_string(self):
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=12345,
            flagger=self.flagger,
            reason="SPAM"
        )
        self.assertIsInstance(flag.object_id, str)
        self.assertEqual(flag.object_id, "12345")

    def test_unique_constraint(self):
        Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.flagger,
            reason="SPAM"
        )
        # Attempting to create the same flag again should fail
        with self.assertRaises(IntegrityError):
            Flag.objects.create(
                content_type="FORUM POST",
                object_id=self.post.id,
                flagger=self.flagger,
                reason="SPAM"
            )

    def test_ordering(self):
        f1 = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.flagger,
            reason="SPAM"
        )
        f2 = Flag.objects.create(
            content_type="FORUM COMMENT",
            object_id=self.comment.id,
            flagger=self.flagger,
            reason="OFFENSIVE"
        )
        flags = list(Flag.objects.all())
        # f2 created after f1, so should appear first due to "-created_at" ordering
        self.assertEqual(flags[0], f2)
        self.assertEqual(flags[1], f1)

    def test_str_representation(self):
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.flagger,
            reason="SPAM"
        )
        expected_str = f"Flag by {self.flagger.username} on FORUM POST (PENDING)"
        self.assertEqual(str(flag), expected_str)


class ModerationViewsAdditionalTest(TestCase):
    """
    Additional tests for moderation views including:
    - Creating flags for different content types
    - Reviewing flags as admin
    - Checking flag status
    """

    def setUp(self):
        """Set up test environment before each test"""
        self.client = Client()

        # Create regular user and admin user
        self.regular_user = CustomUser.objects.create_user(
            username='regularuser', email='regular@example.com', password='regularpass'
        )
        self.admin_user = CustomUser.objects.create_user(
            username='adminuser', email='admin@example.com', password='adminpass', is_superuser=True
        )

        # Ensure regular_user is not a superuser
        self.regular_user.is_superuser = False
        self.regular_user.save()

        # Create category, post, and comment
        self.category = Category.objects.create(name="General")
        self.post = Post.objects.create(
            title="Test Post",
            content="Content of the test post.",
            author=self.regular_user,
            category=self.category
        )
        self.comment = Comment.objects.create(
            content="Test comment.",
            author=self.regular_user,
            post=self.post
        )

        # Create a ReviewDTO instance
        self.review_id = str(uuid.uuid4())
        self.review_dto = ReviewDTO(
            review_id=self.review_id,
            service_id="service_test",
            user_id=str(self.regular_user.id),
            username=self.regular_user.username,
            rating_stars=4,
            rating_message="Good service.",
            timestamp=datetime.now().isoformat(),
            responseText="",
            responded_at=""
        )

    def login_regular_user(self):
        """Helper method to log in as regular user"""
        self.client.login(username='regularuser', password='regularpass')

    def login_admin_user(self):
        """Helper method to log in as admin user"""
        self.client.login(username='adminuser', password='adminpass')

    @patch('services.repositories.ReviewRepository.get_review')
    def test_create_flag_post_success(self, mock_get_review):
        """Test successful flag creation for a forum post"""
        mock_get_review.return_value = None  # Not used for posts

        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "FORUM POST",
                "object_id": self.post.id,
                "reason": "SPAM",
                "explanation": "This post is spam."
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Content has been flagged for review")

        # Verify the flag was created
        flag = Flag.objects.get(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.regular_user
        )
        self.assertEqual(flag.reason, "SPAM")
        self.assertEqual(flag.explanation, "This post is spam.")

        # Verify notifications were created for admins
        notifications = Notification.objects.filter(
            recipient=self.admin_user,
            notification_type="flag_admin",
            is_read=False
        )
        self.assertTrue(notifications.exists())

    @patch('services.repositories.ReviewRepository.get_review')
    def test_create_flag_comment_success(self, mock_get_review):
        """Test successful flag creation for a forum comment"""
        mock_get_review.return_value = None  # Not used for comments

        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "FORUM COMMENT",
                "object_id": self.comment.id,
                "reason": "OFFENSIVE",
                "explanation": "This comment is offensive."
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Content has been flagged for review")

        # Verify the flag was created
        flag = Flag.objects.get(
            content_type="FORUM COMMENT",
            object_id=self.comment.id,
            flagger=self.regular_user
        )
        self.assertEqual(flag.reason, "OFFENSIVE")
        self.assertEqual(flag.explanation, "This comment is offensive.")

        # Verify notifications were created for admins
        notifications = Notification.objects.filter(
            recipient=self.admin_user,
            notification_type="flag_admin",
            is_read=False
        )
        self.assertTrue(notifications.exists())

    @patch('services.repositories.ReviewRepository.get_review')
    def test_create_flag_review_success(self, mock_get_review):
        """Test successful flag creation for a review"""
        mock_get_review.return_value = self.review_dto

        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "REVIEW",
                "object_id": self.review_id,
                "reason": "MISINFORMATION",
                "explanation": "This review contains false information."
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Content has been flagged for review")

        # Verify the flag was created
        flag = Flag.objects.get(
            content_type="REVIEW",
            object_id=self.review_id,
            flagger=self.regular_user
        )
        self.assertEqual(flag.reason, "MISINFORMATION")
        self.assertEqual(flag.explanation, "This review contains false information.")
        self.assertEqual(flag.content_rating, self.review_dto.rating_stars)

        # Verify notifications were created for admins
        notifications = Notification.objects.filter(
            recipient=self.admin_user,
            notification_type="flag_admin",
            is_read=False
        )
        self.assertTrue(notifications.exists())

    def test_create_flag_invalid_content_type(self):
        """Test flag creation with invalid content type"""
        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "INVALID_TYPE",
                "object_id": "test123",
                "reason": "SPAM",
                "explanation": "Invalid content type test."
            },
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid content type", data["error"])

    @patch("moderation.views.Post.objects.get")
    def test_create_flag_nonexistent_post(self, mock_post_get):
        """Test flag creation for a nonexistent forum post"""
        mock_post_get.side_effect = Post.DoesNotExist

        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "FORUM POST",
                "object_id": "nonexistent_post",
                "reason": "SPAM",
                "explanation": "Nonexistent post test."
            },
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn("Post not found", data["error"])

    @patch('services.repositories.ReviewRepository.get_review')
    def test_create_flag_nonexistent_review(self, mock_get_review):
        """Test flag creation for a nonexistent review"""
        mock_get_review.return_value = None

        self.login_regular_user()

        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "REVIEW",
                "object_id": "nonexistent_review",
                "reason": "SPAM",
                "explanation": "Nonexistent review test."
            },
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn("Review not found", data["error"])

    def test_create_flag_duplicate_flag(self):
        """Test that a user cannot flag the same content twice"""
        # First flag creation
        Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="First flag."
        )

        self.login_regular_user()

        # Attempt to create the same flag again
        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "FORUM POST",
                "object_id": self.post.id,
                "reason": "SPAM",
                "explanation": "Second flag attempt."
            },
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("You have already flagged this content", data["error"])

    def test_create_flag_unauthenticated(self):
        """Test that unauthenticated users cannot create flags"""
        response = self.client.post(
            reverse("moderation:create_flag"),
            {
                "content_type": "FORUM POST",
                "object_id": self.post.id,
                "reason": "SPAM",
                "explanation": "Unauthenticated flag attempt."
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue("/login/" in response.url)

    @patch('services.repositories.ReviewRepository.get_review')
    def test_review_flag_dismiss(self, mock_get_review):
        """Test admin dismissing a flag"""
        mock_get_review.return_value = self.review_dto

        # Create a flag
        flag = Flag.objects.create(
            content_type="REVIEW",
            object_id=self.review_id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="Flag to dismiss."
        )

        self.login_admin_user()

        response = self.client.post(
            reverse("moderation:review_flag", args=[flag.id]),
            {"action": "dismiss"}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "DISMISSED")

        # Refresh flag from DB
        flag.refresh_from_db()
        self.assertEqual(flag.status, "DISMISSED")
        self.assertEqual(flag.reviewed_by, self.admin_user)

        # Verify notification to flagger
        notification = Notification.objects.get(
            recipient=self.regular_user,
            notification_type="flag_reviewed",
            message="Your flag has been reviewed and dismissed"
        )
        self.assertIsNotNone(notification)

    @patch('services.repositories.ReviewRepository.get_review')
    def test_review_flag_revoke(self, mock_get_review):
        """Test admin revoking a flag and deleting the content"""
        mock_get_review.return_value = self.review_dto

        # Create a flag
        flag = Flag.objects.create(
            content_type="REVIEW",
            object_id=self.review_id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="Flag to revoke."
        )

        self.login_admin_user()

        # Mock HomeRepository.delete_review
        with patch.object(HomeRepository, 'delete_review') as mock_delete_review:
            response = self.client.post(
                reverse("moderation:review_flag", args=[flag.id]),
                {"action": "revoke"}
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertEqual(data["status"], "REVOKED")

            # Refresh flag from DB
            flag.refresh_from_db()
            self.assertEqual(flag.status, "REVOKED")
            self.assertEqual(flag.reviewed_by, self.admin_user)

            # Verify content is deleted
            # Assuming HomeRepository.delete_review deletes the review
            mock_delete_review.assert_called_once_with(self.review_id)

            # Verify notification to flagger
            notification = Notification.objects.get(
                recipient=self.regular_user,
                notification_type="flag_reviewed",
                message="Your flag has been reviewed and accepted"
            )
            self.assertIsNotNone(notification)

    def test_review_flag_invalid_action(self):
        """Test admin reviewing a flag with an invalid action"""
        # Create a flag
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="Flag with invalid action."
        )

        self.login_admin_user()

        response = self.client.post(
            reverse("moderation:review_flag", args=[flag.id]),
            {"action": "invalid_action"}
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("Invalid action", data["error"])

    def test_review_flag_invalid_flag_id(self):
        """Test admin reviewing a nonexistent flag"""
        self.login_admin_user()

        response = self.client.post(
            reverse("moderation:review_flag", args=[999]),  # Assuming 999 doesn't exist
            {"action": "dismiss"}
        )

        self.assertEqual(response.status_code, 404)
        # Forbidden

    def test_review_flag_unauthenticated(self):
        """Test that unauthenticated users cannot review flags"""
        # Create a flag
        flag = Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="Flag by unauthenticated user."
        )

        response = self.client.post(
            reverse("moderation:review_flag", args=[flag.id]),
            {"action": "dismiss"}
        )

        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue("/login/" in response.url)

    def test_check_flag_status_user_has_flagged(self):
        """Test checking flag status when user has flagged the content"""
        # Create a flag
        Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=self.regular_user,
            reason="SPAM",
            explanation="User has flagged this post."
        )

        self.login_regular_user()

        response = self.client.get(
            reverse(
                "moderation:check_flag_status",
                kwargs={
                    "content_type": "FORUM POST",
                    "object_id": self.post.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["userHasFlagged"])
        self.assertTrue(data["hasPendingFlags"])
        self.assertEqual(data["pendingFlagsCount"], 1)

    def test_check_flag_status_user_has_not_flagged(self):
        """Test checking flag status when user has not flagged the content"""
        # Create a flag by another user
        other_user = CustomUser.objects.create_user(
            username='otheruser', email='other@example.com', password='otherpass'
        )
        Flag.objects.create(
            content_type="FORUM POST",
            object_id=self.post.id,
            flagger=other_user,
            reason="SPAM",
            explanation="Another user has flagged this post."
        )

        self.login_regular_user()

        response = self.client.get(
            reverse(
                "moderation:check_flag_status",
                kwargs={
                    "content_type": "FORUM POST",
                    "object_id": self.post.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["userHasFlagged"])
        self.assertTrue(data["hasPendingFlags"])
        self.assertEqual(data["pendingFlagsCount"], 1)

    def test_check_flag_status_no_pending_flags(self):
        """Test checking flag status when there are no pending flags"""
        self.login_regular_user()

        response = self.client.get(
            reverse(
                "moderation:check_flag_status",
                kwargs={
                    "content_type": "FORUM POST",
                    "object_id": self.post.id,
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["userHasFlagged"])
        self.assertFalse(data["hasPendingFlags"])
        self.assertEqual(data["pendingFlagsCount"], 0)

    def test_check_flag_status_invalid_content_type(self):
        """Test checking flag status with an invalid content type"""
        self.login_regular_user()

        response = self.client.get(
            reverse(
                "moderation:check_flag_status",
                kwargs={
                    "content_type": "INVALID_TYPE",
                    "object_id": "test123",
                },
            )
        )

        # Depending on implementation, this might return an error or simply false
        # Here, assuming it returns a 200 with flags info
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["userHasFlagged"])
        self.assertFalse(data["hasPendingFlags"])
        self.assertEqual(data["pendingFlagsCount"], 0)

    def test_check_flag_status_unauthenticated(self):
        """Test that unauthenticated users cannot check flag status"""
        response = self.client.get(
            reverse(
                "moderation:check_flag_status",
                kwargs={
                    "content_type": "FORUM POST",
                    "object_id": self.post.id,
                },
            )
        )

        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue("/login/" in response.url)
