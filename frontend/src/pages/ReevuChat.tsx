/**
 * ReevuChat — Full-page REEVU Chat
 */

import { useRef } from 'react'
import * as React from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ReevuLogo } from '@/components/ai/ReevuTrigger'
import { ArrowLeft, Trash2, Settings, KeyRound, FlaskConical, Dna, BarChart3, TrendingUp, Wheat, Microscope, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useReevuChat, ReevuMessage } from '@/hooks/useReevuChat'
import { ProposalCard } from '@/components/ai/ProposalCard'
import { ProposalReviewModal } from '@/components/ai/ProposalReviewModal'
import { UsageFuelGauge } from '@/components/ai/UsageFuelGauge'
import EvidenceTraceCard from '@/components/ai/EvidenceTraceCard'
import ReevuExecutionTraceCard from '@/components/ai/ReevuExecutionTraceCard'
import ReevuSafeFailureCard from '@/components/ai/ReevuSafeFailureCard'
import { ReevuComposer } from '@/components/ai/ReevuComposer'
import { ReevuMessageContextPills } from '@/components/ai/ReevuMessageContextPills'
import ReevuRunTimelineCard from '@/components/ai/ReevuRunTimelineCard'
import ReevuWorkbenchPanel from '@/components/ai/ReevuWorkbenchPanel'
import { buildReevuWorkbenchState, persistReevuAdvisoryCaseFile } from '@/lib/reevu-workbench'

