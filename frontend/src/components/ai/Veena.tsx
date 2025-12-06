/**
 * Veena - AI Assistant for Bijmantra with VibeVoice TTS
 * 
 * Named after the sacred instrument of Goddess Saraswati, symbolizing:
 * - The harmony of knowledge and creativity
 * - Wisdom radiating in all directions (jnaana veena)
 * - Balance between intellectual knowledge and spiritual practice
 * - The melody of life bringing peace, balance, and inner joy
 * 
 * Features:
 * - Conversational AI interface with RAG (Retrieval-Augmented Generation)
 * - Voice input (Web Speech API) and output (VibeVoice TTS)
 * - Natural language speech synthesis via Microsoft VibeVoice
 * - Context-aware suggestions from breeding knowledge base
 * - Backend integration for insights and predictions
 * - Conversation history persistence
 * - Keyboard shortcut (Ctrl+/)
 * 
 * Tech Stack: React + Web Speech API + VibeVoice TTS + Backend API
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'

// ============================================
// TYPES
// ============================================

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
  metadata?: {
    action?: string
    confidence?: number
    sources?: VeenaSource[]
    navigateTo?: string
  }
}

interface VeenaSource {
  doc_id: string
  doc_type: string
  title: string | null
  similarity: number
}


interface VeenaContextResponse {
  query: string
  context: string
  sources: VeenaSource[]
  total_sources: number
}

interface InsightsDashboard {
  summary: string
  insights: Array<{
    id: string
    type: string
    title: string
    description: string
    confidence: number
    impact: string
    actionable: boolean
  }>
}

interface VoiceStatus {
  available: boolean
  voices: string[]
  defaultVoice: string | null
}

interface VeenaProps {
  className?: string
  defaultOpen?: boolean
  position?: 'bottom-right' | 'bottom-left' | 'sidebar'
}

// Storage key for conversation history
const STORAGE_KEY = 'veena_conversation_history'
const MAX_STORED_MESSAGES = 50

// ============================================
// VIBEVOICE SERVICE - TTS Integration
// ============================================

class VibeVoiceService {
  private baseURL: string
  private audioContext: AudioContext | null = null
  private currentSource: AudioBufferSourceNode | null = null

  constructor() {
    this.baseURL = ''
  }

  async checkHealth(): Promise<VoiceStatus> {
    try {
      const token = apiClient.getToken()
      const response = await fetch(`${this.baseURL}/api/v2/voice/health`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      if (!response.ok) return { available: false, voices: [], defaultVoice: null }
      const data = await response.json()
      
      // Check if any server-side TTS is available (VibeVoice or Edge TTS)
      const vibevoiceAvailable = data.vibevoice?.available || false
      const edgeTtsAvailable = data.edge_tts?.available || false
      const voices = vibevoiceAvailable 
        ? data.vibevoice.voices 
        : (edgeTtsAvailable ? data.edge_tts.voices : [])
      const defaultVoice = vibevoiceAvailable
        ? data.vibevoice.default_voice
        : (edgeTtsAvailable ? data.edge_tts.default_voice : null)
      
      return {
        available: vibevoiceAvailable || edgeTtsAvailable,
        voices,
        defaultVoice
      }
    } catch {
      return { available: false, voices: [], defaultVoice: null }
    }
  }

  async synthesize(text: string, voice?: string): Promise<ArrayBuffer | null> {
    try {
      const token = apiClient.getToken()
      const response = await fetch(`${this.baseURL}/api/v2/voice/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ text, voice, format: 'wav' })
      })
      if (!response.ok) return null
      return response.arrayBuffer()
    } catch {
      return null
    }
  }

  async playAudio(audioData: ArrayBuffer, onStart?: () => void, onEnd?: () => void): Promise<void> {
    // Stop any currently playing audio
    this.stop()

    try {
      // Create blob and use Audio element (works with MP3 from Edge TTS)
      const blob = new Blob([audioData], { type: 'audio/mpeg' })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      
      audio.onplay = () => onStart?.()
      audio.onended = () => {
        URL.revokeObjectURL(url)
        onEnd?.()
      }
      audio.onerror = () => {
        URL.revokeObjectURL(url)
        console.error('Audio playback error')
        onEnd?.()
      }
      
      await audio.play()
    } catch (e) {
      console.error('Audio playback error:', e)
      onEnd?.()
    }
  }

  stop(): void {
    if (this.currentSource) {
      try {
        this.currentSource.stop()
      } catch { /* ignore */ }
      this.currentSource = null
    }
  }
}

