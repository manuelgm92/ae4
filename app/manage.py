#!/usr/bin/env python
"""Utilidad de línea de comandos de Django (curso DPL, UT4).

No se usa en el despliegue (Gunicorn sirve config.wsgi), pero forma parte
de un proyecto Django real: permite lanzar tareas de administración dentro
del contenedor, por ejemplo `python manage.py check`.
"""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Están instaladas las dependencias "
            "del proyecto? (pip install -r requirements.txt)"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()