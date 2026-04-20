/**
 * Audio System Types
 * 
 * Type definitions for the startup audio system.
 */

export interface AudioState {
  isEnabled: boolean
  isPlaying: boolean
  hasPlayed: boolean
  isAvailable: boolean
  isQuietByDefault: boolean
}

export interface AudioConfig {
  storageKey: string
  sessionKey: string
  source: string
  peakVolume: number
  fallbackDurationMs: number
}

export const AUDIO_CONFIG: AudioConfig = {
  storageKey: 'bijmantra.login.startup-audio-enabled',
  sessionKey: 'bijmantra.login.startup-audio-played',
  source: new URL('../../../bijmantra-start-audio.mp3', import.meta.url).href,
  peakVolume: 0.34,
  fallbackDurationMs: 2600,
}
