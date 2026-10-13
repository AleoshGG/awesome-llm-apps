"""Gemini Live configuration and tool declarations for onboarding."""

from __future__ import annotations

import os
from datetime import datetime

from google.genai import types

from .prompts import SYSTEM_INSTRUCTION


LIVE_MODEL_ID = os.getenv("NEUROTRY_LIVE_MODEL", "gemini-3.8-live")
IMAGE_MODEL_ID = os.getenv("NEUROTRY_IMAGE_MODEL", "gemini-3.1-flash-image")
VOICE_NAME = os.getenv("NEUROTRY_VOICE", "Kore")


async def receive_live_messages(live_session):
    """Yield consecutive model turns without treating turn completion as disconnect."""
    while True:
        received = False
        async for message in live_session.receive():
            received = True
            yield message
        if not received:
            return


def _string(description: str) -> types.Schema:
    return types.Schema(type=types.Type.STRING, description=description)


def tool_declarations() -> list[types.Tool]:
    update = types.FunctionDeclaration(
        name="update_user_profile",
        description="Guarda datos personales que la persona acaba de proporcionar o corregir.",
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "full_name": _string("Nombre completo exacto, solo si fue proporcionado."),
                "age": types.Schema(type=types.Type.INTEGER, description="Edad numérica entre 1 y 120."),
                "department": _string("Departamento o área exacta."),
                "short_description": _string("Descripción corta de rol, superpoder o afición."),
            },
        ),
    )
    capture = types.FunctionDeclaration(
        name="capture_user_photo",
        description="Congela el frame más reciente después del consentimiento y la cuenta regresiva.",
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "consent_confirmed": types.Schema(
                    type=types.Type.BOOLEAN,
                    description="True únicamente si la persona acaba de dar permiso explícito.",
                )
            },
            required=["consent_confirmed"],
        ),
    )
    generate = types.FunctionDeclaration(
        name="generate_corporate_avatar",
        description=(
            "Genera en segundo plano un avatar corporativo estático desde la foto capturada. "
            "Llámala inmediatamente después de una captura exitosa y continúa la entrevista."
        ),
        behavior=types.Behavior.NON_BLOCKING,
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    )
    return [types.Tool(function_declarations=[update, capture, generate])]


def camera_mode_instruction(enabled: bool) -> str:
    return (
        f"ESTADO DE LA APLICACIÓN: cámara {'ENCENDIDA' if enabled else 'APAGADA'}. "
        "Esto no es una afirmación de la persona ni implica consentimiento."
    )


def build_live_config(*, camera_enabled: bool = False, seed_history: bool = False):
    vocabulary = [
        value.strip()
        for value in os.getenv("NEUROTRY_TRANSCRIPTION_VOCABULARY", "Neurotry").split(",")
        if value.strip()
    ]
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        history_config=types.HistoryConfig(initial_history_in_client_content=True) if seed_history else None,
        system_instruction="\n".join(
            [SYSTEM_INSTRUCTION, camera_mode_instruction(camera_enabled), "Hora de referencia: " + datetime.now().astimezone().isoformat()]
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
            )
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(custom_vocabulary=vocabulary),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        realtime_input_config=types.RealtimeInputConfig(
            activity_handling=types.ActivityHandling.START_OF_ACTIVITY_INTERRUPTS
        ),
        tools=tool_declarations(),
    )
