"""Punto de entrada WSGI para Gunicorn (gunicorn config.wsgi:application).

WSGI (Web Server Gateway Interface) es el protocolo estándar de Python que
conecta el servidor (Gunicorn) con la aplicación (Django). Teoría en
[Servidores de aplicaciones](../../teoria/servidores-aplicaciones.md).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()