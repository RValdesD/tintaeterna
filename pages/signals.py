import logging
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import StoryUpload, Profile


@receiver(post_delete, sender=StoryUpload)
@receiver(post_delete, sender=Profile)
def cleanup_files(sender, instance, **kwargs):
    fields = (instance.file, instance.cover) if sender is StoryUpload else (instance.avatar,)
    for field in fields:
        if field.name:
            storage, name = field.storage, field.name
            def cleanup(storage=storage, name=name):
                try:
                    storage.delete(name)
                except OSError:
                    logging.getLogger(__name__).exception("No se pudo eliminar el archivo %s", name)
            transaction.on_commit(cleanup)
