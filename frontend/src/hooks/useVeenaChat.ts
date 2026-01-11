/**
 * useVeenaChat - Shared hook for Veena AI chat functionality
 * 
 * Consolidates all chat logic from Veena.tsx and VeenaChat.tsx into a single
 * reusable hook. Both the FAB widget and full-page chat use this hook.
 * 
 * UPDATED: Includes Voice (Web Speech API), Streaming (SSE), and Context support.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient } from '@/lib/api-client'
import { useVeenaVoice } from './useVeenaVoice'

// ============================================
// TYPES
// ============================================

export interface VeenaMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    sources?: VeenaSource[]
    provider?: string
    model?: string
  }
}

export interface VeenaSource {
  doc_id: string
  doc_type: string
  title: string | null
  similarity: number
}

export type AIMode = 'cloud'

export interface AIConfig {
  mode: AIMode
  cloud: { provider: string; apiKey: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' }
}

export interface EffectiveBackend {
  mode: 'cloud' | 'none'
  name: string
  ready: boolean
}

// ============================================
// CONSTANTS
// ============================================

const STORAGE_KEY = 'veena_conversation_history'
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2'
const MAX_STORED_MESSAGES = 100

const PROVIDER_NAMES: Record<string, string> = {
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq'
}

const INITIAL_MESSAGE: VeenaMessage = {
  id: '1',
  role: 'assistant',
  content: 'Hello! 🙏 Welcome to our conversation about plant breeding and agricultural research. I\'m Veena.',
  timestamp: new Date()
}

// ============================================
// HOOK
// ============================================

export function useVeenaChat() {
  // AI Configuration
  const [aiConfig, setAiConfig] = useState<AIConfig | null>(null)
  
  // Messages
  const [messages, setMessages] = useState<VeenaMessage[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        return parsed.map((m: VeenaMessage) => ({ ...m, timestamp: new Date(m.timestamp) }))
      }
    } catch { /* ignore */ }
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
  } = useVeenaVoice({
    onTranscript: (text) => setInput(text)
  })

  // Load AI config on mount with migration from old format
  useEffect(() => {
    try {
      const saved = localStorage.getItem(AI_CONFIG_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        // Validate the config has the expected structure
        if (parsed && parsed.cloud && typeof parsed.cloud === 'object') {
          // Ensure cloud object has required fields
          const validConfig: AIConfig = {
            mode: 'cloud',
            cloud: {
              provider: parsed.cloud.provider || 'google',
              apiKey: parsed.cloud.apiKey || '',
              model: parsed.cloud.model || 'gemini-2.5-flash',
              tested: parsed.cloud.tested || false,
              lastTestResult: parsed.cloud.lastTestResult
            }
          }
          setAiConfig(validConfig)
        } else {
          // Old or malformed config - reset to default
          console.warn('[Veena] Invalid AI config in localStorage, resetting')
          localStorage.removeItem(AI_CONFIG_KEY)
        }
      }
    } catch (e) {
      console.warn('[Veena] Error loading AI config:', e)
      localStorage.removeItem(AI_CONFIG_KEY)
    }
  }, [])

  // Determine effective AI backend (cloud-only)
  const getEffectiveBackend = useCallback((): EffectiveBackend => {
    // VEENA OMEGA OVERRIDE: Always "ready" when using local orchestrator
    return { 
      mode: 'cloud', 
      name: 'VEENA Omega (Orchestrator)', 
      ready: true 
    };

    /*
    if (!aiConfig || !aiConfig.cloud) {
      return { mode: 'none', name: 'Not configured', ready: false }
    }

    // Check if we have a valid API key and successful test
    const hasApiKey = aiConfig.cloud.apiKey && aiConfig.cloud.apiKey.trim().length > 0
    const isTestSuccess = aiConfig.cloud.lastTestResult === 'success'

    if (hasApiKey && isTestSuccess) {
      const providerName = PROVIDER_NAMES[aiConfig.cloud.provider] || aiConfig.cloud.provider
      return { 
        mode: 'cloud', 
        name: `${providerName} • ${aiConfig.cloud.model}`, 
        ready: true 
      }
    }
    
    if (hasApiKey) {
      const providerName = PROVIDER_NAMES[aiConfig.cloud.provider] || aiConfig.cloud.provider
      return { mode: 'cloud', name: `${providerName} (not tested)`, ready: false }
    }
    
    return { mode: 'none', name: 'No API key configured', ready: false }
    */
  }, [aiConfig])

  const effectiveBackend = getEffectiveBackend()

  // Save messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)))
    } catch { /* ignore */ }
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
  }, [])

  // Update AI mode
  const setAIMode = useCallback((mode: AIMode) => {
    if (aiConfig) {
      const newConfig = { ...aiConfig, mode }
      setAiConfig(newConfig)
      localStorage.setItem(AI_CONFIG_KEY, JSON.stringify(newConfig))
    }
  }, [aiConfig])

  // Send message
  const sendMessage = useCallback(async (context?: any) => {
    // Determine the message text to send
    const textToSend = context && typeof context === 'string' ? context : input.trim()
    
    if (!textToSend || isProcessing) return

    // Check if AI is properly configured
    const hasValidConfig = aiConfig?.cloud?.apiKey && aiConfig.cloud.apiKey.trim().length > 0
    
    const userMessage: VeenaMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('') // Clear input immediately
    
    // If not configured, show helpful message instead of calling backend
    /* 
    // ORCHESTRATOR BYPASS: We assume local orchestrator is running for now.
    if (!hasValidConfig) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '⚠️ **AI not configured**\n\nTo chat with me, please configure an AI provider first:\n\n1. Go to **Settings → AI Assistant Setup**\n2. Choose a provider (Google Gemini has a free tier)\n3. Enter your API key and test the connection\n\nOnce configured, I\'ll be ready to help with your plant breeding questions!',
        timestamp: new Date(),
        metadata: {
          provider: 'System',
          model: 'Not configured'
        }
      }])
      return
    }
    */
    
    setIsProcessing(true)

    // Add temporary assistant message for streaming
    const assistantMsgId = (Date.now() + 1).toString()
    const providerName = PROVIDER_NAMES[aiConfig.cloud.provider] || aiConfig.cloud.provider
    setMessages(prev => [...prev, {
      id: assistantMsgId,
      role: 'assistant',
      content: '', // Empty initially
      timestamp: new Date(),
      metadata: {
        provider: `Connecting to ${providerName}...`,
        model: aiConfig.cloud.model
      }
    }])

    try {
      // Prepare Conversation History (limited to last 10 messages)
      const conversationHistory = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content
      })) // Removed timestamp to match backend expectation if needed

      // Prepare Request Body
      const requestBody: Record<string, unknown> = {
        message: textToSend,
        conversation_history: conversationHistory,
        include_context: true,
        context_limit: 5,
        // client_context: context // context is unused in backend for now or passed differently
      }
      
      // Set provider and credentials (cloud-only)
      // At this point we've already validated hasValidConfig above
      requestBody.preferred_provider = aiConfig.cloud.provider
      requestBody.user_api_key = aiConfig.cloud.apiKey
      if (aiConfig.cloud.model) {
        requestBody.user_model = aiConfig.cloud.model
      }

      // Fetch stream
      // --- VEENA OMEGA ORCHESTRATOR CONNECTION ---
      // Direct connection to the Python Orchestrator on Port 8080
      const apiUrl = 'http://localhost:8080'; // VEENA Omega Port
      
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: textToSend })
      });

      if (!response.ok || !response.body) {
        throw new Error('Network response was not ok')
      }

      if (!response.ok) {
        throw new Error(`Orchestrator error: ${response.statusText}`);
      }

      const data = await response.json();
      const finalResponse = data.response || "No response received.";
      const activeAgent = data.agent_used || "VEENA";

      // Update message with final response
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMsgId 
            ? { 
                ...msg, 
                content: finalResponse,
                metadata: {
                  provider: 'VEENA Omega',
                  model: `Agent: ${activeAgent}`
                }
              }
            : msg
      ));

    } catch (error) {
      console.error('[Veena] Chat error:', error)
      setMessages(prev => prev.map(m => 
        m.id === assistantMsgId 
          ? { ...m, content: m.content + `\n\n[System Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your connection.]` }
          : m
      ))
    } finally {
      setIsProcessing(false)
    }
  }, [input, isProcessing, messages, aiConfig])

  return {
    // State
    messages,
    input,
    setInput,
    isProcessing,
    aiConfig,
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
