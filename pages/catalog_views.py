from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_GET
from .models import StoryUpload, Tag
from .views import sample_stories
from .sample_works import cover_url


@require_GET
#Muestra las obras publicadas más recientemente. Permite filtrar por texto y etiquetas, pagina los resultados y prepara las tarjetas con enlaces al perfil del autor, al detalle de la obra y a su portada.
def recent(request):
    query = request.GET.get("q", "").strip()[:200]
    tag_ids = [int(value) for value in request.GET.getlist("tag") if value.isdecimal() and len(value) < 10]
    works = StoryUpload.objects.exclude(file="").select_related("owner").prefetch_related("tags").order_by("-uploaded_at", "-pk")
    if query:
        works = works.filter(Q(title__icontains=query) | Q(original_name__icontains=query) | Q(owner__username__icontains=query))
    if tag_ids:
        works = works.filter(tags__pk__in=tag_ids).distinct()
    paginator = Paginator(works, 20)
    page = paginator.get_page(request.GET.get("page"))
    cards = [{"title": work.display_title, "author": work.owner.first_name or work.owner.username,
              "profile_url": reverse("pages:profile", args=[work.owner_id]),
              "work_url": reverse("pages:work_detail", args=[work.pk]),
              "cover_url": cover_url(work),
              "tags": work.tags} for work in page]
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "pages/home.html", {
        "catalog": "recent", "page_title": "Recién Agregados", "query": query,
        "selected_tags": tag_ids, "tags": Tag.objects.order_by("name"),
        "sections": [{"title": "Recién Agregados", "stories": cards}],
        "page_obj": page, "page_numbers": list(paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)),
        "pagination_query": params.urlencode(),
    })


@require_GET
#Muestra el catálogo de obras populares de ejemplo. Vincula las tarjetas con obras reales cuando existe una correspondencia y renderiza la página principal usando la sección Popular.
def popular(request):
    works, _, covers = sample_stories()
    from .sample_works import link_sample_cards
    link_sample_cards(works, covers)
    return render(request, "pages/home.html", {
        "catalog": "popular", "page_title": "Popular", "tags": Tag.objects.order_by("name"),
        "sections": [{"title": "Popular", "stories": works}],
    })
