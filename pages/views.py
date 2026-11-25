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
from .models import StoryUpload, Tag, Bookmark, Profile, Comentarios
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

#Obtiene una obra por su identificador y comprueba que el archivo tenga uno de los formatos admitidos por el lector (PDF, EPUB o TXT). Si no existe o el formato no es compatible, responde con un error 404.
def readable_story(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id)

    if Path(story.file.name).suffix.lower() not in {".pdf", ".epub", ".txt"}:
        raise Http404("Formato no compatible.")

    return story
#Obtiene los comentarios de una obra en orden cronológico. select_related carga de antemano el autor y el comentario padre para reducir consultas al mostrar la conversación.
def get_coments(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id)
    return Comentarios.objects.filter(historia=story).select_related("author__profile", "parent").order_by("fecha", "pk")

@never_cache
@require_http_methods(["GET", "POST"])
#Muestra el lector de una obra y procesa la creación de comentarios y respuestas. Requiere que la obra tenga un formato admitido; para publicar exige una sesión iniciada y que el usuario pueda publicar según las reglas de moderación. También entrega al lector el formato, los comentarios y la última posición guardada.
def reader(request, upload_id):
    story = readable_story(request, upload_id)
    reply_to = None
    parent_id = request.POST.get("parent", "") if request.method == "POST" else request.GET.get("reply", "")
    if parent_id:
        if not parent_id.isdecimal() or len(parent_id) > 18:
            raise Http404("Comentario no encontrado.")
        reply_to = get_object_or_404(Comentarios, pk=int(parent_id), historia=story)
    texto = ""
    comment_error = ""
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("pages:login")
        from .moderation import ensure_can_publish
        ensure_can_publish(request.user)
        texto = request.POST.get("texto", "").strip()
        if texto:
            comment = Comentarios.objects.create(
                historia=story, nombre=request.user.username,
                author=request.user, texto=texto, parent=reply_to,
            )
            return redirect(reverse("pages:reader", args=[story.pk]) + f"#comment-{comment.pk}")
        comment_error = "Escribe un comentario."
    return render(request, "pages/reader.html", {
        "story": story,
        "format": Path(story.file.name).suffix.lower()[1:],
        "comentarios": get_coments(request, upload_id),
        "reply_to": reply_to, "comment_text": texto, "comment_error": comment_error,
        "saved_location": (Bookmark.objects.filter(user=request.user, story=story)
                        .values_list("location", flat=True).first() or "")
                        if request.user.is_authenticated else "",
    })


@never_cache
@require_GET
#Entrega el archivo de una obra como descarga. Verifica previamente el formato y devuelve 404 si el archivo físico ya no está disponible; añade cabeceras para evitar que el navegador interprete el contenido como otro tipo de recurso.
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



#Construye los datos estáticos de las obras populares y recomendadas que se utilizan como contenido de muestra en la página principal, junto con el mapeo de sus portadas.
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


@never_cache
#Renderiza la página principal. Vincula las tarjetas de muestra con obras disponibles, obtiene las recomendaciones correspondientes al usuario actual y entrega las etiquetas ordenadas alfabéticamente.
def home(request):
    popular, recommended, sample_covers = sample_stories()
    from .sample_works import link_sample_cards
    link_sample_cards(popular, sample_covers)

    sections = [{"title": "Popular: Esta Semana", "stories": popular}]
    if request.user.is_authenticated:
        from .recommendations import recommended_cards
        sections.append({
            "title": "Obras Recomendadas",
            "stories": recommended_cards(request.user),
        })

    return render(request, "pages/home.html", {
        "sections": sections,
        "tags": Tag.objects.order_by("name"),
    })


@login_required
@require_http_methods(["GET", "POST"])
#Permite a un usuario autenticado subir una obra y consultar sus propias subidas. Valida el formulario, limita cada envío a un solo archivo, asigna el propietario y guarda las relaciones ManyToMany de etiquetas después de guardar la obra.
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

#Gestiona el inicio de sesión mediante correo electrónico y contraseña. Si las credenciales son válidas inicia la sesión y respeta el parámetro next únicamente cuando apunta al mismo host; de lo contrario redirige a la página principal.
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
#Muestra y procesa el formulario de registro. Evita que una persona que ya inició sesión vuelva a registrarse y, tras crear correctamente la cuenta, la dirige al formulario de inicio de sesión.
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
#Elimina una obra únicamente si pertenece al usuario autenticado. Borra primero los archivos asociados (portada y documento), elimina el registro y muestra un mensaje de confirmación.
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
#Cierra la sesión actual y redirige a la página principal. La vista solo acepta solicitudes POST.
def logout_page(request):
    logout(request)
    return redirect("pages:home")


