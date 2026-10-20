from uuid import uuid4

from google.genai import types

from src.features.sales_agent.domain.entities.agent_event_entity import (
    AgentError, AgentEvent, AudioChunk, Interrupted, ToolCall, ToolCallCancelled,
    TranscriptChunk, TurnComplete,
)


class GeminiEventMapper:
    def __init__(self) -> None:
        self._transcripts: dict[str, tuple[str, str]] = {}

    def _transcript(self, speaker, text: str, final: bool) -> TranscriptChunk:
        transcript_id, previous = self._transcripts.get(speaker, (uuid4().hex, ""))
        combined = previous + text
        if final:
            self._transcripts.pop(speaker, None)
        else:
            self._transcripts[speaker] = (transcript_id, combined)
        return TranscriptChunk(speaker, transcript_id, combined, final)

    def to_domain(self, message: types.LiveServerMessage) -> list[AgentEvent]:
        events: list[AgentEvent] = []
        if message.tool_call:
            for call in message.tool_call.function_calls or []:
                if not call.id or not call.name:
                    raise ValueError("Gemini tool call is missing its id or name")
                events.append(ToolCall(call.id, call.name, call.args or {}))
        if message.tool_call_cancellation:
            events.append(ToolCallCancelled(message.tool_call_cancellation.ids or []))
        content = message.server_content
        if content:
            if content.interrupted:
                events.append(Interrupted())
            if content.model_turn and not content.interrupted:
                for part in content.model_turn.parts or []:
                    blob = part.inline_data
                    if blob and blob.data and (blob.mime_type or "").startswith("audio/pcm"):
                        events.append(AudioChunk(blob.data, blob.mime_type))
            for speaker, transcription in (
                ("user", content.input_transcription),
                ("agent", content.output_transcription),
            ):
                if transcription and (transcription.text or speaker in self._transcripts):
                    events.append(self._transcript(
                        speaker, transcription.text or "", bool(transcription.finished)
                    ))
            if content.turn_complete or content.interrupted:
                for speaker in list(self._transcripts):
                    events.append(self._transcript(speaker, "", True))
            if content.turn_complete:
                events.append(TurnComplete())
        if message.go_away:
            events.append(AgentError("Gemini terminó la sesión. Inicia una nueva conexión."))
        return events
