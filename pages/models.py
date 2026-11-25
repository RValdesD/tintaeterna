from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


def story_file_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"stories/{instance.owner_id}/{uuid4().hex}{extension}"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre del tag")

    def __str__(self):
        return self.name


def cover_file_path(instance, filename):
    return f"covers/{instance.owner_id}/{uuid4().hex}.png"


class StoryUpload(models.Model):
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=3000, blank=True)
    cover = models.ImageField(upload_to=cover_file_path, blank=True)

    @property
    def display_title(self):
        return self.title or self.original_name

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_uploads",
    )
    file = models.FileField(upload_to=story_file_path)
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    tags = models.ManyToManyField(Tag, blank=True, related_name="stories", verbose_name="Tags")

    def __str__(self):
            return self.original_name


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="bookmarks")
    story = models.ForeignKey(StoryUpload, on_delete=models.CASCADE,
                              related_name="bookmarks")
    location = models.CharField(max_length=2000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"],
                                               name="unique_user_story_bookmark")]
        ordering = ["-updated_at"]


def avatar_file_path(instance, filename):
    return f"avatars/{instance.user_id}/{uuid4().hex}.png"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="profile")
    description = models.TextField(max_length=1000, blank=True)
    avatar = models.ImageField(upload_to=avatar_file_path, blank=True)

    def __str__(self):
        return self.user.username


class ModerationAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_account")
    is_admin = models.BooleanField(default=False, editable=False)
    is_silenced = models.BooleanField(default=False)


class ModerationNotice(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_notices")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    work_title = models.CharField(max_length=255)
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)


class ModerationLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=30)
    target = models.CharField(max_length=255)
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)


#clase comentario. id, fecha, nombre, texto, id_story
class Comentarios(models.Model):
    fecha= models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=100)
    texto = models.TextField()
    historia = models.ForeignKey(
        'StoryUpload',
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    def __str__(self):
        return f"{self.nombre} en {self.historia}"
