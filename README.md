# Insurance Claim Live Agent Team

Un agente de reclamos de seguros que puede hablar, escuchar, ver los daños a través de tu cámara y dibujar bocetos del incidente mientras la conversación continúa. Desarrollado con Gemini 3.8 Live, con un avatar en vivo opcional para voz y video sincronizados.

El agente registra los detalles en un cuaderno de campo, verifica registros de pólizas simuladas y solicita la información faltante. Un equipo de agentes en segundo plano aplica reglas de admisión y prepara un paquete de reclamo descargable con notas, evidencia capturada e ilustraciones para revisión humana.

![Notebook and evidence example from the original voice and camera interface](assets/insurance-claim-live-agent-team-notebook.png)

## Características

* **Conversación en vivo:** habla o escribe, con transcripciones en tiempo real.
* **Avatar opcional:** voz y video sincronizados, con Kira y Kore como combinación de ejemplo.
* **Evidencia por cámara:** los fotogramas capturados incluyen descripciones y estado de verificación.
* **Bocetos del incidente:** ilustraciones basadas en la descripción del reclamante, actualizadas tras correcciones.
* **Cuaderno del reclamo:** hechos extraídos, información faltante, comprobaciones de póliza y enrutamiento.
* **Descarga del paquete:** archivo ZIP con notas en Markdown, un manifiesto de evidencia, fotos capturadas y bocetos.
* **Diseño para escritorio:** llamada y cámara a la izquierda, notas en el centro, transcripción y lista de verificación a la derecha. En dispositivos móviles se apilan las secciones.

## Configuración

Requiere Python 3.12 y una clave de API de Google con acceso a los modelos configurados.

```bash
cd voice_ai_agents/insurance_claim_live_agent_team
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configura estos valores en `.env`:

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=False
GOOGLE_API_KEY=tu-clave-de-api-de-google
```

Inicia la aplicación:

```bash
python -m uvicorn live_demo.server:app --reload --host 127.0.0.1 --port 4177
```

