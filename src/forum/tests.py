# from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Notification, Post, Comment
from .forms import PostForm, CommentForm


class ForumModelsTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category", description="Test Description"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
            category=self.category,
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content="Test Comment"
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), "Test Category")

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test Post")

    def test_comment_str(self):
        expected = f"Comment by {self.user.username} on {self.post.title}"
        self.assertEqual(str(self.comment), expected)


class ForumViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category", description="Test Description"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
            category=self.category,
        )

    def test_category_list_view(self):
        response = self.client.get(reverse("forum:category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "category_list.html")

    def test_category_detail_view(self):
        response = self.client.get(
            reverse("forum:category_detail", args=[self.category.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "category_detail.html")

    def test_post_detail_view(self):
        response = self.client.get(reverse("forum:post_detail", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "post_detail.html")

    def test_create_post_view_authenticated(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("forum:create_post", args=[self.category.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_post.html")

    def test_create_post_view_unauthenticated(self):
        response = self.client.get(
            reverse("forum:create_post", args=[self.category.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_edit_post_authenticated_owner(self):
        self.client.login(username="testuser", password="testpass123")

        # Test GET request
        get_response = self.client.get(reverse("forum:edit_post", args=[self.post.id]))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.json(), {"title": "Test Post", "content": "Test Content"}
        )

        # Test POST request
        post_data = {"title": "Updated Post Title", "content": "Updated Content"}
        post_response = self.client.post(
            reverse("forum:edit_post", args=[self.post.id]), post_data
        )
        self.assertEqual(post_response.status_code, 302)  # Redirect after success

        # Verify the post was updated
        updated_post = Post.objects.get(id=self.post.id)
        self.assertEqual(updated_post.title, "Updated Post Title")
        self.assertEqual(updated_post.content, "Updated Content")

    def test_edit_post_authenticated_non_owner(self):
        # Create another user
        _ = get_user_model().objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.client.login(username="otheruser", password="testpass123")

        # Try to edit post
        response = self.client.post(
            reverse("forum:edit_post", args=[self.post.id]),
            {"title": "Malicious Edit", "content": "Malicious Content"},
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_edit_post_unauthenticated(self):
        response = self.client.post(
            reverse("forum:edit_post", args=[self.post.id]),
            {"title": "Malicious Edit", "content": "Malicious Content"},
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_edit_comment_authenticated_owner(self):
        # Create a comment
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="Original Comment"
        )

        # Login as comment owner
        self.client.login(username="testuser", password="testpass123")

        # Test GET request
        get_response = self.client.get(reverse("forum:edit_comment", args=[comment.id]))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), {"content": "Original Comment"})

        # Test POST request
        post_response = self.client.post(
            reverse("forum:edit_comment", args=[comment.id]),
            {"content": "Updated Comment Content"},
        )
        self.assertEqual(post_response.status_code, 302)  # Redirect after success

        # Verify the comment was updated
        updated_comment = Comment.objects.get(id=comment.id)
        self.assertEqual(updated_comment.content, "Updated Comment Content")

    def test_edit_comment_authenticated_non_owner(self):
        # Create a comment
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="Original Comment"
        )

        # Create and login as another user
        _ = get_user_model().objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.client.login(username="otheruser", password="testpass123")

        # Try to edit comment
        response = self.client.post(
            reverse("forum:edit_comment", args=[comment.id]),
            {"content": "Malicious Comment"},
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_edit_comment_unauthenticated(self):
        # Create a comment
        comment = Comment.objects.create(
            post=self.post, author=self.user, content="Original Comment"
        )

        response = self.client.post(
            reverse("forum:edit_comment", args=[comment.id]),
            {"content": "Malicious Comment"},
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login


class ForumFormsTest(TestCase):
    def test_post_form_valid(self):
        form_data = {"title": "Test Title", "content": "Test Content"}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_form_invalid(self):
        form_data = {"title": "", "content": "Test Content"}  # Title is required
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_comment_form_valid(self):
        form_data = {"content": "Test Comment"}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid(self):
        form_data = {"content": ""}  # Content is required
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())


class ForumDeleteCommentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = get_user_model().objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category", description="Test Description"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
            category=self.category,
        )
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content="Test Comment"
        )

    def test_delete_comment_authenticated_owner_post_request(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("forum:delete_comment", args=[self.comment.id])
        )
        self.assertRedirects(
            response, reverse("forum:post_detail", args=[self.post.id])
        )
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_authenticated_owner_get_request(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("forum:delete_comment", args=[self.comment.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_delete_comment_authenticated_non_owner(self):
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse("forum:delete_comment", args=[self.comment.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_unauthenticated(self):
        response = self.client.post(
            reverse("forum:delete_comment", args=[self.comment.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())


class ForumNotificationsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.recipient = get_user_model().objects.create_user(
            username="recipient", email="recipient@example.com", password="testpass123"
        )
        self.sender = get_user_model().objects.create_user(
            username="sender", email="sender@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category", description="Test Description"
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.recipient,
            category=self.category,
        )
        self.notification = Notification.objects.create(
            recipient=self.recipient,
            sender=self.sender,
            post=self.post,
            message="Test Notification",
        )

    def test_mark_notification_read_authenticated_ajax(self):
        self.client.login(username="recipient", password="testpass123")
        response = self.client.post(
            reverse("forum:mark_notification_read", args=[self.notification.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertJSONEqual(response.content, {"status": "success"})

    def test_mark_notification_read_authenticated_non_recipient(self):
        self.client.login(username="sender", password="testpass123")
        response = self.client.post(
            reverse("forum:mark_notification_read", args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 404)  # Not found

    def test_mark_notification_read_unauthenticated(self):
        response = self.client.post(
            reverse("forum:mark_notification_read", args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_get_notifications_count_authenticated(self):
        self.client.login(username="recipient", password="testpass123")
        response = self.client.get(reverse("forum:get_notifications_count"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"count": 1})

    def test_get_notifications_count_unauthenticated(self):
        response = self.client.get(reverse("forum:get_notifications_count"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_mark_all_notifications_read_authenticated_ajax(self):
        # Create another unread notification
        Notification.objects.create(
            recipient=self.recipient,
            sender=self.sender,
            post=self.post,
            message="Another Test Notification",
        )
        self.client.login(username="recipient", password="testpass123")
        response = self.client.post(
            reverse("forum:mark_all_notifications_read"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success"})
        self.assertTrue(
            Notification.objects.filter(recipient=self.recipient, is_read=False).count()
            == 0
        )

    def test_mark_all_notifications_read_authenticated_non_ajax(self):
        # Create another unread notification
        Notification.objects.create(
            recipient=self.recipient,
            sender=self.sender,
            post=self.post,
            message="Another Test Notification",
        )
        self.client.login(username="recipient", password="testpass123")
        response = self.client.post(reverse("forum:mark_all_notifications_read"))
        self.assertEqual(response.status_code, 302)  # Redirect back
        self.assertTrue(
            Notification.objects.filter(recipient=self.recipient, is_read=False).count()
            == 0
        )

    def test_mark_all_notifications_read_authenticated_invalid_method(self):
        self.client.login(username="recipient", password="testpass123")
        response = self.client.get(reverse("forum:mark_all_notifications_read"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_mark_all_notifications_read_unauthenticated(self):
        response = self.client.post(reverse("forum:mark_all_notifications_read"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_delete_notification_authenticated_ajax(self):
        self.client.login(username="recipient", password="testpass123")
        response = self.client.post(
            reverse("forum:delete_notification", args=[self.notification.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success"})
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

    def test_delete_notification_authenticated_non_recipient(self):
        self.client.login(username="sender", password="testpass123")
        response = self.client.post(
            reverse("forum:delete_notification", args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 404)  # Not found
        self.assertTrue(Notification.objects.filter(id=self.notification.id).exists())

    def test_delete_notification_unauthenticated(self):
        response = self.client.post(
            reverse("forum:delete_notification", args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(Notification.objects.filter(id=self.notification.id).exists())

    def test_delete_notification_authenticated_invalid_method(self):
        self.client.login(username="recipient", password="testpass123")
        response = self.client.get(
            reverse("forum:delete_notification", args=[self.notification.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden


class ForumProfanityFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.category = Category.objects.create(
            name="Test Category", description="Test Description"
        )

    def test_post_form_profanity_filter(self):
        """Test that profanity is filtered in both title and content of posts"""
        form_data = {
            "title": "This is a shit title",
            "content": "This damn post content with asshole words",
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        # Check title is censored
        self.assertIn("****", cleaned_data["title"])
        self.assertNotIn("shit", cleaned_data["title"])

        # Check content is censored
        self.assertIn("****", cleaned_data["content"])
        self.assertNotIn("damn", cleaned_data["content"])
        self.assertNotIn("asshole", cleaned_data["content"])

    def test_comment_form_profanity_filter(self):
        """Test that profanity is filtered in comment content"""
        form_data = {"content": "This is a shit comment with damn bad words"}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        self.assertIn("****", cleaned_data["content"])
        self.assertNotIn("shit", cleaned_data["content"])
        self.assertNotIn("damn", cleaned_data["content"])

    def test_post_creation_with_profanity(self):
        """Test that profanity is filtered when creating a new post"""
        self.client.login(username="testuser", password="testpass123")

        post_data = {"title": "A shit title", "content": "Some damn content"}

        response = self.client.post(
            reverse("forum:create_post", args=[self.category.id]), post_data
        )

        # Check if post was created and redirected
        self.assertEqual(response.status_code, 302)

        # Get the created post
        post = Post.objects.latest("created_at")

        # Verify profanity was filtered
        self.assertIn("****", post.title)
        self.assertNotIn("shit", post.title)
        self.assertIn("****", post.content)
        self.assertNotIn("damn", post.content)

    def test_comment_creation_with_profanity(self):
        """Test that profanity is filtered when creating a new comment"""
        self.client.login(username="testuser", password="testpass123")

        # Create a post first
        post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
            category=self.category,
        )

        comment_data = {"content": "This is a shit comment"}

        response = self.client.post(
            reverse("forum:post_detail", args=[post.id]), comment_data
        )

        # Check if comment was created and redirected
        self.assertEqual(response.status_code, 302)

        # Get the created comment
        comment = Comment.objects.latest("created_at")

        # Verify profanity was filtered
        self.assertIn("****", comment.content)
        self.assertNotIn("shit", comment.content)

    def test_post_form_mixed_case_profanity(self):
        """Test that profanity filtering is case-insensitive"""
        form_data = {"title": "A ShIt TiTlE", "content": "Some DaMn CoNtEnT"}

        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        # Check title is censored regardless of case
        self.assertIn("****", cleaned_data["title"])
        self.assertNotIn("ShIt", cleaned_data["title"])

        # Check content is censored regardless of case
        self.assertIn("****", cleaned_data["content"])
        self.assertNotIn("DaMn", cleaned_data["content"])

    def test_post_form_no_profanity(self):
        """Test that clean content remains unchanged"""
        form_data = {"title": "A clean title", "content": "Some clean content"}

        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_data = form.cleaned_data

        # Check content remains unchanged
        self.assertEqual(cleaned_data["title"], "A clean title")
        self.assertEqual(cleaned_data["content"], "Some clean content")

    def test_edit_post_with_profanity(self):
        """Test that profanity is filtered when editing a post"""
        self.client.login(username="testuser", password="testpass123")

        # Create a clean post first
        post = Post.objects.create(
            title="Clean Title",
            content="Clean Content",
            author=self.user,
            category=self.category,
        )

        # Try to edit with profanity
        edit_data = {"title": "A shit title", "content": "Some damn content"}

        response = self.client.post(
            reverse("forum:edit_post", args=[post.id]), edit_data
        )

        # Check if post was updated and redirected
        self.assertEqual(response.status_code, 302)

        # Get the updated post
        post.refresh_from_db()

        # Verify profanity was filtered
        self.assertIn("****", post.title)
        self.assertNotIn("shit", post.title)
        self.assertIn("****", post.content)
        self.assertNotIn("damn", post.content)

    def test_edit_comment_with_profanity(self):
        """Test that profanity is filtered when editing a comment"""
        self.client.login(username="testuser", password="testpass123")

        # Create a post and clean comment first
        post = Post.objects.create(
            title="Test Post",
            content="Test Content",
            author=self.user,
            category=self.category,
        )

        comment = Comment.objects.create(
            post=post, author=self.user, content="Clean comment"
        )

        # Try to edit with profanity
        edit_data = {"content": "This is a shit comment"}

        response = self.client.post(
            reverse("forum:edit_comment", args=[comment.id]), edit_data
        )

        # Check if comment was updated and redirected
        self.assertEqual(response.status_code, 302)

        # Get the updated comment
        comment.refresh_from_db()

        # Verify profanity was filtered
        self.assertIn("****", comment.content)
        self.assertNotIn("shit", comment.content)
