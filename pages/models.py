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
