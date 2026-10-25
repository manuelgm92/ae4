## compose.yml

En el archivo `compose.yml` se crea la infraestructura de la aplicación (Base de Datos, Herramienta de Administración, Backend en Django y Servidor Web/Proxy Inverso con Nginx).

El archivo define un proyecto llamado **`dpl-app`** que despliega 4 servicios interconectados dentro de una red interna de Docker Compose:

1. **`db`**: Capa de datos con PostgreSQL.
2. **`pgadmin`**: Interfaz web de administración para la base de datos.
3. **`app`**: Servidor de aplicaciones backend (Django).
4. **`nginx`**: Servidor web, proxy inverso y distribuidor de la SPA del frontend.

## 🗄️ 1. Servicio de Base de Datos (`db`)

```yaml
  db:
    image: postgres:16-alpine
    container_name: dpl-db
    environment:
      POSTGRES_DB: travelroad
      POSTGRES_USER: alumno
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data # datos persistentes
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # carga inicial
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alumno -d travelroad"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped
```
### **Propósito:**

* Este servicio levanta el motor de base de datos PostgreSQL para almacenar de forma persistente la información de la aplicación.
* Aislamiento de red: Al no incluir la sección ports, ningún puerto de la base de datos se expone hacia el ordenador anfitrión. 

Esto significa que tu máquina física no puede conectarse directamente desde fuera de Docker a este puerto; solo los demás servicios internos de la red de Docker (como la aplicación Django) pueden acceder a ella utilizando el nombre del servicio (db).

### **Configuración técnica paso a paso**

* `image: postgres:16-alpine`
    * Utiliza la imagen oficial de PostgreSQL versión 16, basada en la variante Alpine. Esta variante es una distribución de Linux ultra ligera y minimalista, lo que reduce drásticamente el peso de la imagen, acelera su descarga y optimiza el uso de recursos.
* `container_name: dpl-db`
    * Asigna un nombre fijo, limpio y personalizado (`dpl-db`) al contenedor. Esto facilita enormemente su identificación y gestión al ejecutar comandos en la terminal (como `docker logs dpl-db` o `docker exec -it dpl-db ...`).
* `environment`: (Variables de entorno)
    * Configuran el comportamiento inicial del motor de base de datos sin necesidad de modificar configuraciones internas:
        * `POSTGRES_DB: travelroad`: Crea automáticamente una base de datos inicial llamada `travelroad` la primera vez que se inicia el contenedor.
        * `POSTGRES_USER: alumno`: Define el nombre de usuario administrador/principal con el que se conectará la aplicación.
        * `POSTGRES_PASSWORD: ${DB_PASSWORD}`: Establece la contraseña del usuario leyendo el valor de forma segura desde una variable de entorno externa (definida en tu archivo `.env` o en el sistema), evitando dejar claves en texto plano dentro del código.
* `volumes`: (Persistencia y configuración inicial)
    * `db-data:/var/lib/postgresql/data` # datos persistentes: Conecta un volumen nombrado llamado `db-data` a la ruta interna donde PostgreSQL guarda todos sus registros. Esto garantiza que la información de la base de datos no se pierda aunque apagues o elimines los contenedores con `docker compose down`.
    * `./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro` # carga inicial: Monta un script SQL local (./db/init.sql) dentro de la carpeta de inicialización automática de Postgres en modo solo lectura (`ro` de read-only). PostgreSQL ejecutará este script de forma automática únicamente la primera vez que se cree el volumen de datos (ideal para poblar esquemas, tablas o datos de prueba iniciales).
* `healthcheck`: (Comprobación de estado)
    * Permite que Docker supervise si la base de datos realmente está operativa y lista para recibir tráfico, evitando que otros servicios dependientes arranquen a tiempo antes de que la base de datos acepte conexiones.
    * `test: ["CMD-SHELL", "pg_isready -U alumno -d travelroad"]`: Ejecuta internamente el comando `pg_isready` para verificar si Postgres ya acepta conexiones para el usuario `alumno` y la base de datos `travelroad`.
    * `interval: 10s`: Realiza una nueva comprobación de salud cada 10 segundos.
    * `timeout: 5s`: Si la prueba tarda más de 5 segundos en responder, se cataloga temporalmente como fallida.
    * `retries: 5`: Si la comprobación falla 5 veces consecutivas, el contenedor cambia su estado a no saludable (`unhealthy`).
    * `start_period: 10s`: Otorga un margen inicial de 10 segundos para que el motor de la base de datos arranque con calma sin penalizar los primeros intentos de verificación.
