"""Domain models for the Neurotry onboarding flow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class UserProfile(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=1, le=120)
    department: str | None = Field(default=None, max_length=80)
    short_description: str | None = Field(default=None, max_length=240)
    photo_id: str | None = None
    avatar_id: str | None = None

    @field_validator("full_name", "department", "short_description", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return None
        normalized = " ".join(str(value).split())
        return normalized or None


class ProfilePatch(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    age: int | None = Field(default=None, ge=1, le=120)
    department: str | None = Field(default=None, max_length=80)
    short_description: str | None = Field(default=None, max_length=240)

    @field_validator("full_name", "department", "short_description", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return None
        normalized = " ".join(str(value).split())
        return normalized or None

    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one profile field is required")
        return self


class CapturePhotoCommand(BaseModel):
    consent_confirmed: Literal[True]


class CapturedPhoto(BaseModel):
    id: str
    mime_type: Literal["image/jpeg"] = "image/jpeg"
    captured_at: datetime
    revision: int = 1


class GeneratedAvatar(BaseModel):
    id: str
    mime_type: str
    generated_at: datetime
    source_photo_revision: int


class AvatarState(BaseModel):
    status: Literal["idle", "generating", "ready", "failed"] = "idle"
    asset: GeneratedAvatar | None = None
    error: str | None = None
