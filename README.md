# Live AI Sales Assistant & Online Store

Demo de una tienda online con vista responsiva para móvil integrada con un asistente de ventas en tiempo real impulsado por IA (**Gemini Live**).

A través de la aplicación web, el usuario puede conversar en vivo con el agente, apuntar con la cámara de su teléfono para buscar e identificar productos en tiempo real, consultar el catálogo en la base de datos de la tienda y cerrar la venta durante la sesión.

## Alcance Principal

* **Tienda Online Mobile-First:** Interfaz web responsiva optimizada para dispositivos móviles.
* **Asistente de Ventas Live (Voz y Video):** Conversación bidireccional en tiempo real con Gemini Live.
* **Búsqueda Visual con Cámara:** Uso de la cámara del dispositivo para identificar productos y consultar disponibilidad/precios en el catálogo.
* **Cierre de Venta Asistido:** Orquestación de herramientas sobre la base de datos de la tienda para guiar al cliente hasta completar su compra.

## Architecture Overview

El proyecto sigue los principios de **Clean Architecture** y **Domain-Driven Design (DDD)**, construido principalmente con **FastAPI** (HTTP/WebSocket), **SQLAlchemy + Alembic** (Persistencia), **Strawberry** (GraphQL) y **MCP SDK** (Model Context Protocol).

El código del backend está organizado en capas dentro de `backend/src/`:

* **`core/`**: Preocupaciones transversales (configuración con Pydantic Settings, sesiones de base de datos y migraciones de Alembic en `core/db/`).
* **`features/<feature_name>/`**: Módulos divididos por funcionalidad (*feature-sliced*) que contienen:
  * **`domain/`**: Lógica de negocio pura. Incluye `entities` (objetos puros de Python), `repositories` (interfaces abstractas/protocolos) y `usecases` (orquestadores de reglas de negocio).
  * **`data/`**: Integraciones de datos externas. Incluye `models` (modelos ORM de SQLAlchemy), `mappers` (conversión entre entidad y modelo) y `repositories` (implementaciones de los repositorios).
  * **`presentation/`**: Puntos de entrada y controladores. Incluye `graphql/` (tipos, queries, mutations y routers de Strawberry) y `mcp_tools/` (definición de herramientas MCP).
* **`app.py`**: Aplicación raíz de FastAPI que monta el router GraphQL, herramientas MCP y transporte en tiempo real.

## Base de Datos y Migraciones

Levantar la base de datos PostgreSQL con Docker Compose:

```bash
docker compose up -d db
```

Ejecutar migraciones con Alembic (desde `backend/`):

```bash
alembic upgrade head
```

Cargar el catálogo de productos mock (desde la raíz del proyecto):

```bash
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < backend/src/core/db/seeds/mock_catalog.sql
```
