import base64
from dataclasses import asdict
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from src.features.sales_agent.domain.entities.agent_event_entity import (
    AgentError, AgentEvent, AudioChunk, Interrupted, Paused, Ready, ResumeError,
    SessionStarted, ToolActivity, TranscriptChunk, TurnComplete, UiCommand,
)

MAX_AUDIO_BASE64_BYTES = 800_000
MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BASE64_BYTES = ((MAX_IMAGE_BYTES + 2) // 3) * 4
MAX_MESSAGE_BYTES = 6 * 1024 * 1024


class ClientMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class AudioMessage(ClientMessage):
    type: Literal["audio"]
    data: str = Field(min_length=1, max_length=MAX_AUDIO_BASE64_BYTES)


class ImageMessage(ClientMessage):
    type: Literal["image"]
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    data: str = Field(min_length=1, max_length=MAX_IMAGE_BASE64_BYTES)


class TextMessage(ClientMessage):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=8000)


class CloseMessage(ClientMessage):
    type: Literal["close"]


class PauseMessage(ClientMessage):
    type: Literal["pause"]


class ResumeMessage(ClientMessage):
    type: Literal["resume"]


client_message_adapter = TypeAdapter(
    Annotated[
        AudioMessage | ImageMessage | TextMessage | PauseMessage | ResumeMessage | CloseMessage,
        Field(discriminator="type"),
    ]
)

EVENT_TYPES = {
    SessionStarted: "session", Ready: "ready", AudioChunk: "audio",
    TranscriptChunk: "transcript", ToolActivity: "tool", UiCommand: "ui",
    Interrupted: "interrupted", Paused: "paused", ResumeError: "resume_error",
    TurnComplete: "turn_complete", AgentError: "error",
}


def event_payload(event: AgentEvent) -> dict:
    payload = asdict(event)
    if isinstance(event, AudioChunk):
        payload["data"] = base64.b64encode(event.data).decode("ascii")
    return {"type": EVENT_TYPES[type(event)], **payload}
