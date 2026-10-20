import asyncio
import base64
import binascii

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from src.features.sales_agent.domain.entities.agent_event_entity import AgentEvent
from src.features.sales_agent.domain.entities.client_input_entity import (
    ClientAudio, ClientClose, ClientImage, ClientPause, ClientResume, ClientText,
)
from src.features.sales_agent.presentation.sales_agent_ws_schema import (
    AudioMessage, ImageMessage, MAX_IMAGE_BYTES, MAX_MESSAGE_BYTES, PauseMessage,
    ResumeMessage, TextMessage,
    client_message_adapter, event_payload,
)


class InvalidClientMessageError(ValueError):
    pass


IMAGE_SIGNATURES = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP",
}


class WebSocketClientChannelAdapter:
    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket
        self._send_lock = asyncio.Lock()

    async def receive(self):
        message = await self._websocket.receive()
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message.get("code", 1000))
        raw = message.get("text")
        if raw is None or len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise InvalidClientMessageError("Se requiere un mensaje JSON de hasta 6 MiB.")
        try:
            parsed = client_message_adapter.validate_json(raw)
            if isinstance(parsed, AudioMessage):
                audio = base64.b64decode(parsed.data, validate=True)
                if not audio or len(audio) % 2:
                    raise ValueError("Invalid PCM16")
                return ClientAudio(audio)
            if isinstance(parsed, ImageMessage):
                image = base64.b64decode(parsed.data, validate=True)
                if (not image or len(image) > MAX_IMAGE_BYTES
                        or not IMAGE_SIGNATURES[parsed.mime_type](image)):
                    raise ValueError("Invalid image")
                return ClientImage(image, parsed.mime_type)
            if isinstance(parsed, TextMessage):
                return ClientText(parsed.text)
            if isinstance(parsed, PauseMessage):
                return ClientPause()
            if isinstance(parsed, ResumeMessage):
                return ClientResume()
            return ClientClose()
        except (ValidationError, ValueError, binascii.Error):
            raise InvalidClientMessageError(
                "Mensaje inválido: verifica tipo, campos, base64 y formato del contenido."
            ) from None

    async def send(self, event: AgentEvent) -> None:
        async with self._send_lock:
            await self._websocket.send_json(event_payload(event))
