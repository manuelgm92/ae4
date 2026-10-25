-- Datos de ejemplo de la aplicación (TravelRoad adaptada al curso DPL).
-- PostgreSQL ejecuta este fichero UNA sola vez: al inicializar el volumen de
-- datos (carpeta /docker-entrypoint-initdb.d de la imagen oficial de Postgres).
-- Para volver a ejecutarlo desde cero:
--   docker compose down -v && docker compose up -d
--
-- Carga masiva: en un despliegue real los datos llegarían con COPY (ver
-- db/places.csv y la práctica guiada de PostgreSQL); aquí se incluyen unas
-- filas de ejemplo para que el despliegue sea verificable de inmediato.

CREATE TABLE IF NOT EXISTS places (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR(255) NOT NULL,
    visited BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO places (name, visited) VALUES
    ('Tokio', FALSE),
    ('Budapest', TRUE),
    ('Nairobi', FALSE),
    ('Berlín', TRUE),
    ('Lisboa', TRUE),
    ('Denver', FALSE),
    ('Moscú', FALSE),
    ('Oslo', FALSE),
    ('Río', TRUE),
    ('Cincinnati', FALSE),
    ('Helsinki', FALSE);
