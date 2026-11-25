from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class LoginRedirectTests(TestCase):
    def test_plain_login(self):
        response = self.client.get(reverse('pages:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next" value=""')

    def test_next_in_get(self):
        response = self.client.get(reverse('pages:login'), {'next': '/bookmarks/'})
        self.assertContains(response, 'name="next" value="/bookmarks/"')

    def test_invalid_post_retains_next(self):
        response = self.client.post(reverse('pages:login'), {'email': 'invalid', 'next': '/bookmarks/'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next" value="/bookmarks/"')

    def test_invalid_post_without_next(self):
        self.assertEqual(self.client.post(reverse('pages:login'), {}).status_code, 200)

    def test_redirects_and_external_url_rejected(self):
        get_user_model().objects.create_user(username='test', email='test@example.com', password='test-password')
        for target, expected in [('/bookmarks/', '/bookmarks/'), ('https://example.com', '/'), ('', '/')]:
            self.client.logout()
            response = self.client.post(reverse('pages:login'), {'email':'test@example.com', 'password':'test-password', 'next':target})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, expected)
