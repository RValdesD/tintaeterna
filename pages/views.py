from django.shortcuts import render

from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404

from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .forms import LoginForm, SignupForm
from .forms import StoryUploadForm, StoryPresentationForm
from .models import StoryUpload, Tag, Bookmark, Profile
from .forms import ProfileDescriptionForm, ProfilePictureForm
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
import re
from pathlib import Path
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET
from django.templatetags.static import static


def readable_story(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id)

    if Path(story.file.name).suffix.lower() not in {".pdf", ".epub", ".txt"}:
        raise Http404("Formato no compatible.")

    return story


@never_cache
@require_GET
def reader(request, upload_id):
    story = readable_story(request, upload_id)

    return render(request, "pages/reader.html", {
        "story": story,
        "format": Path(story.file.name).suffix.lower()[1:],
        "saved_location": (Bookmark.objects.filter(user=request.user, story=story)
                           .values_list("location", flat=True).first() or "")
                           if request.user.is_authenticated else "",
    })


@never_cache
@require_GET
def reader_file(request, upload_id):
    story = readable_story(request, upload_id)

    try:
        source = story.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("El archivo ya no está disponible.")

    response = FileResponse(
        source,
        as_attachment=True,
        filename=story.original_name,
        content_type="application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response




def sample_stories():
    popular = [
        {
            "title": "Comment te dire Adieu",
            "author": "Naranja L.",
            "rating": "4.8",
        },
        {
            "title": "El Mayordomo",
            "author": "Laëtitia",
            "rating": "4.6",
        },
        {
            "title": "Monochromia",
            "author": "Aery W.",
            "rating": "4.9",
        },
        {
            "title": "CyberCidio",
            "author": "xXxDanielxXx",
            "rating": "4.7",
        },
        {
            "title": "Carta Blanca",
            "author": "KillerQueen",
            "rating": "4.7",
        },
    ]

    recommended = [
        {
            "title": "Obra5",
            "author": "Autor5",
            "rating": "4.5",
        },
        {
            "title": "Obra6",
            "author": "Autor6",
            "rating": "4.8",
        },
        {
            "title": "Obra7",
            "author": "Autor7",
            "rating": "4.6",
        },
        {
            "title": "Obra8",
            "author": "Autor8",
            "rating": "4.7",
        },
    ]

    sample_covers = {
        "Comment te dire Adieu": "obra1.jpg",
        "El Mayordomo": "obra2.png",
        "Monochromia": "obra3.jpg",
        "CyberCidio": "obra4.jpg",
        "Carta Blanca": "obra5.png",
        "Obra6": "obra6.png",
        "Obra7": "obra7.jpg",
        "Obra8": "obra8.jpg",
    }

    return popular, recommended, sample_covers


def home(request):
    popular, recommended, sample_covers = sample_stories()
    for index, item in enumerate(popular + recommended, start=1):
        item["work_url"] = reverse("pages:sample_work", args=[index])
        item["profile_url"] = reverse(
            "pages:demo_profile",
            args=[item["author"]],
        )

        filename = sample_covers.get(item["title"])
        item["cover_url"] = (
            static(f"public/images/{filename}") if filename else ""
        )


    uploads = (
        StoryUpload.objects.select_related("owner")
        .prefetch_related("tags")
        .order_by("-uploaded_at")
    )
    uploaded_cards = [
        {
            "title": item.display_title,
            "author": item.owner.username,
            "profile_url": reverse("pages:profile", args=[item.owner_id]),
            "reader_url": reverse("pages:reader", args=[item.pk]),
            "work_url": reverse("pages:work_detail", args=[item.pk]),
            "cover_url": reverse("pages:story_cover", args=[item.pk]) if item.cover else "",
            "tags": item.tags,
        }
        for item in uploads
    ]
    return render(request, "pages/home.html", {
        "sections": [
            {"title": "Popular: Esta Semana", "stories": popular},
            {"title": "Obras Recomendadas", "stories": recommended},
            {"title": "Escritos publicados", "stories": uploaded_cards},
        ],
        "tags": Tag.objects.order_by("name"),
    })


@login_required
@require_http_methods(["GET", "POST"])
def upload(request):
    form = StoryUploadForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )

    if request.method == "POST":
        if len(request.FILES.getlist("file")) > 1:
            form.add_error("file", "Sube un archivo a la vez.")

        if form.is_valid():
            story = form.save(commit=False)
            story.owner = request.user
            story.original_name = form.cleaned_data["file"].name
            story.save()

            form.save_m2m() #Guarda tags asociados en la base de datos

            messages.success(request, "Archivo subido correctamente.")
            return redirect("pages:upload")

    uploads = StoryUpload.objects.filter(
        owner=request.user
    ).order_by("-uploaded_at")

    return render(request, "pages/upload.html", {
        "form": form,
        "uploads": uploads,
    })

@sensitive_post_parameters("password")
@never_cache
@require_http_methods(["GET", "POST"])

def login_page(request):
    if request.user.is_authenticated:
        return redirect("pages:home")

    form = LoginForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )

        if user is not None:
            login(request, user)
            target = request.POST.get("next") or request.GET.get("next", "")
            if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
                return redirect(target)
            return redirect("pages:home")

        form.add_error(
            None,
            "Correo electrónico o contraseña incorrectos.",
        )

    return render(request, "pages/login.html", {
        "form": form,
        "next_url": request.POST.get("next") or request.GET.get("next", ""),
    })

