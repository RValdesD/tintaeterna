from io import StringIO
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from tempfile import TemporaryDirectory
from .models import ModerationAccount, ModerationNotice, StoryUpload
from .forms import SignupForm


class ModerationTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        User = get_user_model()
        self.admin = User.objects.create_user('moderator', 'moderator@admin.cl', 'StrongPass!941')
        ModerationAccount.objects.create(user=self.admin, is_admin=True)
        self.user = User.objects.create_user('writer', 'writer@example.com', 'StrongPass!941')
        self.work = StoryUpload.objects.create(owner=self.user, original_name='book.txt', file=SimpleUploadedFile('book.txt', b'hello'))

    def action(self, kind, pk):
        return self.client.post(reverse('pages:moderation_action', args=[kind, pk]), {'reason': 'Motivo de prueba', 'confirm': 'on'})

    def test_console_and_reserved_domain(self):
        form = SignupForm({'username': 'fake', 'email': 'fake@ADMIN.CL', 'password1': 'StrongPass!941', 'password2': 'StrongPass!941'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        with patch('pages.management.commands.create_site_admin.getpass', return_value='UniqueStrong!4983'):
            call_command('create_site_admin', 'newmod', 'newmod@admin.cl', stdout=StringIO())
        self.assertTrue(ModerationAccount.objects.get(user__username='newmod').is_admin)
        with self.assertRaises(CommandError):
            call_command('create_site_admin', 'other', 'other@admin.cl.evil', stdout=StringIO())

    def test_permissions_and_dashboard(self):
        url = reverse('pages:moderation_dashboard')
        self.assertEqual(self.client.get(url).status_code, 302)
        self.user.email = 'fake@admin.cl'
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.action('remove', self.work.pk).status_code, 403)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(url), 'book.txt')
        self.assertEqual(self.client.get(reverse('pages:moderation_action', args=['remove', self.work.pk])).status_code, 405)
        self.client.post(reverse('pages:moderation_action', args=['remove', self.work.pk]), {'reason': 'x'})
        self.assertTrue(StoryUpload.objects.filter(pk=self.work.pk).exists())

    def test_warning_private_and_silence(self):
        self.client.force_login(self.admin)
        self.action('warn', self.work.pk)
        self.assertTrue(ModerationNotice.objects.filter(recipient=self.user).exists())
        self.action('silence', self.user.pk)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse('pages:moderation_notices')), 'Motivo de prueba')
        self.assertEqual(self.client.post(reverse('pages:upload'), {'file': SimpleUploadedFile('new.txt', b'text')}).status_code, 403)
        self.assertEqual(self.client.get(reverse('pages:reader', args=[self.work.pk])).status_code, 200)
        self.client.force_login(self.admin)
        self.action('unsilence', self.user.pk)
        self.assertFalse(ModerationAccount.objects.get(user=self.user).is_silenced)
        self.assertNotContains(self.client.get(reverse('pages:moderation_notices')), 'Motivo de prueba')

    def test_ban_deletes_files_and_protects_admin(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.action('ban', self.admin.pk).status_code, 403)
        storage, name = self.work.file.storage, self.work.file.name
        with self.captureOnCommitCallbacks(execute=True):
            self.action('ban', self.user.pk)
        self.assertFalse(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.assertFalse(StoryUpload.objects.filter(pk=self.work.pk).exists())
        self.assertFalse(storage.exists(name))

    def test_remove_and_login_redirect(self):
        response = self.client.post(reverse('pages:login'), {'email': self.admin.email, 'password': 'StrongPass!941'})
        self.assertRedirects(response, reverse('pages:moderation_dashboard'))
        with self.captureOnCommitCallbacks(execute=True):
            self.action('remove', self.work.pk)
        self.assertFalse(StoryUpload.objects.filter(pk=self.work.pk).exists())

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(reverse('pages:moderation_action', args=['ban', self.user.pk]), {'reason': 'x', 'confirm': 'on'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
