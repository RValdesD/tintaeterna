from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import ModerationAccount


def is_moderator(user):
    return bool(user.is_authenticated and user.is_active
                and user.email.lower().endswith("@admin.cl")
                and ModerationAccount.objects.filter(user=user, is_admin=True).exists())


def moderator_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not is_moderator(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def ensure_can_publish(user):
    if ModerationAccount.objects.filter(user=user, is_silenced=True).exists():
        raise PermissionDenied("Tu cuenta está silenciada. No puedes publicar ni modificar contenido público.")
