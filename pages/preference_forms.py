
from django import forms
from .models import Tag


class GustosWidget(forms.CheckboxSelectMultiple):
    """Define un widget personalizado para seleccionar géneros favoritos."""

    template_name = 'pages/widgets/gustos.html'


def gustos_field():
    """Crea un campo opcional de selección múltiple con los géneros ordenados por nombre."""
    return forms.ModelMultipleChoiceField(
        queryset=Tag.objects.order_by('name'), required=False,
        label='Géneros favoritos', widget=GustosWidget,
    )

