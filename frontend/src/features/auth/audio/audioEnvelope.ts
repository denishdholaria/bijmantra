/**
 * Audio Envelope
 * 
 * Fade-in/fade-out logic for smooth audio playback.
 */

import { AUDIO_CONFIG } from './types'

export function applyStartupAudioEnvelope(
  audio: HTMLAudioElement,
  envelopeFrameRef: React.MutableRefObject<number | null>
): void {
  if (envelopeFrameRef.current !== null) {
    cancelAnimationFrame(envelopeFrameRef.current)
    envelopeFrameRef.current = null
  }

  const totalDurationMs = Number.isFinite(audio.duration) && audio.duration > 0
    ? audio.duration * 1000
    : AUDIO_CONFIG.fallbackDurationMs
  const fadeInMs = Math.min(320, totalDurationMs * 0.18)
  const fadeOutMs = Math.min(880, totalDurationMs * 0.32)
  const startedAt = performance.now()

  const step = (now: number) => {
    const elapsed = now - startedAt
    const remaining = totalDurationMs - elapsed
    let nextVolume = AUDIO_CONFIG.peakVolume

    if (elapsed < fadeInMs) {
      nextVolume = AUDIO_CONFIG.peakVolume * (elapsed / Math.max(fadeInMs, 1))
    } else if (remaining < fadeOutMs) {
      nextVolume = AUDIO_CONFIG.peakVolume * Math.max(remaining / Math.max(fadeOutMs, 1), 0)
    }

    audio.volume = Math.max(0, Math.min(AUDIO_CONFIG.peakVolume, nextVolume))

    if (!audio.paused && elapsed < totalDurationMs) {
      envelopeFrameRef.current = requestAnimationFrame(step)
      return
    }

    envelopeFrameRef.current = null
  }

  audio.volume = 0
  envelopeFrameRef.current = requestAnimationFrame(step)
}