@sensitive_post_parameters("password1", "password2")
@never_cache
@require_http_methods(["GET", "POST"])
def signup_page(request):
    if request.user.is_authenticated:
        return redirect("pages:home")

    form = SignupForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("pages:login")

    return render(
        request,
        "pages/signup.html",
        {"form": form},
    )

@login_required
@require_POST
def delete_upload(request, upload_id):
    story = get_object_or_404(
        StoryUpload,
        pk=upload_id,
        owner=request.user,
    )

    story.cover.delete(save=False)
    story.file.delete(save=False)
    story.delete()

    messages.success(request, "Archivo eliminado correctamente.")
    return redirect("pages:upload")

@require_POST
def logout_page(request):
    logout(request)
    return redirect("pages:home")


@require_GET
def public_profile(request, user_id):
    author = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
    return render(request, "pages/profile.html", {
        "author_name": author.username,
        "author": author,
        "profile": Profile.objects.filter(user=author).first(),
        "works": StoryUpload.objects.filter(owner=author).prefetch_related("tags").order_by("-uploaded_at"),
    })


@require_GET
def demo_profile(request, author):
    demo_titles = {f"Autor{i}": f"Obra{i}" for i in range(1, 9)}
    demo_titles.update({
        "Naranja Corupta": "Comment te dire Adieu",
        "Autor2": "El Mayordomo",
    })
    if author not in demo_titles:
        raise Http404("Perfil no encontrado.")
    return render(request, "pages/profile.html", {
        "author_name": author, "demo": True,
        "demo_title": demo_titles[author],
    })


@login_required
@never_cache
@require_GET
def bookmarks(request):
    return render(request, "pages/bookmarks.html", {
        "bookmarks": Bookmark.objects.filter(user=request.user).select_related("story", "story__owner"),
    })


@login_required
@never_cache
@require_POST
def save_bookmark(request, upload_id):
    story = readable_story(request, upload_id)
    location = request.POST.get("location", "")
    extension = Path(story.file.name).suffix.lower()
    if extension == ".epub":
        valid = (len(location) <= 2000 and location.startswith("epubcfi(")
                 and location.endswith(")") and not any(ord(c) < 32 for c in location))
    else:
        valid = bool(re.fullmatch(r"[1-9][0-9]{0,6}", location))
    if not valid:
        return JsonResponse({"error": "Posición de lectura inválida."}, status=400)
    Bookmark.objects.update_or_create(user=request.user, story=story,
                                     defaults={"location": location})
    return JsonResponse({"location": location})


@login_required
@require_POST
def delete_bookmark(request, upload_id):
    Bookmark.objects.filter(user=request.user, story_id=upload_id).delete()
    return redirect("pages:bookmarks")


@login_required
@require_GET
def my_profile(request):
    return redirect("pages:profile", user_id=request.user.pk)


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileDescriptionForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Descripción actualizada.")
        return redirect("pages:my_profile")
    return render(request, "pages/edit_profile.html", {"form": form, "picture": False})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_picture(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    old_name = profile.avatar.name
    storage = profile.avatar.storage
    form = ProfilePictureForm(request.POST if request.method == "POST" else None,
                              request.FILES if request.method == "POST" else None,
                              instance=profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save()
        if old_name and old_name != profile.avatar.name:
            storage.delete(old_name)
        messages.success(request, "Foto actualizada.")
        return redirect("pages:my_profile")
    return render(request, "pages/edit_profile.html", {"form": form, "picture": True})


@require_GET
def profile_picture(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id, user__is_active=True)
    if not profile.avatar:
        raise Http404("Sin foto de perfil.")
    try:
        source = profile.avatar.open("rb")
    except OSError:
        raise Http404("Imagen no disponible.")
    response = FileResponse(source, content_type="image/png")
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-cache"
    return response


@login_required
@require_http_methods(["GET", "POST"])
def edit_story_presentation(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id, owner=request.user)
    old_cover = story.cover.name
    storage = story.cover.storage
    form = StoryPresentationForm(request.POST if request.method == "POST" else None,
                                 request.FILES if request.method == "POST" else None,
                                 instance=story)
    if request.method == "POST" and form.is_valid():
        story = form.save()
        if old_cover and old_cover != story.cover.name:
            storage.delete(old_cover)
        return redirect("pages:upload")
    return render(request, "pages/edit_story_presentation.html", {"form": form, "story": story})


@require_GET
def story_cover(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id)
    if not story.cover:
        raise Http404("Sin portada.")
    try:
        source = story.cover.open("rb")
    except OSError:
        raise Http404("Portada no disponible.")
    response = FileResponse(source, content_type="image/png")
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-cache"
    return response


@require_GET
def work_detail(request, upload_id):
    story = readable_story(request, upload_id)
    return render(request, "pages/work_detail.html", {
        "title": story.display_title,
        "description": story.description,
        "story": story,
        "format": Path(story.file.name).suffix.lower()[1:],
    })


@require_GET
def sample_work(request, sample_id):
    popular, recommended, _ = sample_stories()
    works = popular + recommended
    if not 1 <= sample_id <= len(works):
        raise Http404("Obra no encontrada.")
    work = works[sample_id - 1]
    return render(request, "pages/work_detail.html", {
        "title": work["title"],
        "description": work.get("description", ""),
        "sample": True,
    })