export function ReevuChat() {
	const navigate = useNavigate()

	const {
		messages,
		input,
		setInput,
		isProcessing,
		agentMode,
		setAgentMode,
		pendingAttachments,
		effectiveBackend,
		messagesEndRef,
		sendMessage,
		clearHistory,
		addAttachments,
		removeAttachment,
		voice
	} = useReevuChat()

	const [reviewProposalId, setReviewProposalId] = React.useState<number | null>(null)
	const inputRef = useRef<HTMLTextAreaElement>(null)
	const workbenchState = React.useMemo(() => buildReevuWorkbenchState(messages), [messages])

	React.useEffect(() => {
		try {
			persistReevuAdvisoryCaseFile(workbenchState.caseFile)
		} catch {
			// Local persistence is a convenience layer; REEVU should keep running if storage is unavailable.
		}
	}, [workbenchState.caseFile])

	const quickActions = [
		{ icon: FlaskConical, label: 'Active Trials', action: 'Show me active trials' },
		{ icon: BarChart3, label: 'Top Performers', action: 'Which germplasm has best yield?' },
		{ icon: Dna, label: 'Crossing Suggestions', action: 'Suggest crossing parents for disease resistance' },
		{ icon: TrendingUp, label: 'Genetic Gain', action: 'Calculate genetic gain for my program' },
		{ icon: Wheat, label: 'Variety Comparison', action: 'Compare top 5 varieties by yield' },
		{ icon: Microscope, label: 'QTL Analysis', action: 'Explain QTL mapping for beginners' },
	]

	return (
		<div className="flex flex-col h-[calc(100dvh-3rem)]">
			<div className="flex items-center justify-between px-4 h-12 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/60 dark:bg-slate-950/60 backdrop-blur-sm flex-shrink-0">
				<div className="flex items-center gap-3 min-w-0">
					<button
						onClick={() => navigate(-1)}
						className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors"
						title="Go back"
					>
						<ArrowLeft className="h-4 w-4" />
					</button>
					<ReevuLogo className="w-6 h-6 flex-shrink-0" />
					<div className="min-w-0">
						<div className="flex items-center gap-1.5">
							<h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">REEVU</h1>
							<div
								className={cn(
									'w-1.5 h-1.5 rounded-full flex-shrink-0',
									isProcessing
										? 'bg-amber-400 animate-pulse'
										: effectiveBackend.ready
											? 'bg-emerald-500'
											: 'bg-slate-300 dark:bg-slate-600'
								)}
							/>
						</div>
						<p className="text-[10px] tracking-wide text-slate-400 dark:text-slate-500 truncate" title={effectiveBackend.ready ? effectiveBackend.name : 'Not configured'}>
							Reason · Evidence · Evaluation · Validation · Unit
						</p>
					</div>
				</div>
				<div className="flex items-center gap-1">
					<UsageFuelGauge />
					<button
						onClick={clearHistory}
						className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors"
						title="Clear history"
					>
						<Trash2 className="h-3.5 w-3.5" />
					</button>
					<button
						onClick={() => navigate('/ai-settings')}
						className="p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-800 transition-colors"
						title="AI Settings"
					>
						<Settings className="h-3.5 w-3.5" />
					</button>
				</div>
			</div>

			{!effectiveBackend.ready && (
				<button
					onClick={() => navigate('/ai-settings')}
					className="flex items-center gap-2 px-4 py-2.5 bg-amber-50 dark:bg-amber-950/30 border-b border-amber-100 dark:border-amber-900/40 text-left group transition-colors hover:bg-amber-100/80 dark:hover:bg-amber-950/50"
				>
					<KeyRound className="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
					<span className="text-xs text-amber-700 dark:text-amber-400">Configure REEVU in AI Settings to enable a managed provider</span>
					<span className="text-xs text-amber-500 group-hover:text-amber-600 ml-auto flex-shrink-0">→</span>
				</button>
			)}

			<div className="min-h-0 flex-1 overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.08),_transparent_30%),linear-gradient(180deg,_rgba(248,250,252,0.86),_rgba(255,255,255,0.96))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.14),_transparent_30%),linear-gradient(180deg,_rgba(2,6,23,0.98),_rgba(15,23,42,0.98))]">
				<div className="grid h-full min-h-0 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_390px] xl:grid-cols-[minmax(0,1fr)_420px] 2xl:grid-cols-[minmax(0,1fr)_460px]">
					<section className="min-h-0 overflow-y-auto overscroll-contain">
						{messages.length === 0 ? (
							<div className="flex min-h-full flex-col items-center justify-center px-6 py-12">
								<div className="w-20 h-20 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 flex items-center justify-center mb-6">
									<ReevuLogo className="w-10 h-10 opacity-60" />
								</div>
								<h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-1">REEVU Agentic Workspace</h2>
								<p className="text-[10px] tracking-[0.15em] uppercase text-slate-400 dark:text-slate-500 mb-3">Reason · Evidence · Evaluation · Validation · Unit</p>
								<p className="text-sm text-slate-500 dark:text-slate-400 mb-8 text-center max-w-md">Ask a question, attach local context, or switch modes when you want REEVU to research, compare, or validate a decision path.</p>
								<div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-w-lg w-full">
									{quickActions.map((a) => (
										<button
											key={a.label}
											onClick={() => { setInput(a.action); inputRef.current?.focus() }}
											className="flex items-center gap-2 px-3 py-2.5 rounded-lg border border-slate-200 dark:border-slate-800 text-left text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
										>
											<a.icon className="h-3.5 w-3.5 text-slate-400 dark:text-slate-500 flex-shrink-0" />
											<span className="truncate">{a.label}</span>
										</button>
									))}
								</div>
							</div>
						) : (
							<div className="max-w-3xl mx-auto px-4 py-4 space-y-4">
								{messages.map((message) => (
									<MessageBubble
										key={message.id}
										message={message}
										onReview={(id) => setReviewProposalId(id)}
									/>
								))}
								{isProcessing && (
									<div className="flex items-start gap-2.5">
										<div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/40 flex-shrink-0 mt-0.5">
											<ReevuLogo className="h-4 w-4" />
										</div>
										<div className="flex items-center gap-1.5 pt-2">
											<span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_infinite]" />
											<span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_0.2s_infinite]" />
											<span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70 animate-[pulse_1.4s_ease-in-out_0.4s_infinite]" />
											<span className="text-xs text-slate-400 ml-1">Thinking…</span>
										</div>
									</div>
								)}
								<div ref={messagesEndRef} />
							</div>
						)}
					</section>

					<aside className="hidden min-h-0 overflow-y-auto border-l border-slate-200/80 bg-white/40 dark:border-slate-800/80 dark:bg-slate-950/40 lg:block">
						<ReevuWorkbenchPanel state={workbenchState} />
					</aside>
				</div>
			</div>

			{messages.length > 0 && (
				<div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800/80">
					<div className="max-w-3xl mx-auto flex gap-2 overflow-x-auto pb-0.5">
						{quickActions.map((a) => (
							<button
								key={a.label}
								onClick={() => { setInput(a.action); inputRef.current?.focus() }}
								className="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 text-[11px] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 rounded-full hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
							>
								<a.icon className="h-3 w-3" />
								{a.label}
							</button>
						))}
					</div>
				</div>
			)}

			<div className="px-4 py-1 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/50">
				<p className="flex items-center justify-center gap-1 text-[10px] text-slate-400 dark:text-slate-600">
					<Info className="h-2.5 w-2.5" />
					AI can make mistakes · Verify with a specialist
				</p>
			</div>

			<div className="px-4 pb-4 pt-2 bg-white dark:bg-slate-950">
				<div className="max-w-3xl mx-auto">
					<ReevuComposer
						ref={inputRef}
						input={input}
						setInput={setInput}
						isProcessing={isProcessing}
						onSend={sendMessage}
						voice={voice}
						agentMode={agentMode}
						onAgentModeChange={setAgentMode}
						attachments={pendingAttachments}
						onAttachFiles={addAttachments}
						onRemoveAttachment={removeAttachment}
					/>
				</div>
			</div>

			<ProposalReviewModal
				proposalId={reviewProposalId!}
				isOpen={!!reviewProposalId}
				onClose={() => setReviewProposalId(null)}
				onActionComplete={() => setReviewProposalId(null)}
			/>
		</div>
	)
}

