from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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