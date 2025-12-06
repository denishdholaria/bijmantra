"""
VibeVoice Integration Service for Veena AI
Real-time Text-to-Speech using Microsoft VibeVoice

Features:
- WebSocket streaming TTS
- ~300ms first speech latency
- Long-form speech generation
- Multiple voice presets
"""

import asyncio
import json
import os
from typing import Optional, AsyncIterator, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VoicePreset(str, Enum):
    """Available voice presets"""
    CARTER = "Carter"
    DEFAULT = "en-WHTest_man"


@dataclass
class VoiceConfig:
    """Configuration for voice synthesis"""
    voice: str = "Carter"
    cfg_scale: float = 1.5
    inference_steps: int = 5
    sample_rate: int = 24000


@dataclass
class VoiceServiceStatus:
    """Status of the voice service"""
    available: bool = False
    model_loaded: bool = False
    device: str = "unknown"
    voices: List[str] = field(default_factory=list)
    default_voice: Optional[str] = None
    error: Optional[str] = None


class VibeVoiceService:
    """
    VibeVoice TTS Service for Veena AI
    
    Connects to VibeVoice WebSocket server for real-time speech synthesis.
    Designed for natural, long-form conversations about research data.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        model_path: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.model_path = model_path or os.getenv(
            "VIBEVOICE_MODEL_PATH",
            "microsoft/VibeVoice-Realtime-0.5B"
        )
        self.ws_url = f"ws://{host}:{port}/stream"
        self._status = VoiceServiceStatus()
        self._config = VoiceConfig()
        
    @property
    def status(self) -> VoiceServiceStatus:
        return self._status
    
    async def check_health(self) -> VoiceServiceStatus:
        """Check if VibeVoice server is available"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{self.host}:{self.port}/config",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._status = VoiceServiceStatus(
                            available=True,
                            model_loaded=True,
                            device="cuda",  # Assumed from server
                            voices=data.get("voices", []),
                            default_voice=data.get("default_voice")
                        )
                    else:
                        self._status = VoiceServiceStatus(
                            available=False,
                            error=f"Server returned {response.status}"
                        )
        except Exception as e:
            self._status = VoiceServiceStatus(
                available=False,
                error=str(e)
            )
        return self._status
    
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        cfg_scale: float = 1.5,
        inference_steps: int = 5
    ) -> AsyncIterator[bytes]:
        """
        Stream audio synthesis from text.
        
        Yields PCM16 audio chunks at 24kHz sample rate.
        
        Args:
            text: Text to synthesize
            voice: Voice preset name
            cfg_scale: Classifier-free guidance scale
            inference_steps: Number of diffusion steps
            
        Yields:
            bytes: PCM16 audio chunks
        """
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed")
            raise RuntimeError("websockets package required for voice synthesis")
        
        # Build WebSocket URL with parameters
        params = {
            "text": text,
            "cfg": str(cfg_scale),
            "steps": str(inference_steps)
        }
        if voice:
            params["voice"] = voice
            
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.ws_url}?{query}"
        
        try:
            async with websockets.connect(url) as ws:
                async for message in ws:
                    if isinstance(message, bytes):
                        # Audio chunk (PCM16)
                        yield message
                    elif isinstance(message, str):
                        # Log message from server
                        try:
                            log_data = json.loads(message)
                            event = log_data.get("event", "unknown")
                            if event == "backend_busy":
                                raise RuntimeError("Voice server is busy")
                            elif event == "generation_error":
                                raise RuntimeError(log_data.get("data", {}).get("message", "Unknown error"))
                            logger.debug(f"VibeVoice event: {event}")
                        except json.JSONDecodeError:
                            logger.debug(f"VibeVoice message: {message}")
        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            raise
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        cfg_scale: float = 1.5,
        inference_steps: int = 5
    ) -> bytes:
        """
        Synthesize complete audio from text.
        
        Returns complete PCM16 audio at 24kHz.
        
        Args:
            text: Text to synthesize
            voice: Voice preset name
            cfg_scale: Classifier-free guidance scale
            inference_steps: Number of diffusion steps
            
        Returns:
            bytes: Complete PCM16 audio
        """
        chunks = []
        async for chunk in self.synthesize_stream(
            text, voice, cfg_scale, inference_steps
        ):
            chunks.append(chunk)
        return b"".join(chunks)
    
    def pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 24000) -> bytes:
        """Convert PCM16 data to WAV format"""
        import struct
        
        # WAV header
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(pcm_data)
        
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,
            b'WAVE',
            b'fmt ',
            16,  # Subchunk1Size
            1,   # AudioFormat (PCM)
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b'data',
            data_size
        )
        
        return header + pcm_data


# ============================================
# EDGE TTS SERVICE (Free, No GPU Required)
# ============================================

