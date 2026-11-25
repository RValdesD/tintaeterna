
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import ModerationAccount


def is_moderator(user):
    """Comprueba si el usuario está activo, autenticado y tiene permisos de moderación."""
    return bool(user.is_authenticated and user.is_active
                and user.email.lower().endswith("@admin.cl")
                and ModerationAccount.objects.filter(user=user, is_admin=True).exists())


def moderator_required(view):
    """Restringe el acceso a una vista exclusivamente a usuarios con permisos de moderación."""
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        """Verifica los permisos del usuario antes de ejecutar la vista protegida."""
        if not is_moderator(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def ensure_can_publish(user):
    """Impide publicar o modificar contenido público cuando la cuenta está silenciada."""
    if ModerationAccount.objects.filter(user=user, is_silenced=True).exists():
        raise PermissionDenied("Tu cuenta está silenciada. No puedes publicar ni modificar contenido público.")
