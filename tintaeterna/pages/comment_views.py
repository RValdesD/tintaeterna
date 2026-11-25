
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Comentarios, ProfileComment
from .moderation import is_moderator


def can_delete_comment(user, comment):
    """Comprueba si el usuario puede eliminar un comentario según su autoría o permisos."""
    if not user.is_authenticated or not user.is_active:
        return False
    owner_id = comment.sender_id if isinstance(comment, ProfileComment) else comment.author_id
    return user.pk == owner_id or user.is_superuser or is_moderator(user)


@login_required
@require_POST
def delete_reader_comment(request, comment_id):
    """Elimina un comentario de una obra si el usuario tiene autorización y redirige al lector."""
    comment = get_object_or_404(Comentarios, pk=comment_id)
    if not can_delete_comment(request.user, comment):
        raise PermissionDenied
    story_id = comment.historia_id
    comment.delete()
    return redirect(reverse('pages:reader', args=[story_id]) + '#comentarios')


@login_required
@require_POST
def delete_profile_comment(request, comment_id):
    """Elimina un comentario de perfil autorizado y redirige al perfil conservando las respuestas."""
    comment = get_object_or_404(ProfileComment.objects.select_related('profile'), pk=comment_id)
    if not can_delete_comment(request.user, comment):
        raise PermissionDenied
    author_id = comment.profile.user_id
    # Replies survive; parent uses SET_NULL.
    comment.delete()
    return redirect(reverse('pages:profile', args=[author_id]) + '#comments')
