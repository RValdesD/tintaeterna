# TintaEterna

Aplicación web para compartir y gestionar escritos, desarrollada como proyecto de Ingeniería de Software. Su diseño es sencillo y está orientado a una comunidad de lectores y autores.

## Funcionalidades

- Registro de cuentas, inicio de sesión con correo y contraseña y cierre de sesión.
- Página de inicio con secciones de obras populares y recomendadas para usuarios conectados.
- Carga de archivos PDF, EPUB y TXT mediante selección o drag n drop, con un límite de 10 MB por archivo.
- Obras con portada personalizable, capitulos asignables, pagina dedicada
- Lector para estos archivos, junto con un sistema de marcadores.
- Listado de archivos propios y eliminación de los archivos del usuario autenticado.
- Modo claro y oscuro con la preferencia guardada entre páginas.
- Perfiles personalizables con imagenes y banners
- Sistema simple de moderación a través de cuentas @admin.cl

## Tecnologías

- **Backend:** Python y Django, con autenticación por sesiones.
- **Frontend:** HTML, CSS y JavaScript.
- **Base de datos:** SQLite.
- **Archivos:** almacenamiento local en la carpeta `media/`.

## Ejecución local

Con las dependencias instaladas y el entorno virtual activado, ejecutar desde la carpeta que contiene `manage.py`:

```bash
python manage.py migrate
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ en el navegador. Para subir y eliminar archivos es necesario iniciar sesión.

## Estado
FInalizado en cuanto a las exigencias esperadas, pero con algunos cambios futuros pendientes.