# Popular Edge TTS voices
EDGE_VOICES = {
    "en-US-AriaNeural": "Aria (Female, US)",
    "en-US-GuyNeural": "Guy (Male, US)",
    "en-US-JennyNeural": "Jenny (Female, US)",
    "en-GB-SoniaNeural": "Sonia (Female, UK)",
    "en-IN-NeerjaNeural": "Neerja (Female, India)",
    "en-IN-PrabhatNeural": "Prabhat (Male, India)",
    "hi-IN-SwaraNeural": "Swara (Female, Hindi)",
    "hi-IN-MadhurNeural": "Madhur (Male, Hindi)",
}


class EdgeTTSService:
    """
    Microsoft Edge TTS Service
    
    Free, high-quality TTS that works without GPU.
    Good middle-ground between VibeVoice and Web Speech API.
    """
    
    def __init__(self):
        self.default_voice = "en-US-AriaNeural"
        self._available: Optional[bool] = None
    
    async def check_available(self) -> bool:
        """Check if edge-tts is installed and working"""
        if self._available is not None:
            return self._available
        try:
            import edge_tts
            self._available = True
        except ImportError:
            self._available = False
        return self._available
    
    def get_voices(self) -> Dict[str, str]:
        """Get available voices"""
        return EDGE_VOICES
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Synthesize speech using Edge TTS.
        
        Returns MP3 audio data.
        """
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts package not installed")
        
        voice = voice or self.default_voice
        communicate = edge_tts.Communicate(text, voice)
        
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        
        return b"".join(audio_chunks)
    
    async def synthesize_stream(self, text: str, voice: Optional[str] = None) -> AsyncIterator[bytes]:
        """Stream audio synthesis"""
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts package not installed")
        
        voice = voice or self.default_voice
        communicate = edge_tts.Communicate(text, voice)
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]


# ============================================
# UNIFIED VOICE SERVICE
# ============================================

class UnifiedVoiceService:
    """
    Unified voice service with automatic fallback:
    1. VibeVoice (best quality, needs GPU server)
    2. Edge TTS (good quality, free, no GPU)
    3. Web Speech API (handled by frontend)
    """
    
    def __init__(self):
        self.vibevoice = VibeVoiceService(
            host=os.getenv("VIBEVOICE_HOST", "localhost"),
            port=int(os.getenv("VIBEVOICE_PORT", "3000"))
        )
        self.edge_tts = EdgeTTSService()
        self._preferred_backend: Optional[str] = None
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all voice backends"""
        vibevoice_status = await self.vibevoice.check_health()
        edge_available = await self.edge_tts.check_available()
        
        return {
            "vibevoice": {
                "available": vibevoice_status.available,
                "voices": vibevoice_status.voices,
                "default_voice": vibevoice_status.default_voice,
                "quality": "premium"
            },
            "edge_tts": {
                "available": edge_available,
                "voices": list(EDGE_VOICES.keys()) if edge_available else [],
                "default_voice": "en-US-AriaNeural" if edge_available else None,
                "quality": "good"
            },
            "web_speech": {
                "available": True,  # Always available in browser
                "quality": "basic"
            },
            "recommended": "vibevoice" if vibevoice_status.available else ("edge_tts" if edge_available else "web_speech")
        }
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        backend: Optional[str] = None
    ) -> tuple[bytes, str, str]:
        """
        Synthesize speech with automatic fallback.
        
        Returns: (audio_data, format, backend_used)
        """
        # Try VibeVoice first
        if backend in (None, "vibevoice"):
            vibevoice_status = await self.vibevoice.check_health()
            if vibevoice_status.available:
                try:
                    pcm_data = await self.vibevoice.synthesize(text, voice)
                    wav_data = self.vibevoice.pcm_to_wav(pcm_data)
                    return wav_data, "wav", "vibevoice"
                except Exception as e:
                    logger.warning(f"VibeVoice failed, falling back: {e}")
        
        # Try Edge TTS
        if backend in (None, "edge_tts"):
            if await self.edge_tts.check_available():
                try:
                    mp3_data = await self.edge_tts.synthesize(text, voice)
                    return mp3_data, "mp3", "edge_tts"
                except Exception as e:
                    logger.warning(f"Edge TTS failed: {e}")
        
        # No server-side TTS available
        raise RuntimeError("No TTS backend available. Use Web Speech API in browser.")


# Singleton instances
_voice_service: Optional[VibeVoiceService] = None
_unified_service: Optional[UnifiedVoiceService] = None


def get_voice_service() -> VibeVoiceService:
    """Get or create VibeVoice service singleton"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VibeVoiceService(
            host=os.getenv("VIBEVOICE_HOST", "localhost"),
            port=int(os.getenv("VIBEVOICE_PORT", "3000"))
        )
    return _voice_service


def get_unified_voice_service() -> UnifiedVoiceService:
    """Get or create unified voice service singleton"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedVoiceService()
    return _unified_service
