"""
AI Domain API Router

Consolidates all AI-related endpoints under /api/v2/ai/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- REEVU Cognitive (legacy compatibility surface)
- DevGuru (PhD mentoring system)
- Chat/REEVU (Multi-tier LLM chat with function calling)
- Voice (Voice interaction)
- Vision (Computer vision and image analysis)
"""

from fastapi import APIRouter

# Import all AI-related routers
from app.api.v2 import (
    chat,
    devguru,
    veena_ai,
    vision,
    voice,
)

# Create main AI router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["AI"])

# Include all AI sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(chat.router, tags=["REEVU AI Chat"])
router.include_router(devguru.router, tags=["DevGuru PhD Mentor"])
router.include_router(veena_ai.router, tags=["REEVU Cognitive"])
router.include_router(vision.router, tags=["Computer Vision"])
router.include_router(voice.router, tags=["Voice Interaction"])
