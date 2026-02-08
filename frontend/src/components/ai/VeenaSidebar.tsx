/**
 * VeenaSidebar — Redesigned AI Chat Panel (v2)
 *
 * Clean, modern right-docked sidebar. Cloud-API-only architecture.
 * Toggle via SystemBar button or ⌘/.
 */

import { useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Trash2, Maximize2, X, Mic, MicOff, ArrowUp, KeyRound, FlaskConical, Dna, BarChart3, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useVeenaChat, VeenaMessage } from '@/hooks/useVeenaChat'
import { VeenaLogo } from './VeenaTrigger'
import { useVeenaSidebarStore } from '@/store/veenaSidebarStore'

interface VeenaSidebarProps {
  className?: string
}

export function VeenaSidebar({ className }: VeenaSidebarProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { isOpen, close, toggle } = useVeenaSidebarStore()

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

  // ─── Keyboard shortcuts ───
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault()
        toggle()
        if (!isOpen) setTimeout(() => inputRef.current?.focus(), 150)
      }
      if (e.key === 'Escape' && isOpen) close()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, toggle, close])

  // Focus input when opened
  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 150)
  }, [isOpen])

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
      if (inputRef.current) inputRef.current.style.height = 'auto'
    }
  }

  // ─── Quick suggestions (only shown on empty state) ───
  const suggestions = [
    { icon: FlaskConical, label: 'Active trials', action: 'Show me active trials' },
    { icon: BarChart3, label: 'Top performers', action: 'Which germplasm has best yield?' },
    { icon: Dna, label: 'Crossing plans', action: 'Suggest crossing parents' },
  ]

  return (
    <>
      {/* Backdrop — mobile only */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-[2px] lg:hidden"
          onClick={close}
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          'fixed top-0 right-0 z-50 h-full',
          'w-full sm:w-[380px] lg:w-[400px]',
          'bg-white dark:bg-slate-950',
          'border-l border-slate-200/80 dark:border-slate-800/80',
          'shadow-[-8px_0_30px_-12px_rgba(0,0,0,0.12)]',
          'transition-transform duration-200 ease-out',
          isOpen ? 'translate-x-0' : 'translate-x-full',
          'flex flex-col',
          className
        )}
      >
        {/* ─── Header ─── */}
        <div className="flex items-center justify-between px-4 h-12 border-b border-slate-100 dark:border-slate-800/80 flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <VeenaLogo className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Veena</span>
            {/* Status dot */}
            <div
              className={cn(
                'w-1.5 h-1.5 rounded-full flex-shrink-0',
                isProcessing
                  ? 'bg-amber-400 animate-pulse'
                  : effectiveBackend.ready
                    ? 'bg-emerald-500'
                    : 'bg-slate-300 dark:bg-slate-600'
              )}
              title={isProcessing ? 'Processing…' : effectiveBackend.ready ? 'Connected' : 'Not configured'}
            />
            {effectiveBackend.ready && (
              <span className="text-[10px] text-slate-400 dark:text-slate-500 truncate hidden sm:block">
                {effectiveBackend.name}
              </span>
            )}
          </div>
          <div className="flex items-center">
            <button
              onClick={clearHistory}
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors"
              title="Clear history"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => { navigate('/veena'); close() }}
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors"
              title="Open full page"
            >
              <Maximize2 className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={close}
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors ml-0.5"
              title="Close (Esc)"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* ─── Not Configured Banner ─── */}
        {!effectiveBackend.ready && (
          <button
            onClick={() => { navigate('/ai-settings'); close() }}
            className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-950/30 border-b border-amber-100 dark:border-amber-900/40 text-left group transition-colors hover:bg-amber-100/80 dark:hover:bg-amber-950/50"
          >
            <KeyRound className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
            <span className="text-xs text-amber-700 dark:text-amber-400">
              Add your AI provider API key to get started
            </span>
            <span className="text-xs text-amber-500 group-hover:text-amber-600 ml-auto flex-shrink-0">→</span>
          </button>
        )}

        {/* ─── Messages ─── */}
        <div className="flex-1 overflow-y-auto overscroll-contain">
          {messages.length === 0 ? (
            /* ─── Empty state ─── */
            <div className="flex flex-col items-center justify-center h-full px-6 py-8">
              <VeenaLogo className="w-12 h-12 opacity-30 mb-4" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">How can I help?</p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mb-6 text-center">
                Ask about trials, germplasm, or breeding recommendations.
              </p>
              <div className="w-full max-w-[280px] space-y-2">
                {suggestions.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => { setInput(s.action); inputRef.current?.focus() }}
                    className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg border border-slate-150 dark:border-slate-800 text-left text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:border-slate-200 dark:hover:border-slate-700 transition-colors"
                  >
                    <s.icon className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500 flex-shrink-0" />
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* ─── Message stream ─── */
            <div className="px-4 py-3 space-y-4">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isProcessing && (
                <div className="flex items-start gap-2.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/40 flex-shrink-0 mt-0.5">
                    <VeenaLogo className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex items-center gap-1.5 pt-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_infinite]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_0.2s_infinite]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_0.4s_infinite]" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* ─── Disclaimer (collapsed, subtle) ─── */}
        <div className="px-4 py-1.5 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/50">
          <p className="flex items-center justify-center gap-1 text-[10px] text-slate-400 dark:text-slate-600">
            <Info className="h-2.5 w-2.5" />
            AI can make mistakes · Verify with a specialist
          </p>
        </div>

        {/* ─── Input ─── */}
        <div className="px-3 pb-3 pt-2 bg-white dark:bg-slate-950">
          <div className={cn(
            'flex items-end gap-1.5 rounded-xl border bg-slate-50 dark:bg-slate-900 px-3 py-2 transition-colors',
            'border-slate-200 dark:border-slate-800',
            'focus-within:border-emerald-300 dark:focus-within:border-emerald-800 focus-within:ring-1 focus-within:ring-emerald-200/50 dark:focus-within:ring-emerald-900/50'
          )}>
            {/* Voice button */}
            <button
              onClick={voice.isListening ? voice.stopListening : voice.startListening}
              className={cn(
                'flex-shrink-0 p-1.5 rounded-lg transition-all',
                voice.isListening
                  ? 'text-red-500 bg-red-50 dark:bg-red-950/30 animate-pulse'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800'
              )}
              title={voice.isListening ? 'Stop' : 'Voice input'}
            >
              {voice.isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>

            {/* Textarea */}
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={voice.isListening ? 'Listening…' : 'Ask Veena…'}
              rows={1}
              className="flex-1 bg-transparent text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-600 resize-none focus:outline-none leading-5 py-1 max-h-[120px]"
            />

            {/* Send button */}
            <button
              onClick={() => { sendMessage(); if (inputRef.current) inputRef.current.style.height = 'auto' }}
              disabled={!input.trim() || isProcessing}
              className={cn(
                'flex-shrink-0 p-1.5 rounded-lg transition-all',
                input.trim() && !isProcessing
                  ? 'text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm'
                  : 'text-slate-300 dark:text-slate-700 cursor-not-allowed'
              )}
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
          {voice.error && (
            <p className="text-[10px] text-red-500 mt-1.5 px-1">{voice.error}</p>
          )}
        </div>
      </div>
    </>
  )
}

