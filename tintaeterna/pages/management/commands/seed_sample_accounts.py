from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from pages.models import Profile
from pages.views import sample_stories


class Command(BaseCommand):
    help = "Crea cuentas reales para los autores de ejemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        group, _ = Group.objects.get_or_create(
            name="Autores de ejemplo"
        )

        popular, recommended, _ = sample_stories()
        authors = sorted({
            story["author"]
            for story in popular + recommended
        })

        for author in authors:
            # Por ejemplo cambia "Naranja L." -> "naranja-l"
            username = slugify(author)

            if not username:
                self.stdout.write(
                    self.style.WARNING(
                        f"No se pudo generar un usuario para: {author}"
                    )
                )
                continue

            existing = User.objects.filter(
                username__iexact=username
            ).first()

            if existing:
                if existing.groups.filter(pk=group.pk).exists():
                    Profile.objects.get_or_create(user=existing)
                    self.stdout.write(f"Ya existe: {username}")
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Conflicto: {username} ya pertenece a otra "
                            "cuenta. No se modificó."
                        )
                    )
                continue

            user = User(
                username=username,
                first_name=author,
                email="",
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )

            user.set_unusable_password()
            user.full_clean()
            user.save()

            user.groups.add(group)
            Profile.objects.create(user=user)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Creado: {author} → {username}"
                )
            )