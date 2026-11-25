from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import StoryUpload


class WorkContentsTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username='writer')
        self.story = StoryUpload.objects.create(owner=self.author, file='story.txt', original_name='Story.txt', title='My work', description='<script>unsafe</script>')

    def test_public_contents_and_escaped_description(self):
        response = self.client.get(reverse('pages:work_detail', args=[self.story.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My work')
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertContains(response, reverse('pages:reader_file', args=[self.story.pk]))
        self.assertContains(response, 'data-format="txt"')

    def test_home_thumbnail_and_author_destinations(self):
        response = self.client.get('/')
        self.assertContains(response, 'href="'+reverse('pages:work_detail', args=[self.story.pk])+'"')
        self.assertContains(response, 'href="'+reverse('pages:profile', args=[self.author.pk])+'"')
        self.assertContains(response, 'href="'+reverse('pages:sample_work', args=[1])+'"')

    def test_sample_is_specific_and_missing_work_is_404(self):
        response = self.client.get(reverse('pages:sample_work', args=[1]))
        self.assertContains(response, 'Comment te dire Adieu')
        self.assertContains(response, 'aún no tiene capítulos')
        self.assertEqual(self.client.get('/works/sample/999/').status_code, 404)
        self.assertEqual(self.client.get('/works/999/').status_code, 404)

    def test_description_edit_and_reader_back_link(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('pages:edit_story_presentation', args=[self.story.pk]), {'title':'My work','description':'New description'})
        self.assertEqual(response.status_code, 302)
        self.story.refresh_from_db()
        self.assertEqual(self.story.description, 'New description')
        self.assertContains(self.client.get(reverse('pages:reader', args=[self.story.pk])), 'href="'+reverse('pages:work_detail', args=[self.story.pk])+'"')
