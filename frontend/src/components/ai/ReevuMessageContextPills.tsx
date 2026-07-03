import { FileText, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ReevuMessage } from '@/hooks/useReevuChat'
import type { ReevuAgentMode } from '@/lib/reevu-ui-context'

const MODE_LABELS: Record<ReevuAgentMode, string> = {
	auto: 'Auto',
	research: 'Research',
	compare: 'Compare',
	validate: 'Validate',
}

function formatBytes(size: number): string {
	if (size < 1024) return `${size} B`
	if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
	return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

interface ReevuMessageContextPillsProps {
	metadata?: ReevuMessage['metadata']
	compact?: boolean
	className?: string
}

export function ReevuMessageContextPills({
	metadata,
	compact = false,
	className,
}: ReevuMessageContextPillsProps) {
	const attachments = metadata?.attachments ?? []
	const mode = metadata?.agent_mode
	const visibleAttachments = attachments.slice(0, compact ? 2 : 4)
	const hiddenAttachmentCount = Math.max(attachments.length - visibleAttachments.length, 0)

	if ((!mode || mode === 'auto') && attachments.length === 0) {
		return null
	}

	return (
		<div className={cn('mt-2 flex flex-wrap gap-1.5', className)}>
			{mode && mode !== 'auto' && (
				<span className="inline-flex max-w-full items-center gap-1 rounded-full border border-white/25 bg-white/15 px-2 py-0.5 text-[10px] font-medium text-white/90">
					<Sparkles className="h-3 w-3 flex-shrink-0" />
					{MODE_LABELS[mode]} mode
				</span>
			)}
			{visibleAttachments.map(attachment => (
				<span
					key={attachment.id}
					className="inline-flex max-w-full items-center gap-1 rounded-full border border-white/25 bg-white/15 px-2 py-0.5 text-[10px] font-medium text-white/90"
					title={`${attachment.name} (${formatBytes(attachment.size)})`}
				>
					<FileText className="h-3 w-3 flex-shrink-0" />
					<span className="truncate">{attachment.name}</span>
				</span>
			))}
			{hiddenAttachmentCount > 0 && (
				<span className="inline-flex items-center rounded-full border border-white/25 bg-white/15 px-2 py-0.5 text-[10px] font-medium text-white/90">
					+{hiddenAttachmentCount} more
				</span>
			)}
		</div>
	)
}

