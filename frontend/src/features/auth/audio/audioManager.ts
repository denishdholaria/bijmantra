/**
 * Audio Manager
 * 
 * Singleton audio manager for startup sound.
 */

import { AUDIO_CONFIG } from './types'

declare global {
  interface Window {
    __bijmantraLoginStartupAudio?: HTMLAudioElement
  }
}

export function getStartupAudioSingleton(): HTMLAudioElement | null {
  if (typeof window === 'undefined' || typeof Audio === 'undefined') {
    return null
  }

  if (!window.__bijmantraLoginStartupAudio) {
    const audio = new Audio(AUDIO_CONFIG.source)
    audio.preload = 'auto'
    audio.load()
    window.__bijmantraLoginStartupAudio = audio
  }

  return window.__bijmantraLoginStartupAudio
}

export function shouldUseQuietStartupAudioDefault(): boolean {
  if (typeof navigator === 'undefined') {
    return false
  }

  const connection = (navigator as Navigator & {
    connection?: { saveData?: boolean }
  }).connection

  return connection?.saveData === true
}
