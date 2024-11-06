# from django.test import TestCase

# Create your tests here.
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Post, Comment
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
