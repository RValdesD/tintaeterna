from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from .models import StoryUpload

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "placeholder": "e-mail",
            "autocomplete": "email",
        }),
        error_messages={
            "required": "Ingresa tu correo electrónico.",
            "invalid": "Ingresa un correo electrónico válido.",
        },
    )

    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "placeholder": "contraseña",
            "autocomplete": "current-password",
        }),
        error_messages={
            "required": "Ingresa tu contraseña.",
        },
    )

class SignupForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "placeholder": "Correo electrónico",
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

        labels = {
            "username": "Nombre de usuario",
        }

        widgets = {
            "username": forms.TextInput(attrs={
                "autocomplete": "username",
                "placeholder": "Nombre de usuario",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Confirmar contraseña"

        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update({
                "autocomplete": "new-password",
                "placeholder": self.fields[name].label,
            })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo electrónico."
            )

        return email
    
class StoryUploadForm(forms.ModelForm):
    class Meta:
        model = StoryUpload
        fields = ("file", "tags")
        labels = {"file": "Archivo",
                  "tags": "Tags (Opcional)"}
        widgets = {
            "file": forms.FileInput(attrs={
                "accept": ".pdf,.epub,.txt",
            }),
            "tags": forms.CheckboxSelectMultiple(), #Muestra cajas de selección múltiple
        }

    def clean_file(self):
        file = self.cleaned_data["file"]
        extension = Path(file.name).suffix.lower()

        if extension not in {".pdf", ".epub", ".txt"}:
            raise forms.ValidationError(
                "Solo se permiten archivos PDF, EPUB y TXT."
            )

        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "El archivo no debe superar los 10 MB."
            )

        try:
            if extension == ".pdf":
                if not file.read(5).startswith(b"%PDF-"):
                    raise forms.ValidationError(
                        "El archivo no parece ser un PDF."
                    )

            elif extension == ".epub":
                try:
                    with ZipFile(file) as archive:
                        info = archive.getinfo("mimetype")

                        if info.file_size != len(b"application/epub+zip"):
                            raise forms.ValidationError(
                                "El archivo no parece ser un EPUB."
                            )

                        if archive.read(info) != b"application/epub+zip":
                            raise forms.ValidationError(
                                "El archivo no parece ser un EPUB."
                            )

                        archive.getinfo("META-INF/container.xml")

                except (
                    BadZipFile,
                    KeyError,
                    RuntimeError,
                    NotImplementedError,
                    OSError,
                ):
                    raise forms.ValidationError(
                        "El archivo EPUB está dañado o no es válido."
                    )

            elif extension == ".txt":
                try:
                    text = file.read().decode("utf-8-sig")
                except UnicodeDecodeError:
                    raise forms.ValidationError(
                        "Guarda el archivo TXT con codificación UTF-8."
                    )

                if any(
                    ord(character) < 32
                    and character not in "\t\n\r\f"
                    for character in text
                ):
                    raise forms.ValidationError(
                        "El archivo contiene datos que no son texto."
                    )
        finally:
            file.seek(0)

        return file

from io import BytesIO
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile
from .models import Profile


class ProfileDescriptionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["description"]
        labels = {"description": "Descripción"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5, "maxlength": 1000})}


class ProfilePictureForm(forms.ModelForm):
    avatar = forms.ImageField(label="Foto de perfil", required=True,
                              widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))

    class Meta:
        model = Profile
        fields = ["avatar"]

    def clean_avatar(self):
        upload = self.cleaned_data["avatar"]
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError("La imagen no puede superar 2 MB.")
        try:
            upload.seek(0)
            with Image.open(upload) as picture:
                if picture.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Usa una imagen JPG, PNG o WebP.")
                if max(picture.size) > 4096:
                    raise forms.ValidationError("El tamaño máximo es 4096 × 4096 píxeles.")
                picture.load()
                normalized = ImageOps.exif_transpose(picture).convert("RGBA")
                normalized.thumbnail((512, 512))
                output = BytesIO()
                normalized.save(output, format="PNG")
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError):
            raise forms.ValidationError("No se pudo leer la imagen.")
        return ContentFile(output.getvalue(), name="avatar.png")
