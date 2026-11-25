
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from .models import StoryUpload, ModerationAccount, ModerationNotice, ModerationLog
from .moderation import moderator_required


class ActionForm(forms.Form):
    """Define los campos de motivo y confirmación para una acción de moderación."""

    reason = forms.CharField(max_length=1000, strip=True)
    confirm = forms.BooleanField(required=True)


@moderator_required
@require_GET
def dashboard(request):
    """Muestra el panel de moderación con listados paginados de obras y cuentas de usuario."""
    return render(request, "pages/moderation_dashboard.html", {
        "works": Paginator(StoryUpload.objects.select_related("owner").order_by("-uploaded_at"), 25).get_page(request.GET.get("works_page")),
        "accounts": Paginator(get_user_model().objects.select_related("moderation_account").order_by("username"), 25).get_page(request.GET.get("users_page")),
    })


@moderator_required
@require_POST
@transaction.atomic
def action(request, kind, target_id):
    """Ejecuta acciones de moderación sobre obras o cuentas, validando permisos y registrando los resultados."""
    if kind not in {"remove", "warn", "ban", "silence", "unsilence"}:
        raise PermissionDenied
    form = ActionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Escribe un motivo (máximo 1000 caracteres) y confirma la acción.")
        return redirect("pages:moderation_dashboard")
    reason = form.cleaned_data["reason"]
    if kind in {"remove", "warn"}:
        work = get_object_or_404(StoryUpload.objects.select_for_update(), pk=target_id)
        target = f"{work.pk}: {work.display_title}"[:255]
        ModerationNotice.objects.create(recipient=work.owner, actor=request.user,
            work_title=work.display_title[:255], reason=("Obra eliminada: " if kind == "remove" else "Advertencia: ") + reason[:970])
        if kind == "remove":
            work.delete()
    else:
        user = get_object_or_404(get_user_model().objects.select_for_update(), pk=target_id)
        if user.pk == request.user.pk or user.is_superuser or user.is_staff or ModerationAccount.objects.filter(user=user, is_admin=True).exists():
            raise PermissionDenied("No puedes sancionar cuentas administrativas ni tu propia cuenta.")
        target = f"{user.pk}: {user.username}"[:255]
        if kind == "ban":
            user.delete()
        else:
            state, _ = ModerationAccount.objects.get_or_create(user=user)
            state.is_silenced = kind == "silence"
            state.save(update_fields=["is_silenced"])
            ModerationNotice.objects.create(recipient=user, actor=request.user, work_title="Cuenta",
                reason=("Cuenta silenciada: " if state.is_silenced else "Silencio retirado: ") + reason[:960])
    ModerationLog.objects.create(actor=request.user, action=kind, target=target, reason=reason)
    messages.success(request, "Acción aplicada.")
    return redirect("pages:moderation_dashboard")


@login_required
@require_GET
def notices(request):
    """Muestra las notificaciones de moderación del usuario autenticado, ordenadas de la más reciente a la más antigua."""
    return render(request, "pages/moderation_notices.html", {
        "notices": request.user.moderation_notices.order_by("-created_at"),
    })
