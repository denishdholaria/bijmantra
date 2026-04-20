/**
 * useAuth Hook
 * 
 * Manages authentication form state, quote rotation, audio playback,
 * and login flow orchestration.
 */

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useWorkspaceStore } from '@/store/workspaceStore'
import type { QuoteRegion } from './quotes'
import {
  inferThoughtRegion,
  getPreferredQuoteIndex,
  getRegionAwareRandomQuoteIndex,
} from './quotes'
import {
  AUDIO_CONFIG,
  getStartupAudioSingleton,
  shouldUseQuietStartupAudioDefault,
  applyStartupAudioEnvelope,
} from './audio'
import { AuthService } from './services/authService'

export function useAuth() {
  const navigate = useNavigate()
  const { login, isLoading, error, clearError } = useAuthStore()
  const { preferences, setActiveWorkspace, dismissGateway } = useWorkspaceStore()

  // Form state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Quote state
  const [currentQuote, setCurrentQuote] = useState(() => Math.floor(Math.random() * 24))
  const [isQuoteFading, setIsQuoteFading] = useState(false)
  const [isAutoRotatePaused, setIsAutoRotatePaused] = useState(false)
  const [inferredThoughtRegion] = useState<QuoteRegion | null>(() => {
    if (typeof navigator === 'undefined') {
      return null
    }

    const locales = navigator.languages?.length ? navigator.languages : [navigator.language]
    return inferThoughtRegion(locales)
  })
  const [pastQuotes, setPastQuotes] = useState<number[]>([])
  const [futureQuotes, setFutureQuotes] = useState<number[]>([])

  // Audio state
  const [isStartupAudioQuietByDefault, setIsStartupAudioQuietByDefault] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }

    return window.localStorage.getItem(AUDIO_CONFIG.storageKey) === null && shouldUseQuietStartupAudioDefault()
  })
  const [isStartupAudioEnabled, setIsStartupAudioEnabled] = useState(() => {
    if (typeof window === 'undefined') {
      return true
    }

    const storedPreference = window.localStorage.getItem(AUDIO_CONFIG.storageKey)

    if (storedPreference !== null) {
      return storedPreference !== 'off'
    }

    return !shouldUseQuietStartupAudioDefault()
  })
  const [hasPlayedStartupAudio, setHasPlayedStartupAudio] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }

    try {
      return window.sessionStorage.getItem(AUDIO_CONFIG.sessionKey) === 'played'
    } catch {
      return false
    }
  })
  const [isStartupAudioAvailable, setIsStartupAudioAvailable] = useState(() => (
    typeof window !== 'undefined' && typeof Audio !== 'undefined'
  ))
  const [isStartupAudioPlaying, setIsStartupAudioPlaying] = useState(false)

  // Refs
  const currentQuoteRef = useRef(currentQuote)
  const startupAudioRef = useRef<HTMLAudioElement | null>(null)
  const startupAudioPreparedForSuccessRef = useRef(false)
  const startupAudioShouldPersistAcrossUnmountRef = useRef(false)
  const startupAudioEnvelopeFrameRef = useRef<number | null>(null)
  const transitionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const autoRotateResumeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    currentQuoteRef.current = currentQuote
  }, [currentQuote])

  // Audio management functions
  const stopStartupAudioPlayback = (resetIndicator = true) => {
    if (startupAudioEnvelopeFrameRef.current !== null) {
      cancelAnimationFrame(startupAudioEnvelopeFrameRef.current)
      startupAudioEnvelopeFrameRef.current = null
    }

    startupAudioPreparedForSuccessRef.current = false
    startupAudioShouldPersistAcrossUnmountRef.current = false

    const audio = startupAudioRef.current
    if (audio) {
      audio.pause()
      audio.loop = false
      audio.muted = false
      audio.currentTime = 0
      audio.volume = AUDIO_CONFIG.peakVolume
    }

    if (resetIndicator) {
      setIsStartupAudioPlaying(false)
    }
  }

  const prepareStartupAudioForSuccessfulLogin = async () => {
    const audio = startupAudioRef.current

    if (
      !audio
      || !isStartupAudioAvailable
      || !isStartupAudioEnabled
      || hasPlayedStartupAudio
      || startupAudioPreparedForSuccessRef.current
      || (typeof document !== 'undefined' && document.visibilityState !== 'visible')
    ) {
      return false
    }

    try {
      audio.pause()
      audio.loop = true
      audio.muted = true
      audio.volume = 0
      audio.currentTime = 0
      await audio.play()
      startupAudioPreparedForSuccessRef.current = true
      return true
    } catch {
      audio.loop = false
      audio.muted = false
      audio.volume = AUDIO_CONFIG.peakVolume
      audio.currentTime = 0
      startupAudioPreparedForSuccessRef.current = false
      return false
    }
  }

  const revealPreparedStartupAudioAfterSuccessfulLogin = () => {
    const audio = startupAudioRef.current

    if (!audio || !startupAudioPreparedForSuccessRef.current) {
      return false
    }

    startupAudioShouldPersistAcrossUnmountRef.current = true
    startupAudioPreparedForSuccessRef.current = false
    setIsStartupAudioPlaying(true)
    audio.loop = false
    audio.muted = false
    audio.volume = AUDIO_CONFIG.peakVolume
    audio.currentTime = 0
    applyStartupAudioEnvelope(audio, startupAudioEnvelopeFrameRef)
    setHasPlayedStartupAudio(true)

    if (typeof window !== 'undefined') {
      try {
        window.sessionStorage.setItem(AUDIO_CONFIG.sessionKey, 'played')
      } catch {
        // Ignore storage failures and continue playback.
      }
    }

    return true
  }

  const playStartupAudio = async (forcePlay = false, persistAcrossUnmount = false) => {
    const audio = startupAudioRef.current

    if (
      !audio
      || !isStartupAudioAvailable
      || (!forcePlay && !isStartupAudioEnabled)
      || (!forcePlay && typeof document !== 'undefined' && document.visibilityState !== 'visible')
    ) {
      return false
    }

    try {
      stopStartupAudioPlayback()
      startupAudioShouldPersistAcrossUnmountRef.current = persistAcrossUnmount
      setIsStartupAudioPlaying(true)
      audio.muted = false
      audio.volume = AUDIO_CONFIG.peakVolume
      audio.currentTime = 0
      await audio.play()
      applyStartupAudioEnvelope(audio, startupAudioEnvelopeFrameRef)
      setHasPlayedStartupAudio(true)
      startupAudioPreparedForSuccessRef.current = false

      if (typeof window !== 'undefined') {
        try {
          window.sessionStorage.setItem(AUDIO_CONFIG.sessionKey, 'played')
        } catch {
          // Ignore storage failures and continue playback.
        }
      }

      return true
    } catch {
      startupAudioPreparedForSuccessRef.current = false
      startupAudioShouldPersistAcrossUnmountRef.current = false
      setIsStartupAudioPlaying(false)
      return false
    }
  }

  // Audio singleton setup
  useEffect(() => {
    if (typeof window === 'undefined' || typeof Audio === 'undefined') {
      return undefined
    }

    const audio = getStartupAudioSingleton()

    if (!audio) {
      return undefined
    }

    startupAudioRef.current = audio

    const handleEnded = () => {
      if (startupAudioEnvelopeFrameRef.current !== null) {
        cancelAnimationFrame(startupAudioEnvelopeFrameRef.current)
        startupAudioEnvelopeFrameRef.current = null
      }

      startupAudioPreparedForSuccessRef.current = false
      startupAudioShouldPersistAcrossUnmountRef.current = false
      audio.loop = false
      audio.volume = AUDIO_CONFIG.peakVolume
      setIsStartupAudioPlaying(false)
    }

    const handleCanPlay = () => {
      setIsStartupAudioAvailable(true)
    }

    const handleError = () => {
      handleEnded()
      setIsStartupAudioAvailable(false)
    }

    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('canplaythrough', handleCanPlay)
    audio.addEventListener('error', handleError)

    return () => {
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('canplaythrough', handleCanPlay)
      audio.removeEventListener('error', handleError)

      startupAudioRef.current = null
    }
  }, [])

  // Visibility change handling
  useEffect(() => {
    if (typeof document === 'undefined' || typeof window === 'undefined') {
      return undefined
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') {
        stopStartupAudioPlayback()
      }
    }

    const handlePageHide = () => {
      stopStartupAudioPlayback()
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('pagehide', handlePageHide)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('pagehide', handlePageHide)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (!startupAudioShouldPersistAcrossUnmountRef.current) {
        stopStartupAudioPlayback(false)
      }

      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current)
      }

      if (autoRotateResumeTimeoutRef.current) {
        clearTimeout(autoRotateResumeTimeoutRef.current)
      }
    }
  }, [])

  // Quote rotation functions
  const resumeAutoRotation = () => {
    if (autoRotateResumeTimeoutRef.current) {
      clearTimeout(autoRotateResumeTimeoutRef.current)
      autoRotateResumeTimeoutRef.current = null
    }

    setIsAutoRotatePaused(false)
  }

  const pauseAutoRotation = () => {
    if (autoRotateResumeTimeoutRef.current) {
      clearTimeout(autoRotateResumeTimeoutRef.current)
      autoRotateResumeTimeoutRef.current = null
    }

    setIsAutoRotatePaused(true)
  }

  const pauseAutoRotationTemporarily = (duration = 15000) => {
    pauseAutoRotation()
    autoRotateResumeTimeoutRef.current = setTimeout(() => {
      setIsAutoRotatePaused(false)
      autoRotateResumeTimeoutRef.current = null
    }, duration)
  }

  const handleQuoteSurfaceBlur = (event: React.FocusEvent<HTMLElement>) => {
    const nextFocused = event.relatedTarget as Node | null

    if (!event.currentTarget.contains(nextFocused)) {
      resumeAutoRotation()
    }
  }

  const transitionQuote = (
    nextIndex: number,
    delay = 300,
    mode: 'push' | 'back' | 'forward' = 'push',
  ) => {
    const previousQuote = currentQuoteRef.current

    if (nextIndex === previousQuote) {
      return
    }

    if (transitionTimeoutRef.current) {
      clearTimeout(transitionTimeoutRef.current)
    }

    setIsQuoteFading(true)
    transitionTimeoutRef.current = setTimeout(() => {
      if (mode === 'back') {
        setPastQuotes((previous) => previous.slice(0, -1))
        setFutureQuotes((previous) => [previousQuote, ...previous])
      } else if (mode === 'forward') {
        setPastQuotes((previous) => [...previous, previousQuote])
        setFutureQuotes((previous) => previous.slice(1))
      } else {
        setPastQuotes((previous) => [...previous, previousQuote])
        setFutureQuotes([])
      }

      currentQuoteRef.current = nextIndex
      setCurrentQuote(nextIndex)
      setIsQuoteFading(false)
      transitionTimeoutRef.current = null
    }, delay)
  }

  const effectiveThoughtRegion = inferredThoughtRegion

  // Auto-rotate quotes every 10 seconds
  useEffect(() => {
    if (isAutoRotatePaused) {
      return undefined
    }

    const interval = setInterval(() => {
      transitionQuote(getRegionAwareRandomQuoteIndex(currentQuoteRef.current, effectiveThoughtRegion), 500)
    }, 10000)

    return () => clearInterval(interval)
  }, [effectiveThoughtRegion, isAutoRotatePaused])

  // Initialize with preferred quote based on locale
  useEffect(() => {
    if (!effectiveThoughtRegion) {
      return
    }

    const nextIndex = getPreferredQuoteIndex(currentQuoteRef.current, effectiveThoughtRegion)

    if (nextIndex === currentQuoteRef.current) {
      return
    }

    if (transitionTimeoutRef.current) {
      clearTimeout(transitionTimeoutRef.current)
      transitionTimeoutRef.current = null
    }

    currentQuoteRef.current = nextIndex
    setCurrentQuote(nextIndex)
    setIsQuoteFading(false)
    setPastQuotes([])
    setFutureQuotes([])
  }, [effectiveThoughtRegion])

  // Event handlers
  const handleStartupAudioToggle = () => {
    const nextEnabled = !isStartupAudioEnabled

    setIsStartupAudioQuietByDefault(false)
    setIsStartupAudioEnabled(nextEnabled)

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(AUDIO_CONFIG.storageKey, nextEnabled ? 'on' : 'off')
    }

    if (startupAudioRef.current) {
      stopStartupAudioPlayback()
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    const shouldPlayStartupToneOnSuccess = (
      isStartupAudioEnabled
      && isStartupAudioAvailable
      && !hasPlayedStartupAudio
    )

    if (shouldPlayStartupToneOnSuccess) {
      await prepareStartupAudioForSuccessfulLogin()
    }

    try {
      await login(email, password)

      if (shouldPlayStartupToneOnSuccess) {
        const revealedPreparedAudio = revealPreparedStartupAudioAfterSuccessfulLogin()

        if (!revealedPreparedAudio) {
          await playStartupAudio(true, true)
        }
      }

      // Determine where to navigate after login
      const result = AuthService.determinePostLoginNavigation(
        preferences.defaultWorkspace,
        preferences.showGatewayOnLogin
      )

      if (result.shouldNavigateToGateway) {
        navigate('/gateway', { replace: true })
      } else if (result.workspaceRoute) {
        setActiveWorkspace(preferences.defaultWorkspace!)
        dismissGateway()
        navigate(result.workspaceRoute, { replace: true })
      }
    } catch {
      stopStartupAudioPlayback()
      // Error is handled by the store
    }
  }

  const handlePreviousQuote = () => {
    const previousQuote = pastQuotes[pastQuotes.length - 1]
    if (previousQuote !== undefined) {
      pauseAutoRotationTemporarily()
      transitionQuote(previousQuote, 300, 'back')
    }
  }

  const handleNextQuote = () => {
    pauseAutoRotationTemporarily()

    if (futureQuotes.length > 0) {
      transitionQuote(futureQuotes[0], 300, 'forward')
      return
    }

    transitionQuote(getRegionAwareRandomQuoteIndex(currentQuoteRef.current, effectiveThoughtRegion))
  }

  const handleDemoCredentials = () => {
    setEmail('demo@bijmantra.org')
    setPassword('Demo123!')
  }

  return {
    // Form state
    email,
    setEmail,
    password,
    setPassword,
    showPassword,
    setShowPassword,
    isLoading,
    error,

    // Quote state
    currentQuote,
    isQuoteFading,
    inferredThoughtRegion,
    pastQuotes,
    futureQuotes,

    // Audio state
    isStartupAudioEnabled,
    isStartupAudioPlaying,
    hasPlayedStartupAudio,
    isStartupAudioAvailable,
    isStartupAudioQuietByDefault,

    // Event handlers
    handleSubmit,
    handleStartupAudioToggle,
    handlePreviousQuote,
    handleNextQuote,
    handleDemoCredentials,
    handleQuoteSurfaceBlur,
    pauseAutoRotation,
    resumeAutoRotation,
    playStartupAudio,
  }
}
