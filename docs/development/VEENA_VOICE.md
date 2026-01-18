# Veena Voice Architecture

> Natural speech synthesis for Veena AI Assistant

## Overview

Veena supports multiple Text-to-Speech (TTS) backends with automatic fallback:

```
┌─────────────────────────────────────────────────────────────┐
│                      User's Device                          │
│  (Browser - Desktop/Tablet/Mobile)                          │
│                         │                                   │
│                    Plays Audio                              │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ Audio Stream
                          │
┌─────────────────────────────────────────────────────────────┐
│                    Bijmantra Backend                        │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ VibeVoice   │   │  Edge TTS   │   │ Web Speech  │       │
│  │ (Best)      │──▶│  (Good)     │──▶│ (Fallback)  │       │
│  │ Needs GPU   │   │  Free API   │   │ Browser     │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## TTS Tiers

| Tier | Provider | Quality | Latency | Cost | Requirements |
|------|----------|---------|---------|------|--------------|
| 1 | **VibeVoice** | ⭐⭐⭐⭐⭐ Natural | ~300ms | Server cost | GPU (CUDA/MPS) |
| 2 | **Edge TTS** | ⭐⭐⭐⭐ Good | ~500ms | Free | Internet |
| 3 | **Web Speech API** | ⭐⭐ Robotic | Instant | Free | Browser |

## How It Works

1. **User clicks speak** on a Veena response
2. **Frontend checks** VibeVoice availability
3. **Fallback chain:**
   - VibeVoice available? → Use it (best quality)
   - Edge TTS configured? → Use it (good quality, free)
   - Neither? → Use Web Speech API (always works)

**Key Point:** The user's device (phone, tablet, laptop) doesn't need a GPU. It just plays the audio stream. Heavy processing happens on the server.

## Device Compatibility

### Server-Side (Where TTS runs)

| Device | VibeVoice Support | Performance |
|--------|-------------------|-------------|
| NVIDIA GPU (T4+) | ✅ `cuda` | Real-time |
| Apple Silicon (M1-M4) | ✅ `mps` | Real-time |
| CPU only | ⚠️ `cpu` | Slower |

### Client-Side (User's browser)

| Device | Support |
|--------|---------|
| Desktop (any OS) | ✅ Plays audio |
| Tablet (iPad/Android) | ✅ Plays audio |
| Mobile (iPhone/Android) | ✅ Plays audio |

No special hardware needed on user devices.

## Deployment Phases

### Phase 1: MVP ✅ CURRENT
- Edge TTS (Microsoft free API) — **Working now!**
- Good voice quality, no GPU needed
- 8 voices: US/UK/India English + Hindi

### Phase 2: Premium Voice (Optional)
- Add VibeVoice server for ultra-natural voice
- Requires GPU server (CUDA) or Apple Silicon (MPS)
- Best for high-value users needing natural conversation

### Phase 3: Fallback
- Web Speech API (browser-native)
- Always available as last resort
- Robotic but functional

## API Endpoints

```
GET  /api/v2/voice/health     - Check TTS availability
GET  /api/v2/voice/voices     - List available voices
POST /api/v2/voice/synthesize - Generate audio (returns WAV)
GET  /api/v2/voice/synthesize/stream - Stream audio (PCM chunks)
WS   /api/v2/voice/ws         - WebSocket for real-time synthesis
```

## Configuration

### Environment Variables

```bash
# VibeVoice server location (if running)
VIBEVOICE_HOST=localhost
VIBEVOICE_PORT=3000

# Edge TTS (Phase 2)
EDGE_TTS_ENABLED=true
```

### Starting VibeVoice Server

```bash
cd VibeVoice
./start_server.sh

# Auto-detects device:
# - Apple Silicon → mps
# - NVIDIA GPU → cuda  
# - Other → cpu
```

## Files

| File | Purpose |
|------|---------|
| `backend/app/services/voice_service.py` | VibeVoice client |
| `backend/app/api/v2/voice.py` | Voice API endpoints |
| `frontend/src/components/ai/Veena.tsx` | UI with voice toggle |
| `VibeVoice/start_server.sh` | Server startup script |

## Current Status

✅ **Working Now:**
- Edge TTS with 8 voices (US, UK, India English + Hindi)
- Automatic fallback to Web Speech API
- Voice toggle in Veena UI (🔊/🔇 button)
- Voice selector dropdown (right-click 🔊 button)

## How to Use

1. Open Veena chat (click 🪷 or press Ctrl+/)
2. Click 🔊 to enable voice
3. Right-click 🔊 to select a voice
4. Click 🔊 on any message to hear it spoken

## Future Enhancements

- [ ] Streaming text-to-speech (speak while generating)
- [ ] VibeVoice integration for premium users
- [ ] Voice cloning for custom Veena voice
- [ ] Speech-to-text for voice input
