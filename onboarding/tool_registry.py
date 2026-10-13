"""Extensible tool registry and onboarding tool handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import ValidationError

from .models import AvatarState, CapturePhotoCommand, ProfilePatch
from .services import AvatarGenerationService, PhotoCaptureError, PhotoCaptureService, ProfileService


Handler = Callable[[Any, dict[str, Any], Callable[[dict[str, Any]], Awaitable[None]]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: Handler
    urgent: bool = False


class ToolRegistry:
    def __init__(self, specs: list[ToolSpec]):
        self._specs = {spec.name: spec for spec in specs}

    @property
    def names(self) -> list[str]:
        return list(self._specs)

    async def execute(self, name: str, session, args: dict[str, Any], emit) -> tuple[dict[str, Any], bool]:
        spec = self._specs.get(name)
        if spec is None:
            return {"error": "Herramienta desconocida."}, False
        try:
            return await spec.handler(session, args, emit), spec.urgent
        except ValidationError as exc:
            return {"error": exc.errors()[0]["msg"]}, spec.urgent
        except (PhotoCaptureError, ValueError) as exc:
            return {"error": str(exc)}, spec.urgent


def build_tool_registry(
    profile_service: ProfileService,
    photo_service: PhotoCaptureService,
    avatar_service: AvatarGenerationService,
) -> ToolRegistry:
    async def update(session, args, emit):
        patch = ProfilePatch.model_validate(args)
        session.profile = profile_service.update(session.profile, patch)
        session.revision += 1
        return {"saved": True, "updated_fields": list(patch.model_dump(exclude_none=True))}

    async def capture(session, args, emit):
        command = CapturePhotoCommand.model_validate(args)
        photo = photo_service.capture(session, consent_confirmed=command.consent_confirmed)
        session.revision += 1
        await emit({"type": "camera_flash", "photo_id": photo.id})
        return {"captured": True, "photo_id": photo.id, "message": "Foto guardada con éxito."}

    async def generate(session, args, emit):
        if session.photo is None:
            raise ValueError("Primero toma una foto.")
        session.avatar = AvatarState(status="generating")
        await emit({"type": "state_changed"})
        asset = await avatar_service.generate(session)
        session.revision += 1
        return {"generated": True, "avatar_id": asset.id, "message": "Avatar corporativo listo."}

    return ToolRegistry([
        ToolSpec("update_user_profile", update),
        ToolSpec("capture_user_photo", capture, urgent=True),
        ToolSpec("generate_corporate_avatar", generate),
    ])
