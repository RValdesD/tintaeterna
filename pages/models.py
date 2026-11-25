from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models


#Construye la ruta de almacenamiento de un archivo de obra. El archivo queda dentro de una carpeta asociada al propietario y recibe un nombre UUID para evitar colisiones; conserva la extensión original en minúsculas.
def story_file_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"stories/{instance.owner_id}/{uuid4().hex}{extension}"

#Representa una etiqueta que puede asociarse a obras y a los gustos de los perfiles. El nombre es único para evitar etiquetas duplicadas.
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre del tag")

    #Devuelve el nombre de la etiqueta para mostrarla de forma legible en formularios y en el panel de administración.
    def __str__(self):
        return self.name

#Genera la ruta de almacenamiento de una portada. La imagen se organiza por propietario y recibe un nombre UUID con extensión PNG.
def cover_file_path(instance, filename):
    return f"covers/{instance.owner_id}/{uuid4().hex}.png"

#Representa una obra subida por un usuario. Guarda el archivo original, sus datos de presentación, portada, fecha de subida y etiquetas. También permite vincular obras de muestra mediante sample_key y sample_cover.
class StoryUpload(models.Model):
    sample_key = models.CharField(max_length=450, unique=True, null=True, blank=True, editable=False)
    sample_cover = models.CharField(max_length=255, blank=True, editable=False)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=3000, blank=True)
    cover = models.ImageField(upload_to=cover_file_path, blank=True)

    @property
    #Entrega el título personalizado cuando existe; en caso contrario, utiliza el nombre original del archivo como título visible.
    def display_title(self):
        return self.title or Path(self.original_name).stem

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="story_uploads",
    )
    file = models.FileField(upload_to=story_file_path, blank=True)
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    tags = models.ManyToManyField(Tag, blank=True, related_name="stories", verbose_name="Tags")
    #Devuelve el nombre original del archivo como representación textual de la obra.
    def __str__(self):
            return self.original_name

    #Si la obra se guarda sin título, usa el nombre del archivo sin su extensión (recortado al largo máximo del campo).
    def save(self, *args, **kwargs):
        if not self.title and self.original_name:
            max_length = self._meta.get_field("title").max_length
            self.title = Path(self.original_name).stem[:max_length]
        super().save(*args, **kwargs)

#Guarda el progreso de lectura de un usuario en una obra. La restricción única de Meta impide que un usuario tenga más de un marcador para la misma obra; el orden predeterminado muestra primero los actualizados recientemente.
class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="bookmarks")
    story = models.ForeignKey(StoryUpload, on_delete=models.CASCADE,
                              related_name="bookmarks")
    location = models.CharField(max_length=2000)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"],
                                               name="unique_user_story_bookmark")]
        ordering = ["-updated_at"]

#Genera una ruta privada por usuario para almacenar su avatar, utilizando un nombre UUID y extensión PNG.
def avatar_file_path(instance, filename):
    return f"avatars/{instance.user_id}/{uuid4().hex}.png"

#Genera una ruta privada por usuario para almacenar su banner, utilizando un nombre UUID y extensión PNG.
def banner_file_path(instance, filename):
    return f"banners/{instance.user_id}/{uuid4().hex}.png"

#Almacena la información complementaria del usuario: descripción, avatar, banner y etiquetas que representan sus gustos. La relación uno a uno garantiza un perfil por cuenta.
class Profile(models.Model):
    gustos = models.ManyToManyField(Tag, blank=True, related_name="preferred_by", verbose_name="Gustos")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="profile")
    description = models.TextField(max_length=1000, blank=True)
    avatar = models.ImageField(upload_to=avatar_file_path, blank=True)
    banner = models.ImageField(upload_to=banner_file_path, blank=True)

    #Devuelve el nombre de usuario asociado al perfil.
    def __str__(self):
        return self.user.username

#Almacena los atributos de moderación de una cuenta. is_admin identifica cuentas con privilegios administrativos y no puede editarse desde formularios; is_silenced indica si la cuenta tiene restringida la publicación.
class ModerationAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_account")
    is_admin = models.BooleanField(default=False, editable=False)
    is_silenced = models.BooleanField(default=False)

#Representa una notificación de moderación dirigida a un usuario. Conserva el título de la obra, el motivo, la fecha y el actor responsable cuando este todavía existe.
class ModerationNotice(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_notices")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    work_title = models.CharField(max_length=255)
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

#Registra una acción de moderación con su responsable, objetivo, motivo y fecha. El actor admite valores nulos para conservar el registro aunque la cuenta relacionada deje de existir.
class ModerationLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=30)
    target = models.CharField(max_length=255)
    reason = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)


#Representa un comentario publicado en una obra. Puede pertenecer a un autor registrado o conservar únicamente el nombre mostrado, y admite respuestas mediante una relación recursiva parent/replies.
class Comentarios(models.Model):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reader_comments")
    fecha= models.DateTimeField(auto_now_add=True)
    nombre = models.CharField(max_length=100)
    texto = models.TextField()
    historia = models.ForeignKey(
        'StoryUpload',
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    #Identifica el comentario mediante el nombre mostrado de su autor y la obra a la que pertenece.
    def __str__(self):
        return f"{self.nombre} en {self.historia}"

#Representa un comentario escrito por un usuario en el perfil de otra persona. La relación recursiva permite respuestas y el orden cronológico facilita mostrar la conversación.
class ProfileComment(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="comments")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile_comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

#Define un capítulo o sección de una obra mediante un rango de páginas. Las restricciones de base de datos exigen que la página inicial sea al menos 1 y que la página final no sea anterior a la inicial.
class StoryChapter(models.Model):
    story = models.ForeignKey(StoryUpload, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()

    class Meta:
        ordering = ['start_page', 'pk']
        constraints = [
            models.CheckConstraint(condition=models.Q(start_page__gte=1), name='chapter_positive_start'),
            models.CheckConstraint(condition=models.Q(end_page__gte=models.F('start_page')), name='chapter_ordered_range'),
        ]