* `restart`: unless-stopped
    * Política de reinicio automático: El contenedor se reiniciará automáticamente si se produce un fallo inesperado o si se reinicia el sistema Docker, a menos que hayas detenido el servicio de forma manual con un comando de parada explícito.

---

## 📊 2. Servicio de Administración (`pgadmin`)

```yaml
  pgadmin:
    image: dpage/pgadmin4
    container_name: dpl-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    volumes:
      - pgadmin-data:/var/lib/pgadmin
    ports: 
      - "5050:80"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -q -O - http://localhost:80/misc/ping | grep -q PING"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 60s
    restart: unless-stopped
```

### **Propósito:** 
Proporciona una interfaz gráfica web (PgAdmin 4) accesible desde el navegador en el puerto **`5050`** para gestionar visualmente la base de datos PostgreSQL.

* Este servicio despliega pgAdmin 4, una interfaz gráfica web en el puerto **`5050`** que permite gestionar, consultar y visualizar tu base de datos PostgreSQL cómodamente desde el navegador.
* Acceso externo controlado: A diferencia de la base de datos (que está completamente aislada en la red interna), pgAdmin sí expone un puerto hacia el anfitrión (5050:80) para que puedas abrir la interfaz web.

**Configuración técnica paso a paso**

* `image: dpage/pgadmin4`
    * Utiliza la imagen oficial y estándar de pgAdmin 4 mantenida por Dave Page, diseñada específicamente para ejecutarse de forma ligera en contenedores Docker.
* `container_name: dpl-pgadmin`
    * Asigna un nombre fijo y personalizado (`dpl-pgadmin`) al contenedor para identificarlo fácilmente al ejecutar comandos de Docker (como `docker logs dpl-pgadmin`).
* `environment`: (Variables de entorno de acceso)
    * Configuran las credenciales iniciales de administrador con las que podrás iniciar sesión en la interfaz web de pgAdmin:
        * `PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}`: Define el correo electrónico de acceso, leyendo su valor de forma segura desde tus variables de entorno externas (como un archivo `.env`).
        * `PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}`: Define la contraseña maestra de acceso, cargándola también desde el entorno para evitar claves en texto plano.
* `volumes`: (Persistencia de configuración)
    * `pgadmin-data:/var/lib/pgadmin`: Conecta un volumen nombrado llamado `pgadmin-data` a la ruta interna donde pgAdmin almacena sus configuraciones, servidores guardados y preferencias de usuario. Esto garantiza que no pierdas tus conexiones configuradas si apagas o eliminas los contenedores.
* `ports`: (Publicación de puertos)
    * `"5050:80"`: Mapea el puerto 80 interno del contenedor (donde el servidor web de pgAdmin está escuchando) al puerto 5050 de tu máquina anfitriona. Esto significa que puedes entrar a la interfaz gráfica abriendo tu navegador web en: `http://localhost:5050`.
* `depends_on`: (Dependencia de arranque)
    * `db`: con `condition: service_healthy`: Establece que el contenedor de pgAdmin no se iniciará hasta que el servicio de la base de datos (`db`) haya completado su arranque y su `healthcheck` indique que está sano (`healthy`).
