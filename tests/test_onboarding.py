import asyncio
import time
import unittest
from types import SimpleNamespace as NS

from pydantic import ValidationError

from onboarding.live import build_live_config, receive_live_messages
from onboarding.models import AvatarState, ProfilePatch, UserProfile
from onboarding.policies import completion_percent, profile_checklist, profile_complete
from onboarding.ports import ImageResult
from onboarding.services import AvatarGenerationService, PhotoCaptureError, PhotoCaptureService, ProfileService
from onboarding.tool_registry import build_tool_registry


def session():
    return NS(
        profile=UserProfile(), camera_enabled=True, last_frame=b"\xff\xd8\xffPHOTO",
        last_frame_at=time.monotonic(), photo_revision=0, photo=None, photo_bytes=None,
        avatar=AvatarState(), avatar_bytes=None, revision=0, deleted=False,
    )


class ProfileTests(unittest.TestCase):
    def test_checklist_has_exactly_five_deterministic_items(self):
        profile = UserProfile(full_name="Ana Ruiz", age=29, department="Producto")
        self.assertEqual(len(profile_checklist(profile)), 5)
        self.assertEqual(completion_percent(profile), 60)
        self.assertFalse(profile_complete(profile))

    def test_profile_normalizes_text_and_validates_age(self):
        patch = ProfilePatch(full_name="  Ana   Ruiz ", short_description="  Diseño productos  ")
        updated = ProfileService().update(UserProfile(), patch)
        self.assertEqual(updated.full_name, "Ana Ruiz")
        self.assertEqual(updated.short_description, "Diseño productos")
        with self.assertRaises(ValidationError):
            ProfilePatch(age=0)
        with self.assertRaises(ValidationError):
            ProfilePatch()


class CaptureTests(unittest.TestCase):
    def test_capture_requires_consent_camera_and_fresh_frame(self):
        service = PhotoCaptureService(max_frame_age_seconds=12)
        current = session()
        with self.assertRaises(PhotoCaptureError):
            service.capture(current, consent_confirmed=False)
        current.camera_enabled = False
        with self.assertRaises(PhotoCaptureError):
            service.capture(current, consent_confirmed=True)
        current.camera_enabled = True
        current.last_frame_at = time.monotonic() - 13
        with self.assertRaises(PhotoCaptureError):
            service.capture(current, consent_confirmed=True)

    def test_capture_freezes_exact_frame_and_invalidates_avatar(self):
        current = session()
        current.avatar_bytes = b"old"
        current.avatar = AvatarState(status="failed", error="old")
        photo = PhotoCaptureService().capture(current, consent_confirmed=True)
        current.last_frame = b"new frame"
        self.assertEqual(current.photo_bytes, b"\xff\xd8\xffPHOTO")
        self.assertEqual(current.profile.photo_id, photo.id)
        self.assertEqual(current.avatar.status, "idle")


class ControlledGenerator:
    def __init__(self):
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def generate(self, photo, mime_type, prompt):
        self.started.set()
        await self.release.wait()
        return ImageResult(b"PNG", "image/png")


class NonBlockingTests(unittest.IsolatedAsyncioTestCase):
    async def test_profile_updates_while_avatar_generation_is_running(self):
        current = session()
        PhotoCaptureService().capture(current, consent_confirmed=True)
        generator = ControlledGenerator()
        avatar_service = AvatarGenerationService(generator)
        generation = asyncio.create_task(avatar_service.generate(current))
        await asyncio.wait_for(generator.started.wait(), .2)

        current.profile = ProfileService().update(
            current.profile,
            ProfilePatch(full_name="Alex Gómez", age=31, department="IA"),
        )
        self.assertFalse(generation.done())
        self.assertEqual(current.profile.full_name, "Alex Gómez")
        generator.release.set()
        asset = await asyncio.wait_for(generation, .2)
        self.assertEqual(current.profile.avatar_id, asset.id)
        self.assertEqual(current.avatar.status, "ready")

    async def test_old_generation_cannot_replace_a_retake(self):
        current = session()
        capture = PhotoCaptureService()
        capture.capture(current, consent_confirmed=True)
        generator = ControlledGenerator()
        task = asyncio.create_task(AvatarGenerationService(generator).generate(current))
        await generator.started.wait()
        current.last_frame = b"\xff\xd8\xffNEW"
        current.last_frame_at = time.monotonic()
        capture.capture(current, consent_confirmed=True)
        generator.release.set()
        with self.assertRaises(RuntimeError):
            await task
        self.assertIsNone(current.avatar_bytes)
        self.assertEqual(current.avatar.status, "idle")

    async def test_registry_validates_and_emits_capture_flash(self):
        current = session()
        generator = ControlledGenerator()
        registry = build_tool_registry(ProfileService(), PhotoCaptureService(), AvatarGenerationService(generator))
        events = []

        async def emit(event):
            events.append(event)

        result, urgent = await registry.execute("capture_user_photo", current, {"consent_confirmed": True}, emit)
        self.assertTrue(result["captured"])
        self.assertTrue(urgent)
        self.assertEqual(events[0]["type"], "camera_flash")


class LiveConfigTests(unittest.TestCase):
    def test_live_agent_is_audio_only_and_has_new_tools(self):
        config = build_live_config()
        self.assertEqual(config.response_modalities, ["AUDIO"])
        names = [item.name for tool in config.tools for item in tool.function_declarations]
        self.assertEqual(names, ["update_user_profile", "capture_user_photo", "generate_corporate_avatar"])
        self.assertIn("Primero pide que encienda la cámara", config.system_instruction)
        self.assertIn("resultado para continuar hablando", config.system_instruction)


class LiveReceiveTests(unittest.IsolatedAsyncioTestCase):
    async def test_turn_completion_does_not_end_the_live_connection(self):
        class Live:
            def __init__(self):
                self.turns = [["first-turn"], ["second-turn"], []]

            def receive(self):
                values = self.turns.pop(0)

                async def messages():
                    for value in values:
                        yield value

                return messages()

        live = Live()
        received = [message async for message in receive_live_messages(live)]
        self.assertEqual(received, ["first-turn", "second-turn"])
