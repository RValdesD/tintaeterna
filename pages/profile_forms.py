
from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django import forms
from django.core.files.base import ContentFile
from .models import Profile, ProfileComment


def normalize_image(upload, size, limit):
    """Valida una imagen y la convierte a PNG respetando las dimensiones y el tamaño máximo permitidos."""
    if not upload or not hasattr(upload, "content_type"):
        return upload
    if upload.size > limit * 1024 * 1024:
        raise forms.ValidationError(f"Máximo {limit} MB.")
    try:
        upload.seek(0)
        with Image.open(upload) as picture:
            if picture.format not in {"PNG", "JPEG", "WEBP"}:
                raise forms.ValidationError("Usa JPG, PNG o WebP.")
            if max(picture.size) > 6000:
                raise forms.ValidationError("Máximo 6000 píxeles por lado.")
            picture.load()
            picture = ImageOps.exif_transpose(picture).convert("RGBA")
            picture.thumbnail(size)
            output = BytesIO()
            picture.save(output, format="PNG")
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise forms.ValidationError("Imagen inválida.")
    return ContentFile(output.getvalue(), name="image.png")


from .preference_forms import gustos_field


class AccountSettingsForm(forms.ModelForm):
    """Gestiona la edición del perfil, incluyendo imágenes, descripción y géneros favoritos."""

    gustos = gustos_field()

    class Meta:
        model = Profile
        fields = ["avatar", "banner", "description", "gustos"]
        labels = {"avatar": "Foto de perfil", "banner": "Banner", "description": "Sobre mí (BBCode)"}
        widgets = {"description": forms.Textarea(attrs={"rows": 8}),
                   "avatar": forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"}),
                   "banner": forms.ClearableFileInput(attrs={"accept": "image/png,image/jpeg,image/webp"})}

    def clean_avatar(self):
        """Valida y normaliza la foto de perfil con un máximo de 720 × 720 píxeles y 2 MB."""
        return normalize_image(self.cleaned_data.get("avatar"), (720, 720), 2)

    def clean_banner(self):
        """Valida y normaliza el banner con un máximo de 1920 × 720 píxeles y 5 MB."""
        return normalize_image(self.cleaned_data.get("banner"), (1920, 720), 5)


class ProfileCommentForm(forms.ModelForm):
    """Gestiona la creación de comentarios de perfil y permite asociarlos a un comentario padre."""

    parent = forms.IntegerField(required=False, min_value=1, widget=forms.HiddenInput)

    class Meta:
        model = ProfileComment
        fields = ["text"]
        labels = {"text": "Comentario"}
        widgets = {"text": forms.Textarea(attrs={"rows": 4, "maxlength": 2000})}

    def clean_text(self):
        """Elimina los espacios sobrantes y rechaza comentarios cuyo contenido esté vacío."""
        value = self.cleaned_data["text"].strip()
        if not value:
            raise forms.ValidationError("Escribe un comentario.")
        return value
