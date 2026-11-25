from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify
from .models import StoryUpload


def sample_key(item):
    """Genera una clave única de identificación para una obra de ejemplo a partir de su autor y título."""
    return f"{slugify(item['author'])}:{slugify(item['title'])}"


def cover_url(story):
    """Obtiene la URL de la portada de una obra, utilizando su imagen guardada o una portada de ejemplo."""
    if story.cover:
        return reverse('pages:story_cover', args=[story.pk])
    return static(story.sample_cover) if story.sample_cover else ''


def link_sample_cards(items, covers, start=1):
    """Actualiza las tarjetas de obras de ejemplo con datos reales cuando existen en la base de datos."""
    stored = {story.sample_key: story for story in
              StoryUpload.objects.filter(sample_key__isnull=False).select_related('owner')}
    for index, item in enumerate(items, start):
        story = stored.get(sample_key(item))
        if story:
            item.update(title=story.display_title,
                        author=story.owner.first_name or story.owner.username,
                        work_url=reverse('pages:work_detail', args=[story.pk]),
                        profile_url=reverse('pages:profile', args=[story.owner_id]),
                        cover_url=cover_url(story))
        else:
            filename = covers.get(item['title'])
            item.update(work_url=reverse('pages:sample_work', args=[index]),
                        profile_url=reverse('pages:demo_profile', args=[item['author']]),
                        cover_url=static('public/images/' + filename) if filename else '')
