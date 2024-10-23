from unittest.mock import patch

from allauth.socialaccount.models import SocialApp
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser


class RootRedirectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass123"
        )
        patcher = patch("allauth.socialaccount.models.SocialApp.objects.get")
        self.mock_get = patcher.start()
        self.mock_get.return_value = SocialApp(
            provider="google", name="Google", client_id="dummy", secret="dummy"
        )
        self.addCleanup(patcher.stop)

    def test_root_redirect_authenticated(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("root_redirect"))
        self.assertRedirects(response, reverse("home"))
