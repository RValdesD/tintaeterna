from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .forms import StoryUploadForm
from .models import StoryUpload, StoryChapter
from .chapter_forms import ChapterFormSet
from .moderation import ensure_can_publish
from .sample_works import cover_url


class StoryEditForm(StoryUploadForm):
    """Adapta el formulario de subida para editar obras existentes sin exigir un archivo nuevo."""

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y configura los requisitos de los campos de archivo y título."""
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['title'].required = True
        self.fields['title'].label = 'Título'

    def clean_file(self):
        """Valida los archivos nuevos con las reglas de subida y conserva el archivo existente si no se reemplaza."""
        # Valida los archivos nuevos utilizando las mismas reglas de subida habituales.
        if 'file' in self.files:
            return super().clean_file()
        return self.instance.file


@login_required
@require_http_methods(['GET', 'POST'])
def edit_story(request, upload_id):
    """Permite al propietario editar una obra y sus capítulos, validando los cambios y gestionando los archivos reemplazados."""
    story = get_object_or_404(StoryUpload, pk=upload_id, owner=request.user)
    old_files = [(field, getattr(story, field).storage, getattr(story, field).name)
                 for field in ('file', 'cover')]
    form = StoryEditForm(request.POST if request.method == 'POST' else None,
                         request.FILES if request.method == 'POST' else None, instance=story)
    initial = list(story.chapters.values('title', 'start_page', 'end_page'))
    chapter_data = request.POST if request.method == 'POST' else None
    if chapter_data is not None and 'chapters-TOTAL_FORMS' not in chapter_data:
        # Los clientes antiguos conservan los capítulos guardados; los archivos reemplazados requieren validarlos nuevamente.
        chapter_data = {'chapters-TOTAL_FORMS': str(len(initial)), 'chapters-INITIAL_FORMS': str(len(initial))}
        for index, row in enumerate(initial):
            chapter_data.update({f'chapters-{index}-{key}': value for key, value in row.items()})
    chapters = ChapterFormSet(chapter_data, initial=initial, prefix='chapters',
                              source=request.FILES.get('file') or story.file)
    if request.method == 'POST':
        ensure_can_publish(request.user)
        form_valid = form.is_valid()
        chapters_valid = chapters.is_valid()
        if form_valid and chapters_valid:
            with transaction.atomic():
                story = form.save(commit=False)
                if 'file' in request.FILES:
                    story.original_name = request.FILES['file'].name
                story.save()
                form.save_m2m()
                story.chapters.all().delete()
                StoryChapter.objects.bulk_create([StoryChapter(story=story, **row) for row in chapters.chapter_rows()])
                for field, storage, name in old_files:
                    if name and name != getattr(story, field).name:
                        transaction.on_commit(lambda s=storage, n=name: s.delete(n))
            messages.success(request, 'Obra actualizada.')
            return redirect('pages:work_detail', upload_id=story.pk)
    return render(request, 'pages/edit_story.html', {
        'story': story, 'form': form, 'chapters': chapters, 'cover_url': cover_url(story)})
