/**
 * NanoAI Assistant Component
 * Human-AI Centric Interface (HMI) for Bijmantra
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

interface NanoAIProps {
  className?: string
  defaultOpen?: boolean
  position?: 'bottom-right' | 'bottom-left' | 'sidebar'
}

export function NanoAI({ className, defaultOpen = false, position = 'bottom-right' }: NanoAIProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m NanoAI, your breeding assistant. I can help you analyze data, navigate the platform, or answer questions about your trials. How can I assist you today?',
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
          'fixed z-50 w-14 h-14 rounded-full bg-gradient-to-br from-[#00d4ff] to-[#00ff88] shadow-lg hover:shadow-[0_0_30px_rgba(0,212,255,0.5)] transition-all duration-300 flex items-center justify-center group',
          position === 'bottom-right' && 'bottom-6 right-6',
          position === 'bottom-left' && 'bottom-6 left-6',
          className
        )}
      >
        <span className="text-2xl group-hover:scale-110 transition-transform">🤖</span>
        {/* Pulse indicator */}
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-[#00ff88] rounded-full animate-pulse" />
      </button>
    )
  }

  return (
    <div
      className={cn(
        'fixed z-50 flex flex-col bg-[#0d1117] border border-[#30363d] rounded-xl shadow-2xl overflow-hidden transition-all duration-300',
        position === 'bottom-right' && 'bottom-6 right-6',
        position === 'bottom-left' && 'bottom-6 left-6',
        isMinimized ? 'w-80 h-14' : 'w-96 h-[600px]',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-[#161b22] to-[#0d1117] border-b border-[#30363d]">
        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="text-xl">🤖</span>
            <span className={cn(
              'absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#0d1117]',
              isProcessing ? 'bg-[#ff9500] animate-pulse' : 'bg-[#00ff88]'
            )} />
          </div>
          <div>
            <h3 className="font-mono text-sm font-semibold text-[#e6edf3]">NanoAI</h3>
            <p className="font-mono text-[10px] text-[#6e7681]">
              {isProcessing ? 'Thinking...' : 'Ready to assist'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] rounded transition-colors"
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#21262d] rounded transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSpeak={() => speak(message.content)}
                isSpeaking={isSpeaking}
              />
            ))}
            {isProcessing && (
              <div className="flex items-center gap-2 text-[#6e7681]">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[#00d4ff] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-[#00d4ff] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-[#00d4ff] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="font-mono text-xs">NanoAI is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="px-4 py-2 border-t border-[#21262d]">
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => {
                    setInput(action.action)
                    inputRef.current?.focus()
                  }}
                  className="flex-shrink-0 px-3 py-1.5 text-[10px] font-mono font-medium text-[#00d4ff] bg-[#00d4ff]/10 border border-[#00d4ff]/30 rounded-full hover:bg-[#00d4ff]/20 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#30363d] bg-[#161b22]">
            <div className="flex items-center gap-2">
              {/* Voice Input */}
              <button
                onClick={toggleVoiceInput}
                className={cn(
                  'p-2.5 rounded-lg transition-all duration-200',
                  isListening
                    ? 'bg-[#ff4444] text-white animate-pulse'
                    : 'bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#30363d]'
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
                placeholder="Ask NanoAI anything..."
                className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-4 py-2.5 text-sm text-[#e6edf3] placeholder-[#6e7681] focus:outline-none focus:border-[#00d4ff] font-mono"
              />

              {/* Send Button */}
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isProcessing}
                className={cn(
                  'p-2.5 rounded-lg transition-all duration-200',
                  input.trim() && !isProcessing
                    ? 'bg-[#00d4ff] text-[#0d1117] hover:shadow-[0_0_20px_rgba(0,212,255,0.5)]'
                    : 'bg-[#21262d] text-[#6e7681] cursor-not-allowed'
                )}
              >
                ➤
              </button>
            </div>

            {/* Voice indicator */}
            {isListening && (
              <div className="mt-2 flex items-center gap-2 text-[#ff4444]">
                <span className="w-2 h-2 bg-[#ff4444] rounded-full animate-pulse" />
                <span className="font-mono text-[10px]">Listening...</span>
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
          ? 'bg-[#00d4ff] text-[#0d1117]'
          : 'bg-[#21262d] text-[#e6edf3]'
      )}>
        <p className="text-sm leading-relaxed">{message.content}</p>
        
        {/* Metadata */}
        {message.metadata && (
          <div className="mt-2 pt-2 border-t border-white/10">
            {message.metadata.confidence && (
              <span className="font-mono text-[10px] opacity-70">
                Confidence: {(message.metadata.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-2">
          <span className="font-mono text-[10px] opacity-50">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && (
            <button
              onClick={onSpeak}
              className={cn(
                'p-1 rounded opacity-50 hover:opacity-100 transition-opacity',
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
      content: 'You have 12 active trials across 5 locations. The wheat variety trial at Location A is showing promising results with 15% above-average yield. Would you like me to generate a detailed report?',
      metadata: { confidence: 0.92, action: 'trial_summary' }
    }
  }

  if (lowerInput.includes('yield') || lowerInput.includes('performer')) {
    return {
      content: 'Based on current data, germplasm GRM-2024-0847 shows the highest yield potential at 4.2 t/ha, followed by GRM-2024-0923 at 3.9 t/ha. Both show excellent disease resistance scores.',
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
      content: 'Data quality scan complete. Found 3 potential issues: 2 missing observation values in Trial T-2024-15, and 1 outlier in yield measurements. Would you like me to show details?',
      metadata: { confidence: 0.91, action: 'data_quality' }
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