@require_GET
#Muestra el perfil público de una cuenta activa, junto con sus datos de perfil y sus obras. prefetch_related carga las etiquetas de las obras para evitar consultas repetidas al renderizar.
def public_profile(request, user_id):
    author = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
    return render(request, "pages/profile.html", {
        "author_name": author.username,
        "author": author,
        "profile": Profile.objects.filter(user=author).first(),
        "works": StoryUpload.objects.filter(owner=author).prefetch_related("tags").order_by("-uploaded_at"),
    })


@require_GET
#Renderiza perfiles de demostración con datos predefinidos. Solo admite autores incluidos en el conjunto de muestras; cualquier otro nombre produce un 404.
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
#Muestra los marcadores del usuario autenticado. La consulta carga también la obra y su propietario para reducir consultas al construir la página.
def bookmarks(request):
    return render(request, "pages/bookmarks.html", {
        "bookmarks": Bookmark.objects.filter(user=request.user).select_related("story", "story__owner"),
    })


@login_required
@never_cache
@require_POST
#Valida y guarda la posición de lectura de una obra para el usuario autenticado. Para EPUB acepta una ubicación EPUB CFI acotada y sin caracteres de control; para los demás formatos acepta un número de página positivo. Actualiza el marcador existente o crea uno nuevo y responde en JSON.
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
#Elimina el marcador de la obra indicada para el usuario autenticado y vuelve a la lista de marcadores.
def delete_bookmark(request, upload_id):
    Bookmark.objects.filter(user=request.user, story_id=upload_id).delete()
    return redirect("pages:bookmarks")


@login_required
@require_GET
#Redirige al perfil público correspondiente al usuario autenticado, evitando mantener una segunda implementación de la página de perfil.
def my_profile(request):
    return redirect("pages:profile", user_id=request.user.pk)


@login_required
@require_http_methods(["GET", "POST"])
#Permite crear o actualizar la descripción del perfil del usuario autenticado. Si el formulario es válido guarda los cambios y vuelve al perfil; en solicitudes GET muestra el formulario.
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
#ermite actualizar el avatar del usuario autenticado. Si se reemplaza una imagen anterior, elimina el archivo previo del almacenamiento para no dejar archivos huérfanos.
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
#Entrega el avatar de una cuenta activa. Responde 404 si el perfil o la imagen no existen o si el archivo no puede abrirse, y evita almacenar en caché la respuesta.
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
#Permite al propietario modificar el título, la descripción y la portada de una obra. Si se reemplaza la portada, elimina el archivo anterior y luego vuelve a la lista de subidas.
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
#Entrega la portada de una obra como imagen PNG. Si no hay portada o el archivo no está disponible, responde con 404 y evita que el navegador almacene la respuesta en caché.
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
#Muestra la página de detalle de una obra. Si el registro todavía no tiene archivo asociado, presenta la vista de obra pendiente con su portada; de lo contrario entrega título, descripción, obra y formato al detalle.
def work_detail(request, upload_id):
    story = get_object_or_404(StoryUpload, pk=upload_id)
    if not story.file:
        from .sample_works import cover_url
        return render(request, "pages/work_pending.html", {"story": story, "cover_url": cover_url(story)})
    return render(request, "pages/work_detail.html", {
        "title": story.display_title,
        "description": story.description,
        "story": story,
        "format": Path(story.file.name).suffix.lower()[1:],
    })


@require_GET
#Muestra una obra del catálogo de muestra según su posición en la lista de populares y recomendadas. Si existe una obra real vinculada a esa muestra redirige a ella; si no, renderiza los datos de muestra.
def sample_work(request, sample_id):
    popular, recommended, _ = sample_stories()
    works = popular + recommended
    if not 1 <= sample_id <= len(works):
        raise Http404("Obra no encontrada.")
    work = works[sample_id - 1]
    from .sample_works import sample_key
    linked = StoryUpload.objects.filter(sample_key=sample_key(work)).first()
    if linked:
        return redirect("pages:work_detail", upload_id=linked.pk)
    return render(request, "pages/work_detail.html", {
        "title": work["title"],
        "description": work.get("description", ""),
        "sample": True,
    })
