
from pathlib import Path
from django import forms
from django.forms import BaseFormSet, formset_factory
from pypdf import PdfReader


class ChapterForm(forms.Form):
    """Define los campos de un capítulo: título y rango de páginas."""

    title = forms.CharField(label='Título', max_length=200)
    start_page = forms.IntegerField(label='Primera página', min_value=1)
    end_page = forms.IntegerField(label='Última página', min_value=1)


class ChapterBaseFormSet(BaseFormSet):
    """Valida los capítulos y sus rangos de páginas dentro de un archivo PDF."""

    def __init__(self, *args, source=None, **kwargs):
        """Inicializa el conjunto de formularios y almacena el archivo de origen."""
        self.source = source
        super().__init__(*args, **kwargs)

    def clean(self):
        """Comprueba que los rangos sean válidos, no se superpongan y estén dentro del PDF."""
        super().clean()
        if any(self.errors):
            return
        rows = self.chapter_rows()
        if not rows:
            return
        if not self.source or Path(self.source.name).suffix.lower() != '.pdf':
            raise forms.ValidationError('Los rangos de páginas solo están disponibles para archivos PDF. Elimina los capítulos para usar otro formato.')
        try:
            self.source.open('rb')
            self.source.seek(0)
            reader = PdfReader(self.source)
            if reader.is_encrypted:
                raise forms.ValidationError('Usa un PDF sin contraseña para definir capítulos.')
            count = len(reader.pages)
        except forms.ValidationError:
            raise
        except Exception as exc:
            raise forms.ValidationError('No se pudo leer el PDF para verificar sus páginas.') from exc
        finally:
            if self.source and not self.source.closed:
                self.source.seek(0)
        last_end = 0
        for row in sorted(rows, key=lambda row: row['start_page']):
            if row['end_page'] < row['start_page']:
                raise forms.ValidationError('La última página no puede ser anterior a la primera.')
            if row['end_page'] > count:
                raise forms.ValidationError(f'El PDF tiene {count} páginas. Corrige los rangos que superan ese límite.')
            if row['start_page'] <= last_end:
                raise forms.ValidationError('Los rangos de capítulos no pueden superponerse.')
            last_end = row['end_page']

    def chapter_rows(self):
        """Retorna los capítulos válidos, excluyendo formularios incompletos o eliminados."""
        return [{key: form.cleaned_data[key] for key in ('title', 'start_page', 'end_page')}
                for form in self.forms if form.cleaned_data and not form.cleaned_data.get('DELETE')
                and all(key in form.cleaned_data for key in ('title', 'start_page', 'end_page'))]


ChapterFormSet = formset_factory(ChapterForm, formset=ChapterBaseFormSet,
    extra=1, can_delete=True, max_num=100, validate_max=True, absolute_max=100)
