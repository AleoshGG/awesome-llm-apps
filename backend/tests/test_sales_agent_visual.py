import asyncio
import base64
import json
import sys
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.products.domain.entities.category_entity import Category
from src.features.sales_agent.data.services.adk_visual_product_search_service import (
    AdkVisualProductSearchService, VisualModelOutput, VisualSearchToolbox,
)
from src.features.sales_agent.domain.entities.agent_event_entity import ToolActivity
from src.features.sales_agent.domain.entities.client_input_entity import (
    ClientAudio, ClientClose, ClientImage, ClientText,
)
from src.features.sales_agent.domain.entities.visual_search_result_entity import VisualSearchResult
from src.features.sales_agent.domain.tools.tool_registry import ToolRegistry
from src.features.sales_agent.domain.usecases.sales_agent_run_session_usecase import SalesAgentRunSessionUseCase
from src.features.sales_agent.presentation.websocket_client_channel_adapter import (
    InvalidClientMessageError, WebSocketClientChannelAdapter,
)

try:
    from test_sales_agent import FakeChannel, FakeSession, config
except ImportError:
    from tests.test_sales_agent import FakeChannel, FakeSession, config


class FakeWebSocket:
    def __init__(self, payload):
        self.payload = payload

    async def receive(self):
        return {"type": "websocket.receive", "text": json.dumps(self.payload)}


class ImageValidationTests(unittest.IsolatedAsyncioTestCase):
    async def receive(self, mime_type, data):
        payload = {"type": "image", "mime_type": mime_type,
                   "data": base64.b64encode(data).decode()}
        return await WebSocketClientChannelAdapter(FakeWebSocket(payload)).receive()

    async def test_accepts_jpeg_png_and_webp_signatures(self):
        cases = [
            ("image/jpeg", b"\xff\xd8\xff\xe0payload"),
            ("image/png", b"\x89PNG\r\n\x1a\npayload"),
            ("image/webp", b"RIFF\x04\x00\x00\x00WEBPpayload"),
        ]
        for mime_type, data in cases:
            with self.subTest(mime_type=mime_type):
                self.assertEqual(await self.receive(mime_type, data), ClientImage(data, mime_type))

    async def test_rejects_bad_base64_unknown_mismatch_and_oversize(self):
        payloads = [
            {"type": "image", "mime_type": "image/jpeg", "data": "@@"},
            {"type": "image", "mime_type": "image/gif", "data": "R0lGODlh"},
            {"type": "image", "mime_type": "image/png",
             "data": base64.b64encode(b"\xff\xd8\xffpayload").decode()},
            {"type": "image", "mime_type": "image/jpeg",
             "data": base64.b64encode(b"\xff\xd8\xff" + b"x" * (4 * 1024 * 1024)).decode()},
        ]
        for payload in payloads:
            with self.subTest(mime_type=payload["mime_type"]):
                with self.assertRaises(InvalidClientMessageError):
                    await WebSocketClientChannelAdapter(FakeWebSocket(payload)).receive()


class ToolboxTests(unittest.IsolatedAsyncioTestCase):
    def provider(self, usecase):
        @asynccontextmanager
        async def provide():
            yield usecase
        return provide

    async def test_order_arguments_limits_deduplication_and_real_rows_only(self):
        categories = SimpleNamespace(execute=AsyncMock(return_value=[
            Category("c1", "Panadería"), Category("c2", "Bebidas")
        ]))
        products = SimpleNamespace(execute=AsyncMock())
        toolbox = VisualSearchToolbox(self.provider(categories), self.provider(products))

        with self.assertRaisesRegex(ValueError, "list_categories"):
            await toolbox.search_products(name="pan")
        await toolbox.list_categories()
        with self.assertRaises(ValueError):
            await toolbox.search_products(category_name="Inventada")
        with self.assertRaises(ValueError):
            await toolbox.search_products(min_price_cents=20, max_price_cents=10)

        rows = [{"id": f"p{i}", "name": f"Producto {i}"} for i in range(12)]
        products.execute.side_effect = [rows[:7], rows[3:10], rows[8:12]]
        for name in ("pan", "bollo", "trigo"):
            response = await toolbox.search_products(name=name, category_name="Panadería")
            self.assertLessEqual(len(response["products"]), 5)
        with self.assertRaisesRegex(ValueError, "three"):
            await toolbox.search_products(name="cuarta")

        result = toolbox.result(VisualModelOutput(
            summary="Parece pan empacado.",
            observed_features=["bolsa", "bolsa", "color café"],
            matched_categories=["Panadería", "Inventada"],
        ))
        self.assertEqual(result.matched_categories, ["Panadería"])
        self.assertEqual(result.observed_features, ["bolsa", "color café"])
        self.assertEqual(len(result.searches), 3)
        self.assertLessEqual(len(result.products), 10)
        self.assertTrue(all(product in rows for product in result.products))


