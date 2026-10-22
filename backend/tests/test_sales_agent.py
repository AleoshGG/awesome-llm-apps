import asyncio
import json
import sys
import unittest
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from google.genai import types

from src.features.products.domain.entities.product_query_entity import ProductQuery
from src.features.sales.domain.entities.sale_entity import Sale
from src.features.sales.domain.exceptions import EmptyCartError, ProductNotFoundError
from src.features.sales_agent.data.mappers.gemini_event_mapper import GeminiEventMapper
from src.features.sales_agent.data.mappers.gemini_tool_mapper import to_gemini_tools
from src.features.sales_agent.data.services.gemini_realtime_voice_service_adapter import (
    GeminiRealtimeVoiceServiceAdapter, GeminiRealtimeVoiceSession,
)
from src.features.sales_agent.domain.entities.agent_event_entity import (
    AudioChunk, Interrupted, Paused, Ready, ToolActivity, ToolCall, ToolCallCancelled,
    TranscriptChunk, TurnComplete, UiCommand,
)
from src.features.sales_agent.domain.entities.client_input_entity import (
    ClientAudio, ClientClose, ClientPause, ClientResume, ClientText,
)
from src.features.sales_agent.domain.entities.realtime_session_config_entity import RealtimeSessionConfig
from src.features.sales_agent.domain.prompts.sales_agent_prompt import SYSTEM_INSTRUCTION
from src.features.sales_agent.domain.entities.tool_definition_entity import ToolDefinition
from src.features.sales_agent.domain.entities.tool_result_entity import ToolResult
from src.features.sales_agent.domain.exceptions import InvalidToolArgumentsError, ProviderConnectionError
from src.features.sales_agent.domain.tools.agent_tool import AgentTool
from src.features.sales_agent.domain.tools.tool_registry import ToolRegistry
from src.features.sales_agent.domain.usecases.sales_agent_run_session_usecase import (
    MAX_CONTEXT_BYTES, SalesAgentRunSessionUseCase, SessionMemory, _tool_ui,
)
from src.features.sales_agent.presentation.sales_agent_dependencies import build_tool_registry, usecase_provider
from src.features.sales_agent.services.tools.sales_tools import (
    AddToCartTool, CheckoutTool, GetProductDetailsTool, SearchProductsTool,
)


def config():
    return RealtimeSessionConfig("gemini-3.8-live", "Kore", "Vende productos", [])


