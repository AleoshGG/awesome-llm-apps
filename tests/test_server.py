import time
import unittest
from types import SimpleNamespace as NS

from live_demo import server
from onboarding.models import AvatarState, CapturedPhoto, GeneratedAvatar, UserProfile


def complete_session():
    item = server.OnboardingSession("complete", owner="owner")
    item.profile = UserProfile(
        full_name="Ana Ruiz", age=28, department="Producto",
        short_description="Convierto ideas en experiencias", photo_id="p", avatar_id="a",
    )
    item.photo = CapturedPhoto(id="p", captured_at="2026-10-13T10:00:00-06:00", revision=1)
    item.photo_bytes = b"JPEG"
    asset = GeneratedAvatar(id="a", mime_type="image/png", generated_at="2026-10-13T10:00:02-06:00", source_photo_revision=1)
    item.avatar = AvatarState(status="ready", asset=asset)
    item.avatar_bytes = b"PNG"
    return item


class ServerTests(unittest.TestCase):
    def setUp(self):
        server.sessions.clear()

    def tearDown(self):
        server.sessions.clear()

    def test_session_exposes_new_state_contract(self):
        item = server.OnboardingSession("new", owner="owner")
        server.append_turn(item, "Agent", "Enciende la cámara")
        state = server.public_state(item)
        self.assertEqual(len(state["checklist"]), 5)
        self.assertEqual(state["avatar"]["status"], "idle")
        self.assertFalse(state["card_ready"])
        self.assertIn("cámara", state["transcript"][0]["text"])

    def test_assets_and_print_card_use_owned_complete_session(self):
        item = complete_session()
        server.sessions[item.session_id] = item
        request = NS(cookies={"onboarding_owner": "owner"})
        photo = server.photo_asset(item.session_id, request)
        avatar = server.avatar_asset(item.session_id, request)
        card = server.business_card(item.session_id, request)
        self.assertEqual(photo.body, b"JPEG")
        self.assertEqual(avatar.media_type, "image/png")
        self.assertIn("Ana Ruiz", card.body.decode())
        self.assertIn("window.print()", card.body.decode())

    def test_stale_session_is_rejected(self):
        item = server.OnboardingSession("expired", owner="owner", updated_at=time.monotonic() - server.SESSION_TTL - 1)
        server.sessions[item.session_id] = item
        with self.assertRaises(server.HTTPException) as raised:
            server.owned_session("expired", "owner")
        self.assertEqual(raised.exception.status_code, 410)