* `healthcheck`: (Comprobación de estado)
    * `Supervisa de forma automatizada que el servidor web interno de pgAdmin responda correctamente a las peticiones HTTP.
test: `["CMD-SHELL", "wget -q -O - http://localhost:80/misc/ping | grep -q PING"]`: Ejecuta una solicitud HTTP silenciosa (`wget`) a la ruta interna de diagnóstico `/misc/ping` y busca la palabra clave `PING` mediante `grep` para confirmar que la aplicación web está viva y respondiendo.
    * `interval: 15s`: Realiza la comprobación de salud cada 15 segundos.
    * `timeout: 5s`: Si la respuesta tarda más de 5 segundos, la prueba se cataloga como fallida.
    * `retries: 5`: Si falla 5 veces consecutivas, el contenedor se marca como no saludable (`unhealthy`).
    * `start_period`: 60s: Otorga un margen generoso de 60 segundos (1 minuto) de gracia inicial. Esto es muy útil porque pgAdmin es una aplicación pesada (basada en Python/Flask) y tarda un tiempo prudencial en arrancar por completo la primera vez.
* `restart: unless-stopped`
    * Política de reinicio automático: El contenedor se reiniciará automáticamente ante un fallo inesperado o un reinicio del sistema, a menos que lo hayas detenido de forma manual.

---

## ⚙️ 3. Servidor de Aplicaciones Backend (`app`)

```yaml
  app:
    build: ./app
    container_name: dpl-django
    environment:
      APP_MENSAJE: "Hola desde el servidor de aplicaciones DPL (UT4)"
      APP_DATA_DIR: /data
      DB_HOST: db
      DB_NAME: travelroad
      DB_USER: alumno
      DB_PASSWORD: ${DB_PASSWORD}
      LDAP_HOST: ${LDAP_HOST:-}
      LDAP_BASE_DN: "ou=usuarios,dc=dpl,dc=local"
      LDAP_USER_FILTER: "(uid=%s)"
    volumes:
      - ./data:/data
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=3)"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s
    restart: unless-stopped
```

### **Propósito:** 

* Este servicio despliega el backend de la aplicación desarrollado en Django. Es el núcleo que procesa la lógica de negocio, expone los endpoints de la API y conecta la interfaz de usuario con la base de datos y los servicios externos (como LDAP).
* Aislamiento de red: Al igual que la base de datos, no expone puertos directamente hacia tu ordenador anfitrión (el puerto 8000 de Django se queda dentro de la red interna de Docker). Todo el tráfico externo pasa primero de forma segura a través del servidor Nginx (el proxy inverso).

#### **Configuración técnica paso a paso**
* `build: ./app`
    * Indica que la imagen de Docker para este servicio no se descarga de un registro público, sino que se construye localmente utilizando el código y el archivo `Dockerfile` ubicados dentro de la carpeta `./app`.
* `container_name: dpl-django`
    * Asigna un nombre fijo, limpio y personalizado al contenedor para facilitar su identificación y manejo al ejecutar comandos en la terminal (como `docker logs dpl-django`).
* `environment`: (Variables de entorno)
    * Configuran el comportamiento del backend de Django sin necesidad de alterar su código fuente:
        * `APP_MENSAJE` / `APP_DATA_DIR`: Parámetros de configuración interna de la aplicación (como el mensaje de bienvenida y la ruta del directorio de datos).
        * Conexión a PostgreSQL (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`): Configuran la conexión a la base de datos apuntando al nombre del servicio db dentro de la red de Docker, reutilizando la contraseña segura mediante ${DB_PASSWORD}.
        * Autenticación LDAP (`LDAP_HOST`, `LDAP_BASE_DN`, `LDAP_USER_FILTER`): Prepara el backend para autenticar usuarios (típico de UT5) contra un servidor de directorio si se define la variable LDAP_HOST. Si no se define, usa el valor por defecto vacío (`${LDAP_HOST:-}`).
* `volumes`: (Persistencia local en el anfitrión)
    * `- ./data:/data`: Realiza un montaje de tipo bind mount. Conecta la carpeta local `./data` de tu ordenador directamente con la ruta `/data` dentro del contenedor. Esto permite que la aplicación guarde archivos que persistirán y podrás editar o consultar directamente desde tu sistema operativo.
* `depends_on`: (Condición de arranque)
    * `db` con `condition: service_healthy`: Establece una dependencia estricta. El contenedor de Django no se iniciará hasta que el servicio de la base de datos (`db`) haya arrancado por completo y su healthcheck confirme que está sano (`healthy`), evitando errores iniciales de conexión rechazada.
