/**
 * VeenaChat - Full-page Veena AI Assistant
 * 
 * Dedicated page for extended conversations with Veena.
 * Provides a larger, more comfortable chat experience.
 * 
 * REFACTORED: Uses shared useVeenaChat hook for all state/logic.
 */

import { useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { VeenaLogo } from '@/components/ai/VeenaTrigger'

import { cn } from '@/lib/utils'
import { MultiServiceNotice } from '@/components/ApiKeyNotice'
import { useVeenaChat, VeenaMessage } from '@/hooks/useVeenaChat'


// MAIN COMPONENT
// ============================================

export function VeenaChat() {
  const navigate = useNavigate()
  
  // Use the shared hook for all chat logic
  const {
    messages,
    input,
    setInput,
    isProcessing,
    effectiveBackend,
    messagesEndRef,
    sendMessage,
    clearHistory,
    voice
  } = useVeenaChat()
  
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

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
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Go back"
            >
              ←
            </button>
            <VeenaLogo className="w-9 h-9" />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold">Veena</h1>
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
              <p className="text-xs opacity-90">
                {effectiveBackend.ready 
                  ? `☁️ ${effectiveBackend.name}`
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
              onClick={() => navigate('/ai-settings')}
              className="px-3 py-1.5 text-sm hover:bg-white/20 rounded-lg transition-colors flex items-center gap-1"
              title="AI Settings"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto flex flex-col" style={{ height: 'calc(100dvh - 60px)' }}>
        {/* AI Backend Info */}
        <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">☁️ Cloud AI:</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {effectiveBackend.ready ? effectiveBackend.name : 'Not configured'}
              </span>
            </div>
            <button
              onClick={() => navigate('/ai-settings')}
              className="text-sm text-emerald-600 hover:text-emerald-700 hover:underline"
            >
              Configure AI →
            </button>
          </div>
        </div>

        {/* Scientific Disclaimer & Preview Warning */}
        <div className="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 flex flex-col sm:flex-row items-center justify-center gap-2">
          <p className="text-xs text-amber-800 dark:text-amber-300 text-center leading-relaxed font-medium">
            ⚖️ <strong>Scientific Disclaimer:</strong> AI responses are for assistance only. Verify all analysis independently.
          </p>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border border-amber-200 whitespace-nowrap">
            🚧 Under Development
          </span>
        </div>

        {/* Not Configured Banner */}
        {!effectiveBackend.ready && (
          <div className="px-4 py-3">
            <MultiServiceNotice 
              serviceIds={['google_ai', 'groq', 'openai', 'anthropic']} 
              title="AI Configuration Required"
            />
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center p-8 opacity-0 animate-in fade-in zoom-in duration-700">
              <div className="w-32 h-32 rounded-full overflow-hidden bg-gradient-to-br from-gray-900 to-emerald-950 flex items-center justify-center mb-8 shadow-2xl shadow-emerald-500/20 border border-emerald-500/20 relative">
                <div className="absolute inset-0 bg-emerald-500/10 animate-pulse"></div>
                <VeenaLogo className="w-20 h-20 relative z-10" />
              </div>
              <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-800 dark:from-emerald-400 dark:to-teal-200 mb-3">
                Namaste! I'm Veena
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-md text-center text-lg">
                Your intelligent breeding assistant. Ready to analyze trials, germplasm, and genetic data.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}
          {isProcessing && (
            <div className="flex items-center gap-3 text-gray-500 px-4">
              <div className="flex gap-1">
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
                className="flex-shrink-0 px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-full hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-end gap-3">
            <button
              onClick={voice.isListening ? voice.stopListening : voice.startListening}
              className={cn(
                'p-3 rounded-xl transition-all flex-shrink-0',
                voice.isListening 
                  ? 'bg-red-500 text-white animate-pulse shadow-lg' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'
              )}
              title={voice.isListening ? 'Stop listening' : 'Voice input'}
              style={{ height: '48px', width: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              {voice.isListening ? '⏹️' : '🎤'}
            </button>
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
              placeholder={voice.isListening ? "Listening..." : "Ask Veena anything about plant breeding..."}
              rows={1}
              className="flex-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
              style={{ minHeight: '48px', maxHeight: '200px' }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || isProcessing}
              className={cn(
                'p-3 rounded-xl transition-all flex-shrink-0',
                input.trim() && !isProcessing
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-lg hover:shadow-xl'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
              )}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <div className="flex justify-center mt-2 h-5">
            {voice.error ? (
              <p className="text-xs text-red-500">{voice.error}</p>
            ) : (
              <p className="text-xs text-gray-400">
                Press Enter to send, Shift+Enter for new line
              </p>
            )}
          </div>
        </div>
      </div>
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
        'max-w-[80%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md'
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
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-600 dark:text-emerald-400 underline hover:no-underline">
                    {children}
                  </a>
                ),
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-3 border-emerald-400 pl-3 my-2 italic text-gray-600 dark:text-gray-400">{children}</blockquote>
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
                <span key={i} className="text-[10px] px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-200 rounded">
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
