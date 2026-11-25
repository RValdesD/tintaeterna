from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods
from .models import Profile, ProfileComment, StoryUpload
from .profile_forms import AccountSettingsForm, ProfileCommentForm
from .moderation import ensure_can_publish


@login_required
@require_http_methods(["GET", "POST"])
def settings_page(request):
    """Permite consultar y actualizar el perfil, validando permisos y eliminando archivos reemplazados."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    old = [(field, getattr(profile, field).storage, getattr(profile, field).name) for field in ("avatar", "banner")]
    form = AccountSettingsForm(request.POST if request.method == "POST" else None,
                               request.FILES if request.method == "POST" else None, instance=profile)
    if request.method == "POST":
        ensure_can_publish(request.user)
        if form.is_valid():
            with transaction.atomic():
                profile = form.save()
                for field, storage, name in old:
                    if name and name != getattr(profile, field).name:
                        transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))
            messages.success(request, "Perfil actualizado.")
            return redirect("pages:profile", user_id=request.user.pk)
    return render(request, "pages/account_settings.html", {"form": form})


@require_GET
def banner(request, user_id):
    """Entrega el banner de un perfil activo o devuelve un error 404 si no está disponible."""
    profile = get_object_or_404(Profile, user_id=user_id, user__is_active=True)
    if not profile.banner:
        raise Http404
    try:
        source = profile.banner.open("rb")
    except OSError:
        raise Http404
    response = FileResponse(source, content_type="image/png")
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_http_methods(["GET", "POST"])
def public_profile(request, user_id):
    """Muestra el perfil público, sus obras y comentarios, y permite publicar comentarios o respuestas autorizadas."""
    author = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
    profile = Profile.objects.filter(user=author).first()
    form = ProfileCommentForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(reverse("pages:login") + "?next=" + request.path)
        ensure_can_publish(request.user)
        if form.is_valid():
            parent_id = form.cleaned_data.get("parent")
            parent = None
            if parent_id:
                parent = get_object_or_404(ProfileComment, pk=parent_id, profile__user=author)
            profile, _ = Profile.objects.get_or_create(user=author)
            comment = ProfileComment.objects.create(profile=profile, sender=request.user,
                text=form.cleaned_data["text"], parent=parent)
            count = ProfileComment.objects.filter(profile=profile, pk__lte=comment.pk).count()
            return redirect(reverse("pages:profile", args=[author.pk]) + f"?page={(count - 1) // 20 + 1}#comment-{comment.pk}")
    comments = ProfileComment.objects.filter(profile__user=author).select_related("sender__profile", "parent__sender")
    page = Paginator(comments, 20).get_page(request.GET.get("page"))
    reply_to = None
    if request.GET.get("reply", "").isdigit():
        reply_to = get_object_or_404(ProfileComment, pk=request.GET["reply"], profile__user=author)
        if request.method == "GET":
            form = ProfileCommentForm(initial={"parent": reply_to.pk})
    return render(request, "pages/profile.html", {"author": author, "author_name": author.first_name or author.username,
        "profile": profile, "works": StoryUpload.objects.filter(owner=author).order_by("-uploaded_at"),
        "comments_page": page, "comment_form": form, "reply_to": reply_to})
