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

## Backend del agente de ventas

La feature `sales_agent` usa exclusivamente **Gemini Live**, con orquestación propia
de herramientas sobre los casos de uso de `products`, `providers` y `sales`.
El servidor y frontend antiguos de seguros se conservan; todavía no consumen este endpoint.

Configura las variables `DB_*` habituales y agrega a `.env` en la raíz:

```dotenv
GOOGLE_API_KEY=tu-clave
SALES_AGENT_GEMINI_MODEL=gemini-3.8-live
SALES_AGENT_VOICE=Kore
```

Desde `backend/`, instala las dependencias, aplica las migraciones y arranca:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn src.app:app --host 127.0.0.1 --port 8000 --workers 1 --ws-max-size 800000
```

Conecta un cliente a `ws://127.0.0.1:8000/ws/sales-agent`. La clave permanece en el
backend. El agente comienza en español y acepta estos mensajes JSON:

```json
{"type":"text","text":"Busca productos de panadería"}
{"type":"audio","data":"<PCM16 mono little-endian a 16000 Hz, en base64>"}
{"type":"close"}
```

El audio es PCM crudo, sin cabecera WAV. Envía fragmentos cortos continuamente;
Gemini detecta los turnos de voz. El texto inicia una respuesta y puede interrumpir
la generación en curso. El límite es de 800000 bytes por mensaje y 8000 caracteres
por texto. El cliente debe esperar `ready` antes de enviar contenido.

| Evento del servidor | Contenido y uso |
|---|---|
| `session` | `provider`, `model`, `tools`, `input_sample_rate: 16000`, `output_sample_rate: 24000` |
| `ready` | Conexión con Gemini establecida |
| `audio` | `data` en base64 y `mime_type`; reproducir PCM16 mono a 24 kHz |
| `transcript` | `speaker: user\|agent`, `id`, `text`, `final`; reemplazar el texto del mismo `id`, no concatenarlo |
| `tool` | `id`, `name`, `args`, `phase: running\|done\|error\|cancelled`, `result` |
| `interrupted` | Detener reproducción y descartar audio pendiente |
| `turn_complete` | El modelo terminó el turno |
| `error` | `message` legible; la sesión se cerrará |

Herramientas: `search_products`, `get_product_details`, `list_categories`,
`list_providers`, `add_to_cart`, `remove_from_cart`, `get_cart`, `checkout`.
Los precios son enteros en centavos; las fechas se serializan en ISO 8601.
`checkout` exige `confirmed: true`: el prompt instruye al modelo a pedir confirmación
explícita del cliente tras resumir el carrito. Este campo no constituye una
autorización independiente del modelo ni procesa un pago.

Cada ejecución abre su propia sesión de base de datos. Las operaciones del carrito
comparten un bloqueo por proceso: ejecuta **un solo worker/instancia** para esta demo
de un único cliente. El registro de una venta vacía el carrito y conserva el catálogo;
los precios no son históricos. No hay reintentos automáticos de operaciones ni
reconexión automática. Los identificadores repetidos de herramientas se ignoran
dentro de la misma conexión; no hay deduplicación entre conexiones distintas.

Las sesiones duran hasta 20 minutos o hasta que Gemini o el cliente cierren la
conexión. Se cancelan las tareas pendientes al cerrar. Si se pierde la conexión
durante una escritura, comprueba el estado antes de repetirla: la cancelación no
revierte una transacción ya confirmada. Los clientes web deben usar el mismo origen
que el backend (o un proxy del mismo origen). Este endpoint no agrega autenticación
y está pensado para uso local de la demo.

Pruebas desde `backend/`, con Gemini simulado y sin llamadas de pago:

```bash
python -m unittest discover -s tests -p 'test_sales*.py' -v
```
