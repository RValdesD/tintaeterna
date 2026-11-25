from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from pages.models import StoryUpload
from pages.sample_works import sample_key
from pages.views import sample_stories


class Command(BaseCommand):
    help = 'Vincula las obras de ejemplo a sus cuentas existentes, sin reemplazar sus archivos.'

    @transaction.atomic
    def handle(self, *args, **options):
        popular, recommended, covers = sample_stories()
        users = {u.username: u for u in get_user_model().objects.filter(groups__name='Autores de ejemplo')}
        missing = [item['author'] for item in popular + recommended if slugify(item['author']) not in users]
        if missing:
            raise CommandError('Primero crea las cuentas de ejemplo con seed_sample_accounts. Faltan: ' + ', '.join(missing))
        for item in popular + recommended:
            owner = users[slugify(item['author'])]
            key = sample_key(item)
            story = StoryUpload.objects.filter(sample_key=key).first()
            if story:
                if story.owner_id != owner.pk:
                    raise CommandError('La obra ya pertenece a otra cuenta: ' + item['title'])
                self.stdout.write('Ya vinculada: ' + story.display_title)
                continue
            # Reuse a matching upload rather than creating a second work.
            matches = list(StoryUpload.objects.filter(owner=owner, title=item['title'], sample_key__isnull=True)[:2])
            if len(matches) > 1:
                raise CommandError('Hay varias obras con el mismo título; resuelve el duplicado: ' + item['title'])
            story = matches[0] if matches else StoryUpload(owner=owner, title=item['title'])
            story.sample_key = key
            filename = covers.get(item['title'])
            story.sample_cover = 'public/images/' + filename if filename else ''
            story.save()
            self.stdout.write(self.style.SUCCESS('Vinculada: ' + story.display_title))
