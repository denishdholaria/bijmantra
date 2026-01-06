/**
 * VeenaChat - Full-page Veena AI Assistant
 * 
 * Dedicated page for extended conversations with Veena.
 * Provides a larger, more comfortable chat experience.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'
import { MultiServiceNotice } from '@/components/ApiKeyNotice'

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

type AIMode = 'auto' | 'local' | 'cloud'

interface AIConfig {
  mode: AIMode
  local: { host: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' }
  cloud: { provider: string; apiKey: string; model: string; tested: boolean; lastTestResult?: 'success' | 'error' }
}

// Storage keys
const STORAGE_KEY = 'veena_conversation_history'
const AI_CONFIG_KEY = 'bijmantra_ai_config_v2'
const MAX_STORED_MESSAGES = 100

// Provider display names
const PROVIDER_NAMES: Record<string, string> = {
  google: 'Google Gemini',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  groq: 'Groq',
  ollama: 'Ollama'
}

// ============================================
// MAIN COMPONENT
// ============================================

export function VeenaChat() {
  const navigate = useNavigate()
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
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load AI config on mount
  useEffect(() => {
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

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

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
      
      const requestBody: Record<string, unknown> = {
        message: query,
        conversation_history: conversationHistory,
        include_context: true,
        context_limit: 5
      }
      
      if (aiConfig?.mode === 'cloud' && aiConfig.cloud.apiKey) {
        requestBody.preferred_provider = aiConfig.cloud.provider
        requestBody.user_api_key = aiConfig.cloud.apiKey
        if (aiConfig.cloud.model) {
          requestBody.user_model = aiConfig.cloud.model
        }
      } else if (aiConfig?.mode === 'local') {
        requestBody.preferred_provider = 'ollama'
      }

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
      console.error('[VeenaChat] Chat error:', error)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm having trouble connecting. Please check AI Settings to configure your AI backend.",
        timestamp: new Date()
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  // Quick actions
  const quickActions = [
    { label: '📊 Active Trials', action: 'Show me active trials' },
    { label: '🏆 Top Performers', action: 'Which germplasm has best yield?' },
    { label: '🧬 Crossing Suggestions', action: 'Suggest crossing parents for disease resistance' },
    { label: '📈 Genetic Gain', action: 'Calculate genetic gain for my program' },
    { label: '🌾 Variety Comparison', action: 'Compare top 5 varieties by yield' },
    { label: '🔬 QTL Analysis', action: 'Explain QTL mapping for beginners' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Go back"
            >
              ←
            </button>
            <span className="text-2xl">🪷</span>
            <div>
              <h1 className="text-lg font-bold">Veena</h1>
              <p className="text-xs opacity-90">
                {effectiveBackend.ready 
                  ? `${effectiveBackend.mode === 'local' ? '🏠' : effectiveBackend.mode === 'cloud' ? '☁️' : '🔄'} ${effectiveBackend.name}`
                  : '⚠️ Setup required'
                }
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearHistory}
              className="px-3 py-1.5 text-sm hover:bg-white/20 rounded-lg transition-colors flex items-center gap-1"
              title="Clear chat history"
            >
              🗑️ Clear
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={cn(
                "px-3 py-1.5 text-sm hover:bg-white/20 rounded-lg transition-colors flex items-center gap-1",
                showSettings && "bg-white/20"
              )}
              title="AI Settings"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto flex flex-col" style={{ height: 'calc(100vh - 60px)' }}>
        {/* Settings Panel */}
        {showSettings && (
          <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">AI Backend:</span>
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
                        'px-3 py-1.5 text-sm rounded-lg transition-colors',
                        (aiConfig?.mode || 'auto') === mode
                          ? 'bg-amber-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                      )}
                    >
                      {mode === 'auto' ? '🔄 Auto' : mode === 'local' ? '🏠 Local' : '☁️ Cloud'}
                    </button>
                  ))}
                </div>
              </div>
              <button
                onClick={() => navigate('/ai-settings')}
                className="text-sm text-amber-600 hover:text-amber-700 hover:underline"
              >
                Open full AI Settings →
              </button>
            </div>
          </div>
        )}

        {/* AI Disclaimer */}
        <div className="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
          <p className="text-xs text-amber-700 dark:text-amber-300 text-center">
            ⚠️ AI can make mistakes. Always verify research analysis independently.
          </p>
        </div>

        {/* Not Configured Banner */}
        {!effectiveBackend.ready && (
          <div className="px-4 py-3">
            <MultiServiceNotice 
              serviceIds={['google_ai', 'groq', 'ollama', 'openai', 'anthropic']} 
              title="AI Backend Configuration Required"
            />
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isProcessing && (
            <div className="flex items-center gap-3 text-gray-500 px-4">
              <div className="flex gap-1">
                <span className="w-2.5 h-2.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2.5 h-2.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2.5 h-2.5 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm">Veena is thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {quickActions.map((action) => (
              <button
                key={action.label}
                onClick={() => { setInput(action.action); inputRef.current?.focus() }}
                className="flex-shrink-0 px-3 py-1.5 text-xs font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-full hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-end gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Ask Veena anything about plant breeding..."
              rows={1}
              className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isProcessing}
              className={cn(
                'p-3 rounded-xl transition-all flex-shrink-0',
                input.trim() && !isProcessing
                  ? 'bg-amber-500 text-white hover:bg-amber-600 shadow-lg hover:shadow-xl'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
              )}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
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
        'max-w-[80%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-amber-500 text-white'
          : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-md'
      )}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="veena-markdown text-sm leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className="text-lg font-bold mt-3 mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mt-3 mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>,
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                code: ({ className, children }) => {
                  const isInline = !className
                  return isInline ? (
                    <code className="bg-gray-100 dark:bg-gray-600 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
                  ) : (
                    <code className="block bg-gray-100 dark:bg-gray-800 p-3 rounded-lg text-xs font-mono overflow-x-auto my-2">{children}</code>
                  )
                },
                pre: ({ children }) => <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg text-xs overflow-x-auto my-2">{children}</pre>,
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full text-xs border-collapse border border-gray-300 dark:border-gray-600">{children}</table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-gray-100 dark:bg-gray-700">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-gray-200 dark:border-gray-600">{children}</tr>,
                th: ({ children }) => <th className="px-3 py-2 text-left font-semibold border border-gray-300 dark:border-gray-600">{children}</th>,
                td: ({ children }) => <td className="px-3 py-2 border border-gray-300 dark:border-gray-600">{children}</td>,
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-amber-600 dark:text-amber-400 underline hover:no-underline">
                    {children}
                  </a>
                ),
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-3 border-amber-400 pl-3 my-2 italic text-gray-600 dark:text-gray-400">{children}</blockquote>
                ),
                hr: () => <hr className="my-3 border-gray-200 dark:border-gray-600" />,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        {/* Provider info */}
        {!isUser && message.metadata?.provider && (
          <p className="text-[10px] opacity-60 mt-2">
            via {message.metadata.provider}{message.metadata.model ? ` • ${message.metadata.model}` : ''}
          </p>
        )}
        
        {/* Sources */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
            <p className="text-[10px] font-medium mb-1 opacity-70">Sources:</p>
            <div className="flex flex-wrap gap-1">
              {message.metadata.sources.slice(0, 5).map((source, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 rounded">
                  {source.doc_type}: {source.title || source.doc_id}
                </span>
              ))}
            </div>
          </div>
        )}

        <span className={cn('text-[10px] block mt-2', isUser ? 'opacity-70' : 'text-gray-400')}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}

export default VeenaChat
