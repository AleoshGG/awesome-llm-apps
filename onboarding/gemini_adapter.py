"""Google GenAI implementation of the avatar generation port."""

from __future__ import annotations

import asyncio

from .ports import ImageResult


class GeminiAvatarGenerator:
    def __init__(self, client_factory, model: str, timeout_seconds: float = 75.0):
        self.client_factory = client_factory
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def generate(self, photo: bytes, mime_type: str, prompt: str) -> ImageResult:
        from google.genai import types

        response = await asyncio.wait_for(
            self.client_factory().aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=photo, mime_type=mime_type),
                    types.Part(text=prompt),
                ],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            ),
            self.timeout_seconds,
        )
        part = next(
            (
                part
                for candidate in response.candidates or []
                for part in (candidate.content.parts if candidate.content else [])
                if part.inline_data and part.inline_data.data
            ),
            None,
        )
        if part is None:
            raise RuntimeError("El modelo no devolvió una imagen.")
        return ImageResult(
            data=part.inline_data.data,
            mime_type=part.inline_data.mime_type or "image/png",
        )
