"""Configuración del proyecto Django (curso DPL, UT4).

Entorno de laboratorio: `ALLOWED_HOSTS = ["*"]` solo es válido en prácticas
con Docker y red interna (nginx como única puerta). En producción se fija
el dominio real del sitio (por ejemplo `ALLOWED_HOSTS = ["app.dpl.local"]`).

La capa de datos es OPCIONAL: si existen las variables de entorno de conexión
(DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) la aplicación usa PostgreSQL; si no,
funciona sin base de datos (modo mínimo para las primeras prácticas).
Teoría: [Base de datos para el despliegue](../../teoria/base-datos.md).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Clave de laboratorio: jamás usar esta clave en un despliegue real.
# En producción se inyecta por variable de entorno (SECRET_KEY).
SECRET_KEY = "dpl-laboratorio-2026-cambiar-en-produccion"

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Aplicaciones instaladas: solo "api" (el proyecto es deliberadamente mínimo).
INSTALLED_APPS = [
    "api",
]

# Sin middlewares ni sesiones: el proyecto mínimo no las necesita.
MIDDLEWARE = []

ROOT_URLCONF = "config.urls"

# Sin plantillas: las vistas devuelven HTML/JSON directamente.
TEMPLATES = []

# Punto de entrada WSGI que usa Gunicorn: gunicorn config.wsgi:application
WSGI_APPLICATION = "config.wsgi.application"

# --- Capa de datos (opcional): PostgreSQL por variables de entorno ---------
# Si DB_HOST está definida se configura el motor PostgreSQL con el driver
# psycopg. Nunca se escriben credenciales en el código: llegan por el entorno
# (por ejemplo, desde compose.yml; valores de ejemplo alumno / CAMBIAR_ESTO).
DB_HOST = os.environ.get("DB_HOST", "")
if DB_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "travelroad"),
            "USER": os.environ.get("DB_USER", "alumno"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "CAMBIAR_ESTO"),
            "HOST": DB_HOST,
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    # Sin base de datos: el estado de la aplicación (contador de visitas) se
    # persiste en un fichero sobre un volumen Docker (/data/visitas.txt).
    DATABASES = {}

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"