// ─────────────────────────────────────────────
// Message Bubble
// ─────────────────────────────────────────────

function MessageBubble({ message }: { message: VeenaMessage }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-md px-3.5 py-2.5 bg-emerald-600 text-white shadow-sm">
          <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
          <span className="text-[9px] opacity-60 block mt-1 text-right">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2.5">
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/40 flex-shrink-0 mt-0.5">
        <VeenaLogo className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="veena-markdown text-[13px] leading-relaxed text-slate-800 dark:text-slate-200">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h1 className="text-sm font-bold mt-3 mb-1">{children}</h1>,
              h2: ({ children }) => <h2 className="text-[13px] font-bold mt-2.5 mb-1">{children}</h2>,
              h3: ({ children }) => <h3 className="text-[13px] font-semibold mt-2 mb-0.5">{children}</h3>,
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
              li: ({ children }) => <li className="text-[13px]">{children}</li>,
              code: ({ className, children }) => {
                const isInline = !className
                return isInline ? (
                  <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-xs font-mono text-emerald-700 dark:text-emerald-400">{children}</code>
                ) : (
                  <code className="block bg-slate-100 dark:bg-slate-800 p-2.5 rounded-lg text-xs font-mono overflow-x-auto my-2">{children}</code>
                )
              },
              pre: ({ children }) => <pre className="bg-slate-100 dark:bg-slate-800 p-2.5 rounded-lg text-xs overflow-x-auto my-2">{children}</pre>,
              table: ({ children }) => (
                <div className="overflow-x-auto my-2 rounded-lg border border-slate-200 dark:border-slate-700">
                  <table className="min-w-full text-xs">{children}</table>
                </div>
              ),
              thead: ({ children }) => <thead className="bg-slate-50 dark:bg-slate-800">{children}</thead>,
              tbody: ({ children }) => <tbody className="divide-y divide-slate-100 dark:divide-slate-800">{children}</tbody>,
              tr: ({ children }) => <tr>{children}</tr>,
              th: ({ children }) => <th className="px-2.5 py-1.5 text-left font-semibold text-slate-600 dark:text-slate-400">{children}</th>,
              td: ({ children }) => <td className="px-2.5 py-1.5">{children}</td>,
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-600 dark:text-emerald-400 underline decoration-emerald-300/50 hover:decoration-emerald-500 transition-colors">
                  {children}
                </a>
              ),
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              blockquote: ({ children }) => (
                <blockquote className="border-l-2 border-emerald-300 dark:border-emerald-700 pl-3 my-2 text-slate-600 dark:text-slate-400">{children}</blockquote>
              ),
              hr: () => <hr className="my-3 border-slate-200 dark:border-slate-800" />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Provider & model */}
        {message.metadata?.provider && (
          <p className="text-[9px] text-slate-400 dark:text-slate-600 mt-1">
            {message.metadata.provider}{message.metadata.model ? ` · ${message.metadata.model}` : ''}
          </p>
        )}

        {/* Sources */}
        {message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {message.metadata.sources.slice(0, 3).map((source, i) => (
              <span key={i} className="text-[9px] px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-md">
                {source.doc_type}: {source.title || source.doc_id}
              </span>
            ))}
          </div>
        )}

        <span className="text-[9px] text-slate-400 dark:text-slate-600 block mt-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}
