import { forwardRef, useCallback, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import {
	ArrowUp,
	BrainCircuit,
	CheckCircle2,
	FileText,
	GitCompareArrows,
	Mic,
	MicOff,
	Paperclip,
	Search,
	ShieldCheck,
	Sparkles,
	X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ReevuAgentMode, ReevuAttachment } from '@/hooks/useReevuChat'

interface ReevuComposerVoice {
	isListening: boolean
	startListening: () => void
	stopListening: () => void
	isSupported?: boolean
	error?: string | null
}

interface ReevuComposerProps {
	input: string
	setInput: (value: string) => void
	isProcessing: boolean
	onSend: () => void | Promise<void>
	voice: ReevuComposerVoice
	agentMode: ReevuAgentMode
	onAgentModeChange: (mode: ReevuAgentMode) => void
	attachments: ReevuAttachment[]
	onAttachFiles: (files: FileList | File[]) => void | Promise<void>
	onRemoveAttachment: (attachmentId: string) => void
	placeholder?: string
	compact?: boolean
}

const AGENT_MODES: Array<{
	value: ReevuAgentMode
	label: string
	description: string
	icon: typeof Sparkles
}> = [
	{
		value: 'auto',
		label: 'Auto',
		description: 'Let REEVU route the task',
		icon: Sparkles,
	},
	{
		value: 'research',
		label: 'Research',
		description: 'Gather evidence and context',
		icon: Search,
	},
	{
		value: 'compare',
		label: 'Compare',
		description: 'Contrast options and tradeoffs',
		icon: GitCompareArrows,
	},
	{
		value: 'validate',
		label: 'Validate',
		description: 'Check assumptions and risk',
		icon: CheckCircle2,
	},
]

function formatBytes(size: number): string {
	if (size < 1024) return `${size} B`
	if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
	return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

export const ReevuComposer = forwardRef<HTMLTextAreaElement, ReevuComposerProps>(
	function ReevuComposer({
		input,
		setInput,
		isProcessing,
		onSend,
		voice,
		agentMode,
		onAgentModeChange,
		attachments,
		onAttachFiles,
		onRemoveAttachment,
		placeholder = 'Ask REEVU to reason, compare, validate, or analyze attached context...',
		compact = false,
	}, forwardedRef) {
		const fileInputRef = useRef<HTMLInputElement>(null)
		const textareaRef = useRef<HTMLTextAreaElement | null>(null)
		const [isDragging, setIsDragging] = useState(false)
		const canSend = (input.trim().length > 0 || attachments.length > 0) && !isProcessing

		const setTextareaRef = useCallback((node: HTMLTextAreaElement | null) => {
			textareaRef.current = node
			if (typeof forwardedRef === 'function') {
				forwardedRef(node)
			} else if (forwardedRef) {
				forwardedRef.current = node
			}
		}, [forwardedRef])

		useEffect(() => {
			const textarea = textareaRef.current
			if (!textarea) return
			textarea.style.height = 'auto'
			textarea.style.height = `${Math.min(textarea.scrollHeight, compact ? 120 : 168)}px`
		}, [compact, input])

		const handleFiles = useCallback((files: FileList | null) => {
			if (!files || files.length === 0) return
			void onAttachFiles(files)
		}, [onAttachFiles])

		const handleSend = useCallback(() => {
			if (!canSend) return
			void onSend()
		}, [canSend, onSend])

		const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
			if (event.key === 'Enter' && !event.shiftKey) {
				event.preventDefault()
				handleSend()
			}
		}

		return (
			<div
				className={cn(
					'rounded-[1.35rem] border bg-white/85 shadow-[0_22px_60px_-32px_rgba(15,23,42,0.75)] backdrop-blur-xl transition-all dark:bg-slate-950/85',
					'border-slate-200/80 dark:border-slate-800/80',
					'focus-within:border-emerald-300 focus-within:ring-2 focus-within:ring-emerald-100 dark:focus-within:border-emerald-800 dark:focus-within:ring-emerald-950',
					isDragging && 'border-emerald-400 bg-emerald-50/80 ring-2 ring-emerald-200 dark:bg-emerald-950/20 dark:ring-emerald-900',
				)}
				onDragEnter={(event) => {
					event.preventDefault()
					setIsDragging(true)
				}}
				onDragOver={(event) => {
					event.preventDefault()
					setIsDragging(true)
				}}
				onDragLeave={(event) => {
					event.preventDefault()
					setIsDragging(false)
				}}
				onDrop={(event) => {
					event.preventDefault()
					setIsDragging(false)
					handleFiles(event.dataTransfer.files)
				}}
			>
				<input
					ref={fileInputRef}
					type="file"
					multiple
					accept=".csv,.json,.md,.txt,.tsv,.yaml,.yml,.pdf,.xlsx,.xls"
					className="sr-only"
					aria-label="Attach files to REEVU"
					onChange={(event) => {
						handleFiles(event.currentTarget.files)
						event.currentTarget.value = ''
					}}
				/>

				<div className={cn('border-b border-slate-100 px-3 pt-3 dark:border-slate-800/80', compact ? 'pb-2' : 'pb-2.5')}>
					<div className="mb-2 flex items-center justify-between gap-2">
						<div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">
							<BrainCircuit className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
							Agent mode
						</div>
						<button
							type="button"
							onClick={() => fileInputRef.current?.click()}
							className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600 transition-colors hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-emerald-900 dark:hover:bg-emerald-950/40"
						>
							<Paperclip className="h-3.5 w-3.5" />
							Attach
						</button>
					</div>

					<div className={cn(compact ? 'grid grid-cols-2 gap-1.5' : 'flex flex-wrap gap-1.5')}>
						{AGENT_MODES.map(mode => {
							const Icon = mode.icon
							const selected = mode.value === agentMode
							return (
								<button
									key={mode.value}
									type="button"
									onClick={() => onAgentModeChange(mode.value)}
									className={cn(
										'group inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[11px] font-medium transition-all',
										selected
											? 'border-emerald-300 bg-emerald-50 text-emerald-800 shadow-sm dark:border-emerald-800 dark:bg-emerald-950/45 dark:text-emerald-200'
											: 'border-slate-200 bg-white/70 text-slate-500 hover:border-slate-300 hover:bg-slate-50 hover:text-slate-700 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400 dark:hover:border-slate-700 dark:hover:text-slate-200',
									)}
									aria-pressed={selected}
									title={mode.description}
								>
									<Icon className={cn('h-3.5 w-3.5', selected ? 'text-emerald-600 dark:text-emerald-300' : 'text-slate-400')} />
									{mode.label}
								</button>
							)
						})}
					</div>
				</div>

				{attachments.length > 0 && (
					<div className="flex flex-wrap gap-1.5 border-b border-slate-100 px-3 py-2 dark:border-slate-800/80">
						{attachments.map(attachment => (
							<div
								key={attachment.id}
								className="group inline-flex max-w-full items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
								title={`${attachment.name} (${formatBytes(attachment.size)})`}
							>
								<FileText className={cn(
									'h-3.5 w-3.5 flex-shrink-0',
									attachment.status === 'ready' ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-500',
								)} />
								<span className="max-w-[11rem] truncate">{attachment.name}</span>
								<span className="text-slate-400">{formatBytes(attachment.size)}</span>
								{attachment.status === 'metadata_only' && (
									<span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
										Metadata
									</span>
								)}
								<button
									type="button"
									onClick={() => onRemoveAttachment(attachment.id)}
									className="rounded-full p-0.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-100"
									aria-label={`Remove ${attachment.name}`}
								>
									<X className="h-3 w-3" />
								</button>
							</div>
						))}
					</div>
				)}

				<div className="flex items-end gap-2 px-3 py-2.5">
					<button
						type="button"
						onClick={voice.isListening ? voice.stopListening : voice.startListening}
						disabled={voice.isSupported === false}
						className={cn(
							'flex-shrink-0 rounded-xl p-2 transition-all',
							voice.isListening
								? 'bg-red-50 text-red-500 shadow-sm dark:bg-red-950/30'
								: 'text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200',
							voice.isSupported === false && 'cursor-not-allowed opacity-40',
						)}
						title={voice.isListening ? 'Stop voice input' : 'Voice input'}
					>
						{voice.isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
					</button>

					<textarea
						ref={setTextareaRef}
						value={input}
						onChange={(event) => setInput(event.target.value)}
						onKeyDown={handleKeyDown}
						placeholder={voice.isListening ? 'Listening...' : placeholder}
						rows={1}
						className={cn(
							'max-h-[168px] min-h-[2.25rem] flex-1 resize-none bg-transparent py-2 text-sm leading-5 text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-600',
							compact && 'max-h-[120px] text-[13px]',
						)}
					/>

					<button
						type="button"
						onClick={handleSend}
						disabled={!canSend}
						title="Send message to REEVU"
						aria-label="Send message to REEVU"
						className={cn(
							'flex-shrink-0 rounded-xl p-2 transition-all',
							canSend
								? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/10 hover:bg-emerald-700'
								: 'cursor-not-allowed text-slate-300 dark:text-slate-700',
						)}
					>
						<ArrowUp className="h-4 w-4" />
					</button>
				</div>

				<div className="flex flex-wrap items-center justify-between gap-1.5 px-3 pb-2.5 text-[10px] text-slate-400 dark:text-slate-600">
					<span>Enter to send. Shift+Enter for new line.</span>
					<span className="inline-flex items-center gap-1">
						<ShieldCheck className="h-3 w-3" />
						Files are task context, not trusted evidence.
					</span>
				</div>
				{voice.error && (
					<p className="px-3 pb-2 text-[10px] text-red-500">{voice.error}</p>
				)}
			</div>
		)
	},
)
