"""Ports implemented by provider-specific infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ImageResult:
    data: bytes
    mime_type: str


class AvatarGenerator(Protocol):
    async def generate(self, photo: bytes, mime_type: str, prompt: str) -> ImageResult: ...


class CardRenderer(Protocol):
    def render(self, state: dict[str, object]) -> str: ...
