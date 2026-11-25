from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import StoryUpload


class StoryCardTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = override_settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.owner = get_user_model().objects.create_user(username='Ana')
        self.other = get_user_model().objects.create_user(username='Other')
        self.story = StoryUpload.objects.create(owner=self.owner, file='test.txt', original_name='test.txt')
        self.edit_url = reverse('pages:edit_story_presentation', args=[self.story.pk])

    def picture(self):
        out = BytesIO()
        Image.new('RGB', (30, 50), 'red').save(out, 'JPEG')
        return SimpleUploadedFile('cover.jpg', out.getvalue(), content_type='image/jpeg')

    def test_owner_can_edit_and_image_is_public(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.edit_url, {'title': 'Mi historia', 'cover': self.picture()}).status_code, 302)
        self.story.refresh_from_db()
        old = self.story.cover.name
        self.client.post(self.edit_url, {'title': 'Nuevo título'})
        self.story.refresh_from_db()
        self.assertEqual(self.story.cover.name, old)
        self.client.logout()
        response = self.client.get(reverse('pages:story_cover', args=[self.story.pk]))
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'\x89PNG'))
        home = self.client.get('/')
        self.assertContains(home, '<h3 class="story-title">Nuevo título</h3>')
        self.assertContains(home, 'alt="Portada de Nuevo título"')
        self.assertNotContains(home, 'name="cover"')

    def test_reject_invalid_image_and_other_owner(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.edit_url, {'title': 'Hijacked'}).status_code, 404)
        self.client.force_login(self.owner)
        response = self.client.post(self.edit_url, {'title': 'Bad', 'cover': SimpleUploadedFile('bad.png', b'invalid')})
        self.assertEqual(response.status_code, 200)
        self.story.refresh_from_db()
        self.assertEqual(self.story.title, '')

    def test_new_upload_with_cover_and_title(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('pages:upload'), {'title': 'Nueva obra', 'file': SimpleUploadedFile('new.txt', b'Hola mundo'), 'cover': self.picture()})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StoryUpload.objects.get(title='Nueva obra').cover)
