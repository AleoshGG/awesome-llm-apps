"""Deterministic onboarding policies with no transport or provider dependencies."""

from __future__ import annotations

from .models import UserProfile


PROFILE_FIELDS = (
    ("full_name", "Nombre"),
    ("age", "Edad"),
    ("department", "Departamento"),
    ("short_description", "Descripción corta"),
    ("photo_id", "Foto tomada"),
)


def profile_checklist(profile: UserProfile) -> list[dict[str, object]]:
    return [
        {"key": key, "label": label, "complete": getattr(profile, key) is not None}
        for key, label in PROFILE_FIELDS
    ]


def completion_percent(profile: UserProfile) -> int:
    completed = sum(bool(item["complete"]) for item in profile_checklist(profile))
    return round(100 * completed / len(PROFILE_FIELDS))


def profile_complete(profile: UserProfile) -> bool:
    return all(bool(item["complete"]) for item in profile_checklist(profile))
