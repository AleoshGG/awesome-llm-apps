import asyncio
from contextlib import AsyncExitStack, asynccontextmanager

from google import genai
from google.genai import types
from google.genai.live import AsyncSession

from src.features.sales_agent.data.mappers.gemini_event_mapper import GeminiEventMapper
from src.features.sales_agent.data.mappers.gemini_tool_mapper import to_gemini_tools
from src.features.sales_agent.domain.entities.realtime_session_config_entity import RealtimeSessionConfig
from src.features.sales_agent.domain.entities.tool_result_entity import ToolResult
from src.features.sales_agent.domain.exceptions import ProviderConnectionError


class GeminiRealtimeVoiceSession:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mapper = GeminiEventMapper()
        self._send_lock = asyncio.Lock()

    async def send_audio(self, data: bytes) -> None:
        async with self._send_lock:
            await self._session.send_realtime_input(
                audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
            )

    async def send_text(self, text: str) -> None:
        await self._send_text(text)

    async def send_context(self, text: str) -> None:
        await self._send_text(text)

    async def restore_context(self, turns: list[tuple[str, str]]) -> None:
        if not turns:
            return
        async with self._send_lock:
            await self._session.send_client_content(
                turns=[
                    types.Content(role=role, parts=[types.Part(text=text)])
                    for role, text in turns
                ],
                turn_complete=False,
            )

    async def _send_text(self, text: str) -> None:
        async with self._send_lock:
            await self._session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=text)]),
                turn_complete=True,
            )

    async def send_tool_result(self, result: ToolResult) -> None:
        async with self._send_lock:
            await self._session.send_tool_response(function_responses=[
                types.FunctionResponse(
                    id=result.call_id,
                    name=result.name,
                    response={"error" if result.is_error else "result": result.output},
                    scheduling=types.FunctionResponseScheduling.WHEN_IDLE,
                )
            ])

    async def events(self):
        # receive() stops at each completed turn, not at the end of the session.
        while True:
            received = False
            async for message in self._session.receive():
                received = True
                for event in self._mapper.to_domain(message):
                    yield event
                if message.go_away:
                    return
            if not received:
                return

    async def close(self) -> None:
        await self._session.close()


class GeminiRealtimeVoiceServiceAdapter:
    def __init__(self, api_key: str | None) -> None:
        self._api_key = api_key

    @asynccontextmanager
    async def connect(self, config: RealtimeSessionConfig):
        if not self._api_key:
            raise ProviderConnectionError("Configura GOOGLE_API_KEY para iniciar el agente.")
        async with AsyncExitStack() as stack:
            try:
                client = genai.Client(api_key=self._api_key)
                stack.callback(client.close)
                stack.push_async_callback(client.aio.aclose)
                session = await stack.enter_async_context(client.aio.live.connect(
                    model=config.model,
                    config=types.LiveConnectConfig(
                        response_modalities=[types.Modality.AUDIO],
                        system_instruction=config.system_instruction,
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=config.voice
                                )
                            )
                        ),
                        input_audio_transcription=types.AudioTranscriptionConfig(),
                        output_audio_transcription=types.AudioTranscriptionConfig(),
                        tools=to_gemini_tools(config.tools),
                    ),
                ))
            except Exception as exc:
                raise ProviderConnectionError("No se pudo conectar con Gemini Live.") from exc
            yield GeminiRealtimeVoiceSession(session)
