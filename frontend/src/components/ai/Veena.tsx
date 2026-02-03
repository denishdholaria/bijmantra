/**
 * Veena (वीणा) - AI Assistant FAB Widget for Bijmantra
 * 
 * Named after the sacred instrument of Goddess Saraswati, symbolizing:
 * - The harmony of knowledge and creativity
 * - Wisdom radiating in all directions (jnaana veena)
 * 
 * REFACTORED: Uses shared useVeenaChat hook for all state/logic.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { useVeenaChat, VeenaMessage } from '@/hooks/useVeenaChat'

// ============================================
// TYPES
// ============================================

interface VeenaProps {
  className?: string
  defaultOpen?: boolean
}

// Storage keys for position
const POSITION_STORAGE_KEY = 'veena_position'

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
  const [showSettings, setShowSettings] = useState(false)
  
  // Use the shared hook for all chat logic
  const {
    messages,
    input,
    setInput,
    isProcessing,
    aiConfig,
    effectiveBackend,
    messagesEndRef,
    sendMessage,
    clearHistory,
    setAIMode,
    voice
  } = useVeenaChat()
  
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
                {(['local', 'cloud'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => {
                      if (aiConfig) {
                        setAIMode(mode)
                      } else {
                        navigate('/ai-settings')
                      }
                    }}
                    className={cn(
                      'flex-1 px-2 py-1.5 text-xs rounded transition-colors',
                      aiConfig?.mode === mode
                        ? 'bg-amber-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                    )}
                  >
                    {mode === 'local' ? '🏠 Local' : '☁️ Cloud'}
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

          {/* Scientific Disclaimer & Preview Warning */}
          <div className="px-3 py-1.5 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 space-y-1">
            <p className="text-[9px] text-amber-800 dark:text-amber-300 text-center leading-tight">
              ⚖️ <strong>Scientific Disclaimer:</strong> All breeding data analysis must be verified.
            </p>
            <div className="flex justify-center">
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[8px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border border-amber-200">
                🚧 Under Development
              </span>
            </div>
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
              <button
                onClick={voice.isListening ? voice.stopListening : voice.startListening}
                className={cn(
                  'p-2 rounded-lg transition-all',
                  voice.isListening 
                    ? 'bg-red-500 text-white animate-pulse' 
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'
                )}
                title={voice.isListening ? 'Stop listening' : 'Voice input'}
              >
                {voice.isListening ? '⏹️' : '🎤'}
              </button>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                placeholder={voice.isListening ? "Listening..." : "Ask Veena..."}
                className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <button
                onClick={() => sendMessage()}
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
            {voice.error && (
              <p className="text-[10px] text-red-500 mt-1 px-1">{voice.error}</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ============================================
// MESSAGE BUBBLE
// ============================================

function MessageBubble({ message }: { message: VeenaMessage }) {
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
                h1: ({ children }) => <h1 className="text-base font-bold mt-2 mb-1">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold mt-2 mb-1">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold mt-1.5 mb-0.5">{children}</h3>,
                p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-1.5 space-y-0.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-1.5 space-y-0.5">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                code: ({ className, children }) => {
                  const isInline = !className
                  return isInline ? (
                    <code className="bg-gray-100 dark:bg-gray-600 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                  ) : (
                    <code className="block bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs font-mono overflow-x-auto my-1">{children}</code>
                  )
                },
                pre: ({ children }) => <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded text-xs overflow-x-auto my-1.5">{children}</pre>,
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
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-amber-600 dark:text-amber-400 underline hover:no-underline">
                    {children}
                  </a>
                ),
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-amber-400 pl-2 my-1.5 italic text-gray-600 dark:text-gray-400">{children}</blockquote>
                ),
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