function MessageBubble({ message, onReview }: { message: ReevuMessage, onReview?: (id: number) => void }) {
	const isUser = message.role === 'user'

	if (isUser) {
		return (
			<div className="flex justify-end">
				<div className="max-w-[75%] rounded-2xl rounded-br-md px-4 py-3 bg-emerald-600 text-white shadow-sm">
					<p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
					<ReevuMessageContextPills metadata={message.metadata} />
					<span className="text-[9px] opacity-60 block mt-1.5 text-right">
						{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
					</span>
				</div>
			</div>
		)
	}

	return (
		<div className="flex items-start gap-3">
			<div className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/40 flex-shrink-0 mt-0.5">
				<ReevuLogo className="h-4 w-4" />
			</div>
			<div className="min-w-0 flex-1">
				<div className="reevu-markdown text-sm leading-relaxed text-slate-800 dark:text-slate-200">
					<div className="lg:hidden">
						<ReevuRunTimelineCard events={message.metadata?.run_events} />
					</div>
					<ReactMarkdown
						remarkPlugins={[remarkGfm]}
						components={{
							h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1.5">{children}</h1>,
							h2: ({ children }) => <h2 className="text-sm font-bold mt-2.5 mb-1">{children}</h2>,
							h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-0.5">{children}</h3>,
							p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
							ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
							ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
							li: ({ children }) => React.createElement('li', { className: 'text-sm' }, children),
							code: ({ className, children }) => {
								const isInline = !className
								return isInline ? (
									<code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-xs font-mono text-emerald-700 dark:text-emerald-400">{children}</code>
								) : (
									<code className="block bg-slate-100 dark:bg-slate-800 p-3 rounded-lg text-xs font-mono overflow-x-auto my-2">{children}</code>
								)
							},
							pre: ({ children }) => <pre className="bg-slate-100 dark:bg-slate-800 p-3 rounded-lg text-xs overflow-x-auto my-2">{children}</pre>,
							table: ({ children }) => (
								<div className="overflow-x-auto my-2 rounded-lg border border-slate-200 dark:border-slate-700">
									<table className="min-w-full text-xs">{children}</table>
								</div>
							),
							thead: ({ children }) => <thead className="bg-slate-50 dark:bg-slate-800">{children}</thead>,
							tbody: ({ children }) => <tbody className="divide-y divide-slate-100 dark:divide-slate-800">{children}</tbody>,
							tr: ({ children }) => <tr>{children}</tr>,
							th: ({ children }) => <th className="px-3 py-2 text-left font-semibold text-slate-600 dark:text-slate-400">{children}</th>,
							td: ({ children }) => <td className="px-3 py-2">{children}</td>,
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

				{message.metadata?.provider && (
					<p className="text-[9px] text-slate-400 dark:text-slate-600 mt-1">
						{message.metadata.provider}{message.metadata.model ? ` · ${message.metadata.model}` : ''}
					</p>
				)}

				{message.metadata?.sources && message.metadata.sources.length > 0 && (
					<div className="flex flex-wrap gap-1 mt-1.5">
						{message.metadata.sources.slice(0, 5).map((source, i) => (
							<span key={i} className="text-[9px] px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-md">
								{source.doc_type}: {source.title || source.doc_id}
							</span>
						))}
					</div>
				)}

				<span className="text-[9px] text-slate-400 dark:text-slate-600 block mt-1">
					{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
				</span>

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

				{message.metadata?.proposal && onReview && (
					<ProposalCard
						proposal={message.metadata.proposal}
						onReview={onReview}
					/>
				)}
			</div>
		</div>
	)
}

export default ReevuChat
