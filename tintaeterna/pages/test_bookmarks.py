from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import Bookmark, StoryUpload, Tag


class ReaderFeaturesTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username='author', email='author@example.com', password='test-password')
        self.other = get_user_model().objects.create_user(username='reader', password='test-password')
        self.story = StoryUpload.objects.create(owner=self.author, file='stories/example.txt', original_name='Story.txt')
        self.save_url = reverse('pages:save_bookmark', args=[self.story.pk])
        self.read_url = reverse('pages:reader', args=[self.story.pk])

    def test_public_reader_profiles_and_home(self):
        self.assertEqual(self.client.get(self.read_url).status_code, 200)
        response = self.client.get(reverse('pages:profile', args=[self.author.pk]))
        self.assertContains(response, 'Story.txt')
        self.assertNotContains(response, 'author@example.com')
        self.assertContains(self.client.get('/'), reverse('pages:demo_profile', args=['Autor1']))
        self.assertContains(self.client.get('/'), self.read_url)
        self.assertContains(self.client.get(reverse('pages:demo_profile', args=['Autor1'])), 'Perfil de ejemplo')
        self.assertEqual(self.client.get('/authors/demo/Unknown/').status_code, 404)

    def test_login_required_and_post_only(self):
        self.assertEqual(self.client.post(self.save_url, {'location': '2'}).status_code, 302)
        self.assertEqual(Bookmark.objects.count(), 0)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.save_url).status_code, 405)
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(self.other)
        self.assertEqual(secure_client.post(self.save_url, {'location': '2'}).status_code, 403)

    def test_save_update_restore_and_account_isolation(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.save_url, {'location': '2', 'user': self.author.pk}).status_code, 200)
        self.assertEqual(self.client.post(self.save_url, {'location': '3'}).status_code, 200)
        self.assertEqual(Bookmark.objects.count(), 1)
        self.assertEqual(Bookmark.objects.get().user, self.other)
        self.assertContains(self.client.get(self.read_url), '"3"</script>')
        self.assertContains(self.client.get(reverse('pages:bookmarks')), 'Story.txt')
        self.client.force_login(self.author)
        self.assertNotContains(self.client.get(reverse('pages:bookmarks')), 'Story.txt')
        self.client.post(reverse('pages:delete_bookmark', args=[self.story.pk]))
        self.assertEqual(Bookmark.objects.count(), 1)
        self.client.force_login(self.other)
        self.client.post(reverse('pages:delete_bookmark', args=[self.story.pk]))
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_invalid_positions_and_epub(self):
        self.client.force_login(self.other)
        for value in ['', '0', '-2', 'abc', '1.5', '9' * 2001]:
            self.assertEqual(self.client.post(self.save_url, {'location': value}).status_code, 400)
        self.story.file = 'stories/example.epub'
        self.story.save()
        cfi = 'epubcfi(/6/2!/4/2/1:0)'
        self.assertEqual(self.client.post(self.save_url, {'location': cfi}).status_code, 200)
        self.assertEqual(Bookmark.objects.get().location, cfi)
        self.assertEqual(self.client.post(self.save_url, {'location': 'https://example.com'}).status_code, 400)
        self.story.delete()
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_login_return_url_is_local(self):
        login_url = reverse('pages:login')
        self.assertRedirects(self.client.post(login_url, {'email': 'author@example.com', 'password': 'test-password', 'next': self.read_url}), self.read_url)
        self.client.logout()
        self.assertRedirects(self.client.post(login_url, {'email': 'author@example.com', 'password': 'test-password', 'next': 'https://example.com'}), '/')

    def test_tags_and_upload_template(self):
        tag = Tag.objects.create(name='Ciencia ficción')
        self.story.tags.add(tag)
        response = self.client.get('/')
        self.assertContains(response, 'data-tags="%s "' % tag.pk)
        self.assertContains(response, '<details id="tag-dropdown"')
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('pages:upload')), '<details class="upload-tags"')
