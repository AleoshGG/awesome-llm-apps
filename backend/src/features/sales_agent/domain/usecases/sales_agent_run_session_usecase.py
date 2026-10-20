import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import replace
from uuid import uuid4

from src.features.sales.domain.exceptions import EmptyCartError, InvalidQuantityError, ProductNotFoundError
from src.features.sales_agent.domain.entities.agent_event_entity import (
    AgentError, Ready, SessionStarted, ToolActivity, ToolCall, ToolCallCancelled,
    TranscriptChunk,
)
from src.features.sales_agent.domain.entities.client_input_entity import ClientAudio, ClientClose, ClientText
from src.features.sales_agent.domain.entities.realtime_session_config_entity import RealtimeSessionConfig
from src.features.sales_agent.domain.entities.tool_result_entity import ToolResult
from src.features.sales_agent.domain.exceptions import InvalidToolArgumentsError, ToolNotFoundError
from src.features.sales_agent.domain.services.client_channel_service import ClientChannel
from src.features.sales_agent.domain.services.realtime_voice_service import RealtimeVoiceService
from src.features.sales_agent.domain.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class SalesAgentRunSessionUseCase:
    def __init__(
        self,
        voice_service: RealtimeVoiceService,
        registry: ToolRegistry,
        config: RealtimeSessionConfig,
        cart_lock: asyncio.Lock,
        timeout_seconds: float = 1200,
    ) -> None:
        self._voice_service = voice_service
        self._registry = registry
        self._config = replace(config, tools=registry.definitions())
        self._cart_lock = cart_lock
        self._timeout_seconds = timeout_seconds

    @asynccontextmanager
    async def _tool_slot(self, uses_cart: bool, semaphore: asyncio.Semaphore):
        # Acquire the shared FIFO lock before the concurrency slot so checkout
        # cannot overtake an earlier cart operation waiting for that slot.
        if uses_cart:
            async with self._cart_lock:
                async with semaphore:
                    yield
        else:
            async with semaphore:
                yield

    async def execute(self, channel: ClientChannel) -> None:
        async with asyncio.timeout(self._timeout_seconds):
            async with self._voice_service.connect(self._config) as session:
                await channel.send(SessionStarted(
                    self._config.model, [tool.name for tool in self._config.tools]
                ))
                await channel.send(Ready())
                tasks: dict[str, asyncio.Task] = {}
                calls: dict[str, ToolCall] = {}
                failure = asyncio.get_running_loop().create_future()
                semaphore = asyncio.Semaphore(4)

                async def run_tool(call: ToolCall) -> None:
                    await channel.send(ToolActivity(call.id, call.name, call.args, "running"))
                    try:
                        tool = self._registry.get(call.name)
                        async with self._tool_slot(tool.uses_cart, semaphore):
                            output = await tool.execute(call.args)
                        result = ToolResult(call.id, call.name, output)
                    except (ToolNotFoundError, InvalidToolArgumentsError, EmptyCartError,
                            InvalidQuantityError, ProductNotFoundError) as exc:
                        result = ToolResult(call.id, call.name, {"message": str(exc)}, True)
                    except Exception:
                        logger.exception("Sales tool failed: %s", call.name)
                        result = ToolResult(call.id, call.name, {
                            "message": "No se pudo completar la operación. No la reintentes automáticamente."
                        }, True)
                    await channel.send(ToolActivity(
                        call.id, call.name, call.args,
                        "error" if result.is_error else "done", result.output,
                    ))
                    await session.send_tool_result(result)

                def tool_finished(task: asyncio.Task) -> None:
                    if not task.cancelled():
                        error = task.exception()
                        if error is not None and not failure.done():
                            failure.set_result(error)

                async def client_to_model() -> None:
                    while True:
                        message = await channel.receive()
                        if isinstance(message, ClientClose):
                            return
                        if isinstance(message, ClientAudio):
                            await session.send_audio(message.data)
                        elif isinstance(message, ClientText):
                            await channel.send(TranscriptChunk("user", uuid4().hex, message.text, True))
                            await session.send_text(message.text)

                async def model_to_client() -> None:
                    async for event in session.events():
                        if isinstance(event, ToolCall):
                            if event.id not in tasks:
                                calls[event.id] = event
                                tasks[event.id] = asyncio.create_task(run_tool(event))
                                tasks[event.id].add_done_callback(tool_finished)
                        elif isinstance(event, ToolCallCancelled):
                            for call_id in event.ids:
                                task = tasks.get(call_id)
                                if task is not None and not task.done():
                                    task.cancel()
                                    await asyncio.gather(task, return_exceptions=True)
                                    call = calls[call_id]
                                    await channel.send(ToolActivity(
                                        call.id, call.name, call.args, "cancelled"
                                    ))
                        else:
                            await channel.send(event)
                            if isinstance(event, AgentError):
                                return

                readers = [
                    asyncio.create_task(client_to_model()),
                    asyncio.create_task(model_to_client()),
                ]
                try:
                    done, _ = await asyncio.wait(
                        [*readers, failure], return_when=asyncio.FIRST_COMPLETED
                    )
                    for completed in done:
                        if completed is failure:
                            raise failure.result()
                        completed.result()
                finally:
                    for task in [*readers, *tasks.values()]:
                        task.cancel()
                    await asyncio.gather(*readers, *tasks.values(), return_exceptions=True)
                    failure.cancel()
