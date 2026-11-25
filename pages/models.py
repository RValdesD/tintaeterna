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


class StoryUpload(models.Model):
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


class Comentarios(models.Model):
    """Existing comment schema retained from the comments migrations."""
    fecha = models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=100)
    texto = models.TextField()
    historia = models.ForeignKey(
        StoryUpload, on_delete=models.CASCADE, related_name="comentarios"
    )
