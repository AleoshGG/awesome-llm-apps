import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from src.app import app
from src.features.sales_agent.data.services.gemini_realtime_voice_service_adapter import GeminiRealtimeVoiceServiceAdapter
from src.features.sales_agent.domain.entities.agent_event_entity import AudioChunk, TranscriptChunk, TurnComplete
from src.features.sales_agent.domain.tools.tool_registry import ToolRegistry
from src.features.sales_agent.domain.usecases.sales_agent_run_session_usecase import SalesAgentRunSessionUseCase
from src.features.sales_agent.presentation.sales_agent_dependencies import get_sales_agent

from test_sales_agent import FakeSession, config


class SalesAgentWebSocketTests(unittest.TestCase):
    def setUp(self):
        self.sessions = []

        def dependency(websocket: WebSocket):
            session = FakeSession()

            async def respond(text):
                await session.incoming.put(TranscriptChunk("agent", "answer", "Hola", True))
                await session.incoming.put(AudioChunk(b"\x01\x00"))
                await session.incoming.put(TurnComplete())

            session.send_text.side_effect = respond
            self.sessions.append(session)
            return SalesAgentRunSessionUseCase(
                session, ToolRegistry([]), config(), websocket.app.state.sales_agent_cart_lock
            )

        app.dependency_overrides[get_sales_agent] = dependency
        self.client = self.enterContext(TestClient(app))

    def tearDown(self):
        app.dependency_overrides.clear()

    def ready(self, ws):
        session = ws.receive_json()
        self.assertEqual(session["type"], "session")
        self.assertEqual((session["provider"], session["input_sample_rate"], session["output_sample_rate"]),
                         ("gemini", 16000, 24000))
        self.assertEqual(ws.receive_json(), {"type": "ready"})

    def test_real_route_text_audio_and_explicit_close(self):
        with self.client.websocket_connect("/ws/sales-agent") as ws:
            self.ready(ws)
            ws.send_json({"type": "audio", "data": base64.b64encode(b"\0\0").decode()})
            ws.send_json({"type": "text", "text": "Hola"})
            user = ws.receive_json()
            self.assertEqual((user["speaker"], user["text"], user["final"]), ("user", "Hola", True))
            self.assertEqual(ws.receive_json()["speaker"], "agent")
            audio = ws.receive_json()
            self.assertEqual(base64.b64decode(audio["data"]), b"\x01\x00")
            self.assertEqual(ws.receive_json(), {"type": "turn_complete"})
            ws.send_json({"type": "close"})
            with self.assertRaises(WebSocketDisconnect) as closed:
                ws.receive_json()
            self.assertEqual(closed.exception.code, 1000)
        self.assertTrue(self.sessions[0].closed)
        self.sessions[0].send_audio.assert_awaited_once_with(b"\0\0")

    def test_invalid_messages_close_with_policy_error(self):
        for raw in [
            "not json", '{"type":"unknown"}', '{"type":"text","text":" "}',
            '{"type":"audio","data":"@@"}', '{"type":"audio","data":"AA=="}',
            '{"type":"close","unexpected":true}', "x" * 800001,
        ]:
            with self.subTest(raw=raw[:70]):
                with self.client.websocket_connect("/ws/sales-agent") as ws:
                    self.ready(ws)
                    ws.send_text(raw)
                    self.assertEqual(ws.receive_json()["type"], "error")
                    with self.assertRaises(WebSocketDisconnect) as closed:
                        ws.receive_json()
                    self.assertEqual(closed.exception.code, 1008)
                self.assertTrue(self.sessions[-1].closed)

    def test_disconnect_closes_provider(self):
        with self.client.websocket_connect("/ws/sales-agent") as ws:
            self.ready(ws)
        self.assertTrue(self.sessions[-1].closed)

    def test_cross_origin_browser_is_rejected(self):
        with self.assertRaises(WebSocketDisconnect) as closed:
            with self.client.websocket_connect("/ws/sales-agent", headers={"origin": "https://other.example"}):
                self.fail("Origin should be rejected")
        self.assertEqual(closed.exception.code, 1008)

    def test_missing_key_returns_clear_error(self):
        def missing_key(websocket: WebSocket):
            return SalesAgentRunSessionUseCase(
                GeminiRealtimeVoiceServiceAdapter(None), ToolRegistry([]), config(),
                websocket.app.state.sales_agent_cart_lock,
            )

        app.dependency_overrides[get_sales_agent] = missing_key
        with self.client.websocket_connect("/ws/sales-agent") as ws:
            error = ws.receive_json()
            self.assertEqual(error["type"], "error")
            self.assertIn("GOOGLE_API_KEY", error["message"])
            with self.assertRaises(WebSocketDisconnect) as closed:
                ws.receive_json()
            self.assertEqual(closed.exception.code, 1011)


if __name__ == "__main__":
    unittest.main()
