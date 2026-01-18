/**
 * VeenaSidebar - The Right-Docked AI Chat Panel
 * 
 * A full-height sidebar that slides in from the right edge.
 * Integrates with the VeenaTrigger (slashed edge button).
 * Uses the shared useVeenaChat hook for all chat state/logic.
 */

import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { useVeenaChat, VeenaMessage } from '@/hooks/useVeenaChat'
import { VeenaTrigger, VeenaLogo } from './VeenaTrigger'

interface VeenaSidebarProps {
  className?: string
}

export function VeenaSidebar({ className }: VeenaSidebarProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Sidebar open state
  const [isOpen, setIsOpen] = useState(false)
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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault()
        setIsOpen(prev => !prev)
        if (!isOpen) setTimeout(() => inputRef.current?.focus(), 150)
      }
      if (e.key === 'Escape' && isOpen) setIsOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150)
    }
  }, [isOpen])

  // Quick actions
  const quickActions = [
    { label: '📊 Trials', action: 'Show me active trials' },
    { label: '🏆 Top Performers', action: 'Which germplasm has best yield?' },
    { label: '🧬 Crossing', action: 'Suggest crossing parents' },
  ]

  return (
    <>
      {/* The Slashed Edge Trigger Button */}
      <VeenaTrigger
        isOpen={isOpen}
        onClick={() => setIsOpen(true)}
        isReady={effectiveBackend.ready}
        isProcessing={isProcessing}
      />

      {/* Backdrop (optional - click to close) */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* The Sidebar Panel */}
      <div
        className={cn(
          // Positioning
          'fixed top-0 right-0 z-50 h-full',
          // Size
          'w-full sm:w-96 lg:w-[420px]',
          // Appearance
          'bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl',
          'border-l border-gray-200 dark:border-gray-700',
          'shadow-2xl',
          // Animation
          'transition-transform duration-300 ease-out',
          isOpen ? 'translate-x-0' : 'translate-x-full',
          // Flex layout
          'flex flex-col',
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-emerald-600 to-teal-700 text-white">
          <div className="flex items-center gap-3 min-w-0">
            <VeenaLogo className="w-7 h-7" />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold">Veena</h2>
                {/* Status indicator */}
                <div
                  className={cn(
                    "w-2 h-2 rounded-full",
                    isProcessing
                      ? "bg-yellow-400 animate-pulse"
                      : effectiveBackend.ready
                        ? "bg-green-400"
                        : "bg-red-400"
                  )}
                  title={isProcessing ? "Processing..." : effectiveBackend.ready ? "Ready" : "Not configured"}
                />
              </div>
              <p className="text-[11px] opacity-90 truncate">
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
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Clear chat history"
            >
              🗑️
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={cn("p-2 hover:bg-white/20 rounded-lg transition-colors", showSettings && "bg-white/20")}
              title="AI Settings"
            >
              ⚙️
            </button>
            <button
              onClick={() => navigate('/veena')}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Open full page"
            >
              ⛶
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors ml-1"
              title="Close (Esc)"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 space-y-2">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">AI Backend</p>
            <div className="flex gap-2">
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
                    'flex-1 px-3 py-2 text-xs rounded-lg transition-colors',
                    aiConfig?.mode === mode
                      ? 'bg-emerald-500 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                  )}
                >
                  {mode === 'local' ? '🏠 Local' : '☁️ Cloud'}
                </button>
              ))}
            </div>
            <button
              onClick={() => navigate('/ai-settings')}
              className="w-full text-xs text-emerald-600 hover:text-emerald-700 hover:underline pt-1"
            >
              Open full AI Settings →
            </button>
          </div>
        )}

        {/* Scientific Disclaimer & Preview Warning */}
        <div className="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 space-y-1">
          <p className="text-[10px] text-amber-800 dark:text-amber-300 text-center leading-tight">
            ⚖️ <strong>Scientific Disclaimer:</strong> AI can make mistakes. All breeding data analysis must be verified by a specialist.
          </p>
          <div className="flex justify-center">
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border border-amber-200">
              🚧 Under Development
            </span>
          </div>
        </div>

        {/* Not Configured Banner */}
        {!effectiveBackend.ready && (
          <div className="px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200">
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

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-800/50">
          {messages.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <VeenaLogo className="w-16 h-16 mx-auto mb-3 opacity-50" />
              <p className="text-sm font-medium">How can I help you today?</p>
              <p className="text-xs mt-1">Ask about trials, germplasm, or get breeding recommendations.</p>
            </div>
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isProcessing && (
            <div className="flex items-center gap-2 text-gray-500">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs">Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {quickActions.map((action) => (
              <button
                key={action.label}
                onClick={() => { setInput(action.action); inputRef.current?.focus() }}
                className="flex-shrink-0 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-full hover:bg-emerald-100 transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-center gap-2">
            <button
              onClick={voice.isListening ? voice.stopListening : voice.startListening}
              className={cn(
                'p-2.5 rounded-xl transition-all',
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
              className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || isProcessing}
              className={cn(
                'p-2.5 rounded-xl transition-all',
                input.trim() && !isProcessing
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-md shadow-emerald-900/10'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
              )}
            >
              ➤
            </button>
          </div>
          {voice.error && (
            <p className="text-xs text-red-500 mt-2 px-1">{voice.error}</p>
          )}
        </div>

        {/* Bottom decorative slashed edge (mirrors the trigger) */}
        <div 
          className="absolute bottom-0 right-0 w-16 h-16 pointer-events-none"
          style={{
            background: 'linear-gradient(to bottom right, transparent 50%, rgba(16, 185, 129, 0.2) 50%)',
          }}
        />
      </div>
    </>
  )
}

// ============================================
// MESSAGE BUBBLE (Extracted for clarity)
// ============================================

function MessageBubble({ message }: { message: VeenaMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[85%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-900/10'
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
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-600 dark:text-emerald-400 underline hover:no-underline">
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
                  <span key={i} className="text-[9px] px-1.5 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-200 rounded">
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
