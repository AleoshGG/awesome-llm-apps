"""FastAPI composition root for the Neurotry live onboarding demo."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
import secrets
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

APP_DIR = Path(__file__).resolve().parents[1]
DEMO_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


def _load_dotenv() -> None:
    path = APP_DIR / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

from google.genai import types  # noqa: E402
from onboarding.card_renderer import HtmlBusinessCardRenderer  # noqa: E402
from onboarding.gemini_adapter import GeminiAvatarGenerator  # noqa: E402
from onboarding.live import (  # noqa: E402
    IMAGE_MODEL_ID,
    LIVE_MODEL_ID,
    build_live_config,
    camera_mode_instruction,
    receive_live_messages,
)
from onboarding.models import AvatarState, CapturedPhoto, UserProfile  # noqa: E402
from onboarding.policies import completion_percent, profile_checklist, profile_complete  # noqa: E402
from onboarding.services import AvatarGenerationService, PhotoCaptureService, ProfileService  # noqa: E402
from onboarding.tool_registry import build_tool_registry  # noqa: E402

logger = logging.getLogger(__name__)
GENAI_CLIENT = None
SESSION_TTL = 30 * 60
MAX_SESSIONS = 32
MAX_MESSAGE_BYTES = 800_000


def _cors_origins() -> list[str]:
    raw = os.getenv("NEUROTRY_CORS_ORIGINS", "")
    if raw.strip():
        return [value.strip() for value in raw.split(",") if value.strip()]
    return ["http://127.0.0.1:4177", "http://localhost:4177"]


def _has_api_key() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def _client():
    global GENAI_CLIENT
    if not _has_api_key():
        raise RuntimeError("Falta GOOGLE_API_KEY en el entorno del servidor.")
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    if GENAI_CLIENT is None:
        from google import genai
        GENAI_CLIENT = genai.Client()
    return GENAI_CLIENT


@dataclass
class OnboardingSession:
    session_id: str
    owner: str = ""
    profile: UserProfile = field(default_factory=UserProfile)
    transcript: list[dict[str, str]] = field(default_factory=list)
    tool_activity: list[dict[str, Any]] = field(default_factory=list)
    photo: CapturedPhoto | None = None
    photo_bytes: bytes | None = None
    photo_revision: int = 0
    avatar: AvatarState = field(default_factory=AvatarState)
    avatar_bytes: bytes | None = None
    last_frame: bytes | None = None
    last_frame_at: float = 0.0
    camera_enabled: bool = False
    revision: int = 0
    updated_at: float = field(default_factory=time.monotonic)
    deleted: bool = False
    live_socket: Any = None
    tasks: set = field(default_factory=set)


sessions: dict[str, OnboardingSession] = {}
profile_service = ProfileService()
photo_service = PhotoCaptureService()
avatar_service = AvatarGenerationService(GeminiAvatarGenerator(_client, IMAGE_MODEL_ID))
tool_registry = build_tool_registry(profile_service, photo_service, avatar_service)
card_renderer = HtmlBusinessCardRenderer()

app = FastAPI(title="Neurotry Live Onboarding API")
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins(), allow_methods=["*"], allow_headers=["*"])


def append_turn(session: OnboardingSession, speaker: str, text: str, turn_id: str | None = None) -> str:
    value = text.strip()[:8000]
    turn_id = turn_id or uuid.uuid4().hex
    if not value or any(turn.get("id") == turn_id for turn in session.transcript):
        return turn_id
    if len(session.transcript) >= 300:
        raise ValueError("La conversación alcanzó su límite. Inicia una sesión nueva.")
    session.transcript.append({"id": turn_id, "speaker": speaker, "text": value})
    session.updated_at = time.monotonic()
    return turn_id


def public_state(session: OnboardingSession) -> dict[str, Any]:
    base = f"/api/sessions/{session.session_id}/assets"
    photo = None
    if session.photo:
        photo = {**session.photo.model_dump(mode="json"), "url": f"{base}/photo?v={session.photo.id}"}
    avatar = session.avatar.model_dump(mode="json")
    avatar["url"] = (
        f"{base}/avatar?v={session.avatar.asset.id}"
        if session.avatar.asset and session.avatar.status == "ready" else None
    )
    usable_image = bool(avatar["url"] or (photo and photo["url"]))
    return {
        "session_id": session.session_id,
        "revision": session.revision,
        "profile": session.profile.model_dump(mode="json"),
        "checklist": profile_checklist(session.profile),
        "progress": completion_percent(session.profile),
        "photo": photo,
        "avatar": avatar,
        "profile_complete": profile_complete(session.profile),
        "card_ready": profile_complete(session.profile) and session.avatar.status == "ready",
        "print_ready": profile_complete(session.profile) and usable_image,
        "transcript": session.transcript,
        "tool_activity": session.tool_activity[-12:],
        "camera_enabled": session.camera_enabled,
    }


def allowed_origin(origin: str | None, host: str, scheme: str = "http") -> bool:
    return bool(origin and origin in set(_cors_origins()) | {f"{scheme}://{host}"})


def local_host(host: str) -> bool:
    return host.split(":")[0] in {"localhost", "127.0.0.1"}


@app.middleware("http")
async def local_access(request: Request, call_next):
    if not local_host(request.headers.get("host", "")) or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        return Response("Esta demo solo acepta conexiones locales.", status_code=403)
    origin = request.headers.get("origin")
    if origin and not allowed_origin(origin, request.headers.get("host", ""), request.url.scheme):
        return Response("Origen no permitido.", status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


def owned_session(session_id: str, owner: str | None) -> OnboardingSession:
    session = sessions.get(session_id)
    if not session or session.deleted or not owner or not secrets.compare_digest(owner, session.owner):
        raise HTTPException(404, "Sesión no encontrada o expirada.")
    if time.monotonic() - session.updated_at > SESSION_TTL:
        raise HTTPException(410, "La sesión expiró.")
    session.updated_at = time.monotonic()
    return session


async def discard_session(session: OnboardingSession) -> None:
    session.deleted = True
    sessions.pop(session.session_id, None)
    if session.live_socket:
        with contextlib.suppress(Exception):
            await session.live_socket.close(code=1000)
    for task in list(session.tasks):
        task.cancel()
    if session.tasks:
        await asyncio.gather(*list(session.tasks), return_exceptions=True)
    session.photo_bytes = session.avatar_bytes = session.last_frame = None


async def cleanup_sessions() -> None:
    for session in list(sessions.values()):
        if time.monotonic() - session.updated_at > SESSION_TTL:
            await discard_session(session)


@app.on_event("startup")
async def start_cleanup():
    async def sweep():
        while True:
            await asyncio.sleep(60)
            await cleanup_sessions()
    app.state.cleanup_task = asyncio.create_task(sweep())


@app.on_event("shutdown")
async def stop_cleanup():
    app.state.cleanup_task.cancel()
    await asyncio.gather(app.state.cleanup_task, return_exceptions=True)
    for session in list(sessions.values()):
        await discard_session(session)


@app.get("/api/health")
def health():
    return {"ok": True, "has_api_key": _has_api_key(), "live_model": LIVE_MODEL_ID,
            "image_model": IMAGE_MODEL_ID, "tools": tool_registry.names}


@app.post("/api/sessions")
async def create_session(request: Request, response: Response):
    await cleanup_sessions()
    owner = request.cookies.get("onboarding_owner") or secrets.token_urlsafe(32)
    if len(sessions) >= MAX_SESSIONS or sum(item.owner == owner for item in sessions.values()) >= 4:
        raise HTTPException(429, "Hay demasiadas sesiones activas.")
    session = OnboardingSession(session_id=uuid.uuid4().hex, owner=owner)
    append_turn(session, "Agent", "¡Hola! Te doy la bienvenida a Neurotry. Primero crearemos tu retrato: enciende la cámara y dime si autorizas que tome una foto para esta tarjeta.")
    sessions[session.session_id] = session
    response.set_cookie("onboarding_owner", owner, httponly=True, samesite="strict",
                        max_age=SESSION_TTL, secure=request.url.scheme == "https")
    return {"session_id": session.session_id, "has_api_key": _has_api_key(), "state": public_state(session)}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str, request: Request):
    session = owned_session(session_id, request.cookies.get("onboarding_owner"))
    return {"session_id": session_id, "has_api_key": _has_api_key(), "state": public_state(session)}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    session = owned_session(session_id, request.cookies.get("onboarding_owner"))
    await discard_session(session)
    return {"deleted": True}


@app.get("/api/sessions/{session_id}/assets/photo")
def photo_asset(session_id: str, request: Request):
    session = owned_session(session_id, request.cookies.get("onboarding_owner"))
    if not session.photo_bytes:
        raise HTTPException(404, "La foto todavía no existe.")
    return Response(session.photo_bytes, media_type="image/jpeg")


@app.get("/api/sessions/{session_id}/assets/avatar")
def avatar_asset(session_id: str, request: Request):
    session = owned_session(session_id, request.cookies.get("onboarding_owner"))
    if not session.avatar_bytes or not session.avatar.asset:
        raise HTTPException(404, "El avatar todavía no existe.")
    return Response(session.avatar_bytes, media_type=session.avatar.asset.mime_type)


@app.get("/api/sessions/{session_id}/business-card", response_class=HTMLResponse)
def business_card(session_id: str, request: Request):
    session = owned_session(session_id, request.cookies.get("onboarding_owner"))
    state = public_state(session)
    if not state["print_ready"]:
        raise HTTPException(409, "Completa los datos y toma una foto antes de imprimir.")
    return HTMLResponse(card_renderer.render(state))


def tool_headline(name: str, phase: str) -> str:
    labels = {"update_user_profile": "Guardando datos del perfil", "capture_user_photo": "Capturando foto",
              "generate_corporate_avatar": "Creando avatar Neurotry"}
    return labels.get(name, name) + {"done": " — listo", "error": " — error"}.get(phase, "")


@app.websocket("/ws/live")
async def live_voice(websocket: WebSocket):
    host = websocket.headers.get("host", "")
    scheme = "https" if websocket.url.scheme == "wss" else "http"
    if not local_host(host) or websocket.client.host not in {"127.0.0.1", "::1", "testclient"} or not allowed_origin(websocket.headers.get("origin"), host, scheme):
        await websocket.close(code=1008)
        return
    try:
        session = owned_session(websocket.query_params.get("session_id", ""), websocket.cookies.get("onboarding_owner"))
    except HTTPException:
        await websocket.close(code=1008)
        return
    if session.live_socket is not None:
        await websocket.close(code=1008)
        return
    session.live_socket = websocket
    await websocket.accept()
    send_lock = asyncio.Lock()
    tasks: set[asyncio.Task] = set()
    tool_tasks: dict[str, asyncio.Task] = {}
    pending = {"User": {"id": uuid.uuid4().hex, "text": ""}, "Agent": {"id": uuid.uuid4().hex, "text": ""}}

    async def send(payload: dict[str, Any]):
        if not session.deleted:
            async with send_lock:
                await websocket.send_json({**payload, "session_id": session.session_id})

    def track(task: asyncio.Task):
        tasks.add(task)
        session.tasks.add(task)
        def finished(done):
            tasks.discard(done)
            session.tasks.discard(done)
            if not done.cancelled() and done.exception():
                logger.error("Background onboarding task failed: %s", type(done.exception()).__name__)
        task.add_done_callback(finished)
        return task

    async def finalize(speaker: str):
        turn = pending[speaker]
        if not turn["text"].strip():
            return
        append_turn(session, speaker, turn["text"], turn["id"])
        await send({"type": "transcript", "speaker": speaker, "text": turn["text"], "id": turn["id"], "final": True})
        pending[speaker] = {"id": uuid.uuid4().hex, "text": ""}

    async def publish_tool(entry: dict[str, Any]):
        session.tool_activity = [item for item in session.tool_activity if item["id"] != entry["id"]] + [dict(entry)]
        await send({"type": "tool", **entry})

    async def execute_tool(fc, live_session):
        started = time.monotonic()
        name, args, call_id = str(fc.name or ""), dict(fc.args or {}), str(fc.id or uuid.uuid4().hex)
        entry = {"id": call_id, "name": name, "phase": "running", "headline": tool_headline(name, "running")}
        await publish_tool(entry)

        async def emit(event):
            if event.get("type") == "state_changed":
                await send({"type": "state", "state": public_state(session)})
            else:
                await send(event)

        try:
            result, urgent = await tool_registry.execute(name, session, args, emit)
        except asyncio.CancelledError:
            entry.update(phase="cancelled", headline="Tarea cancelada")
            with contextlib.suppress(Exception):
                await publish_tool(entry)
            raise
        except Exception:
            logger.exception("Tool %s failed", name)
            result, urgent = {"error": f"{tool_headline(name, 'running')} falló. Puedes reintentar."}, False
        phase = "error" if "error" in result else "done"
        scheduling = types.FunctionResponseScheduling.INTERRUPT if urgent else types.FunctionResponseScheduling.WHEN_IDLE
        entry.update(phase=phase, headline=result.get("error") or tool_headline(name, phase), result=result,
                     duration_ms=int((time.monotonic() - started) * 1000), scheduling=scheduling.value)
        await publish_tool(entry)
        await send({"type": "state", "state": public_state(session)})
        await live_session.send_tool_response(function_responses=[types.FunctionResponse(
            id=call_id, name=name, response=result, scheduling=scheduling)])

    async def launch_tool(fc, live_session):
        key = str(fc.id)
        if key in tool_tasks:
            return
        if len(tool_tasks) >= 4:
            await live_session.send_tool_response(function_responses=[types.FunctionResponse(
                id=fc.id, name=fc.name, response={"error": "Espera a que termine una tarea en curso."})])
            return
        task = track(asyncio.create_task(execute_tool(fc, live_session)))
        tool_tasks[key] = task
        task.add_done_callback(lambda done, item=key: tool_tasks.pop(item, None))

    try:
        if not _has_api_key():
            await send({"type": "error", "message": "Configura GOOGLE_API_KEY para iniciar la conversación."})
            return
        history = [types.Content(role="user" if turn["speaker"] == "User" else "model",
                                 parts=[types.Part(text=turn["text"])])
                   for turn in session.transcript if turn["speaker"] in {"User", "Agent"}]
        config = build_live_config(camera_enabled=session.camera_enabled, seed_history=bool(history))
        async with _client().aio.live.connect(model=LIVE_MODEL_ID, config=config) as live_session:
            if history:
                await live_session.send_client_content(turns=history, turn_complete=True)
            await send({"type": "session", "model": LIVE_MODEL_ID, "image_model": IMAGE_MODEL_ID, "tools": tool_registry.names})
            await send({"type": "state", "state": public_state(session)})
            await send({"type": "ready"})

            async def client_to_gemini():
                windows = {key: deque() for key in ("text", "audio", "video", "camera_state")}
                while True:
                    raw = await websocket.receive_text()
                    if len(raw) > MAX_MESSAGE_BYTES:
                        await send({"type": "error", "message": "La entrada excede el límite permitido."})
                        continue
                    try:
                        message = json.loads(raw)
                        kind = message.get("type")
                        if kind == "close":
                            await finalize("User"); await finalize("Agent"); return
                        if kind not in windows:
                            raise ValueError("Tipo de entrada desconocido")
                        now = time.monotonic()
                        window = windows[kind]
                        period, limit = (60, 20) if kind == "text" else (1, 100 if kind == "audio" else 5)
                        while window and now - window[0] >= period:
                            window.popleft()
                        if len(window) >= limit:
                            raise ValueError("Demasiadas entradas; espera un momento")
                        window.append(now); session.updated_at = now
                        if kind == "camera_state":
                            enabled = message.get("enabled")
                            if not isinstance(enabled, bool): raise ValueError("Estado de cámara inválido")
                            session.camera_enabled = enabled
                            if not enabled: session.last_frame = None; session.last_frame_at = 0
                            await live_session.send_client_content(turns=types.Content(
                                role="user", parts=[types.Part(text=camera_mode_instruction(enabled))]), turn_complete=False)
                            await send({"type": "state", "state": public_state(session)})
                        elif kind == "text":
                            value = message.get("text", "")
                            if not isinstance(value, str) or not value.strip() or len(value) > 8000:
                                raise ValueError("El texto debe tener entre 1 y 8000 caracteres")
                            turn_id = str(message.get("id") or uuid.uuid4().hex)
                            append_turn(session, "User", value, turn_id)
                            await send({"type": "transcript", "speaker": "User", "text": value, "id": turn_id, "final": True})
                            await live_session.send_client_content(turns=types.Content(
                                role="user", parts=[types.Part(text=value)]), turn_complete=True)
                        else:
                            encoded = message.get("data")
                            if not isinstance(encoded, str): raise ValueError("Faltan datos multimedia")
                            data = base64.b64decode(encoded, validate=True)
                            if not data or len(data) > (512_000 if kind == "video" else 128_000):
                                raise ValueError("Multimedia inválida")
                            if kind == "video":
                                if not data.startswith(b"\xff\xd8\xff"): raise ValueError("Los frames deben ser JPEG")
                                session.camera_enabled = True; session.last_frame = data; session.last_frame_at = now
                                await live_session.send_realtime_input(video=types.Blob(data=data, mime_type="image/jpeg"))
                            else:
                                await live_session.send_realtime_input(audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000"))
                    except (ValueError, json.JSONDecodeError) as exc:
                        await send({"type": "error", "message": str(exc)})

            async def gemini_to_client():
                async for response in receive_live_messages(live_session):
                    if response.tool_call:
                        for fc in response.tool_call.function_calls or []: await launch_tool(fc, live_session)
                    if response.tool_call_cancellation:
                        for call_id in response.tool_call_cancellation.ids or []:
                            if task := tool_tasks.get(str(call_id)): task.cancel()
                    content = response.server_content
                    if not content: continue
                    if content.interrupted:
                        await send({"type": "interrupted"}); await finalize("Agent")
                    for speaker, chunk in (("User", content.input_transcription), ("Agent", content.output_transcription)):
                        if speaker == "Agent" and content.interrupted: continue
                        if chunk and chunk.text:
                            if speaker == "Agent": await finalize("User")
                            pending[speaker]["text"] += chunk.text
                            await send({"type": "transcript", "speaker": speaker, **pending[speaker], "final": False})
                        if chunk and getattr(chunk, "finished", False): await finalize(speaker)
                    if content.model_turn and not content.interrupted:
                        for part in content.model_turn.parts or []:
                            if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                                await finalize("User")
                                await send({"type": "audio", "data": base64.b64encode(part.inline_data.data).decode("ascii")})
                    if getattr(content, "turn_complete", False):
                        await finalize("User"); await finalize("Agent"); await send({"type": "turn_complete"})

            pair = [track(asyncio.create_task(client_to_gemini())), track(asyncio.create_task(gemini_to_client()))]
            done, _ = await asyncio.wait(pair, timeout=20 * 60, return_when=asyncio.FIRST_COMPLETED)
            if not done: await send({"type": "error", "message": "La llamada llegó al límite de 20 minutos."})
            for task in done: task.result()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Gemini Live session failed")
        with contextlib.suppress(Exception): await send({"type": "error", "message": "La conexión en vivo terminó. Puedes reconectarte."})
    finally:
        for task in list(tasks): task.cancel()
        await asyncio.gather(*list(tasks), return_exceptions=True)
        session.live_socket = None; session.camera_enabled = False; session.last_frame = None
        with contextlib.suppress(Exception): await websocket.close()


@app.get("/")
def index(): return FileResponse(DEMO_DIR / "index.html")


@app.get("/index.html")
def index_alias(): return index()


@app.get("/app.js")
def javascript(): return FileResponse(DEMO_DIR / "app.js", media_type="application/javascript")


@app.get("/styles.css")
def styles(): return FileResponse(DEMO_DIR / "styles.css", media_type="text/css")