class AdkServiceTests(unittest.IsolatedAsyncioTestCase):
    def provider(self, usecase):
        @asynccontextmanager
        async def provide():
            yield usecase
        return provide

    async def test_adk_runner_uses_tools_and_ephemeral_session(self):
        categories = SimpleNamespace(execute=AsyncMock(return_value=[Category("c1", "Panadería")]))
        products = SimpleNamespace(execute=AsyncMock(return_value=[{"id": "p1", "name": "Pan"}]))
        fake_client = SimpleNamespace(
            aio=SimpleNamespace(aclose=AsyncMock()), close=unittest.mock.Mock()
        )

        class FakeRunner:
            def __init__(runner_self, *, agent, session_service, **kwargs):
                runner_self.agent = agent
                runner_self.sessions = session_service

            async def run_async(runner_self, *, user_id, session_id, new_message):
                await runner_self.agent.tools[0]()
                await runner_self.agent.tools[1](name="pan", category_name="Panadería")
                session = await runner_self.sessions.get_session(
                    app_name="sales_agent_visual_search", user_id=user_id, session_id=session_id
                )
                session.state["visual_output"] = {
                    "summary": "Parece pan.", "observed_features": ["bolsa"],
                    "matched_categories": ["Panadería"],
                }
                yield SimpleNamespace()

            async def close(runner_self):
                pass

        class FakeSessions:
            def __init__(sessions_self):
                sessions_self.session = SimpleNamespace(state={})

            async def create_session(sessions_self, **kwargs):
                return sessions_self.session

            async def get_session(sessions_self, **kwargs):
                return sessions_self.session

        def fake_agent(**kwargs):
            return SimpleNamespace(tools=kwargs["tools"])

        service = AdkVisualProductSearchService(
            "key", "gemini-test", self.provider(categories), self.provider(products)
        )
        with patch("src.features.sales_agent.data.services.adk_visual_product_search_service.genai.Client",
                   return_value=fake_client), patch(
            "src.features.sales_agent.data.services.adk_visual_product_search_service.Gemini",
            return_value=object()), patch(
            "src.features.sales_agent.data.services.adk_visual_product_search_service.LlmAgent",
            side_effect=fake_agent), patch(
            "src.features.sales_agent.data.services.adk_visual_product_search_service.Runner",
            FakeRunner), patch(
            "src.features.sales_agent.data.services.adk_visual_product_search_service.InMemorySessionService",
            FakeSessions):
            result = await service.analyze(ClientImage(b"\xff\xd8\xffx", "image/jpeg"))
        self.assertEqual([p["id"] for p in result.products], ["p1"])
        categories.execute.assert_awaited_once()
        products.execute.assert_awaited_once()
        fake_client.aio.aclose.assert_awaited_once()
        fake_client.close.assert_called_once()


class VisualOrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def start(self, visual):
        self.channel = FakeChannel()
        self.session = FakeSession()
        self.task = asyncio.create_task(SalesAgentRunSessionUseCase(
            self.session, ToolRegistry([]), config(), asyncio.Lock(), 2, visual
        ).execute(self.channel))
        await self.channel.events.get()
        await self.channel.events.get()

    async def asyncTearDown(self):
        if hasattr(self, "task") and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def test_background_sequence_context_and_second_image_rejection(self):
        release = asyncio.Event()

        async def analyze(image):
            await release.wait()
            return VisualSearchResult("Parece pan", ["bolsa"], ["Panadería"],
                                      [{"name": "pan"}], [{"id": "p1", "name": "Pan"}])

        visual = SimpleNamespace(analyze=AsyncMock(side_effect=analyze))
        await self.start(visual)
        image = ClientImage(b"\xff\xd8\xffx", "image/jpeg")
        await self.channel.inputs.put(image)
        running = await self.channel.events.get()
        self.assertEqual((running.name, running.phase), ("visual_product_search", "running"))
        self.assertEqual((await self.channel.events.get()).action, "catalog_search")

        await self.channel.inputs.put(image)
        rejected = await self.channel.events.get()
        self.assertEqual(rejected.phase, "error")
        self.assertEqual((await self.channel.events.get()).phase, "error")
        await self.channel.inputs.put(ClientAudio(b"\0\0"))
        await self.channel.inputs.put(ClientText("sigo hablando"))
        transcript = await self.channel.events.get()
        self.assertEqual(transcript.text, "sigo hablando")
        self.session.send_audio.assert_awaited_once_with(b"\0\0")
        release.set()
        done = await self.channel.events.get()
        self.assertEqual(done.phase, "done")
        self.assertEqual((await self.channel.events.get()).phase, "done")
        self.assertNotIn("data", done.args)
        await asyncio.sleep(0)
        context = self.session.send_context.call_args.args[0]
        self.assertIn('"products":[{"id":"p1"', context)
        await self.channel.inputs.put(ClientClose())
        await self.task

    async def test_failure_is_recoverable_and_disconnect_cancels(self):
        failing = SimpleNamespace(analyze=AsyncMock(side_effect=RuntimeError("provider")))
        await self.start(failing)
        await self.channel.inputs.put(ClientImage(b"\xff\xd8\xffx", "image/jpeg"))
        self.assertEqual((await self.channel.events.get()).phase, "running")
        self.assertEqual((await self.channel.events.get()).phase, "running")
        self.assertEqual((await self.channel.events.get()).phase, "error")
        self.assertEqual((await self.channel.events.get()).phase, "error")
        await asyncio.sleep(0)
        self.session.send_context.assert_awaited()
        await self.channel.inputs.put(ClientText("todavía aquí"))
        self.assertEqual((await self.channel.events.get()).text, "todavía aquí")
        await self.channel.inputs.put(ClientClose())
        await self.task

        blocker = asyncio.Event()

        async def wait_forever(image):
            await blocker.wait()

        blocking = SimpleNamespace(analyze=AsyncMock(side_effect=wait_forever))
        await self.start(blocking)
        await self.channel.inputs.put(ClientImage(b"\xff\xd8\xffx", "image/jpeg"))
        self.assertEqual((await self.channel.events.get()).phase, "running")
        self.assertEqual((await self.channel.events.get()).phase, "running")
        await self.channel.inputs.put(ClientClose())
        await self.task
        cancelled = await self.channel.events.get()
        self.assertIsInstance(cancelled, ToolActivity)
        self.assertEqual(cancelled.phase, "cancelled")


if __name__ == "__main__":
    unittest.main()
