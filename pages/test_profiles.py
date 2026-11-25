from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Profile, StoryUpload


class ProfileTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.ana = get_user_model().objects.create_user(username='Ana')
        self.bob = get_user_model().objects.create_user(username='Bob')
        self.url = reverse('pages:profile', args=[self.ana.pk])

    def picture(self, name='photo.png'):
        content = BytesIO()
        Image.new('RGB', (32, 32), 'red').save(content, 'PNG')
        return SimpleUploadedFile(name, content.getvalue(), content_type='image/png')

    def test_menu_and_existing_account_without_profile(self):
        self.client.force_login(self.ana)
        home = self.client.get('/')
        self.assertContains(home, 'class="account-menu"')
        self.assertContains(home, 'Mi perfil')
        self.assertRedirects(self.client.get(reverse('pages:my_profile')), self.url)
        response = self.client.get(self.url)
        self.assertContains(response, 'Sin descripción.')
        self.assertContains(response, 'Cambiar foto de perfil')
        self.assertContains(response, 'Obras publicadas')

    def test_own_description_and_public_privacy(self):
        self.client.force_login(self.ana)
        self.client.post(reverse('pages:edit_profile'), {'description': '<script>alert(1)</script>', 'user': self.bob.pk})
        self.assertEqual(Profile.objects.get(user=self.ana).description, '<script>alert(1)</script>')
        self.assertFalse(Profile.objects.filter(user=self.bob).exists())
        self.client.logout()
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, 'Editar descripción')
        self.assertNotContains(response, 'Cambiar foto de perfil')
        for route in ['edit_profile', 'edit_profile_picture', 'my_profile']:
            self.assertEqual(self.client.get(reverse('pages:'+route)).status_code, 302)

    def test_photo_upload_public_serving_and_replacement(self):
        self.client.force_login(self.ana)
        url = reverse('pages:edit_profile_picture')
        response = self.client.post(url, {'avatar': self.picture(), 'user': self.bob.pk})
        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user=self.ana)
        old = profile.avatar.name
        response = self.client.get(reverse('pages:profile_picture', args=[self.ana.pk]))
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'\x89PNG'))
        self.client.post(url, {'avatar': self.picture()})
        profile.refresh_from_db()
        self.assertNotEqual(old, profile.avatar.name)
        self.assertFalse(profile.avatar.storage.exists(old))
        self.assertFalse(Profile.objects.filter(user=self.bob).exists())

    def test_invalid_image_and_description(self):
        self.client.force_login(self.ana)
        response = self.client.post(reverse('pages:edit_profile_picture'), {'avatar': SimpleUploadedFile('bad.png', b'<script>bad</script>')})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.ana).avatar)
        response = self.client.post(reverse('pages:edit_profile'), {'description': 'x' * 1001})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Profile.objects.get(user=self.ana).description, '')

    def test_only_authors_works(self):
        StoryUpload.objects.create(owner=self.ana, original_name='Ana.txt', file='ana.txt')
        StoryUpload.objects.create(owner=self.bob, original_name='Bob.txt', file='bob.txt')
        response = self.client.get(self.url)
        self.assertContains(response, 'Ana.txt')
        self.assertNotContains(response, 'Bob.txt')