Abre [localhost:4177](http://127.0.0.1:4177/).

* **Talk:** inicia la conversación por voz.
* **Show camera:** comparte los daños con el agente.
* **Text box:** envía un turno escrito a través de la misma sesión en vivo.
* **Adjuster packet:** previsualiza y descarga el paquete.
* **New intake:** limpia la admisión actual y detiene sus recursos multimedia y trabajo en segundo plano.

Los datos de admisión se almacenan en memoria. Descarga tu paquete antes de reiniciar o restablecer; la aplicación no lo envía a una aseguradora.

## Avatar en vivo opcional

Requiere acceso a Google Cloud para Gemini Live y Application Default Credentials. Los requisitos de Python incluyen soporte para el avatar.

```bash
gcloud auth application-default login
```

Agrégalo a `.env`, luego reinicia el servidor:

```dotenv
FNOL_AVATAR_NAME=Kira
FNOL_AVATAR_PROJECT=tu-id-de-proyecto
FNOL_AVATAR_LOCATION=us-central1
FNOL_AVATAR_VOICE=Kore
```

* Mantén `GOOGLE_API_KEY` y `GOOGLE_GENAI_USE_VERTEXAI=False` para el procesamiento del reclamo y los bocetos.
* Solo la conexión del avatar utiliza el proyecto de Cloud y las credenciales anteriores.
* Deja sin definir tanto `FNOL_AVATAR_NAME` como `FNOL_AVATAR_IMAGE` para el modo de solo voz.
* La reproducción requiere Media Source Extensions y soporte para H.264/AAC. Los navegadores no compatibles usan el modo de voz.
* Si la reproducción automática se bloquea, selecciona **Play voice and video**. Los errores del decodificador ofrecen **Continue with voice**.
* El video del avatar es independiente de la cámara del reclamante y nunca cuenta como evidencia.

### Apariencia personalizada

Los retratos personalizados requieren un proyecto de Google Cloud habilitado en la lista de permitidos para avatares personalizados.

```dotenv
FNOL_AVATAR_IMAGE=/ruta/a/tu/avatar.png
FNOL_AVATAR_VOICE=Kore
```

* Proporciona un archivo PNG de menos de 5 MB, de al menos 704 × 1280 píxeles.
* Las rutas pueden ser absolutas o relativas al directorio de la aplicación.
* La imagen anula `FNOL_AVATAR_NAME` como referencia del avatar para la API.
* La vestimenta de los avatares predeterminados no se puede cambiar mediante un prompt.

## Configuración de variables

Reinicia el servidor después de cambiar `.env`.

| Variable | Valor por defecto | Propósito |
| --- | --- | --- |
| `FNOL_GEMINI_LIVE_MODEL` | `gemini-3.8-live` | Conversación en vivo y avatar |
| `FNOL_SKETCH_MODEL` | `gemini-3.1-flash-image` | Bocetos del incidente |
| `FNOL_VOICE` | `Kore` | Respuestas de solo voz |
| `FNOL_TRANSCRIPTION_VOCABULARY` | Vacío | Pistas de reconocimiento de voz separadas por comas |
| `FNOL_AVATAR_NAME` | Vacío | Avatar predeterminado; vacío lo desactiva salvo que se configure una imagen |
| `FNOL_AVATAR_PROJECT` | Vacío | Proyecto de Cloud del avatar |
| `FNOL_AVATAR_LOCATION` | `us-central1` | Región de la API del avatar |
| `FNOL_AVATAR_VOICE` | `Kore` | Voz del avatar |
| `FNOL_AVATAR_IMAGE` | Vacío | Ruta del retrato personalizado |

Las pistas de vocabulario son opcionales, no establecen identidad y no garantizan la ortografía. La plantilla no incluye modificaciones de nombres personales ni un guion de conversación fijo.

## Comportamiento de la cámara y bocetos

| Entrada | Comportamiento |
| --- | --- |
| Cámara apagada, con suficiente detalle del incidente | Dibuja una ilustración |
| Cámara encendida, mostrando daños | Captura y verifica el fotograma de forma independiente |
| Vista de cámara poco clara | Solicita una toma más clara |
| Solicitud explícita de diagrama | Dibuja en cualquiera de los modos de cámara |
| Corrección sobre un boceto | Vuelve a dibujar utilizando los detalles corregidos |

* Los saludos iniciales, descripciones vagas e inspecciones sin pérdidas no activan bocetos automáticos.
* Los bocetos generados son ilustraciones, no evidencia fotográfica.
* Los documentos descritos como disponibles no se marcan como recibidos hasta que el servidor los capture.

## Prueba un reclamo

Usa este ejemplo ficticio con la cámara apagada:

> Soy Maya Singh, póliza H0-44721. Nuestro sótano se inundó cuando falló la bomba de sumidero.
>
> Nadie resultó herido. El agua entró por las escaleras y se extendió por la alfombra hacia las cajas.

El agente consulta la póliza simulada, registra los hechos, pide los detalles faltantes y dibuja un boceto cuando tiene suficiente información de la escena.

### Pólizas simuladas

| Póliza | Titular | Tipo | Estado |
| --- | --- | --- | --- |
| H0-44721 | Maya Singh | Propietarios (*Homeowners*) | Activa |
| AUTO-90210 | Jordan Lee | Auto | Activa |
| RNT-3008 | Priya Shah | Inquilinos (*Renters*) | Activa |
| TRV-7711 | Alex Chen | Viajes (*Travel*) | Activa |
| MED-5520 | Sam Rivera | Reembolso médico | Activa |
| AUTO-11111 | Chris Park | Auto | Vencida (*Lapsed*) |

Las pólizas desconocidas, vencidas, que no coinciden o fuera del período de cobertura se enrutan a revisión humana. Estos registros son ejemplos, no una conexión con una aseguradora real.

## Arquitectura

| Componente | Responsabilidad |
| --- | --- |
| `agent.py` | Grafo ADK: normalización, clasificación, validación y generación del paquete |
| `policies.py`, `schemas.py` | Reglas de admisión, enrutamiento y datos estructurados |
| `policy_directory.py` | Registros de pólizas simuladas |
| `live_demo/live_tools.py` | Configuración en vivo, prompts y declaración de herramientas |
| `live_demo/server.py` | Sesiones, transporte WebSocket, herramientas y descargas |
| `live_demo/app.js` | Conversación, entrada de cámara y actualizaciones del cuaderno |
| `live_demo/avatar.js` | Reproducción sincronizada del avatar, interrupción y alternativa de contingencia |
| `live_demo/index.html`, `styles.css` | Interfaz responsiva |

* `gemini-3.8-live` gestiona la conversación, la entrada de cámara y la salida del avatar opcional.
* `gemini-3.8-flash` extrae los hechos del reclamo y verifica las fotos capturadas.
* `gemini-3.1-flash-image` genera los bocetos.
* Herramientas en segundo plano: `lookup_policy`, `sync_claim_packet`, `pin_evidence_photo` y `draw_incident_sketch`.
* Las herramientas se ejecutan sin bloquear la conversación. Los resultados urgentes pueden interrumpir; otros resultados llegan cuando el usuario está inactivo.
* El grafo del reclamo también se ejecuta después de los turnos finalizados del reclamante y almacena en caché los resultados por revisión de reclamo.

## Pruebas

Ejecuta desde el directorio de la aplicación. Las pruebas de JavaScript requieren Node.js.

```bash
python -m unittest discover -s tests -p 'test_*.py'
node tests/client-regressions.cjs
node tests/avatar-player.cjs
```

Las pruebas cubren reglas de reclamos, evidencia, sesiones, transcripciones, interrupciones, reproducción del avatar y descargas. Las llamadas a modelos y dispositivos están simuladas (*mocked*); verifica el comportamiento del micrófono y la cámara en vivo por separado.