class EventMapperTests(unittest.TestCase):
    def test_prompt_converts_internal_cents_to_spoken_mxn(self):
        self.assertIn('`6000` se dice "60 pesos mexicanos"', SYSTEM_INSTRUCTION)
        self.assertIn("60 pesos se envían a la herramienta como `6000`", SYSTEM_INSTRUCTION)
        self.assertIn("build_basic_basket", SYSTEM_INSTRUCTION)

    def test_prompt_requires_one_catalog_backed_cross_sell_without_chaining(self):
        self.assertIn("una sola recomendación complementaria", SYSTEM_INSTRUCTION)
        self.assertIn("hasta tres búsquedas enfocadas", SYSTEM_INSTRUCTION)
        self.assertIn("Elige exactamente un producto real", SYSTEM_INSTRUCTION)
        self.assertIn("no generes otra recomendación", SYSTEM_INSTRUCTION)
        self.assertIn("No afirmes que otros clientes compraron", SYSTEM_INSTRUCTION)
        self.assertIn("nombre exacto", SYSTEM_INSTRUCTION)
        self.assertIn("precio a MXN", SYSTEM_INSTRUCTION)

    def test_all_parts_and_transcript_lifecycle(self):
        mapper = GeminiEventMapper()
        events = mapper.to_domain(types.LiveServerMessage(server_content={
            "model_turn": {"parts": [
                {"inline_data": {"data": b"\x00\x00", "mime_type": "audio/pcm;rate=24000"}},
                {"inline_data": {"data": b"\x01\x00", "mime_type": "audio/pcm;rate=24000"}},
            ]},
            "input_transcription": {"text": "Quiero pan", "finished": True},
            "output_transcription": {"text": "Hola "},
        }))
        self.assertEqual(len([e for e in events if isinstance(e, AudioChunk)]), 2)
        user, agent = [e for e in events if isinstance(e, TranscriptChunk)]
        self.assertTrue(user.final)
        self.assertFalse(agent.final)
        completed = mapper.to_domain(types.LiveServerMessage(server_content={
            "output_transcription": {"text": "cliente"}, "turn_complete": True,
        }))
        transcripts = [e for e in completed if isinstance(e, TranscriptChunk)]
        self.assertEqual(transcripts[-1], TranscriptChunk("agent", agent.id, "Hola cliente", True))
        self.assertIsInstance(completed[-1], TurnComplete)
        new = mapper.to_domain(types.LiveServerMessage(server_content={
            "output_transcription": {"text": "Otra respuesta"}
        }))
        self.assertNotEqual(new[0].id, agent.id)

    def test_interruption_cancellation_and_call_in_same_message(self):
        mapper = GeminiEventMapper()
        mapper.to_domain(types.LiveServerMessage(server_content={
            "output_transcription": {"text": "Parcial"}
        }))
        events = mapper.to_domain(types.LiveServerMessage(
            tool_call={"function_calls": [{"id": "a", "name": "get_cart", "args": {}}]},
            tool_call_cancellation={"ids": ["b"]},
            server_content={"interrupted": True},
        ))
        self.assertEqual(events[:3], [ToolCall("a", "get_cart", {}), ToolCallCancelled(["b"]), Interrupted()])
        self.assertTrue(events[-1].final)

    def test_all_tool_schemas_can_be_declared_to_gemini(self):
        declarations = to_gemini_tools(build_tool_registry().definitions())[0].function_declarations
        self.assertEqual(len(declarations), 10)
        basket = next(d for d in declarations if d.name == "build_basic_basket")
        self.assertNotIn("required", basket.parameters_json_schema)
        clear_cart = next(d for d in declarations if d.name == "clear_cart")
        self.assertNotIn("required", clear_cart.parameters_json_schema)
        checkout = next(d for d in declarations if d.name == "checkout")
        self.assertEqual(checkout.parameters_json_schema["required"], ["confirmed"])
        self.assertEqual(checkout.behavior, types.Behavior.NON_BLOCKING)

    def test_session_memory_is_bounded_and_never_retains_media(self):
        memory = SessionMemory()
        for index in range(30):
            memory.transcript("user", f"mensaje {index}")
        memory.result("visual_search", {"data": "base64", "audio": b"bytes", "products": []})
        turns = memory.turns()
        serialized = json.dumps(turns, ensure_ascii=False, separators=(",", ":")).encode()
        self.assertLessEqual(len(serialized), MAX_CONTEXT_BYTES)
        self.assertEqual(sum(role == "user" and text.startswith("mensaje") for role, text in turns), 24)
        self.assertNotIn(b"base64", serialized)

    def test_semantic_ui_is_derived_from_real_tool_result(self):
        event = _tool_ui(ToolCall("s", "search_products", {"name": "pan"}), "done",
                         {"products": [{"id": "p1"}]})
        self.assertEqual((event.action, event.payload["products"][0]["id"]),
                         ("catalog_search", "p1"))
        self.assertNotIn("cross_sell", event.payload)
        cross_sell = _tool_ui(ToolCall("s2", "search_products", {"name": "leche"}), "done",
                              {"products": [{"id": "p2"}]}, cross_sell=True)
        self.assertTrue(cross_sell.payload["cross_sell"])
        cleared = _tool_ui(ToolCall("c", "clear_cart", {}), "done", {"cart": []})
        self.assertEqual((cleared.action, cleared.payload["operation"]),
                         ("cart_update", "clear"))
        basket = _tool_ui(ToolCall("b", "build_basic_basket", {}), "done", {
            "cart": [{"product": {"id": "p1"}, "quantity": 1}],
            "basket": {"coverage": {"matched": 1, "requested": 24}},
        })
        self.assertEqual((basket.action, basket.payload["operation"]),
                         ("cart_update", "add"))


class GeminiAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_audio_text_results_and_receive_across_turns(self):
        sdk = SimpleNamespace(send_realtime_input=AsyncMock(), send_client_content=AsyncMock(),
                              send_tool_response=AsyncMock(), close=AsyncMock())
        turns = iter([
            [types.LiveServerMessage(server_content={"turn_complete": True})],
            [types.LiveServerMessage(server_content={"output_transcription": {"text": "Otro"},
                                                     "turn_complete": True})],
            [],
        ])

        async def receive():
            for message in next(turns):
                yield message

        sdk.receive = receive
        session = GeminiRealtimeVoiceSession(sdk)
        await session.send_audio(b"\0\0")
        await session.send_text("Hola")
        await session.send_tool_result(ToolResult("id1", "checkout", {"sale": {"id": "s1"}}))
        events = [event async for event in session.events()]
        self.assertEqual(sum(isinstance(e, TurnComplete) for e in events), 2)
        self.assertEqual(sdk.send_realtime_input.call_args.kwargs["audio"].mime_type, "audio/pcm;rate=16000")
        self.assertTrue(sdk.send_client_content.call_args.kwargs["turn_complete"])
        result = sdk.send_tool_response.call_args.kwargs["function_responses"][0]
        self.assertEqual((result.id, result.name, result.response),
                         ("id1", "checkout", {"result": {"sale": {"id": "s1"}}}))
        await session.close()
        sdk.close.assert_awaited_once()

    async def test_connection_configuration_and_cleanup(self):
        sdk = MagicMock()
        sdk.aio.aclose = AsyncMock()
        closed = []

        @asynccontextmanager
        async def connect(**kwargs):
            self.assertEqual(kwargs["model"], "gemini-3.8-live")
            setup = kwargs["config"]
            self.assertIsNotNone(setup.input_audio_transcription)
            self.assertIsNotNone(setup.output_audio_transcription)
            try:
                yield AsyncMock()
            finally:
                closed.append(True)

        sdk.aio.live.connect = connect
        target = "src.features.sales_agent.data.services.gemini_realtime_voice_service_adapter.genai.Client"
        with patch(target, return_value=sdk):
            with self.assertRaisesRegex(RuntimeError, "caller failure"):
                async with GeminiRealtimeVoiceServiceAdapter("fake-key").connect(config()):
                    raise RuntimeError("caller failure")
        self.assertEqual(closed, [True])
        sdk.aio.aclose.assert_awaited_once()
        sdk.close.assert_called_once()

    async def test_missing_key_fails_without_opening_connection(self):
        with self.assertRaises(ProviderConnectionError):
            async with GeminiRealtimeVoiceServiceAdapter(None).connect(config()):
                self.fail("Should not connect")


class ToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.usecase = AsyncMock()
        self.opened = 0

        @asynccontextmanager
        async def provider():
            self.opened += 1
            yield self.usecase

        self.provider = provider

    async def test_invalid_arguments_never_open_database_session(self):
        cases = [
            (AddToCartTool, {"product_id": "p", "quantity": quantity})
            for quantity in (0, -1, True, "2", 1.5)
        ] + [
            (AddToCartTool, {"product_id": " ", "quantity": 1}),
            (AddToCartTool, {"product_id": "p", "quantity": 1, "extra": 5}),
            (CheckoutTool, {}), (CheckoutTool, {"confirmed": False}),
            (CheckoutTool, {"confirmed": "true"}),
            (SearchProductsTool, {"min_price_cents": 20, "max_price_cents": 10}),
        ]
        for tool, args in cases:
            with self.subTest(tool=tool, args=args):
                with self.assertRaises(InvalidToolArgumentsError):
                    await tool(self.provider).execute(args)
        self.assertEqual(self.opened, 0)

    async def test_search_uses_domain_query_and_checkout_serializes_date(self):
        self.usecase.execute.return_value = []
        await SearchProductsTool(self.provider).execute({"name": "pan", "min_price_cents": 10})
        self.usecase.execute.assert_awaited_with(query=ProductQuery(name="pan", min_price_cents=10))
        self.usecase.execute.return_value = Sale("s1", datetime(2026, 1, 1, tzinfo=UTC), [])
        result = await CheckoutTool(self.provider).execute({"confirmed": True})
        self.usecase.execute.assert_awaited_with()
        self.assertEqual(result["sale"]["created_at"], "2026-01-01T00:00:00+00:00")

    async def test_add_quantity_defaults_to_one(self):
        self.usecase.execute.return_value = []
        await AddToCartTool(self.provider).execute({"product_id": "p1"})
        self.usecase.execute.assert_awaited_once_with(product_id="p1", quantity=1)

    async def test_unknown_product_and_empty_cart_propagate(self):
        self.usecase.execute.return_value = None
        with self.assertRaises(ProductNotFoundError):
            await GetProductDetailsTool(self.provider).execute({"product_id": "missing"})
        self.usecase.execute.side_effect = EmptyCartError("empty")
        with self.assertRaises(EmptyCartError):
            await CheckoutTool(self.provider).execute({"confirmed": True})

    async def test_provider_creates_and_closes_a_session_per_execution(self):
        sessions = []
        closed = []

        @asynccontextmanager
        async def session_factory():
            session = object()
            sessions.append(session)
            try:
                yield session
            finally:
                closed.append(session)

        provider = usecase_provider(lambda session: session)
        with patch("src.features.sales_agent.presentation.sales_agent_dependencies.AsyncSessionLocal", session_factory):
            async with provider() as first:
                async with provider() as second:
                    self.assertIsNot(first, second)
        self.assertCountEqual(sessions, closed)