* `healthcheck`: (Comprobación de estado)
    * Supervisa automáticamente que el servidor Django esté vivo y respondiendo peticiones web de forma correcta.
    * `test`: Utiliza el propio intérprete de Python de la imagen para ejecutar un script rápido de una línea con `urllib.request` que realiza una petición HTTP GET interna a la ruta de diagnóstico `http://localhost:8000/healthz`, esperando una respuesta con un tiempo límite de 3 segundos.
    * `interval: 15s`: Realiza la prueba de salud cada 15 segundos.
    * `timeout: 5s`: Si la respuesta tarda más de 5 segundos, la comprobación se cataloga como fallida.
    * `retries: 3`: Si falla 3 veces consecutivas, el contenedor se marca oficialmente como no saludable (unhealthy).
    * `start_period: 10s`: Otorga un margen inicial de 10 segundos para que la aplicación Django cargue todas sus dependencias y levante el servidor antes de empezar a penalizar los fallos de salud.
* `restart: unless-stopped`
    * Política de reinicio automático: El contenedor se reiniciará automáticamente si se produce un fallo inesperado o si se reinicia el sistema Docker, a menos que hayas detenido el servicio de forma manual.

---

## 🌐 4. Servidor Web y Proxy Inverso (`nginx`)

```yaml
  nginx:
    image: nginx:1.27-alpine
    container_name: dpl-nginx
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - "8000:80"
    depends_on:
      app:
        condition: service_healthy
    restart: unless-stopped
```

* **Propósito:** 

Actúa como la única puerta de entrada pública de la arquitectura. Sirve los archivos estáticos de la interfaz frontend (SPA) y reenvía las peticiones dirigidas a `/api/` y `/healthz` hacia el servicio backend (`app`).

* Este servicio despliega Nginx y actúa como la puerta de entrada principal (front-door) de toda tu aplicación.
    * Doble función:
        1. Servidor Web: Se encarga de servir los archivos estáticos de la interfaz gráfica (el frontend compilado con Vite).
        2. Proxy Inverso: Intercepta las peticiones de los usuarios y las redirige inteligentemente: manda el tráfico de `/api/` y `/healthz` hacia el contenedor del backend (app / Django).
    * Punto único de acceso: Es el único servicio que expone un puerto hacia el exterior (`8000`), manteniendo ocultos y protegidos los servicios internos de la red de Docker (Django, PostgreSQL y pgAdmin).

**Configuración técnica paso a paso**

* `image: nginx:1.27-alpine`
    * Utiliza la imagen oficial de Nginx versión 1.27, basada en la variante Alpine (una distribución de Linux minimalista que garantiza un contenedor sumamente ligero, rápido y seguro).
* `container_name: dpl-nginx`
    * Asigna un nombre fijo, limpio y personalizado al contenedor para facilitar su identificación y control en la terminal (por ejemplo, al revisar registros con `docker logs dpl-nginx`).
* `volumes`: (Configuración de enrutamiento)
    * `- ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro`: Realiza un montaje de tipo bind mount en modo solo lectura (ro de read-only). Toma tu archivo de configuración personalizado local (`./nginx/default.conf`) y lo inyecta directamente dentro de la ruta donde Nginx busca las configuraciones de los servidores virtuales. Aquí es donde se definen las reglas de `try_files` para la SPA y las directivas `proxy_pass` hacia Django.
* `ports`: (Publicación del puerto principal al anfitrión)
    * `- "8000:80"`: Mapea el puerto 80 interno del contenedor (donde Nginx está escuchando las peticiones web) al puerto 8000 de tu máquina anfitriona. Esto significa que para ver la aplicación en tu navegador solo tienes que entrar a: `http://localhost:8000`.
* `depends_on`: (Condición de arranque)
    * `app` con `condition: service_healthy`: Establece una dependencia estricta. El contenedor de Nginx no se iniciará hasta que el servicio de la aplicación (app / Django) haya arrancado por completo y su `healthcheck` confirme que está sano (`healthy`). Esto evita errores molestos de tipo Bad Gateway o Connection Refused si un usuario intenta entrar a la web antes de que el backend esté listo.
* `restart`: unless-stopped
    * Política de reinicio automático: El contenedor se reiniciará de forma automática ante un fallo inesperado o un reinicio del sistema Docker, a menos que hayas detenido el servicio manualmente.

---

## 📦 Declaración de Volúmenes Globales

```yaml
volumes:
  db-data:
  pgadmin-data:
```

* Se declaran los volúmenes persistentes gestionados por Docker (`db-data` y `pgadmin-data`) para garantizar que la información de la base de datos y las preferencias de PgAdmin no se pierdan al destruir o recrear los contenedores.