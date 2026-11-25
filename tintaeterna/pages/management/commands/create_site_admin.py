from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction, IntegrityError
from pages.models import ModerationAccount


class Command(BaseCommand):
    help = "Crea una cuenta de moderación @admin.cl (no concede acceso a /admin/)."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("email")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].strip().lower()
        try:
            validate_email(email)
            if email.rsplit("@", 1)[-1] != "admin.cl":
                raise CommandError("El correo debe terminar exactamente en @admin.cl.")
            if User.objects.filter(email__iexact=email).exists():
                raise CommandError("El correo ya está registrado; no se promoverá una cuenta existente.")
            user = User(username=options["username"], email=email)
            user.full_clean(exclude=["password"])
            password = getpass("Contraseña: ")
            if password != getpass("Confirmar contraseña: "):
                raise CommandError("Las contraseñas no coinciden.")
            validate_password(password, user)
            with transaction.atomic():
                user.set_password(password)
                user.save()
                ModerationAccount.objects.create(user=user, is_admin=True)
        except (ValidationError, IntegrityError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Cuenta de moderación creada."))
