/**
 * Veena (वीणा) - AI Assistant for Bijmantra
 * 
 * Named after the sacred instrument of Goddess Saraswati, symbolizing:
 * - The harmony of knowledge and creativity
 * - Wisdom radiating in all directions (jnaana veena)
 * 
 * REDESIGNED (Dec 31, 2025):
 * - Three AI modes: Auto, Local (Ollama), Cloud (API Key)
 * - Settings gear to switch AI backend
 * - Clear history button always visible
 * - Shows ACTUAL configured backend, not server default
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
  metadata?: {
    sources?: VeenaSource[]
    provider?: string
    model?: string
  }
}

interface VeenaSource {
  doc_id: string
  doc_type: string
  title: string | null
  similarity: number
}

interface VeenaProps {
  className?: string
  defaultOpen?: boolean
}

type AIMode = 'auto' | 'local' | 'cloud'

interface AIConfig {
  mode: AIMode
  local: { host: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' }
  cloud: { provider: string; apiKey: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' }
}

// Storage keys
const STORAGE_KEY = 'veena_conversation_history'
const POSITION_STORAGE_KEY = 'veena_position'
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2'
const MAX_STORED_MESSAGES = 50

// Provider display names
const PROVIDER_NAMES: Record<string, string> = {
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq',
  ollama: 'Ollama'
}

// Default positions
const getDefaultPosition = () => {
  if (typeof window === 'undefined') return { x: 100, y: 100 }
  return {
    x: Math.max(60, window.innerWidth - 80),
    y: Math.max(60, window.innerHeight - 80)
  }
}

const validatePosition = (pos: { x: number; y: number } | null) => {
  if (!pos || typeof window === 'undefined') return null
  const { x, y } = pos
  if (x < 20 || x > window.innerWidth - 20 || y < 20 || y > window.innerHeight - 20) {
    return null
  }
  return pos
}

// ============================================
// MAIN COMPONENT
// ============================================

export function Veena({ className, defaultOpen = false }: VeenaProps) {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [isMinimized, setIsMinimized] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  
  // AI Configuration
  const [aiConfig, setAiConfig] = useState<AIConfig | null>(null)
  const [serverOllamaAvailable, setServerOllamaAvailable] = useState(false)
  
  // Messages
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
  const [isProcessing, setIsProcessing] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Draggable position
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(() => {
    try {
      const stored = localStorage.getItem(POSITION_STORAGE_KEY)
      if (stored) return validatePosition(JSON.parse(stored))
    } catch { /* ignore */ }
    return null
  })
  const [isDragging, setIsDragging] = useState(false)
  const dragRef = useRef<{ startX: number; startY: number; startPosX: number; startPosY: number } | null>(null)

  // Load AI config on mount
  useEffect(() => {
    // Load user's AI config
    try {
      const saved = localStorage.getItem(AI_CONFIG_KEY)
      if (saved) {
        setAiConfig(JSON.parse(saved))
      }
    } catch { /* ignore */ }

    // Check server's Ollama status
    const checkServer = async () => {
      try {
        const token = apiClient.getToken()
        const response = await fetch('/api/v2/chat/status', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        })
        if (response.ok) {
          const data = await response.json()
          setServerOllamaAvailable(data.providers?.ollama?.available || false)
        }
      } catch { /* ignore */ }
    }
    checkServer()
  }, [])

  // Determine effective AI backend
  const getEffectiveBackend = useCallback(() => {
    if (!aiConfig) {
      // No config - check server
      if (serverOllamaAvailable) {
        return { mode: 'auto', name: 'Ollama (Server)', ready: true }
      }
      return { mode: 'none', name: 'Not configured', ready: false }
    }

    if (aiConfig.mode === 'local') {
      if (aiConfig.local.lastTestResult === 'success') {
        return { mode: 'local', name: `Ollama • ${aiConfig.local.model}`, ready: true }
      }
      return { mode: 'local', name: 'Ollama (not tested)', ready: false }
    }

    if (aiConfig.mode === 'cloud') {
      if (aiConfig.cloud.apiKey && aiConfig.cloud.lastTestResult === 'success') {
        const providerName = PROVIDER_NAMES[aiConfig.cloud.provider] || aiConfig.cloud.provider
        return { 
          mode: 'cloud', 
          name: `${providerName}${aiConfig.cloud.model ? ` • ${aiConfig.cloud.model}` : ''}`, 
          ready: true 
        }
      }
      if (aiConfig.cloud.apiKey) {
        return { mode: 'cloud', name: `${PROVIDER_NAMES[aiConfig.cloud.provider]} (not tested)`, ready: false }
      }
      return { mode: 'cloud', name: 'Cloud (no API key)', ready: false }
    }

    // Auto mode
    if (serverOllamaAvailable) {
      return { mode: 'auto', name: 'Auto • Ollama', ready: true }
    }
    if (aiConfig.cloud.apiKey && aiConfig.cloud.lastTestResult === 'success') {
      return { mode: 'auto', name: `Auto • ${PROVIDER_NAMES[aiConfig.cloud.provider]}`, ready: true }
    }
    return { mode: 'auto', name: 'Auto (checking...)', ready: serverOllamaAvailable }
  }, [aiConfig, serverOllamaAvailable])

  const effectiveBackend = getEffectiveBackend()

  // Get current position
  const getCurrentPosition = useCallback(() => {
    const validated = validatePosition(dragPosition)
    return validated || getDefaultPosition()
  }, [dragPosition])

  // Drag handlers
  const handleDragStart = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault()
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
    const pos = getCurrentPosition()
    
    dragRef.current = { startX: clientX, startY: clientY, startPosX: pos.x, startPosY: pos.y }
    setIsDragging(true)
  }, [getCurrentPosition])

  useEffect(() => {
    if (!isDragging) return

    const handleMove = (e: MouseEvent | TouchEvent) => {
      if (!dragRef.current) return
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
      
      const newX = Math.max(60, Math.min(window.innerWidth - 20, dragRef.current.startPosX + (clientX - dragRef.current.startX)))
      const newY = Math.max(60, Math.min(window.innerHeight - 20, dragRef.current.startPosY + (clientY - dragRef.current.startY)))
      setDragPosition({ x: newX, y: newY })
    }

    const handleEnd = () => {
      setIsDragging(false)
      dragRef.current = null
      if (dragPosition) {
        localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(dragPosition))
      }
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', handleEnd)
    window.addEventListener('touchmove', handleMove)
    window.addEventListener('touchend', handleEnd)
    return () => {
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', handleEnd)
      window.removeEventListener('touchmove', handleMove)
      window.removeEventListener('touchend', handleEnd)
    }
  }, [isDragging, dragPosition])

  // Save messages
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-MAX_STORED_MESSAGES)))
    } catch { /* ignore */ }
  }, [messages])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault()
        setIsOpen(prev => !prev)
        if (!isOpen) setTimeout(() => inputRef.current?.focus(), 100)
      }
      if (e.key === 'Escape' && isOpen) setIsOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

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

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || isProcessing) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const query = input.trim()
    setInput('')
    setIsProcessing(true)

    try {
      const conversationHistory = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString()
      }))

      const token = apiClient.getToken()
      
      // Build request based on AI config
      const requestBody: Record<string, unknown> = {
        message: query,
        conversation_history: conversationHistory,
        include_context: true,
        context_limit: 5
      }
      
      // Add BYOK config if cloud mode with API key
      if (aiConfig?.mode === 'cloud' && aiConfig.cloud.apiKey) {
        requestBody.preferred_provider = aiConfig.cloud.provider
        requestBody.user_api_key = aiConfig.cloud.apiKey
        if (aiConfig.cloud.model) {
          requestBody.user_model = aiConfig.cloud.model
        }
      } else if (aiConfig?.mode === 'local') {
        requestBody.preferred_provider = 'ollama'
      }
      // Auto mode: let backend decide

      const response = await fetch('/api/v2/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) throw new Error('Chat API error')

      const data = await response.json()
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        metadata: {
          provider: data.provider,
          model: data.model,
          sources: data.context?.map((c: any) => ({
            doc_id: c.doc_id,
            doc_type: c.doc_type,
            title: c.title,
            similarity: c.similarity
          }))
        }
      }
      setMessages(prev => [...prev, assistantMessage])

    } catch (error) {
      console.error('[Veena] Chat error:', error)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm having trouble connecting. Please check AI Settings (⚙️) to configure your AI backend.",
        timestamp: new Date()
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  // Quick actions
  const quickActions = [
    { label: '📊 Trials', action: 'Show me active trials' },
    { label: '🏆 Top Performers', action: 'Which germplasm has best yield?' },
    { label: '🧬 Crossing', action: 'Suggest crossing parents' },
  ]

  // Closed state - FAB
  if (!isOpen) {
    const pos = getCurrentPosition()
    return (
      <button
        onClick={() => !isDragging && setIsOpen(true)}
        onMouseDown={handleDragStart}
        onTouchStart={handleDragStart}
        style={{ left: pos.x - 28, top: pos.y - 28, cursor: isDragging ? 'grabbing' : 'grab' }}
        className={cn(
          'fixed z-50 w-14 h-14 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center group touch-none select-none',
          isDragging && 'scale-110',
          className
        )}
        title="Ask Veena (Ctrl+/)"
      >
        <span className="text-2xl group-hover:scale-110 transition-transform">🪷</span>
        <span className={cn(
          'absolute -top-1 -right-1 w-4 h-4 rounded-full animate-pulse',
          effectiveBackend.ready ? 'bg-green-500' : 'bg-yellow-500'
        )} />
      </button>
    )
  }

  // Panel position
  const getPanelPosition = () => {
    const pos = getCurrentPosition()
    const panelWidth = isMinimized ? 320 : 384
    const panelHeight = isMinimized ? 56 : 550
    
    let left = pos.x - panelWidth + 28
    let top = pos.y - panelHeight - 10
    
    if (left < 10) left = 10
    if (left + panelWidth > window.innerWidth - 10) left = window.innerWidth - panelWidth - 10
    if (top < 10) top = pos.y + 40
    if (top + panelHeight > window.innerHeight - 10) top = window.innerHeight - panelHeight - 10
    
    return { left, top }
  }

  const panelPos = getPanelPosition()

  return (
    <div
      style={{ left: panelPos.left, top: panelPos.top }}
      className={cn(
        'fixed z-50 flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-2xl overflow-hidden transition-all duration-300',
        isMinimized ? 'w-80 h-14' : 'w-96 h-[550px]',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg">🪷</span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">Veena</h3>
            <p className="text-[10px] opacity-90 truncate">
              {isProcessing ? '⏳ Thinking...' : (
                effectiveBackend.ready 
                  ? `${effectiveBackend.mode === 'local' ? '🏠' : effectiveBackend.mode === 'cloud' ? '☁️' : '🔄'} ${effectiveBackend.name}`
                  : '⚠️ Setup required'
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={clearHistory}
            className="p-1.5 hover:bg-white/20 rounded transition-colors text-sm"
            title="Clear chat history"
          >
            🗑️
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={cn("p-1.5 hover:bg-white/20 rounded transition-colors text-sm", showSettings && "bg-white/20")}
            title="AI Settings"
          >
            ⚙️
          </button>
          <button
            onClick={() => navigate('/veena')}
            className="p-1.5 hover:bg-white/20 rounded transition-colors text-sm"
            title="Open full page"
          >
            ⛶
          </button>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 hover:bg-white/20 rounded transition-colors text-sm"
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-white/20 rounded transition-colors text-sm"
          >
            ✕
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Settings Panel */}
          {showSettings && (
            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 space-y-2">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">AI Backend</p>
              <div className="flex gap-1">
                {(['auto', 'local', 'cloud'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => {
                      if (aiConfig) {
                        const newConfig = { ...aiConfig, mode }
                        setAiConfig(newConfig)
                        localStorage.setItem(AI_CONFIG_KEY, JSON.stringify(newConfig))
                      } else {
                        navigate('/ai-settings')
                      }
                    }}
                    className={cn(
                      'flex-1 px-2 py-1.5 text-xs rounded transition-colors',
                      (aiConfig?.mode || 'auto') === mode
                        ? 'bg-amber-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                    )}
                  >
                    {mode === 'auto' ? '🔄 Auto' : mode === 'local' ? '🏠 Local' : '☁️ Cloud'}
                  </button>
                ))}
              </div>
              <button
                onClick={() => navigate('/ai-settings')}
                className="w-full text-xs text-amber-600 hover:text-amber-700 hover:underline"
              >
                Open full AI Settings →
              </button>
            </div>
          )}

          {/* Experimental Notice */}
          <div className="px-3 py-1 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800">
            <p className="text-[9px] text-purple-700 dark:text-purple-300 text-center">
              🧪 <strong>Experimental</strong> — AI can make mistakes. Verify recommendations independently.
            </p>
          </div>

          {/* Not Configured Banner */}
          {!effectiveBackend.ready && (
            <div className="px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200">
              <p className="text-xs text-yellow-800 dark:text-yellow-200">
                🔧 <strong>Setup Required:</strong>{' '}
                <button 
                  onClick={() => navigate('/ai-settings')}
                  className="underline hover:no-underline"
                >
                  Configure AI backend
                </button>
              </p>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50 dark:bg-gray-800">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isProcessing && (
              <div className="flex items-center gap-2 text-gray-500">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs">Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex gap-1.5 overflow-x-auto">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => { setInput(action.action); inputRef.current?.focus() }}
                  className="flex-shrink-0 px-2 py-1 text-[10px] font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-full hover:bg-amber-100 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Ask Veena..."
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isProcessing}
                className={cn(
                  'p-2 rounded-lg transition-all',
                  input.trim() && !isProcessing
                    ? 'bg-amber-500 text-white hover:bg-amber-600'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                )}
              >
                ➤
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ============================================
// MESSAGE BUBBLE
// ============================================

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[85%] rounded-xl px-3 py-2',
        isUser
          ? 'bg-amber-500 text-white'
          : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
      )}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="veena-markdown text-sm leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Headings
                h1: ({ children }) => <h1 className="text-base font-bold mt-2 mb-1">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold mt-2 mb-1">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold mt-1.5 mb-0.5">{children}</h3>,
                // Paragraphs
                p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
                // Lists
                ul: ({ children }) => <ul className="list-disc list-inside mb-1.5 space-y-0.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-1.5 space-y-0.5">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                // Code
                code: ({ className, children }) => {
                  const isInline = !className
                  return isInline ? (
                    <code className="bg-gray-100 dark:bg-gray-600 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                  ) : (
                    <code className="block bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs font-mono overflow-x-auto my-1">{children}</code>
                  )
                },
                pre: ({ children }) => <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs overflow-x-auto my-1.5">{children}</pre>,
                // Tables
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full text-xs border-collapse border border-gray-300 dark:border-gray-600">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-gray-100 dark:bg-gray-700">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-gray-200 dark:border-gray-600">{children}</tr>,
                th: ({ children }) => <th className="px-2 py-1 text-left font-semibold border border-gray-300 dark:border-gray-600">{children}</th>,
                td: ({ children }) => <td className="px-2 py-1 border border-gray-300 dark:border-gray-600">{children}</td>,
                // Links
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-amber-600 dark:text-amber-400 underline hover:no-underline">
                    {children}
                  </a>
                ),
                // Bold & Italic
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                // Blockquote
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-amber-400 pl-2 my-1.5 italic text-gray-600 dark:text-gray-400">{children}</blockquote>
                ),
                // Horizontal rule
                hr: () => <hr className="my-2 border-gray-200 dark:border-gray-600" />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        {/* Provider info for assistant messages */}
        {!isUser && message.metadata?.provider && (
          <p className="text-[9px] opacity-60 mt-1">
            via {message.metadata.provider}{message.metadata.model ? ` • ${message.metadata.model}` : ''}
          </p>
        )}
        
        {/* Sources */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
            <div className="flex flex-wrap gap-1">
              {message.metadata.sources.slice(0, 3).map((source, i) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900/30 rounded">
                  {source.doc_type}: {source.title || source.doc_id}
                </span>
              ))}
            </div>
          </div>
        )}

        <span className={cn('text-[9px] block mt-1', isUser ? 'opacity-70' : 'text-gray-400')}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}
