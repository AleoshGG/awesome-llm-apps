import base64
from dataclasses import asdict
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from src.features.sales_agent.domain.entities.agent_event_entity import (
    AgentError, AgentEvent, AudioChunk, Interrupted, Ready, SessionStarted,
    ToolActivity, TranscriptChunk, TurnComplete,
)

MAX_MESSAGE_BYTES = 800_000


class ClientMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class AudioMessage(ClientMessage):
    type: Literal["audio"]
    data: str = Field(min_length=1, max_length=MAX_MESSAGE_BYTES)


class TextMessage(ClientMessage):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=8000)


class CloseMessage(ClientMessage):
    type: Literal["close"]


client_message_adapter = TypeAdapter(
    Annotated[AudioMessage | TextMessage | CloseMessage, Field(discriminator="type")]
)

EVENT_TYPES = {
    SessionStarted: "session", Ready: "ready", AudioChunk: "audio",
    TranscriptChunk: "transcript", ToolActivity: "tool", Interrupted: "interrupted",
    TurnComplete: "turn_complete", AgentError: "error",
}


def event_payload(event: AgentEvent) -> dict:
    payload = asdict(event)
    if isinstance(event, AudioChunk):
        payload["data"] = base64.b64encode(event.data).decode("ascii")
    return {"type": EVENT_TYPES[type(event)], **payload}
