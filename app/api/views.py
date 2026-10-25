"""Vistas de la aplicación 'api' (curso DPL, UT4).

La aplicación expone:
- /             -> HTML generado por el servidor de aplicaciones (Django)
- /healthz      -> JSON 200 para healthchecks
- /api/mensaje  -> JSON con mensaje, hostname y fecha
- /api/visitas  -> contador de visitas persistido en /data/visitas.txt
- /api/lugares  -> filas de la tabla "places" de PostgreSQL (si hay BD)
- /api/login    -> autenticación contra un directorio LDAP (si hay LDAP_HOST)

La puerta pública del despliegue es el servidor Web (nginx) con el build de
Vite; estas vistas se consumen por detrás del proxy inverso (teoría en
[Servidores de aplicaciones](../../teoria/servidores-aplicaciones.md)).
La capa de datos se explica en [Base de datos](../../teoria/base-datos.md):
la tabla `places` la crea y carga `db/init.sql` al inicializarse el volumen.
"""

import json
import os
import socket
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponse, JsonResponse

# Configuración por variables de entorno (ninguna credencial real).
DATA_DIR = os.environ.get("APP_DATA_DIR", "/data")
APP_MENSAJE = os.environ.get("APP_MENSAJE", "Hola desde el servidor de aplicaciones DPL")


def _leer_contador():
    """Devuelve el contador actual desde el fichero de visitas."""
    ruta = os.path.join(DATA_DIR, "visitas.txt")
    try:
        with open(ruta, "r", encoding="utf-8") as fichero:
            return int(fichero.read().strip() or "0")
    except (FileNotFoundError, OSError, ValueError):
        return 0


def _incrementar_contador():
    """Incrementa el contador, lo persiste en el volumen y devuelve el valor."""
    os.makedirs(DATA_DIR, exist_ok=True)
    ruta = os.path.join(DATA_DIR, "visitas.txt")
    visitas = _leer_contador() + 1
    try:
        with open(ruta, "w", encoding="utf-8") as fichero:
            fichero.write(str(visitas))
    except OSError as error:
        # La aplicación sigue funcionando; el fallo queda en los logs.
        print(f"[aviso] No se pudo persistir el contador: {error}", flush=True)
    return visitas


def inicio(request):
    """Página HTML generada por el servidor de aplicaciones (vista Django)."""
    visitas = _incrementar_contador()
    html = (
        "<!doctype html>\n"
        '<html lang="es">\n'
        "<head><meta charset=\"utf-8\">"
        f"<title>{APP_MENSAJE}</title></head>\n"
        "<body>\n"
        f"<h1>{APP_MENSAJE}</h1>\n"
        f"<p>Contenedor: <strong>{socket.gethostname()}</strong></p>\n"
        f"<p>Visitas totales: <strong>{visitas}</strong></p>\n"
        "</body>\n"
        "</html>\n"
    )
    return HttpResponse(html)


def healthz(request):
    """Endpoint de salud: 200 solo si la aplicación responde."""
    return JsonResponse({"status": "ok", "hostname": socket.gethostname()})


def api_mensaje(request):
    """Endpoint JSON con el mensaje, el hostname del contenedor y la fecha."""
    return JsonResponse(
        {
            "mensaje": APP_MENSAJE,
            "hostname": socket.gethostname(),
            "fecha": datetime.now().isoformat(timespec="seconds"),
        }
    )


def api_visitas(request):
    """Endpoint JSON con el contador de visitas (persistido en el volumen)."""
    return JsonResponse({"visitas": _incrementar_contador()})


def api_lugares(request):
    """Endpoint JSON con los lugares de PostgreSQL (tabla `places`).

    Si no hay base de datos configurada (sin DB_HOST) devuelve 503 con un
    mensaje claro: la aplicación es funcional, pero consultar datos requiere
    el servicio `db` del despliegue (ver compose.yml).
    """
    if not getattr(settings, "DB_HOST", ""):
        return JsonResponse(
            {
                "error": "Base de datos no configurada",
                "detalle": "Define DB_HOST, DB_NAME, DB_USER y DB_PASSWORD",
            },
            status=503,
        )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, visited FROM places ORDER BY id")
            columnas = [columna[0] for columna in cursor.description]
            lugares = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    except (OperationalError, ProgrammingError) as error:
        return JsonResponse(
            {
                "error": "No se pudo consultar PostgreSQL",
                "detalle": str(error),
            },
            status=503,
        )
    return JsonResponse({"lugares": lugares, "total": len(lugares)})


def api_login(request):
    """Autentica a un usuario contra el directorio LDAP.

    Recibe `usuario` y `password` (formulario o JSON) y hace un *bind* LDAP con
    el DN del usuario. Es el mecanismo que integra la aplicación Web con el
    servicio de directorio (RA5-e, RA5-f). Variables de entorno:

    - ``LDAP_HOST``: URL del directorio (por ejemplo ``ldap://dpl-lab`` o
      ``ldap://IP_DPL_LAB``). Si no está definida, la autenticación LDAP está
      desactivada y se responde 503.
    - ``LDAP_BASE_DN``: base de búsqueda (por defecto ``ou=usuarios,dc=dpl,dc=local``).
    - ``LDAP_USER_FILTER``: filtro por usuario (por defecto ``(uid=%s)``).

    Nunca se escriben credenciales en el código: el bind usa el usuario y la
    contraseña que llegan en la petición.
    """
    ldap_host = os.environ.get("LDAP_HOST", "")
    if not ldap_host:
        return JsonResponse(
            {
                "error": "Directorio no configurado",
                "detalle": "Define LDAP_HOST para habilitar /api/login",
            },
            status=503,
        )

    if request.content_type == "application/json":
        try:
            datos = json.loads(request.body or "{}")
        except ValueError:
            datos = {}
        usuario = datos.get("usuario", "")
        password = datos.get("password", "")
    else:
        usuario = request.POST.get("usuario", "")
        password = request.POST.get("password", "")

    if not usuario or not password:
        return JsonResponse({"error": "Faltan usuario o contrasena"}, status=400)

    base_dn = os.environ.get("LDAP_BASE_DN", "ou=usuarios,dc=dpl,dc=local")
    filtro = os.environ.get("LDAP_USER_FILTER", "(uid=%s)")
    if "%s" in filtro:
        filtro = filtro % usuario
    user_dn = f"uid={usuario},{base_dn}"

    try:
        from ldap3 import Connection
        from ldap3.core.exceptions import LDAPException
    except ImportError:
        return JsonResponse({"error": "ldap3 no instalado"}, status=500)

    try:
        conexion = Connection(ldap_host, user=user_dn, password=password, auto_bind=True)
    except LDAPException as error:
        return JsonResponse(
            {"autenticado": False, "usuario": usuario, "detalle": str(error)},
            status=401,
        )

    perfil = {}
    try:
        conexion.search(search_base=base_dn, search_filter=filtro, attributes=["cn", "mail"])
        if conexion.entries:
            entrada = conexion.entries[0]
            perfil = {"cn": str(entrada.cn), "mail": str(entrada.mail)}
    except LDAPException:
        perfil = {}
    finally:
        conexion.unbind()

    return JsonResponse({"autenticado": True, "usuario": usuario, "perfil": perfil})
