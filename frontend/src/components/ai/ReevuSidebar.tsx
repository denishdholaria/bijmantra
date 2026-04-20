/**
 * ReevuSidebar — Canonical REEVU Chat Panel
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
import { useReevuChat, ReevuMessage } from '@/hooks/useReevuChat'
import { ReevuLogo } from './ReevuTrigger'
import { useReevuSidebarStore } from '@/store/reevuSidebarStore'
import EvidenceTraceCard from './EvidenceTraceCard'
import ReevuExecutionTraceCard from './ReevuExecutionTraceCard'
import ReevuSafeFailureCard from './ReevuSafeFailureCard'

interface ReevuSidebarProps {
	className?: string
}

export function ReevuSidebar({ className }: ReevuSidebarProps) {
	const navigate = useNavigate()
	const inputRef = useRef<HTMLTextAreaElement>(null)

	const { isOpen, close, toggle } = useReevuSidebarStore()

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
	} = useReevuChat()

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

	const suggestions = [
		{ icon: FlaskConical, label: 'Active trials', action: 'Show me active trials' },
		{ icon: BarChart3, label: 'Top performers', action: 'Which germplasm has best yield?' },
		{ icon: Dna, label: 'Crossing plans', action: 'Suggest crossing parents' },
	]

	return (
		<>
			{isOpen && (
				<div
					className="fixed inset-0 z-40 bg-black/30 backdrop-blur-[2px] lg:hidden"
					onClick={close}
				/>
			)}

			<div
				className={cn(
					'fixed top-0 right-0 z-50 h-full',
					'w-full sm:w-[380px] lg:w-[400px]',
					'bg-background/70 backdrop-blur-2xl backdrop-saturate-150 border-l border-white/10 dark:border-white/5',
					'shadow-[-20px_0_40px_-15px_rgba(0,0,0,0.3)] ring-1 ring-white/10',
					'transition-transform duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]',
					isOpen ? 'translate-x-0' : 'translate-x-full',
					'flex flex-col',
					className
				)}
			>
				<div className="flex items-center justify-between px-4 h-12 border-b border-border/40 flex-shrink-0 bg-transparent">
					<div className="flex items-center gap-2.5 min-w-0">
						<ReevuLogo className="w-5 h-5 flex-shrink-0" />
						<span className="text-sm font-semibold text-foreground">REEVU</span>
						<div
							className={cn(
								'w-1.5 h-1.5 rounded-full flex-shrink-0',
								isProcessing
									? 'bg-amber-400 animate-pulse'
									: effectiveBackend.ready
										? 'bg-prakruti-patta'
										: 'bg-muted-foreground'
							)}
							title={isProcessing ? 'Processing…' : effectiveBackend.ready ? 'Connected' : 'Not configured'}
						/>
						{effectiveBackend.ready && (
							<span className="text-[10px] tracking-wide text-muted-foreground truncate hidden sm:block" title={effectiveBackend.name}>
								Reason · Evidence · Evaluation · Validation · Unit
							</span>
						)}
					</div>
					<div className="flex items-center">
						<button onClick={clearHistory} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors" title="Clear history">
							<Trash2 className="h-3.5 w-3.5" />
						</button>
						<button onClick={() => { navigate('/reevu'); close() }} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors" title="Open full page">
							<Maximize2 className="h-3.5 w-3.5" />
						</button>
						<button onClick={close} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors ml-0.5" title="Close (Esc)">
							<X className="h-3.5 w-3.5" />
						</button>
					</div>
				</div>

				{!effectiveBackend.ready && (
					<button
						onClick={() => { navigate('/ai-settings'); close() }}
						className="flex items-center gap-2 px-4 py-2.5 bg-prakruti-sona-pale border-b border-prakruti-sona/20 text-left group transition-colors hover:bg-prakruti-sona-pale/80"
					>
						<KeyRound className="h-3.5 w-3.5 text-prakruti-sona flex-shrink-0" />
						<span className="text-xs text-prakruti-sona-dark">Add your AI provider API key to get started</span>
						<span className="text-xs text-prakruti-sona group-hover:text-prakruti-sona-dark ml-auto flex-shrink-0">→</span>
					</button>
				)}

				<div className="flex-1 overflow-y-auto overscroll-contain">
					{messages.length === 0 ? (
						<div className="flex flex-col items-center justify-center h-full px-6 py-8">
							<ReevuLogo className="w-12 h-12 opacity-30 mb-4" />
							<p className="text-sm font-medium text-foreground mb-1">How can I help?</p>
							<p className="text-xs text-muted-foreground mb-6 text-center">Ask about trials, germplasm, or breeding recommendations.</p>
							<div className="w-full max-w-[280px] space-y-2">
								{suggestions.map((s) => (
									<button
										key={s.label}
										onClick={() => { setInput(s.action); inputRef.current?.focus() }}
										className="flex items-center gap-2.5 w-full px-3 py-2 rounded-lg border border-border text-left text-xs text-foreground hover:bg-muted hover:border-border transition-colors"
									>
										<s.icon className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
										{s.label}
									</button>
								))}
							</div>
						</div>
					) : (
						<div className="px-4 py-3 space-y-4">
							{messages.map((message) => (
								<MessageBubble key={message.id} message={message} />
							))}
							{isProcessing && (
								<div className="flex items-start gap-2.5">
									<div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted flex-shrink-0 mt-0.5">
										<ReevuLogo className="h-3.5 w-3.5" />
									</div>
									<div className="flex items-center gap-1.5 pt-1.5">
										<span className="w-1.5 h-1.5 rounded-full bg-prakruti-patta/70 animate-[pulse_1.4s_ease-in-out_infinite]" />
										<span className="w-1.5 h-1.5 rounded-full bg-prakruti-patta/70 animate-[pulse_1.4s_ease-in-out_0.2s_infinite]" />
										<span className="w-1.5 h-1.5 rounded-full bg-prakruti-patta/70 animate-[pulse_1.4s_ease-in-out_0.4s_infinite]" />
									</div>
								</div>
							)}
							<div ref={messagesEndRef} />
						</div>
					)}
				</div>

				<div className="px-4 py-1.5 border-t border-border/40 bg-transparent">
					<p className="flex items-center justify-center gap-1 text-[10px] text-muted-foreground">
						<Info className="h-2.5 w-2.5" />
						AI can make mistakes · Verify with a specialist
					</p>
				</div>

				<div className="px-3 pb-3 pt-2 bg-transparent">
					<div className={cn(
						'flex items-end gap-1.5 rounded-xl border bg-background/50 backdrop-blur-md px-3 py-2 transition-colors',
						'border-border',
						'focus-within:border-prakruti-patta-light focus-within:ring-1 focus-within:ring-prakruti-patta/50'
					)}>
						<button
							onClick={voice.isListening ? voice.stopListening : voice.startListening}
							className={cn(
								'flex-shrink-0 p-1.5 rounded-lg transition-all',
								voice.isListening
									? 'text-red-500 bg-red-50 dark:bg-red-950/30 animate-pulse'
									: 'text-muted-foreground hover:text-foreground hover:bg-muted'
							)}
							title={voice.isListening ? 'Stop' : 'Voice input'}
						>
							{voice.isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
						</button>

						<textarea
							ref={inputRef}
							value={input}
							onChange={handleInputChange}
							onKeyDown={handleKeyDown}
							placeholder={voice.isListening ? 'Listening…' : 'Ask REEVU…'}
							rows={1}
							className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none leading-5 py-1 max-h-[120px]"
						/>

						<button
							onClick={() => { sendMessage(); if (inputRef.current) inputRef.current.style.height = 'auto' }}
							disabled={!input.trim() || isProcessing}
							className={cn(
								'flex-shrink-0 p-1.5 rounded-lg transition-all',
								input.trim() && !isProcessing
									? 'text-white bg-prakruti-patta hover:bg-prakruti-patta-dark shadow-sm'
									: 'text-muted-foreground cursor-not-allowed'
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

function MessageBubble({ message }: { message: ReevuMessage }) {
	const isUser = message.role === 'user'

	if (isUser) {
		return (
			<div className="flex justify-end">
				<div className="max-w-[80%] rounded-2xl rounded-br-md px-3.5 py-2.5 bg-prakruti-patta text-white shadow-sm">
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
			<div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted flex-shrink-0 mt-0.5">
				<ReevuLogo className="h-3.5 w-3.5" />
			</div>
			<div className="min-w-0 flex-1">
				<div className="reevu-markdown text-[13px] leading-relaxed text-foreground">
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
									<code className="bg-muted px-1 py-0.5 rounded text-xs font-mono text-prakruti-patta-dark">{children}</code>
								) : (
									<code className="block bg-muted p-2.5 rounded-lg text-xs font-mono overflow-x-auto my-2">{children}</code>
								)
							},
							pre: ({ children }) => <pre className="bg-muted p-2.5 rounded-lg text-xs overflow-x-auto my-2">{children}</pre>,
							table: ({ children }) => (
								<div className="overflow-x-auto my-2 rounded-lg border border-border">
									<table className="min-w-full text-xs">{children}</table>
								</div>
							),
							thead: ({ children }) => <thead className="bg-muted/50">{children}</thead>,
							tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
							tr: ({ children }) => <tr>{children}</tr>,
							th: ({ children }) => <th className="px-2.5 py-1.5 text-left font-semibold text-muted-foreground">{children}</th>,
							td: ({ children }) => <td className="px-2.5 py-1.5">{children}</td>,
							a: ({ href, children }) => (
								<a href={href} target="_blank" rel="noopener noreferrer" className="text-prakruti-patta underline decoration-prakruti-patta/50 hover:decoration-prakruti-patta transition-colors">
									{children}
								</a>
							),
							strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
							em: ({ children }) => <em className="italic">{children}</em>,
							blockquote: ({ children }) => (
								<blockquote className="border-l-2 border-prakruti-patta/50 pl-3 my-2 text-muted-foreground">{children}</blockquote>
							),
							hr: () => <hr className="my-3 border-border" />,
						}}
					>
						{message.content}
					</ReactMarkdown>
				</div>

				{message.metadata?.provider && (
					<p className="text-[9px] text-muted-foreground mt-1">
						{message.metadata.provider}{message.metadata.model ? ` · ${message.metadata.model}` : ''}
					</p>
				)}

				{message.metadata?.sources && message.metadata.sources.length > 0 && (
					<div className="flex flex-wrap gap-1 mt-1.5">
						{message.metadata.sources.slice(0, 3).map((source, i) => (
							<span key={i} className="text-[9px] px-1.5 py-0.5 bg-muted text-muted-foreground rounded-md">
								{source.doc_type}: {source.title || source.doc_id}
							</span>
						))}
					</div>
				)}

				{message.metadata?.evidence_envelope && (
					<EvidenceTraceCard envelope={message.metadata.evidence_envelope} />
				)}

				{(message.metadata?.retrieval_audit || message.metadata?.plan_execution_summary) && (
					<ReevuExecutionTraceCard
						retrievalAudit={message.metadata?.retrieval_audit}
						planExecutionSummary={message.metadata?.plan_execution_summary}
					/>
				)}

				{message.metadata?.safe_failure && (
					<ReevuSafeFailureCard safeFailure={message.metadata.safe_failure} />
				)}

				<span className="text-[9px] text-muted-foreground block mt-1">
					{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
				</span>
			</div>
		</div>
	)
}

export default ReevuSidebar