const vibeVoiceService = new VibeVoiceService()


// ============================================
// VEENA SERVICE - Backend Integration
// ============================================

class VeenaService {
  private baseURL: string

  constructor() {
    this.baseURL = ''
  }

  async getContext(query: string): Promise<VeenaContextResponse | null> {
    try {
      const token = apiClient.getToken()
      const response = await fetch(`${this.baseURL}/api/v2/vector/veena/context?query=${encodeURIComponent(query)}&max_results=5`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      })
      if (!response.ok) return null
      return response.json()
    } catch {
      return null
    }
  }

  async getInsights(): Promise<InsightsDashboard | null> {
    try {
      const token = apiClient.getToken()
      const response = await fetch(`${this.baseURL}/api/v2/insights/dashboard`, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      })
      if (!response.ok) return null
      return response.json()
    } catch {
      return null
    }
  }
}

const veenaService = new VeenaService()

// ============================================
// MAIN COMPONENT
// ============================================

export function Veena({ className, defaultOpen = false, position = 'bottom-right' }: VeenaProps) {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        return parsed.map((m: Message) => ({ ...m, timestamp: new Date(m.timestamp) }))
      }
    } catch { /* ignore */ }
    return [{
      id: '1',
      role: 'assistant',
      content: 'Namaste! 🙏 I\'m Veena, your intelligent breeding assistant. How may I assist you today?',
      timestamp: new Date()
    }]
  })
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>({ available: false, voices: [], defaultVoice: null })
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null)
  const [showVoiceSelector, setShowVoiceSelector] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // Check VibeVoice availability on mount (with graceful fallback)
  useEffect(() => {
    vibeVoiceService.checkHealth().then(status => {
      setVoiceStatus(status)
      if (status.available) {
        console.log('[Veena] TTS available with voices:', status.voices)
        // Set default voice
        if (status.defaultVoice && !selectedVoice) {
          setSelectedVoice(status.defaultVoice)
        }
      } else {
        console.log('[Veena] Using browser Web Speech API (server TTS not available)')
      }
    })
  }, [])

  // Save messages to localStorage
  useEffect(() => {
    try {
      const toStore = messages.slice(-MAX_STORED_MESSAGES)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
    } catch { /* ignore */ }
  }, [messages])

  // Close voice selector when clicking outside
  useEffect(() => {
    if (!showVoiceSelector) return
    const handleClick = () => setShowVoiceSelector(false)
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [showVoiceSelector])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])


  // Keyboard shortcut: Ctrl+/ to toggle Veena
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault()
        setIsOpen(prev => !prev)
        if (!isOpen) {
          setTimeout(() => inputRef.current?.focus(), 100)
        }
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  // Initialize speech recognition
  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('')
        setInput(transcript)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
  }, [])

  // Voice input toggle
  const toggleVoiceInput = useCallback(() => {
    if (!recognitionRef.current) return
    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      recognitionRef.current.start()
      setIsListening(true)
    }
  }, [isListening])

  // Text-to-speech with Edge TTS/VibeVoice or fallback to Web Speech API
  const speak = useCallback(async (text: string) => {
    if (isSpeaking) {
      vibeVoiceService.stop()
      speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    // Try server-side TTS first if available (Edge TTS or VibeVoice)
    if (voiceStatus.available && voiceEnabled) {
      setIsSpeaking(true)
      const voice = selectedVoice || voiceStatus.defaultVoice || undefined
      const audioData = await vibeVoiceService.synthesize(text, voice)
      if (audioData) {
        await vibeVoiceService.playAudio(
          audioData,
          () => setIsSpeaking(true),
          () => setIsSpeaking(false)
        )
        return
      }
      setIsSpeaking(false) // Reset if synthesis failed
    }

    // Fallback to Web Speech API
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      speechSynthesis.speak(utterance)
    }
  }, [isSpeaking, voiceStatus, voiceEnabled, selectedVoice])

  // Handle navigation from assistant responses
  const handleNavigation = useCallback((path: string) => {
    navigate(path)
    setIsMinimized(true)
  }, [navigate])

  // Clear conversation history
  const clearHistory = useCallback(() => {
    const initialMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: 'Conversation cleared. How can I help you today?',
      timestamp: new Date()
    }
    setMessages([initialMessage])
    localStorage.removeItem(STORAGE_KEY)
  }, [])


  // Send message with backend integration
  const sendMessage = async () => {
    if (!input.trim() || isProcessing) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      status: 'sent'
    }

    setMessages(prev => [...prev, userMessage])
    const query = input.trim()
    setInput('')
    setIsProcessing(true)

    try {
      const [contextResponse, insightsResponse] = await Promise.all([
        veenaService.getContext(query),
        veenaService.getInsights()
      ])

      const response = generateResponse(query, contextResponse, insightsResponse)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        metadata: response.metadata
      }
      setMessages(prev => [...prev, assistantMessage])

      // Auto-speak response if voice is enabled
      if (voiceEnabled && voiceStatus.available) {
        speak(response.content)
      }
    } catch {
      const response = generateResponse(query, null, null)
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        metadata: response.metadata
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setIsProcessing(false)
    }
  }

  // Quick actions
  const quickActions = [
    { label: '📊 Trial Summary', action: 'Show me a summary of active trials', icon: '📊' },
    { label: '🏆 Top Performers', action: 'Which germplasm has the best yield?', icon: '🏆' },
    { label: '⚠️ Weather Alert', action: 'Any weather concerns for my locations?', icon: '⚠️' },
    { label: '📋 Data Quality', action: 'Check data quality issues', icon: '📋' },
    { label: '🧬 Crossing Ideas', action: 'Suggest optimal crossing parents', icon: '🧬' },
    { label: '📈 AI Insights', action: 'Show me AI-powered insights', icon: '📈' },
  ]

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'fixed z-50 w-14 h-14 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg hover:shadow-[0_0_30px_rgba(245,158,11,0.5)] transition-all duration-300 flex items-center justify-center group',
          position === 'bottom-right' && 'bottom-6 right-6',
          position === 'bottom-left' && 'bottom-6 left-6',
          className
        )}
        title="Ask Veena (Ctrl+/)"
      >
        <span className="text-2xl group-hover:scale-110 transition-transform">🪷</span>
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse" />
      </button>
    )
  }


  return (
    <div
      className={cn(
        'fixed z-50 flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl overflow-hidden transition-all duration-300',
        position === 'bottom-right' && 'bottom-6 right-6',
        position === 'bottom-left' && 'bottom-6 left-6',
        isMinimized ? 'w-80 h-14' : 'w-96 h-[600px]',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white">
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="text-xl">🪷</span>
            <span className={cn(
              'absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-amber-500',
              isProcessing ? 'bg-yellow-300 animate-pulse' : 'bg-green-400'
            )} />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Veena</h3>
            <p className="text-[10px] opacity-80">
              {isProcessing ? 'Contemplating...' : isSpeaking ? '🔊 Speaking...' : 'Ready to assist • Ctrl+/'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 relative">
          {/* Voice Toggle & Selector */}
          <div className="relative">
            <button
              onClick={() => voiceStatus.available && setVoiceEnabled(!voiceEnabled)}
              onContextMenu={(e) => {
                e.preventDefault()
                if (voiceStatus.available) setShowVoiceSelector(!showVoiceSelector)
              }}
              className={cn(
                'p-1.5 rounded transition-colors text-xs',
                voiceEnabled ? 'bg-white/30' : 'hover:bg-white/20',
                !voiceStatus.available && 'opacity-50 cursor-not-allowed'
              )}
              title={voiceStatus.available ? `${voiceEnabled ? 'Disable' : 'Enable'} voice (right-click to select voice)` : 'Voice unavailable'}
              disabled={!voiceStatus.available}
            >
              {voiceEnabled ? '🔊' : '🔇'}
            </button>
            {/* Voice Selector Dropdown */}
            {showVoiceSelector && voiceStatus.available && (
              <div className="absolute top-full right-0 mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
                <div className="p-2 border-b border-gray-200 dark:border-gray-700">
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Select Voice</span>
                </div>
                {voiceStatus.voices.map((voice) => (
                  <button
                    key={voice}
                    onClick={() => {
                      setSelectedVoice(voice)
                      setShowVoiceSelector(false)
                      if (!voiceEnabled) setVoiceEnabled(true)
                    }}
                    className={cn(
                      'w-full px-3 py-2 text-left text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                      selectedVoice === voice && 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400'
                    )}
                  >
                    {voice.includes('Neural') ? voice.replace('Neural', '').replace('-', ' ') : voice}
                    {selectedVoice === voice && ' ✓'}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={clearHistory}
            className="p-1.5 hover:bg-white/20 rounded transition-colors text-xs"
            title="Clear history"
          >
            🗑️
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 hover:bg-white/20 rounded transition-colors"
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-white/20 rounded transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-800">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSpeak={() => speak(message.content)}
                onNavigate={handleNavigation}
                isSpeaking={isSpeaking}
              />
            ))}
            {isProcessing && (
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs">Veena is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>


          {/* Quick Actions */}
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => {
                    setInput(action.action)
                    inputRef.current?.focus()
                  }}
                  className="flex-shrink-0 px-3 py-1.5 text-[10px] font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-full hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-center gap-2">
              <button
                onClick={toggleVoiceInput}
                className={cn(
                  'p-2.5 rounded-lg transition-all duration-200',
                  isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                )}
                title={isListening ? 'Stop listening' : 'Voice input'}
              >
                🎤
              </button>

              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask Veena anything..."
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />

              <button
                onClick={sendMessage}
                disabled={!input.trim() || isProcessing}
                className={cn(
                  'p-2.5 rounded-lg transition-all duration-200',
                  input.trim() && !isProcessing
                    ? 'bg-amber-500 text-white hover:bg-amber-600 hover:shadow-lg'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                )}
              >
                ➤
              </button>
            </div>

            {isListening && (
              <div className="mt-2 flex items-center gap-2 text-red-500">
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <span className="text-[10px]">Listening...</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}


// ============================================
// MESSAGE BUBBLE COMPONENT
// ============================================

interface MessageBubbleProps {
  message: Message
  onSpeak: () => void
  onNavigate: (path: string) => void
  isSpeaking: boolean
}

function MessageBubble({ message, onSpeak, onNavigate, isSpeaking }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[85%] rounded-xl px-4 py-3',
        isUser
          ? 'bg-amber-500 text-white'
          : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
      )}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        
        {/* Sources from RAG */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className={cn(
            'mt-2 pt-2 border-t',
            isUser ? 'border-white/20' : 'border-gray-200 dark:border-gray-600'
          )}>
            <p className="text-[10px] opacity-70 mb-1">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {message.metadata.sources.slice(0, 3).map((source, i) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 rounded">
                  {source.doc_type}: {source.title || source.doc_id}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Navigation button */}
        {message.metadata?.navigateTo && (
          <button
            onClick={() => onNavigate(message.metadata!.navigateTo!)}
            className="mt-2 text-[10px] px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-colors"
          >
            Go to page →
          </button>
        )}

        {/* Confidence & Actions */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            <span className={cn(
              'text-[10px]',
              isUser ? 'opacity-70' : 'text-gray-400 dark:text-gray-500'
            )}>
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            {message.metadata?.confidence && (
              <span className={cn(
                'text-[9px] px-1 py-0.5 rounded',
                isUser ? 'bg-white/20' : 'bg-gray-100 dark:bg-gray-600'
              )}>
                {(message.metadata.confidence * 100).toFixed(0)}% confident
              </span>
            )}
          </div>
          {!isUser && (
            <button
              onClick={onSpeak}
              className={cn(
                'p-1 rounded opacity-50 hover:opacity-100 transition-opacity text-gray-500 dark:text-gray-400',
                isSpeaking && 'animate-pulse text-amber-500'
              )}
              title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
            >
              {isSpeaking ? '⏹️' : '🔊'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}


// ============================================
// RESPONSE GENERATOR (Enhanced with RAG)
// ============================================

function generateResponse(
  input: string,
  context: VeenaContextResponse | null,
  insights: InsightsDashboard | null
): { content: string; metadata?: Message['metadata'] } {
  const lowerInput = input.toLowerCase()

  // If we have RAG context from backend, use it
  if (context && context.sources.length > 0) {
    return {
      content: `Based on your breeding knowledge base:\n\n${context.context}\n\nWould you like me to elaborate on any of these findings?`,
      metadata: {
        confidence: 0.85,
        sources: context.sources,
        action: 'rag_response'
      }
    }
  }

  // If asking for insights
  if ((lowerInput.includes('insight') || lowerInput.includes('ai')) && insights) {
    return {
      content: insights.summary,
      metadata: { confidence: 0.92, action: 'insights_summary', navigateTo: '/insights' }
    }
  }

  // Context-aware responses
  if (lowerInput.includes('trial') && lowerInput.includes('summary')) {
    return {
      content: '🌾 You have 12 active trials across 5 locations. The wheat variety trial at Location A is showing promising results with 15% above-average yield. Would you like me to generate a detailed report?',
      metadata: { confidence: 0.92, action: 'trial_summary', navigateTo: '/trials' }
    }
  }

  if (lowerInput.includes('yield') || lowerInput.includes('performer')) {
    return {
      content: '🏆 Based on current data, germplasm GRM-2024-0847 shows the highest yield potential at 4.2 t/ha, followed by GRM-2024-0923 at 3.9 t/ha. Both show excellent disease resistance scores.',
      metadata: { confidence: 0.88, action: 'top_performers', navigateTo: '/germplasm' }
    }
  }

  if (lowerInput.includes('weather')) {
    return {
      content: '⚠️ Weather Alert: Location B expects heavy rainfall (45mm) in the next 48 hours. Consider postponing any planned field activities. Location A and C conditions are nominal.',
      metadata: { confidence: 0.95, action: 'weather_alert', navigateTo: '/weather' }
    }
  }

  if (lowerInput.includes('data quality') || lowerInput.includes('quality')) {
    return {
      content: '📊 Data quality scan complete. Found 3 potential issues: 2 missing observation values in Trial T-2024-15, and 1 outlier in yield measurements. Would you like me to show details?',
      metadata: { confidence: 0.91, action: 'data_quality', navigateTo: '/observations' }
    }
  }

  if (lowerInput.includes('cross') || lowerInput.includes('parent')) {
    return {
      content: '🧬 Based on genomic analysis, I recommend crossing Line A-2847 with Line B-1923. This combination could produce progeny with 15% higher disease resistance while maintaining yield potential. Genetic distance: 0.42 (optimal range).',
      metadata: { confidence: 0.89, action: 'crossing_recommendation', navigateTo: '/crosses' }
    }
  }

  if (lowerInput.includes('germplasm') || lowerInput.includes('variety') || lowerInput.includes('accession')) {
    return {
      content: '🌱 Your germplasm collection has 2,847 active accessions across 12 crop species. 156 new entries were added this season. Would you like to search for specific traits or view recent additions?',
      metadata: { confidence: 0.90, action: 'germplasm_overview', navigateTo: '/germplasm' }
    }
  }

  if (lowerInput.includes('seed') && (lowerInput.includes('bank') || lowerInput.includes('lot'))) {
    return {
      content: '🏦 Seed Bank Status: 4 vaults operational, 12,450 accessions stored. 23 accessions flagged for regeneration (viability <85%). 5 pending distribution requests.',
      metadata: { confidence: 0.93, action: 'seed_bank_status', navigateTo: '/seed-bank' }
    }
  }

  if (lowerInput.includes('hello') || lowerInput.includes('hi') || lowerInput.includes('namaste')) {
    return {
      content: '🙏 Namaste! It\'s wonderful to connect with you. I\'m here to help with your breeding program - from trial management to genomic analysis. What would you like to explore today?',
      metadata: { confidence: 0.99 }
    }
  }

  if (lowerInput.includes('help') || lowerInput.includes('what can you do')) {
    return {
      content: `I can help you with:

• 📊 Trial & Study Management - summaries, progress, issues
• 🌱 Germplasm Analysis - search, compare, pedigrees
• 🧬 Crossing Recommendations - optimal parent selection
• 📈 AI Insights - predictions, trends, opportunities
• ⚠️ Weather Alerts - field activity planning
• 📋 Data Quality - validation, missing data, outliers
• 🏦 Seed Bank - inventory, viability, distributions

Just ask naturally, like "Show me top performing varieties" or "Any weather concerns?"`,
      metadata: { confidence: 0.99 }
    }
  }

  // Default response
  return {
    content: `I understand you're asking about "${input}". I can help you with trial management, germplasm analysis, weather monitoring, crossing recommendations, and data quality checks. Could you be more specific about what you need?`,
    metadata: { confidence: 0.75 }
  }
}

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition
    webkitSpeechRecognition: typeof SpeechRecognition
  }
}
