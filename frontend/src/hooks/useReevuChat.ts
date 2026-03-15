/**
 * useReevuChat - Shared hook for REEVU AI chat functionality
 *
 * Consolidates all chat logic from legacy and REEVU chat UIs into a single
 * reusable hook. Both the FAB widget and full-page chat use this hook.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { useWorkspaceStore } from '@/store/workspaceStore'
import {
  createUnreachableReevuBackendStatus,
  getEffectiveReevuBackend,
  getReevuProviderDisplayName,
  requestReevuBackendStatusCached,
  requestReevuBackendStatus,
} from '@/lib/reevu-backend-status'
import {
  buildReevuChatStreamRequest,
  readReevuStreamEvents,
} from '@/lib/reevu-chat-stream'
import {
  clearStoredReevuMessages,
  defaultReevuConfig,
  loadStoredReevuConfig,
  loadStoredReevuMessages,
  persistReevuConfig,
  persistReevuMessages,
} from '@/lib/reevu-local-state'
import {
  appendReevuAssistantError,
  createPendingReevuAssistantMessage,
  createReevuSystemMessage,
  createReevuUserMessage,
  finalizeReevuAssistantMessage,
  patchReevuAssistantChunk,
  patchReevuAssistantEvidence,
  patchReevuAssistantProposal,
} from '@/lib/reevu-message-state'
import { useReevuTaskContextStore } from '@/store/reevuTaskContextStore'
import { useReevuVoice } from './useReevuVoice'
import type { EvidenceEnvelope } from '@/components/ai/EvidenceTraceCard'
export type { EffectiveBackend, ReevuBackendStatus } from '@/lib/reevu-backend-status'
import type { ReevuBackendStatus } from '@/lib/reevu-backend-status'
import type { ReevuConfig } from '@/lib/reevu-local-state'

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

// ============================================
// CONSTANTS
// ============================================

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
  const location = useLocation()
  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId)
  const routeTaskContextOverride = useReevuTaskContextStore(
    state => state.routeContexts[location.pathname],
  )

  // Runtime configuration (single path: backend chat stream)
  const [reevuConfig, setReevuConfig] = useState<ReevuConfig>(defaultReevuConfig)
  const [status, setStatus] = useState<ReevuBackendStatus>(createUnreachableReevuBackendStatus(false))

  // Messages
  const [messages, setMessages] = useState<ReevuMessage[]>(() => loadStoredReevuMessages(
    { ...INITIAL_MESSAGE, timestamp: new Date() },
    undefined,
  ))

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

  useEffect(() => {
    setReevuConfig(loadStoredReevuConfig(undefined, error => {
      console.warn('[REEVU] Error loading AI config:', error)
    }))
  }, [])

  const refreshStatus = useCallback(async (force = false) => {
    const token = useAuthStore.getState().token
    const next = force
      ? await requestReevuBackendStatus(fetch, token)
      : await requestReevuBackendStatusCached(fetch, token)
    setStatus(next)
    return next
  }, [])

  // Check backend chat status on mount
  useEffect(() => {
    void refreshStatus()
  }, [refreshStatus])

  const effectiveBackend = getEffectiveReevuBackend(status)

  // Save messages to localStorage
  useEffect(() => {
    try {
      persistReevuMessages(messages)
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
    clearStoredReevuMessages()
  }, [])

  // Update mode (kept for compatibility)
  const setAIMode = useCallback((mode: AIMode) => {
    const nextMode: ReevuConfig['mode'] = mode === 'cloud' ? 'managed' : 'managed'
    const updated = { ...reevuConfig, mode: nextMode }
    setReevuConfig(updated)
    persistReevuConfig(updated)
  }, [reevuConfig])

  // Send message
  const sendMessage = useCallback(async (context?: any) => {
    // Determine the message text to send
    const textToSend = context && typeof context === 'string' ? context : input.trim()

    if (!textToSend || isProcessing) return

    const userMessage: ReevuMessage = createReevuUserMessage({
      id: Date.now().toString(),
      content: textToSend,
    })

    setMessages(prev => [...prev, userMessage])
    setInput('')

    const token = useAuthStore.getState().token
    if (!token) {
      setMessages(prev => [...prev, createReevuSystemMessage({
        id: (Date.now() + 1).toString(),
        content: '⚠️ **Login required**\n\nPlease sign in again. REEVU chat APIs require authentication.',
        model: 'Unauthorized',
      })])
      return
    }

    const latestStatus = await refreshStatus(true)
    if (latestStatus?.authRequired) {
      setMessages(prev => [...prev, createReevuSystemMessage({
        id: (Date.now() + 1).toString(),
        content: '⚠️ **Session expired**\n\nPlease sign in again to continue using REEVU.',
        model: 'Unauthorized',
      })])
      return
    }

    if (!effectiveBackend.ready) {
      setMessages(prev => [...prev, createReevuSystemMessage({
        id: (Date.now() + 1).toString(),
        content: '⚠️ **Managed backend is not AI-ready**\n\nREEVU cannot answer yet because no live provider is available.\n\nFix options:\n1) Add server key (GROQ/GOOGLE/OPENAI/ANTHROPIC) in backend env\n2) Switch to **BYOK** in AI Settings and paste your provider key.',
        model: status.model || 'Not configured',
      })])
      return
    }

    setIsProcessing(true)

    // Add temporary assistant message for streaming
    const assistantMsgId = (Date.now() + 1).toString()
    const providerName = getReevuProviderDisplayName(status.provider, 'Managed backend')
    setMessages(prev => [...prev, createPendingReevuAssistantMessage({
      id: assistantMsgId,
      providerName,
      model: status.model || 'auto',
    })])

    try {
      const requestBody = buildReevuChatStreamRequest({
        message: textToSend,
        messages,
        pathname: location.pathname,
        search: location.search,
        activeWorkspaceId,
        routeTaskContextOverride,
      })

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

      let fullContent = ''
      let actualProvider = providerName
      let actualModel = status.model || 'unknown'

      for await (const event of readReevuStreamEvents(response.body)) {
        if (event.type === 'start') {
          actualProvider = event.provider || providerName
          actualModel = event.model || actualModel
        } else if (event.type === 'chunk') {
          fullContent += event.content
          setMessages(prev => patchReevuAssistantChunk(prev, {
            assistantMessageId: assistantMsgId,
            provider: actualProvider,
            model: actualModel,
            content: fullContent,
          }))
        } else if (event.type === 'proposal_created') {
          setMessages(prev => patchReevuAssistantProposal(prev, {
            assistantMessageId: assistantMsgId,
            provider: actualProvider,
            model: actualModel,
            proposal: event.data,
          }))
        } else if (event.type === 'summary') {
          setMessages(prev => patchReevuAssistantEvidence(prev, {
            assistantMessageId: assistantMsgId,
            provider: actualProvider,
            model: actualModel,
            evidenceEnvelope: event.evidence_envelope as EvidenceEnvelope,
          }))
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Stream error')
        }
      }

      // Final update with complete content
      setMessages(prev => finalizeReevuAssistantMessage(prev, {
        assistantMessageId: assistantMsgId,
        provider: actualProvider,
        model: actualModel,
        content: fullContent,
      }))
    } catch (error) {
      console.error('[REEVU] Chat error:', error)
      setMessages(prev => appendReevuAssistantError(
        prev,
        assistantMsgId,
        error instanceof Error ? error.message : 'Unknown error',
      ))
    } finally {
      setIsProcessing(false)
    }
  }, [input, isProcessing, messages, status, effectiveBackend, refreshStatus, location.pathname, location.search, activeWorkspaceId, routeTaskContextOverride])

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

