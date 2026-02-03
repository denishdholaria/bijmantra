"""
Veena Voice API - VibeVoice TTS Integration

Endpoints:
- POST /api/v2/voice/synthesize - Synthesize speech from text
- GET /api/v2/voice/stream - WebSocket streaming synthesis
- GET /api/v2/voice/health - Check voice service status
- GET /api/v2/voice/voices - List available voices
"""

import asyncio
from typing import Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from app.services.voice_service import get_voice_service, get_unified_voice_service, VoiceServiceStatus, EDGE_VOICES

router = APIRouter(prefix="/voice", tags=["Veena Voice"])


# ============================================
# SCHEMAS
# ============================================

class SynthesizeRequest(BaseModel):
    """Request to synthesize speech"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice preset name")
    backend: Optional[str] = Field(None, description="TTS backend: vibevoice, edge_tts, or auto")
    cfg_scale: float = Field(1.5, ge=0.1, le=5.0, description="Classifier-free guidance scale (VibeVoice)")
    inference_steps: int = Field(5, ge=1, le=20, description="Number of diffusion steps (VibeVoice)")


class SynthesizeResponse(BaseModel):
    """Response with synthesis info"""
    success: bool
    duration_ms: float
    sample_rate: int = 24000
    format: str
    size_bytes: int


class VoiceInfo(BaseModel):
    """Information about a voice preset"""
    name: str
    language: str = "en"
    description: Optional[str] = None


class VoicesResponse(BaseModel):
    """List of available voices"""
    voices: List[VoiceInfo]
    default: Optional[str]


class HealthResponse(BaseModel):
    """Voice service health status"""
    available: bool
    model_loaded: bool
    device: str
    voices: List[str]
    default_voice: Optional[str]
    error: Optional[str]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/health")
async def voice_health():
    """
    Check all voice service backends.
    
    Returns status of VibeVoice, Edge TTS, and recommended backend.
    """
    service = get_unified_voice_service()
    return await service.get_status()


@router.get("/voices", response_model=VoicesResponse)
async def list_voices():
    """
    List available voice presets from all backends.
    
    Returns voices from VibeVoice (if available) and Edge TTS.
    """
    service = get_unified_voice_service()
    status = await service.get_status()
    
    voices = []
    
    # Add VibeVoice voices if available
    if status["vibevoice"]["available"]:
        for v in status["vibevoice"]["voices"]:
            voices.append(VoiceInfo(name=v, language="en", description=f"VibeVoice: {v}"))
    
    # Add Edge TTS voices (always available)
    if status["edge_tts"]["available"]:
        for name, desc in EDGE_VOICES.items():
            voices.append(VoiceInfo(name=name, language="en" if "en-" in name else "hi", description=f"Edge: {desc}"))
    
    # Fallback if nothing available
    if not voices:
        voices = [VoiceInfo(name="browser", language="en", description="Web Speech API (browser)")]
    
    default = status["vibevoice"]["default_voice"] or status["edge_tts"]["default_voice"] or "browser"
    return VoicesResponse(voices=voices, default=default)


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text with automatic backend selection.
    
    Tries backends in order: VibeVoice → Edge TTS → Error (use Web Speech in browser)
    """
    service = get_unified_voice_service()
    
    try:
        import time
        start = time.time()
        
        # Synthesize with automatic fallback
        audio_data, audio_format, backend_used = await service.synthesize(
            text=request.text,
            voice=request.voice,
            backend=request.backend
        )
        
        duration_ms = (time.time() - start) * 1000
        
        # Determine media type
        media_type = "audio/wav" if audio_format == "wav" else "audio/mpeg"
        
        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "X-Duration-Ms": str(int(duration_ms)),
                "X-Backend": backend_used,
                "X-Format": audio_format,
                "Content-Disposition": f'attachment; filename="veena_speech.{audio_format}"'
            }
        )
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/synthesize/stream")
async def synthesize_stream(
    text: str = Query(..., min_length=1, max_length=10000),
    voice: Optional[str] = Query(None),
    cfg_scale: float = Query(1.5, ge=0.1, le=5.0),
    inference_steps: int = Query(5, ge=1, le=20)
):
    """
    Stream synthesized speech.
    
    Returns chunked PCM16 audio at 24kHz.
    Use this for real-time playback of long texts.
    """
    service = get_voice_service()
    
    status = await service.check_health()
    if not status.available:
        raise HTTPException(
            status_code=503,
            detail=f"Voice service unavailable: {status.error}"
        )
    
    async def audio_generator():
        async for chunk in service.synthesize_stream(
            text=text,
            voice=voice,
            cfg_scale=cfg_scale,
            inference_steps=inference_steps
        ):
            yield chunk
    
    return StreamingResponse(
        audio_generator(),
        media_type="audio/pcm",
        headers={
            "X-Sample-Rate": "24000",
            "X-Channels": "1",
            "X-Bits-Per-Sample": "16"
        }
    )


@router.websocket("/ws")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice synthesis.
    
    Protocol:
    1. Client sends JSON: {"text": "...", "voice": "...", "cfg_scale": 1.5}
    2. Server streams PCM16 audio chunks
    3. Server sends JSON status messages between chunks
    
    This enables ~300ms first-speech latency for natural conversations.
    """
    await websocket.accept()
    service = get_voice_service()
    
    try:
        while True:
            # Receive synthesis request
            data = await websocket.receive_json()
            text = data.get("text", "")
            voice = data.get("voice")
            cfg_scale = data.get("cfg_scale", 1.5)
            inference_steps = data.get("inference_steps", 5)
            
            if not text:
                await websocket.send_json({
                    "type": "error",
                    "message": "No text provided"
                })
                continue
            
            # Send start notification
            await websocket.send_json({
                "type": "start",
                "text_length": len(text)
            })
            
            try:
                chunk_count = 0
                async for chunk in service.synthesize_stream(
                    text=text,
                    voice=voice,
                    cfg_scale=cfg_scale,
                    inference_steps=inference_steps
                ):
                    await websocket.send_bytes(chunk)
                    chunk_count += 1
                    
                    # Send progress every 10 chunks
                    if chunk_count % 10 == 0:
                        await websocket.send_json({
                            "type": "progress",
                            "chunks": chunk_count
                        })
                
                # Send completion
                await websocket.send_json({
                    "type": "complete",
                    "total_chunks": chunk_count
                })
                
            except RuntimeError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
