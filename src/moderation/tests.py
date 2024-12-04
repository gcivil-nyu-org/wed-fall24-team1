import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, Client
from django.urls import reverse

from forum.models import Post
from services.models import ReviewDTO


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
        self.regular_user.id = 'user123'
        self.regular_user.username = 'regular_user'

        self.admin_user = MagicMock()
        self.admin_user.is_authenticated = True
        self.admin_user.is_superuser = True
        self.admin_user.id = 'admin456'
        self.admin_user.username = 'admin_user'

        # Create mock content objects
        self.mock_post = MagicMock()
        self.mock_post.id = 'post789'
        self.mock_post.author = self.regular_user

        self.mock_comment = MagicMock()
        self.mock_comment.id = 'comment101'
        self.mock_comment.author = self.regular_user

        # Create mock review with all required fields
        self.mock_review = ReviewDTO(
            review_id='review123',
            service_id='service789',
            user_id='user123',
            username='testuser',
            rating_stars=5,
            rating_message='Great service',
            timestamp=datetime.now().isoformat(),
            responseText='',
            responded_at=''
        )

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        with patch('django.contrib.auth.middleware.get_user', return_value=AnonymousUser()):
            response = self.client.post(reverse('moderation:create_flag'))
            self.assertEqual(response.status_code, 302)  # Should redirect to login
            self.assertTrue('/login/' in response.url)


    @patch('moderation.views.Flag.objects.filter')
    def test_check_flag_status(self, mock_flag_filter):
        """Test checking the status of flags on content"""
        # Setup mock for pending flags
        mock_flag_filter.return_value.exists.return_value = True
        mock_flag_filter.return_value.count.return_value = 2

        with patch('django.contrib.auth.middleware.get_user', return_value=self.regular_user):
            response = self.client.get(
                reverse('moderation:check_flag_status', kwargs={
                    'content_type': 'REVIEW',
                    'object_id': self.mock_review.review_id
                })
            )

        data = json.loads(response.content)
        self.assertTrue(data['userHasFlagged'])
        self.assertTrue(data['hasPendingFlags'])
        self.assertEqual(data['pendingFlagsCount'], 2)

    def test_invalid_content_type(self):
        """Test flag creation with invalid content type"""
        with patch('django.contrib.auth.middleware.get_user', return_value=self.regular_user):
            response = self.client.post(reverse('moderation:create_flag'), {
                'content_type': 'INVALID_TYPE',
                'object_id': 'test123',
                'reason': 'SPAM'
            })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('Invalid content type', data['error'])

    @patch('moderation.views.Post.objects.get')
    def test_nonexistent_content(self, mock_post_get):
        """Test flag creation for nonexistent content"""
        mock_post_get.side_effect = Post.DoesNotExist

        with patch('django.contrib.auth.middleware.get_user', return_value=self.regular_user):
            response = self.client.post(reverse('moderation:create_flag'), {
                'content_type': 'FORUM POST',
                'object_id': 'nonexistent',
                'reason': 'SPAM'
            })

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('not found', data['error'])

    @patch('moderation.views.Flag.objects.get')
    def test_review_flag_unauthorized(self, mock_flag_get):
        """Test that non-admin users cannot review flags"""
        mock_flag_get.return_value = MagicMock()

        with patch('django.contrib.auth.middleware.get_user', return_value=self.regular_user):
            response = self.client.post(
                reverse('moderation:review_flag', args=[1]),
                {'action': 'dismiss'}
            )

        self.assertEqual(response.status_code, 302)  # Should redirect