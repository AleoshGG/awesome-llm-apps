from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    mime_type: str = "audio/pcm;rate=24000"


@dataclass(frozen=True)
class TranscriptChunk:
    speaker: Literal["user", "agent"]
    id: str
    text: str
    final: bool = False


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass(frozen=True)
class ToolCallCancelled:
    ids: list[str]


@dataclass(frozen=True)
class TurnComplete:
    pass


@dataclass(frozen=True)
class Interrupted:
    pass


@dataclass(frozen=True)
class AgentError:
    message: str


@dataclass(frozen=True)
class SessionStarted:
    model: str
    tools: list[str]
    provider: str = "gemini"
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000


@dataclass(frozen=True)
class Ready:
    pass


@dataclass(frozen=True)
class ToolActivity:
    id: str
    name: str
    args: dict
    phase: Literal["running", "done", "error", "cancelled"]
    result: dict | None = None


AgentEvent = (
    AudioChunk | TranscriptChunk | ToolCall | ToolCallCancelled | TurnComplete
    | Interrupted | AgentError | SessionStarted | Ready | ToolActivity
)