class FakeChannel:
    def __init__(self):
        self.inputs = asyncio.Queue()
        self.events = asyncio.Queue()

    async def receive(self):
        return await self.inputs.get()

    async def send(self, event):
        await self.events.put(event)


class FakeSession:
    def __init__(self):
        self.incoming = asyncio.Queue()
        self.results = asyncio.Queue()
        self.send_audio = AsyncMock()
        self.send_text = AsyncMock()
        self.send_context = AsyncMock()
        self.restore_context = AsyncMock()
        self.closed = False

    async def send_tool_result(self, result):
        await self.results.put(result)

    async def events(self):
        while True:
            event = await self.incoming.get()
            if event is None:
                return
            yield event

    @asynccontextmanager
    async def connect(self, config):
        try:
            yield self
        finally:
            self.closed = True


class FakeTool(AgentTool):
    def __init__(self, name, execute, uses_cart=False):
        self.name = name
        self._execute = execute
        self.uses_cart = uses_cart

    async def execute(self, args):
        return await self._execute(args)

    @property
    def definition(self):
        return ToolDefinition(self.name, "test", {"type": "object"})


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def start(self, tools=(), timeout=2, visual_search=None):
        self.channel = FakeChannel()
        self.session = FakeSession()
        usecase = SalesAgentRunSessionUseCase(
            self.session, ToolRegistry(list(tools)), config(), asyncio.Lock(), timeout,
            visual_search,
        )
        self.task = asyncio.create_task(usecase.execute(self.channel))
        await self.channel.events.get()  # session
        self.assertIsInstance(await self.channel.events.get(), Ready)

    async def asyncTearDown(self):
        if hasattr(self, "task"):
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def test_text_audio_and_disconnect_cleanup(self):
        await self.start()
        await self.channel.inputs.put(ClientAudio(b"\0\0"))
        await self.channel.inputs.put(ClientText("pan"))
        transcript = await self.channel.events.get()
        self.assertEqual((transcript.speaker, transcript.text, transcript.final), ("user", "pan", True))
        await self.channel.inputs.put(ClientClose())
        await self.task
        self.session.send_audio.assert_awaited_once_with(b"\0\0")
        self.session.send_text.assert_awaited_once_with("pan")
        self.assertTrue(self.session.closed)

    async def test_pause_resume_keeps_channel_and_restores_context_without_turn(self):
        await self.start()
        await self.channel.inputs.put(ClientText("pan"))
        await self.channel.events.get()
        await self.channel.inputs.put(ClientPause())
        self.assertIsInstance(await self.channel.events.get(), Paused)
        self.assertTrue(self.session.closed)
        await self.channel.inputs.put(ClientResume())
        self.assertIsInstance(await self.channel.events.get(), Ready)
        turns = self.session.restore_context.call_args.args[0]
        self.assertIn(("user", "pan"), turns)
        self.session.send_text.assert_awaited_once_with("pan")
        await self.channel.inputs.put(ClientClose())
        await self.task

    async def test_pause_waits_for_started_cart_mutation_exactly_once(self):
        started = asyncio.Event()
        release = asyncio.Event()
        execute = AsyncMock()

        async def mutate(args):
            started.set()
            await release.wait()
            return {"cart": []}

        execute.side_effect = mutate
        await self.start([FakeTool("add_to_cart", execute, uses_cart=True)])
        await self.session.incoming.put(ToolCall("m1", "add_to_cart", {"product_id": "p1"}))
        await started.wait()
        await self.channel.inputs.put(ClientPause())
        await asyncio.sleep(0)
        self.assertFalse(self.task.done())
        release.set()
        while not isinstance(event := await self.channel.events.get(), Paused):
            pass
        execute.assert_awaited_once()
        await self.channel.inputs.put(ClientClose())
        await self.task

    async def test_tools_report_errors_and_duplicate_ids_execute_once(self):
        execute = AsyncMock(return_value={"ok": True})
        await self.start([FakeTool("tool", execute)])
        for call in [ToolCall("1", "tool", {}), ToolCall("1", "tool", {}), ToolCall("2", "unknown", {})]:
            await self.session.incoming.put(call)
        results = [await self.session.results.get(), await self.session.results.get()]
        self.assertEqual([r.is_error for r in results], [False, True])
        execute.assert_awaited_once()

    async def test_cart_operations_are_fifo_and_cancelled_waiter_does_not_execute(self):
        started = asyncio.Event()
        release = asyncio.Event()
        order = []

        async def execute(args):
            order.append(args["step"])
            if args["step"] == "add":
                started.set()
                await release.wait()
            return {"ok": True}

        await self.start([FakeTool("cart", execute, uses_cart=True)])
        for call_id, step in [("1", "add"), ("2", "remove"), ("3", "checkout")]:
            await self.session.incoming.put(ToolCall(call_id, "cart", {"step": step}))
        await started.wait()
        await self.session.incoming.put(ToolCallCancelled(["2"]))
        while True:
            event = await self.channel.events.get()
            if isinstance(event, ToolActivity) and event.phase == "cancelled":
                break
        self.assertEqual(order, ["add"])
        release.set()
        await self.session.results.get()
        await self.session.results.get()
        self.assertEqual(order, ["add", "checkout"])

    async def test_four_tools_maximum_and_disconnect_cancels_pending_work(self):
        active = 0
        started = asyncio.Event()
        release = asyncio.Event()

        async def execute(args):
            nonlocal active
            active += 1
            if active == 4:
                started.set()
            try:
                await release.wait()
                return {}
            finally:
                active -= 1

        await self.start([FakeTool("tool", execute)])
        for index in range(8):
            await self.session.incoming.put(ToolCall(str(index), "tool", {}))
        await started.wait()
        self.assertEqual(active, 4)
        await self.channel.inputs.put(ClientClose())
        await self.task
        self.assertEqual(active, 0)
        self.assertTrue(self.session.closed)

    async def test_tool_transport_failure_terminates_session(self):
        await self.start([FakeTool("tool", AsyncMock(return_value={}))])
        self.session.send_tool_result = AsyncMock(side_effect=RuntimeError("transport closed"))
        await self.session.incoming.put(ToolCall("1", "tool", {}))
        with self.assertRaisesRegex(RuntimeError, "transport closed"):
            await self.task
        self.assertTrue(self.session.closed)

    async def test_timeout_closes_provider(self):
        await self.start(timeout=0.03)
        with self.assertRaises(TimeoutError):
            await self.task
        self.assertTrue(self.session.closed)

    async def test_add_to_cart_precedes_cross_sell_search_in_same_turn(self):
        order = []

        async def add_exec(args):
            await asyncio.sleep(0.01)
            order.append("add")
            return {"cart": [{"product": {"id": "p1"}, "quantity": 1}]}

        async def search_exec(args):
            order.append("search")
            return {"products": [{"id": "p2"}]}

        await self.start([
            FakeTool("add_to_cart", add_exec, uses_cart=True),
            FakeTool("search_products", search_exec),
        ])
        await self.session.incoming.put(ToolCall("1", "add_to_cart", {"product_id": "p1"}))
        await self.session.incoming.put(ToolCall("2", "search_products", {"name": "complemento"}))
        await self.session.results.get()
        await self.session.results.get()
        self.assertEqual(order, ["add", "search"])
        ui_events = []
        while not self.channel.events.empty():
            ev = await self.channel.events.get()
            if isinstance(ev, UiCommand) and ev.phase == "done":
                ui_events.append(ev)
        self.assertEqual([e.action for e in ui_events], ["cart_update", "catalog_search"])
        self.assertTrue(ui_events[1].payload.get("cross_sell"))
        await self.channel.inputs.put(ClientClose())
        await self.task


if __name__ == "__main__":
    unittest.main()
