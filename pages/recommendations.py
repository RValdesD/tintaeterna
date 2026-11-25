from django.urls import reverse
from .models import Profile, StoryUpload
from .sample_works import cover_url


def recommended_cards(user, limit=5):
    """Obtiene obras recomendadas aleatoriamente según los géneros favoritos del usuario y el límite indicado."""
    works = StoryUpload.objects.exclude(file='').filter(owner__is_active=True)
    preferences = []
    if user.is_authenticated:
        profile = Profile.objects.filter(user=user).first()
        if profile:
            preferences = list(profile.gustos.values_list('pk', flat=True))
    if preferences:
        # La subconsulta evita duplicar tarjetas cuando coinciden varias etiquetas seleccionadas.
        matches = StoryUpload.objects.filter(tags__pk__in=preferences).values('pk')
        works = works.filter(pk__in=matches)
    works = works.select_related('owner').prefetch_related('tags').order_by('?')[:limit]
    return [{
        'title': story.display_title,
        'author': story.owner.first_name or story.owner.username,
        'profile_url': reverse('pages:profile', args=[story.owner_id]),
        'work_url': reverse('pages:work_detail', args=[story.pk]),
        'cover_url': cover_url(story),
        'tags': story.tags,
    } for story in works]
