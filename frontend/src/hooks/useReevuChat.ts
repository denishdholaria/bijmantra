/**
 * useReevuChat - Shared hook for REEVU AI chat functionality
 *
 * Consolidates all chat logic from legacy and REEVU chat UIs into a single
 * reusable hook. Both the FAB widget and full-page chat use this hook.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuthStore } from '@/store/auth'
import { LEGACY_REEVU_STORAGE_KEY } from '@/lib/legacyReevu'
import { useReevuVoice } from './useReevuVoice'
import type { EvidenceEnvelope } from '@/components/ai/EvidenceTraceCard'

// ============================================
// TYPES
// ============================================

export interface ReevuMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    sources?: ReevuSource[]
    provider?: string
    model?: string
    proposal?: {
      id: number
      title: string
      status: string
      description: string
    }
    evidence_envelope?: EvidenceEnvelope
  }
}

export interface ReevuSource {
  doc_id: string
  doc_type: string
  title: string | null
  similarity: number
}

export type AIMode = 'cloud'

interface ReevuConfig {
  mode: 'managed' | 'byok'
  byok: {
    provider: string
    apiKey: string
    model: string
  }
}

export interface EffectiveBackend {
  mode: 'cloud' | 'none'
  name: string
  ready: boolean
}

// ============================================
// CONSTANTS
// ============================================

const STORAGE_KEY = 'reevu_conversation_history'
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2'
const REEVU_CONFIG_KEY = 'bijmantra_reevu_config_v1'
const MAX_STORED_MESSAGES = 100
const REAL_PROVIDER_IDS = ['groq', 'google', 'huggingface', 'functiongemma', 'openai', 'anthropic'] as const

const PROVIDER_NAMES: Record<string, string> = {
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq'
}

const INITIAL_MESSAGE: ReevuMessage = {
  id: '1',
  role: 'assistant',
  content: 'Hello! 🙏 Welcome to our conversation about plant breeding and agricultural research. I\'m REEVU.',
  timestamp: new Date()
}

// ============================================
// HOOK
// ============================================

export function useReevuChat() {
  // Runtime configuration (single path: backend chat stream)
  const [reevuConfig, setReevuConfig] = useState<ReevuConfig>({
    mode: 'managed',
    byok: {
      provider: 'google',
      apiKey: '',
      model: 'gemini-2.5-flash'
    }
  })
  const [status, setStatus] = useState<{
    reachable: boolean
    provider?: string
    model?: string
    templateOnly?: boolean
    authRequired?: boolean
  }>({ reachable: false })

  // Messages
  const [messages, setMessages] = useState<ReevuMessage[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_REEVU_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        return parsed.map((m: ReevuMessage) => ({ ...m, timestamp: new Date(m.timestamp) }))
      }
    } catch {
      // ignore invalid local storage payloads
    }
    return [{ ...INITIAL_MESSAGE, timestamp: new Date() }]
  })

  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Voice Hook
  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    isSpeaking,
    speak,
    stopSpeaking,
    isSupported: isVoiceSupported,
    error: voiceError
  } = useReevuVoice({
    onTranscript: (text) => setInput(text)
  })

  // Load REEVU config on mount with migration from legacy config
  useEffect(() => {
    try {
      const savedReevu = localStorage.getItem(REEVU_CONFIG_KEY)
      if (savedReevu) {
        const parsed = JSON.parse(savedReevu)
        if (parsed && (parsed.mode === 'managed' || parsed.mode === 'byok')) {
          const normalized: ReevuConfig = {
            mode: 'managed',
            byok: {
              provider: parsed.byok?.provider || 'google',
              apiKey: '',
              model: parsed.byok?.model || 'gemini-2.5-flash'
            }
          }
          setReevuConfig(normalized)
          localStorage.setItem(REEVU_CONFIG_KEY, JSON.stringify(normalized))
        }
      }

      const saved = localStorage.getItem(AI_CONFIG_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed && parsed.cloud && typeof parsed.cloud === 'object') {
          const migrated: ReevuConfig = {
            mode: 'managed',
            byok: {
              provider: parsed.cloud.provider || 'google',
              apiKey: '',
              model: parsed.cloud.model || 'gemini-2.5-flash'
            }
          }
          setReevuConfig(migrated)
          localStorage.setItem(REEVU_CONFIG_KEY, JSON.stringify(migrated))
        }
      }
    } catch (e) {
      console.warn('[REEVU] Error loading AI config:', e)
    }
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const token = useAuthStore.getState().token
      const response = await fetch('/api/v2/chat/status', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })

      if (response.status === 401) {
        setStatus({ reachable: false, authRequired: true })
        return { reachable: false, authRequired: true }
      }

      if (!response.ok) throw new Error(`Status ${response.status}`)

      const data = await response.json()
      const providers = (data?.providers || {}) as Record<string, { available?: boolean; configured?: boolean }>
      const hasRealProvider = REAL_PROVIDER_IDS.some((providerId) => {
        const p = providers[providerId]
        return Boolean(p?.available || p?.configured)
      })
      const templateOnly = data?.active_provider === 'template' && !hasRealProvider
      const next = {
        reachable: true,
        provider: data?.active_provider,
        model: data?.active_model,
        templateOnly,
        authRequired: false
      }
      setStatus(next)
      return next
    } catch {
      const next = { reachable: false, authRequired: false }
      setStatus(next)
      return next
    }
  }, [])

  // Check backend chat status on mount
  useEffect(() => {
    void refreshStatus()
  }, [refreshStatus])

  // Determine effective AI backend
  const getEffectiveBackend = useCallback((): EffectiveBackend => {
    if (status.authRequired) {
      return { mode: 'none', name: 'Authentication required', ready: false }
    }

    if (!status.reachable) {
      return { mode: 'none', name: 'Managed backend unreachable', ready: false }
    }

    if (status.templateOnly) {
      return {
        mode: 'none',
        name: 'Managed backend in template fallback (no provider configured)',
        ready: false
      }
    }

    if (status.reachable) {
      const providerName = status.provider && PROVIDER_NAMES[status.provider]
        ? PROVIDER_NAMES[status.provider]
        : status.provider || 'Server AI'
      return {
        mode: 'cloud',
        name: `${providerName}${status.model ? ` · ${status.model}` : ''}`,
        ready: true
      }
    }

    return { mode: 'none', name: 'Managed backend status unknown', ready: false }
  }, [status])

  const effectiveBackend = getEffectiveBackend()

  // Save messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)))
    } catch {
      // ignore localStorage write failures
    }
  }, [messages])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Clear history
  const clearHistory = useCallback(() => {
    setMessages([{
      id: Date.now().toString(),
      role: 'assistant',
      content: 'Chat cleared. How can I help you?',
      timestamp: new Date()
    }])
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(LEGACY_REEVU_STORAGE_KEY)
  }, [])

  // Update mode (kept for compatibility)
  const setAIMode = useCallback((mode: AIMode) => {
    const nextMode: ReevuConfig['mode'] = mode === 'cloud' ? 'managed' : 'managed'
    const updated = { ...reevuConfig, mode: nextMode }
    setReevuConfig(updated)
    localStorage.setItem(REEVU_CONFIG_KEY, JSON.stringify(updated))
  }, [reevuConfig])

  // Send message
  const sendMessage = useCallback(async (context?: any) => {
    // Determine the message text to send
    const textToSend = context && typeof context === 'string' ? context : input.trim()

    if (!textToSend || isProcessing) return

    const userMessage: ReevuMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')

    const token = useAuthStore.getState().token
    if (!token) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ **Login required**\n\nPlease sign in again. REEVU chat APIs require authentication.',
        timestamp: new Date(),
        metadata: {
          provider: 'System',
          model: 'Unauthorized'
        }
      }])
      return
    }

    const latestStatus = await refreshStatus()
    if (latestStatus?.authRequired) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ **Session expired**\n\nPlease sign in again to continue using REEVU.',
        timestamp: new Date(),
        metadata: {
          provider: 'System',
          model: 'Unauthorized'
        }
      }])
      return
    }

    if (!effectiveBackend.ready) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ **Managed backend is not AI-ready**\n\nREEVU cannot answer yet because no live provider is available.\n\nFix options:\n1) Add server key (GROQ/GOOGLE/OPENAI/ANTHROPIC) in backend env\n2) Switch to **BYOK** in AI Settings and paste your provider key.',
        timestamp: new Date(),
        metadata: {
          provider: 'System',
          model: status.model || 'Not configured'
        }
      }])
      return
    }

    setIsProcessing(true)

    // Add temporary assistant message for streaming
    const assistantMsgId = (Date.now() + 1).toString()
    const providerName = status.provider && PROVIDER_NAMES[status.provider]
      ? PROVIDER_NAMES[status.provider]
      : status.provider || 'Managed backend'
    setMessages(prev => [...prev, {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      metadata: {
        provider: `Connecting to ${providerName}...`,
        model: status.model || 'auto'
      }
    }])

    try {
      // Prepare Conversation History (limited to last 10 messages)
      const conversationHistory = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content
      }))

      // Prepare request body for streaming endpoint
      const requestBody = {
        message: textToSend,
        conversation_history: conversationHistory,
        include_context: true,
        context_limit: 5,
      }

      const response = await fetch('/api/v2/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok || !response.body) {
        const errorText = await response.text()
        throw new Error(`Chat error: ${response.status} - ${errorText}`)
      }

      // Process SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''
      let actualProvider = providerName
      let actualModel = status.model || 'unknown'
      let sseBuffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        sseBuffer += decoder.decode(value, { stream: true })

        // Process full SSE events separated by blank line
        let eventBoundary = sseBuffer.indexOf('\n\n')
        while (eventBoundary !== -1) {
          const rawEvent = sseBuffer.slice(0, eventBoundary)
          sseBuffer = sseBuffer.slice(eventBoundary + 2)

          const dataLines = rawEvent
            .split('\n')
            .filter((line) => line.startsWith('data: '))
            .map((line) => line.slice(6))

          if (dataLines.length > 0) {
            const payload = dataLines.join('\n')
            try {
              const data = JSON.parse(payload)

              if (data.type === 'start') {
                actualProvider = data.provider || providerName
                actualModel = data.model || actualModel
              } else if (data.type === 'chunk' && data.content) {
                fullContent += data.content
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? {
                      ...msg,
                      content: fullContent,
                      metadata: {
                        provider: actualProvider,
                        model: actualModel
                      }
                    }
                    : msg
                ))
              } else if (data.type === 'proposal_created') {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? {
                      ...msg,
                      metadata: {
                        ...msg.metadata,
                        proposal: data.data
                      }
                    }
                    : msg
                ))
              } else if (data.type === 'summary' && data.evidence_envelope) {
                // Stage B: capture evidence envelope from summary SSE event
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? {
                      ...msg,
                      metadata: {
                        ...msg.metadata,
                        evidence_envelope: data.evidence_envelope as EvidenceEnvelope
                      }
                    }
                    : msg
                ))
              } else if (data.type === 'error') {
                throw new Error(data.message || 'Stream error')
              }
            } catch {
              // Ignore keepalive/comments/non-JSON payloads
            }
          }

          eventBoundary = sseBuffer.indexOf('\n\n')
        }
      }

      // Final update with complete content
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMsgId
          ? {
            ...msg,
            content: fullContent || 'No response received.',
            metadata: {
              provider: actualProvider,
              model: actualModel
            }
          }
          : msg
      ))
    } catch (error) {
      console.error('[REEVU] Chat error:', error)
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId
          ? { ...m, content: m.content + `\n\n[System Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your connection.]` }
          : m
      ))
    } finally {
      setIsProcessing(false)
    }
  }, [input, isProcessing, messages, status, effectiveBackend, refreshStatus])

  return {
    // State
    messages,
    input,
    setInput,
    isProcessing,
    aiConfig: null,
    effectiveBackend,
    messagesEndRef,

    // Actions
    sendMessage,
    clearHistory,
    setAIMode,

    // Voice
    voice: {
      isListening,
      transcript,
      startListening,
      stopListening,
      isSupported: isVoiceSupported,
      isSpeaking,
      speak,
      stopSpeaking,
      error: voiceError
    }
  }
}

