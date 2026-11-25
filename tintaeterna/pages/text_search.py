"""Búsqueda de obras sin distinguir tildes ni mayúsculas ("senor" encuentra "Señor")."""
import unicodedata

from django.db.models import Func, Q, TextField, Value
from django.db.models.functions import Coalesce, NullIf

SQLITE_FUNCTION = "UNACCENT_PY"


def normalize_text(text):
    """Minúsculas y sin tildes: 'Señor  Ñandú' -> 'senor nandu'."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(plain.casefold().split())


class Unaccent(Func):
    """Aplica `normalize_text` a una columna dentro de la consulta SQL."""
    function = SQLITE_FUNCTION
    arity = 1
    output_field = TextField()


def register_sqlite_function(connection):
    """SQLite no trae una función para quitar tildes: se registra la de Python."""
    if connection.vendor == "sqlite":
        connection.connection.create_function(SQLITE_FUNCTION, 1, normalize_text, deterministic=True)


def search_works(works, query):
    """Filtra `works` por título, nombre de archivo y autor (nombre o usuario)."""
    needle = normalize_text(query)
    if not needle:
        return works
    works = works.annotate(
        search_title=Unaccent(Coalesce(NullIf("title", Value("")), "original_name")),
        search_file=Unaccent("original_name"),
        search_user=Unaccent("owner__username"),
        search_name=Unaccent("owner__first_name"),
    )
    return works.filter(
        Q(search_title__contains=needle) | Q(search_file__contains=needle)
        | Q(search_user__contains=needle) | Q(search_name__contains=needle)
    )