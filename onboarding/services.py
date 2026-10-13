"""Application services for profiles, camera capture and avatar generation."""

from __future__ import annotations

import time
import uuid
from datetime import datetime

from .models import AvatarState, CapturedPhoto, GeneratedAvatar, ProfilePatch, UserProfile
from .ports import AvatarGenerator
from .prompts import avatar_prompt


class ProfileService:
    def update(self, current: UserProfile, patch: ProfilePatch) -> UserProfile:
        return current.model_copy(update=patch.model_dump(exclude_none=True))


class PhotoCaptureError(ValueError):
    pass


class PhotoCaptureService:
    def __init__(self, max_frame_age_seconds: float = 12.0):
        self.max_frame_age_seconds = max_frame_age_seconds

    def capture(self, session, *, consent_confirmed: bool) -> CapturedPhoto:
        if not consent_confirmed:
            raise PhotoCaptureError("Necesito tu consentimiento explícito antes de tomar la foto.")
        if not session.camera_enabled:
            raise PhotoCaptureError("La cámara está apagada. Enciéndela para tomar la foto.")
        if session.last_frame is None or time.monotonic() - session.last_frame_at > self.max_frame_age_seconds:
            raise PhotoCaptureError("No hay un frame reciente. Mira a la cámara e inténtalo de nuevo.")
        session.photo_revision += 1
        session.photo_bytes = bytes(session.last_frame)
        session.photo = CapturedPhoto(
            id=uuid.uuid4().hex,
            captured_at=datetime.now().astimezone(),
            revision=session.photo_revision,
        )
        session.avatar_bytes = None
        session.avatar = AvatarState()
        session.profile = session.profile.model_copy(
            update={"photo_id": session.photo.id, "avatar_id": None}
        )
        return session.photo


class AvatarGenerationService:
    def __init__(self, generator: AvatarGenerator):
        self.generator = generator

    async def generate(self, session) -> GeneratedAvatar:
        if session.photo is None or session.photo_bytes is None:
            raise ValueError("Primero toma una foto.")
        source_revision = session.photo.revision
        photo = bytes(session.photo_bytes)
        session.avatar = AvatarState(status="generating")
        try:
            image = await self.generator.generate(photo, "image/jpeg", avatar_prompt())
            if session.deleted or session.photo is None or session.photo.revision != source_revision:
                raise RuntimeError("La generación fue reemplazada por una foto más reciente.")
            asset = GeneratedAvatar(
                id=uuid.uuid4().hex,
                mime_type=image.mime_type,
                generated_at=datetime.now().astimezone(),
                source_photo_revision=source_revision,
            )
            session.avatar_bytes = image.data
            session.avatar = AvatarState(status="ready", asset=asset)
            session.profile = session.profile.model_copy(update={"avatar_id": asset.id})
            return asset
        except Exception as exc:
            if session.photo is not None and session.photo.revision == source_revision:
                session.avatar = AvatarState(status="failed", error=str(exc)[:240])
            raise
