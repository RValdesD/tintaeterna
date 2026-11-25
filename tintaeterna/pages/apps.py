from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'

    def ready(self):
        from . import signals  # noqa: F401
        from django.db import connection
        from django.db.backends.signals import connection_created
        from .text_search import register_sqlite_function

        def on_connection_created(sender, connection, **kwargs):
            register_sqlite_function(connection)

        connection_created.connect(on_connection_created, weak=False, dispatch_uid="pages_unaccent")
        if connection.connection is not None:        # por si la conexión ya estaba abierta
            register_sqlite_function(connection)
