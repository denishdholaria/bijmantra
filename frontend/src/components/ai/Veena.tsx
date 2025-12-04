/**
 * Veena - AI Assistant for Bijmantra
 * 
 * Named after the sacred instrument of Goddess Saraswati, symbolizing:
 * - The harmony of knowledge and creativity
 * - Wisdom radiating in all directions (jnaana veena)
 * - Balance between intellectual knowledge and spiritual practice
 * - The melody of life bringing peace, balance, and inner joy
 * 
 * Features:
 * - Conversational AI interface
 * - Voice input/output support
 * - Context-aware suggestions
 * - Agentic capabilities (future)
 * 
 * Tech Stack: React + Web Speech API + WebSocket
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  status?: 'sending' | 'sent' | 'error'
  metadata?: {
    action?: string
    confidence?: number
    sources?: string[]
  }
}

interface VeenaProps {
  className?: string
  defaultOpen?: boolean
  position?: 'bottom-right' | 'bottom-left' | 'sidebar'
}

export function Veena({ className, defaultOpen = false, position = 'bottom-right' }: VeenaProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello, I\'m Veena, your intelligent breeding assistant. How may I assist you today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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

  // Text-to-speech
  const speak = useCallback((text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      speechSynthesis.speak(utterance)
    }
  }, [])

  // Send message
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
    setInput('')
    setIsProcessing(true)

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const response = generateResponse(userMessage.content)
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        metadata: response.metadata
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsProcessing(false)
    }, 1000)
  }

  // Quick actions
  const quickActions = [
    { label: 'Trial Summary', action: 'Show me a summary of active trials' },
    { label: 'Top Performers', action: 'Which germplasm has the best yield?' },
    { label: 'Weather Alert', action: 'Any weather concerns for my locations?' },
    { label: 'Data Quality', action: 'Check data quality issues' }
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
        title="Ask Veena"
      >
        <span className="text-2xl group-hover:scale-110 transition-transform">🪷</span>
        {/* Pulse indicator */}
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
              {isProcessing ? 'Contemplating...' : 'Ready to assist'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
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
              {/* Voice Input */}
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

              {/* Text Input */}
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask Veena anything..."
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />

              {/* Send Button */}
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

            {/* Voice indicator */}
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

/* ============================================
   MESSAGE BUBBLE COMPONENT
   ============================================ */
interface MessageBubbleProps {
  message: Message
  onSpeak: () => void
  isSpeaking: boolean
}

function MessageBubble({ message, onSpeak, isSpeaking }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[85%] rounded-xl px-4 py-3',
        isUser
          ? 'bg-amber-500 text-white'
          : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
      )}>
        <p className="text-sm leading-relaxed">{message.content}</p>
        
        {/* Metadata */}
        {message.metadata && (
          <div className={cn(
            'mt-2 pt-2 border-t',
            isUser ? 'border-white/20' : 'border-gray-200 dark:border-gray-600'
          )}>
            {message.metadata.confidence && (
              <span className="text-[10px] opacity-70">
                Confidence: {(message.metadata.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-2">
          <span className={cn(
            'text-[10px]',
            isUser ? 'opacity-70' : 'text-gray-400 dark:text-gray-500'
          )}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && (
            <button
              onClick={onSpeak}
              className={cn(
                'p-1 rounded opacity-50 hover:opacity-100 transition-opacity text-gray-500 dark:text-gray-400',
                isSpeaking && 'animate-pulse'
              )}
              title="Read aloud"
            >
              🔊
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* ============================================
   RESPONSE GENERATOR (Placeholder)
   ============================================ */
function generateResponse(input: string): { content: string; metadata?: Message['metadata'] } {
  const lowerInput = input.toLowerCase()

  // Context-aware responses
  if (lowerInput.includes('trial') && lowerInput.includes('summary')) {
    return {
      content: '🌾 You have 12 active trials across 5 locations. The wheat variety trial at Location A is showing promising results with 15% above-average yield. Would you like me to generate a detailed report?',
      metadata: { confidence: 0.92, action: 'trial_summary' }
    }
  }

  if (lowerInput.includes('yield') || lowerInput.includes('performer')) {
    return {
      content: '🏆 Based on current data, germplasm GRM-2024-0847 shows the highest yield potential at 4.2 t/ha, followed by GRM-2024-0923 at 3.9 t/ha. Both show excellent disease resistance scores.',
      metadata: { confidence: 0.88, action: 'top_performers' }
    }
  }

  if (lowerInput.includes('weather')) {
    return {
      content: '⚠️ Weather Alert: Location B expects heavy rainfall (45mm) in the next 48 hours. Consider postponing any planned field activities. Location A and C conditions are nominal.',
      metadata: { confidence: 0.95, action: 'weather_alert' }
    }
  }

  if (lowerInput.includes('data quality') || lowerInput.includes('quality')) {
    return {
      content: '📊 Data quality scan complete. Found 3 potential issues: 2 missing observation values in Trial T-2024-15, and 1 outlier in yield measurements. Would you like me to show details?',
      metadata: { confidence: 0.91, action: 'data_quality' }
    }
  }

  if (lowerInput.includes('hello') || lowerInput.includes('hi') || lowerInput.includes('namaste')) {
    return {
      content: '🙏 Namaste! It\'s wonderful to connect with you. I\'m here to help with your breeding program - from trial management to genomic analysis. What would you like to explore today?',
      metadata: { confidence: 0.99 }
    }
  }

  // Default response
  return {
    content: 'I understand you\'re asking about "' + input + '". I can help you with trial management, germplasm analysis, weather monitoring, and data quality checks. Could you be more specific about what you need?',
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
