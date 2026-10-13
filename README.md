# Neurotry Live Onboarding

Una experiencia multimodal de bienvenida que conversa por voz, captura una foto con consentimiento y crea una tarjeta de presentación corporativa. La generación del avatar ocurre en segundo plano mientras Gemini Live recopila los datos personales, haciendo visible que ambos procesos son no bloqueantes.

## Flujo

1. La IA pide encender la cámara y solicita consentimiento explícito.
2. Tras una cuenta regresiva, `capture_user_photo` congela el frame más reciente y la interfaz muestra un flash y la foto real.
3. `generate_corporate_avatar` comienza a transformar la foto en un retrato Neurotry azul.
4. Sin esperar a la imagen, la conversación recopila nombre, edad, departamento y una descripción corta mediante `update_user_profile`.
5. La tarjeta se actualiza en vivo y puede abrirse en una vista optimizada para guardarla como PDF desde el navegador.

La conversación del agente usa únicamente audio. El avatar de la tarjeta es una imagen estática; no se genera video ni GIF.

## Ejecutar

Requiere Python 3.12 y una clave de Google con acceso a los modelos configurados.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y agrega GOOGLE_API_KEY
python -m uvicorn live_demo.server:app --reload --host 127.0.0.1 --port 4177
```

Abre [http://127.0.0.1:4177](http://127.0.0.1:4177). Permite cámara y micrófono cuando el navegador lo solicite.

## Configuración

| Variable | Predeterminado | Uso |
| --- | --- | --- |
| `GOOGLE_API_KEY` | — | Credencial para Gemini Live y generación de imagen |
| `NEUROTRY_LIVE_MODEL` | `gemini-3.8-live` | Conversación por audio y function calling |
| `NEUROTRY_IMAGE_MODEL` | `gemini-3.1-flash-image` | Transformación foto→avatar |
| `NEUROTRY_VOICE` | `Kore` | Voz sintetizada |
| `NEUROTRY_TRANSCRIPTION_VOCABULARY` | `Neurotry` | Pistas opcionales de reconocimiento separadas por comas |
| `NEUROTRY_CORS_ORIGINS` | Orígenes locales | Orígenes permitidos para desarrollo |

## Arquitectura

El código nuevo está aislado en `onboarding/`:

| Capa | Responsabilidad |
| --- | --- |
| `models.py`, `policies.py` | Perfil, comandos, assets y checklist determinista |
| `services.py` | Actualización de perfil, captura inmutable y control de revisiones del avatar |
| `ports.py` | Contratos independientes del proveedor para imagen y tarjeta |
| `gemini_adapter.py` | Adaptador multimodal de Google GenAI |
| `prompts.py`, `live.py` | Instrucciones, prompt visual y declaraciones de tools |
| `tool_registry.py` | Registro extensible, validación y despacho de tools |
| `card_renderer.py` | HTML autocontenido optimizado para impresión |

`live_demo/server.py` es el composition root: conecta FastAPI, sesiones en memoria, WebSocket, servicios y adaptadores. La UI Vanilla en `live_demo/` consume únicamente el estado público y los eventos del servidor.

### Contrato de estado

Cada actualización WebSocket de tipo `state` incluye `profile`, `checklist`, `progress`, `photo`, `avatar`, `card_ready`, `print_ready`, `transcript` y `tool_activity`. Los bytes no viajan dentro del JSON; se sirven mediante endpoints de assets protegidos por la cookie de la sesión.

## Privacidad y límites de la demo

- La foto requiere consentimiento explícito antes de capturarse.
- Foto, avatar, perfil y transcripción viven solamente en RAM.
- Las sesiones expiran después de 30 minutos de inactividad y también se eliminan con “Nueva tarjeta” o al reiniciar el servidor.
- La aplicación acepta únicamente conexiones locales y no incluye autenticación empresarial ni persistencia.
- “Guardar como PDF” usa el diálogo de impresión del navegador; no envía el archivo a un servicio externo.

## Pruebas

```bash
python -m unittest discover -s tests -p 'test_*.py'
node tests/client-regressions.cjs
```

La suite simula la cámara y el generador. La prueba `test_profile_updates_while_avatar_generation_is_running` mantiene la generación artificialmente pausada, actualiza el perfil y verifica que la entrevista no quede bloqueada.
