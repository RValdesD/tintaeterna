"""Consolidated TintaEterna tests. Run with: python manage.py test pages.tests.

Remove the original test_*.py modules listed below after installing this file
to avoid discovering each test twice. Test assertions are preserved unchanged.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from .models import Bookmark, StoryUpload, Tag, StoryChapter, Profile, ProfileComment, Comentarios, ModerationAccount, ModerationNotice
from io import BytesIO, StringIO
from tempfile import TemporaryDirectory
from django.contrib.auth.models import User, AnonymousUser, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfWriter
from unittest.mock import patch
from .forms import SignupForm
from .recommendations import recommended_cards
from django.core.management import call_command, CommandError
from PIL import Image
from .templatetags.profile_bbcode import bbcode
from django.utils.text import slugify
from .views import sample_stories


# ========================================================================
# Originally: test_bookmarks.py
# ========================================================================

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


# ========================================================================
# Originally: test_catalog.py
# ========================================================================

class CatalogTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user('writer')
        for i in range(23):
            StoryUpload.objects.create(owner=user, title=f'Upload {i}', original_name=f'{i}.txt', file=f'stories/{i}.txt')

    def test_recent_pagination_and_home(self):
        self.assertNotContains(self.client.get(reverse('pages:home')), 'Escritos publicados')
        self.assertNotContains(self.client.get(reverse('pages:home')), 'Upload 22')
        response = self.client.get(reverse('pages:recent'))
        self.assertEqual(len(response.context['sections'][0]['stories']), 20)
        self.assertEqual(response.context['sections'][0]['stories'][0]['title'], 'Upload 22')
        self.assertContains(response, 'Página siguiente')
        response = self.client.get(reverse('pages:recent'), {'page': 2})
        self.assertEqual(len(response.context['sections'][0]['stories']), 3)
        self.assertEqual(self.client.get(reverse('pages:recent'), {'page': 'bad'}).status_code, 200)

    def test_search_across_pages(self):
        response = self.client.get(reverse('pages:recent'), {'q': 'Upload 0'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertContains(response, 'Upload 0')

    def test_popular_uses_home_samples(self):
        home = self.client.get(reverse('pages:home'))
        popular = self.client.get(reverse('pages:popular'))
        self.assertEqual([s['title'] for s in home.context['sections'][0]['stories']], [s['title'] for s in popular.context['sections'][0]['stories']])
        self.assertContains(popular, 'Todo el tiempo')
        self.assertNotContains(popular, 'Upload 22')


# ========================================================================
# Originally: test_chapters.py
# ========================================================================

def pdf(pages=6):
    stream=BytesIO(); writer=PdfWriter()
    for _ in range(pages): writer.add_blank_page(width=100,height=100)
    writer.write(stream)
    return SimpleUploadedFile('book.pdf',stream.getvalue(),content_type='application/pdf')


class ChapterTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        override=override_settings(MEDIA_ROOT=self.tmp.name);override.enable();self.addCleanup(override.disable)
        self.user=User.objects.create_user('author')
        self.story=StoryUpload.objects.create(owner=self.user,title='Book',file=pdf(),original_name='book.pdf')
        self.url=reverse('pages:edit_story',args=[self.story.pk]); self.client.force_login(self.user)

    def payload(self, rows):
        data={'title':'Book','chapters-TOTAL_FORMS':str(len(rows)),'chapters-INITIAL_FORMS':str(self.story.chapters.count())}
        for i,row in enumerate(rows):
            for key,value in row.items():data[f'chapters-{i}-{key}']=value
        return data

    def row(self,start=1,end=3):return {'title':'Chapter one','start_page':start,'end_page':end}

    def test_save_and_public_links(self):
        response=self.client.post(self.url,self.payload([self.row(),self.row(4,6)]))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.story.chapters.count(),2)
        self.client.logout()
        page=self.client.get(reverse('pages:work_detail',args=[self.story.pk]))
        self.assertContains(page,'?page=4')
        self.assertNotContains(page,'work-toc.js')
        self.assertEqual(self.client.get(reverse('pages:reader',args=[self.story.pk])+'?page=4').status_code,200)

    def test_invalid_ranges(self):
        for rows in [[self.row(0,2)],[self.row(3,2)],[self.row(1,7)],[self.row(1,3),self.row(3,6)]]:
            with self.subTest(rows=rows):
                response=self.client.post(self.url,self.payload(rows))
                self.assertEqual(response.status_code,200)
                self.assertFalse(response.context['chapters'].is_valid())
                self.assertEqual(self.story.chapters.count(),0)

    def test_replacement_revalidates_without_mutating(self):
        chapter=StoryChapter.objects.create(story=self.story,**self.row(1,6))
        old=self.story.file.name
        data=self.payload([self.row(1,6)]);data['file']=pdf(2)
        response=self.client.post(self.url,data)
        self.assertEqual(response.status_code,200)
        self.story.refresh_from_db()
        self.assertEqual(self.story.file.name,old)
        self.assertTrue(self.story.chapters.filter(pk=chapter.pk).exists())

    def test_delete_restores_automatic_and_nonpdf_requires_delete(self):
        StoryChapter.objects.create(story=self.story,**self.row())
        data=self.payload([self.row()]);data['file']=SimpleUploadedFile('text.txt',b'text')
        self.assertEqual(self.client.post(self.url,data).status_code,200)
        data=self.payload([{**self.row(),'DELETE':'on'}])
        self.assertEqual(self.client.post(self.url,data).status_code,302)
        self.assertEqual(self.story.chapters.count(),0)
        self.assertContains(self.client.get(reverse('pages:work_detail',args=[self.story.pk])),'work-toc.js')

    def test_invalid_pdf_and_permission(self):
        data=self.payload([self.row()]);data['file']=SimpleUploadedFile('broken.pdf',b'%PDF-broken')
        self.assertEqual(self.client.post(self.url,data).status_code,200)
        self.client.force_login(User.objects.create_user('other'))
        self.assertEqual(self.client.post(self.url,self.payload([self.row()])).status_code,404)


# ========================================================================
# Originally: test_comment_deletion.py
# ========================================================================

class CommentDeletionTests(TestCase):
    def setUp(self):
        self.author=User.objects.create_user('author')
        self.other=User.objects.create_user('other')
        self.admin=User.objects.create_user('moderator',email='moderator@admin.cl')
        ModerationAccount.objects.create(user=self.admin,is_admin=True)
        self.story=StoryUpload.objects.create(owner=self.other,file='stories/test.txt')
        self.profile=Profile.objects.create(user=self.other)

    def create_comment(self,kind):
        if kind=='reader':return Comentarios.objects.create(author=self.author,nombre='author',texto='hello',historia=self.story)
        return ProfileComment.objects.create(profile=self.profile,sender=self.author,text='hello')

    def test_own_and_admin_deletion_both_types(self):
        for kind in ['reader','profile']:
            for user in [self.author,self.admin]:
                comment=self.create_comment(kind)
                self.client.force_login(user)
                response=self.client.post(reverse('pages:delete_'+kind+'_comment',args=[comment.pk]))
                self.assertEqual(response.status_code,302)
                self.assertFalse(type(comment).objects.filter(pk=comment.pk).exists())

    def test_others_get_anonymous_and_csrf(self):
        for kind in ['reader','profile']:
            comment=self.create_comment(kind)
            url=reverse('pages:delete_'+kind+'_comment',args=[comment.pk])
            self.client.force_login(self.other)
            self.assertEqual(self.client.post(url).status_code,403)
            self.client.force_login(self.author)
            self.assertEqual(self.client.get(url).status_code,405)
            secure=Client(enforce_csrf_checks=True);secure.force_login(self.author)
            self.assertEqual(secure.post(url).status_code,403)
            self.client.logout();self.assertEqual(self.client.post(url).status_code,302)
            self.assertTrue(type(comment).objects.filter(pk=comment.pk).exists())

    def test_legacy_not_claimed_by_name_and_fake_admin(self):
        comment=Comentarios.objects.create(nombre='author',texto='old',historia=self.story)
        url=reverse('pages:delete_reader_comment',args=[comment.pk])
        self.client.force_login(self.author);self.assertEqual(self.client.post(url).status_code,403)
        fake=User.objects.create_user('fake',email='fake@admin.cl')
        self.client.force_login(fake);self.assertEqual(self.client.post(url).status_code,403)
        self.client.force_login(self.admin);self.assertEqual(self.client.post(url).status_code,302)

    def test_reply_survives_and_buttons_are_scoped(self):
        comment=self.create_comment('profile')
        reply=ProfileComment.objects.create(profile=self.profile,sender=self.other,parent=comment,text='reply')
        url=reverse('pages:delete_profile_comment',args=[comment.pk])
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('pages:profile',args=[self.other.pk])),url)
        self.client.post(url)
        reply.refresh_from_db();self.assertIsNone(reply.parent_id)

    def test_reader_records_account_and_renders_button(self):
        self.client.force_login(self.author)
        self.client.post(reverse('pages:reader',args=[self.story.pk]),{'texto':'new'})
        comment=Comentarios.objects.get()
        self.assertEqual(comment.author_id,self.author.pk)
        url=reverse('pages:delete_reader_comment',args=[comment.pk])
        self.assertContains(self.client.get(reverse('pages:reader',args=[self.story.pk])),url)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('pages:reader',args=[self.story.pk])),url)


# ========================================================================
# Originally: test_gustos.py
# ========================================================================

class GustosTests(TestCase):
    def setUp(self):
        self.a=Tag.objects.create(name='Fantasía')
        self.b=Tag.objects.create(name='Misterio')
        self.c=Tag.objects.create(name='Romance')
        self.owner=User.objects.create_user('writer')
        self.user=User.objects.create_user('reader')
        self.profile=Profile.objects.create(user=self.user)
        self.one=StoryUpload.objects.create(owner=self.owner,title='Matching',file='stories/one.txt')
        self.one.tags.set([self.a,self.b])
        self.two=StoryUpload.objects.create(owner=self.owner,title='Other',file='stories/two.txt')
        self.two.tags.set([self.c])
        self.draft=StoryUpload.objects.create(owner=self.owner,title='Draft')
        self.draft.tags.set([self.a])

    def test_signup_saves_optional_preferences(self):
        data={'username':'newreader','email':'new@example.com','password1':'Some-random-pass-839!','password2':'Some-random-pass-839!','gustos':[self.a.pk,self.b.pk]}
        response=self.client.post(reverse('pages:signup'),data)
        self.assertEqual(response.status_code,302)
        user=User.objects.get(username='newreader')
        self.assertEqual(set(user.profile.gustos.all()),{self.a,self.b})
        data.update(username='second',email='second@example.com');data.pop('gustos')
        response=self.client.post(reverse('pages:signup'),data)
        self.assertEqual(response.status_code,302)
        self.assertFalse(User.objects.get(username='second').profile.gustos.exists())

    def test_settings_update_clear_and_privacy(self):
        self.client.force_login(self.user)
        response=self.client.post(reverse('pages:account_settings'),{'description':'About','gustos':[self.a.pk]})
        self.assertEqual(response.status_code,302)
        self.assertEqual(list(self.profile.gustos.all()),[self.a])
        self.assertContains(self.client.get(reverse('pages:account_settings')),'gustos-picker')
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('pages:profile',args=[self.user.pk])),'gustos-picker')
        self.client.post(reverse('pages:account_settings'),{'gustos':[self.b.pk]})
        self.assertEqual(list(self.profile.gustos.all()),[self.a])
        self.client.force_login(self.user)
        self.client.post(reverse('pages:account_settings'),{'description':'About'})
        self.assertFalse(self.profile.gustos.exists())

    def test_recommendations_match_any_without_duplicates(self):
        self.profile.gustos.set([self.a,self.b])
        cards=recommended_cards(self.user)
        self.assertEqual([c['title'] for c in cards],['Matching'])
        self.client.force_login(self.user)
        response=self.client.get(reverse('pages:home'))
        self.assertEqual(response.context['sections'][1]['stories'][0]['title'],'Matching')
        self.assertIn('no-store',response['Cache-Control'])
        self.profile.gustos.set([Tag.objects.create(name='No matches')])
        self.assertEqual(recommended_cards(self.user),[])

    def test_random_fallback_pool_and_limit(self):
        for i in range(7):StoryUpload.objects.create(owner=self.owner,title=f'Work {i}',file=f'stories/{i}.txt')
        # Verify random ordering without probabilistic assertions about two shuffles.
        from django.db.models.query import QuerySet
        original=QuerySet.order_by
        calls=[]
        def order(query,*fields):
            calls.append(fields)
            return original(query,*fields)
        with patch.object(QuerySet,'order_by',order):
            for user in [self.user,AnonymousUser()]:
                cards=recommended_cards(user)
                self.assertEqual(len(cards),5)
                self.assertNotIn('Draft',[c['title'] for c in cards])
        self.assertIn(('?',),calls)

    def test_invalid_tag_rejected(self):
        self.client.force_login(self.user)
        response=self.client.post(reverse('pages:account_settings'),{'gustos':['999999']})
        self.assertEqual(response.status_code,200)
        self.assertIn('gustos',response.context['form'].errors)


# ========================================================================
# Originally: test_login.py
# ========================================================================

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


# ========================================================================
# Originally: test_moderation.py
# ========================================================================

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


# ========================================================================
# Originally: test_profile_revamp.py
# ========================================================================

class ProfileRevampTests(TestCase):
    def setUp(self):
        self.media=TemporaryDirectory();self.addCleanup(self.media.cleanup)
        setting=override_settings(MEDIA_ROOT=self.media.name);setting.enable();self.addCleanup(setting.disable)
        self.owner=get_user_model().objects.create_user('author')
        self.sender=get_user_model().objects.create_user('reader')
        self.profile=Profile.objects.create(user=self.owner, description='[b]Hola[/b]')
        self.url=reverse('pages:profile',args=[self.owner.pk])

    def image(self):
        stream=BytesIO();Image.new('RGB',(30,20)).save(stream,'PNG')
        return SimpleUploadedFile('image.png',stream.getvalue(),content_type='image/png')

    def test_settings_images_and_ownership(self):
        self.client.force_login(self.sender)
        response=self.client.post(reverse('pages:account_settings'),{'description':'[i]Bio[/i]','avatar':self.image(),'banner':self.image(),'user':self.owner.pk})
        self.assertEqual(response.status_code,302)
        profile=Profile.objects.get(user=self.sender)
        self.assertTrue(profile.avatar);self.assertTrue(profile.banner)
        self.profile.refresh_from_db();self.assertEqual(self.profile.description,'[b]Hola[/b]')
        self.assertEqual(self.client.get(reverse('pages:profile_banner',args=[self.sender.pk])).status_code,200)
        response=self.client.post(reverse('pages:account_settings'),{'description':'x','banner':SimpleUploadedFile('bad.png',b'bad',content_type='image/png')})
        self.assertEqual(response.status_code,200);self.assertTrue(response.context['form'].errors)

    def test_comments_replies_and_sender(self):
        self.assertEqual(self.client.post(self.url,{'text':'hello'}).status_code,302)
        self.assertEqual(ProfileComment.objects.count(),0)
        self.client.force_login(self.sender)
        self.client.post(self.url,{'text':'Hello','sender':self.owner.pk})
        comment=ProfileComment.objects.get();self.assertEqual(comment.sender,self.sender)
        self.client.post(self.url,{'text':'Reply','parent':comment.pk})
        self.assertEqual(ProfileComment.objects.last().parent,comment)
        other=Profile.objects.create(user=self.sender)
        wrong=ProfileComment.objects.create(profile=other,sender=self.sender,text='other')
        self.assertEqual(self.client.post(self.url,{'text':'bad','parent':wrong.pk}).status_code,404)
        response=self.client.get(self.url)
        self.assertContains(response,'Responder');self.assertContains(response,'En respuesta a')

    def test_silence_csrf_and_pagination(self):
        self.client.force_login(self.sender)
        ModerationAccount.objects.create(user=self.sender,is_silenced=True)
        self.assertEqual(self.client.post(self.url,{'text':'blocked'}).status_code,403)
        self.assertEqual(self.client.post(reverse('pages:account_settings'),{'description':'blocked'}).status_code,403)
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.post(self.url,{'text':'blocked'}).status_code,403)
        for i in range(22):ProfileComment.objects.create(profile=self.profile,sender=self.owner,text=str(i))
        response=self.client.get(self.url,{'page':2})
        self.assertContains(response,'start="21"');self.assertEqual(len(response.context['comments_page']),2)

    def test_bbcode_and_work_links(self):
        rendered=str(bbcode('[b]Hi[/b]<script>alert(1)</script>[img]x[/img]'))
        self.assertIn('<strong>Hi</strong>',rendered);self.assertNotIn('<script>',rendered);self.assertNotIn('<img',rendered)
        work=StoryUpload.objects.create(owner=self.owner,title='My work',original_name='a.txt',file='a.txt')
        response=self.client.get(self.url)
        self.assertContains(response,reverse('pages:work_detail',args=[work.pk]));self.assertContains(response,'<strong>Hola</strong>')


# ========================================================================
# Originally: test_profiles.py
# ========================================================================

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


# ========================================================================
# Originally: test_sample_work_links.py
# ========================================================================

class SampleWorkTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        group = Group.objects.create(name='Autores de ejemplo')
        popular, recommended, _ = sample_stories()
        for item in popular + recommended:
            user, _ = User.objects.get_or_create(username=slugify(item['author']), defaults={'first_name': item['author']})
            user.groups.add(group)
        call_command('seed_sample_works', stdout=StringIO())
        self.owner = User.objects.get(username='killerqueen')
        self.story = StoryUpload.objects.get(owner=self.owner)
        self.edit = reverse('pages:edit_story', args=[self.story.pk])

    def test_seed_repeat_and_static_cover(self):
        count = StoryUpload.objects.count()
        call_command('seed_sample_works', stdout=StringIO())
        self.assertEqual(StoryUpload.objects.count(), count)
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, '/static/public/images/obra5.png')
        self.assertContains(response, reverse('pages:work_detail', args=[self.story.pk]))
        self.assertContains(self.client.get(reverse('pages:work_detail', args=[self.story.pk])), 'aún no tiene contenido')
        self.assertNotContains(self.client.get(reverse('pages:recent')), 'Carta Blanca')

    def test_owner_upload_updates_same_story(self):
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('pages:my_profile'), follow=True), self.edit)
        page = self.client.get(reverse('pages:work_detail', args=[self.story.pk]))
        self.assertContains(page, self.edit)
        self.assertNotContains(page, '<img')
        self.assertNotContains(page, 'work-toc.js')
        response = self.client.post(self.edit, {'title': 'Carta Blanca', 'description': 'Descripción',
            'file': SimpleUploadedFile('carta.txt', b'Capitulo uno')})
        self.assertRedirects(response, reverse('pages:work_detail', args=[self.story.pk]))
        self.story.refresh_from_db()
        name = self.story.file.name
        self.assertTrue(name)
        self.assertEqual(self.story.sample_cover, 'public/images/obra5.png')
        self.assertEqual(StoryUpload.objects.filter(owner=self.owner).count(), 1)
        self.assertEqual(self.client.get(reverse('pages:reader', args=[self.story.pk])).status_code, 200)
        page = self.client.get(reverse('pages:work_detail', args=[self.story.pk]))
        self.assertContains(page, self.edit)
        self.assertContains(page, 'work-toc.js')
        self.assertNotContains(page, '<img')
        self.client.logout()
        self.assertNotContains(self.client.get(reverse('pages:work_detail', args=[self.story.pk])), self.edit)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('pages:recent')), 'Carta Blanca')
        response = self.client.post(self.edit, {'title': 'Nuevo título', 'description': 'Nueva descripción'})
        self.assertEqual(response.status_code, 302)
        self.story.refresh_from_db()
        self.assertEqual(self.story.file.name, name)
        call_command('seed_sample_works', stdout=StringIO())
        self.story.refresh_from_db()
        self.assertEqual(self.story.title, 'Nuevo título')
        self.assertContains(self.client.get(reverse('pages:home')), 'Nuevo título')

    def test_cover_replacement_and_invalid_file(self):
        self.client.force_login(self.owner)
        data=BytesIO();Image.new('RGB',(20,30)).save(data,format='PNG')
        response=self.client.post(self.edit, {'title':'Carta Blanca','cover':SimpleUploadedFile('cover.png',data.getvalue(),content_type='image/png')})
        self.assertEqual(response.status_code,302)
        self.story.refresh_from_db()
        self.assertTrue(self.story.cover)
        self.assertContains(self.client.get(reverse('pages:home')), reverse('pages:story_cover',args=[self.story.pk]))
        response=self.client.post(self.edit, {'title':'Carta Blanca','file':SimpleUploadedFile('bad.exe',b'bad')})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.context['form'].errors)
        self.story.refresh_from_db();self.assertFalse(self.story.file)

    def test_permissions(self):
        self.assertEqual(self.client.get(self.edit).status_code,302)
        other=User.objects.create_user('other')
        self.client.force_login(other)
        self.assertEqual(self.client.post(self.edit,{'title':'Stolen'}).status_code,404)
        self.client.force_login(self.owner)
        ModerationAccount.objects.update_or_create(user=self.owner,defaults={'is_silenced':True})
        self.assertEqual(self.client.post(self.edit,{'title':'Muted'}).status_code,403)


# ========================================================================
# Originally: test_story_cards.py
# ========================================================================

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


# ========================================================================
# Originally: test_work_contents.py
# ========================================================================

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
