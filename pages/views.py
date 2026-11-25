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
from .forms import StoryUploadForm
from .models import StoryUpload, Tag
from pathlib import Path
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


def readable_story(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id, owner=request.user)
    if Path(story.file.name).suffix.lower() not in {".pdf", ".epub", ".txt"}:
        raise Http404("Formato no compatible.")
    return story


@login_required
@never_cache
@require_GET
def reader(request, upload_id):
    story = readable_story(request, upload_id)
    return render(request, "pages/reader.html", {
        "story": story,
        "format": Path(story.file.name).suffix.lower()[1:],
    })


@login_required
@never_cache
@require_GET
def reader_file(request, upload_id):
    story = readable_story(request, upload_id)
    try:
        source = story.file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("El archivo ya no está disponible.")
    response = FileResponse(
        source, as_attachment=True, filename=story.original_name,
        content_type="application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response




def home(request):
    popular = [
        {
            "title": "Obra1",
            "author": "Autor1",
            "rating": "4.8",
        },
        {
            "title": "Obra2",
            "author": "Autor2",
            "rating": "4.6",
        },
        {
            "title": "Obra3",
            "author": "Autor3",
            "rating": "4.9",
        },
        {
            "title": "Obra4",
            "author": "Autor4",
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

    tags = Tag.objects.all() #obtiene todos los tags creados

    return render(request, "pages/home.html", {
        "sections": [
            {"title": "Popular: Esta Semana", "stories": popular},
            {"title": "Obras Recomendadas", "stories": recommended},
        ],
        "tags": tags,
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
            return redirect("pages:home")

        form.add_error(
            None,
            "Correo electrónico o contraseña incorrectos.",
        )

    return render(request, "pages/login.html", {"form": form})

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

    story.file.delete(save=False)
    story.delete()

    messages.success(request, "Archivo eliminado correctamente.")
    return redirect("pages:upload")

@require_POST
def logout_page(request):
    logout(request)
    return redirect("pages:home")
