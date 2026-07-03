"""AI domain router aggregator."""
from fastapi import APIRouter

from app.api.bijmantra.ai import (
    ai_configuration,
    chat,
    devguru,
    nim_proxy,
    vector,
    veena_ai,
    voice,
)

ai_router = APIRouter()

# AI Configuration
ai_router.include_router(ai_configuration.router, tags=["AI Configuration"])

# Chat (hot file - external consumers: BeingBijMantra VS Code extension, OpenClaw bridge)
ai_router.include_router(chat.router, tags=["REEVU AI"])

# DevGuru PhD Mentor
ai_router.include_router(devguru.router, tags=["DevGuru PhD Mentor"])

# NVIDIA NIM proxy (server-side key, never browser-facing)
ai_router.include_router(nim_proxy.router, tags=["NVIDIA NIM"])

# Vector Search
ai_router.include_router(vector.router, tags=["Vector Search"])

# Veena AI (Cognitive)
ai_router.include_router(veena_ai.router, tags=["REEVU Cognitive"])

# Voice
ai_router.include_router(voice.router, tags=["REEVU Voice"])
