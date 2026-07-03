import { useMemo, useState, type ReactNode } from 'react'
import {
  Activity,
  AlertTriangle,
  Archive,
  CheckCircle2,
  Circle,
  Clock,
  Database,
  FileText,
  GitBranch,
  Layers,
  Lock,
  Play,
  ShieldCheck,
  Upload,
  Wrench,
} from 'lucide-react'

import ReevuRunTimelineCard from '@/components/ai/ReevuRunTimelineCard'
import type {
  ReevuApprovalGate,
  ReevuArtifact,
  ReevuDomainExpertLane,
  ReevuToolCallCard,
  ReevuToolDefinition,
  ReevuTrustState,
  ReevuWorkbenchState,
} from '@/lib/reevu-workbench'
import { cn } from '@/lib/utils'

interface ReevuWorkbenchPanelProps {
  state: ReevuWorkbenchState
}

function formatLabel(value: string): string {
  return value
    .replace(/[._-]/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase())
}

function formatDuration(durationMs?: number): string {
  if (typeof durationMs !== 'number') {
    return 'pending'
  }

  if (durationMs >= 1000) {
    return `${(durationMs / 1000).toFixed(1)}s`
  }

  return `${Math.round(durationMs)}ms`
}

function trustClasses(state: ReevuTrustState): string {
  switch (state) {
    case 'trusted':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300'
    case 'partial':
      return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/70 dark:bg-sky-950/30 dark:text-sky-300'
    case 'user_provided':
      return 'border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900/70 dark:bg-blue-950/30 dark:text-blue-300'
    case 'missing_authority':
      return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/30 dark:text-rose-300'
    case 'requires_review':
      return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-200'
    case 'model_synthesis':
    default:
      return 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-300'
  }
}

function statusClasses(status: string): string {
  const normalized = status.toLowerCase()

  if (normalized.includes('completed') || normalized.includes('reviewed')) {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-300'
  }

  if (normalized.includes('failed') || normalized.includes('missing')) {
    return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/70 dark:bg-rose-950/30 dark:text-rose-300'
  }

  if (normalized.includes('required') || normalized.includes('pending') || normalized.includes('review')) {
    return 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/30 dark:text-amber-200'
  }

  if (normalized.includes('started') || normalized.includes('active')) {
    return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/70 dark:bg-sky-950/30 dark:text-sky-300'
  }

  return 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-300'
}

function StatusIcon({ status }: { status: string }) {
  const normalized = status.toLowerCase()

  if (normalized.includes('completed') || normalized.includes('reviewed')) {
    return <CheckCircle2 className="h-3.5 w-3.5" />
  }

  if (normalized.includes('failed') || normalized.includes('missing')) {
    return <AlertTriangle className="h-3.5 w-3.5" />
  }

  if (normalized.includes('started') || normalized.includes('active')) {
    return <Activity className="h-3.5 w-3.5" />
  }

  return <Circle className="h-3.5 w-3.5" />
}

function PanelSection({
  title,
  eyebrow,
  icon,
  children,
  className,
}: {
  title: string
  eyebrow?: string
  icon: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cn(
      'rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm shadow-slate-900/[0.03] backdrop-blur dark:border-slate-800/80 dark:bg-slate-950/60',
      className,
    )}>
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-emerald-200/70 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
          {icon}
        </div>
        <div className="min-w-0">
          {eyebrow && (
            <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">
              {eyebrow}
            </p>
          )}
          <h2 className="text-sm font-semibold text-slate-950 dark:text-slate-100">{title}</h2>
        </div>
      </div>
      {children}
    </section>
  )
}

function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-3 py-4 text-center text-xs leading-relaxed text-slate-500 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-400">
      {children}
    </div>
  )
}

function TrustBadge({ state }: { state: ReevuTrustState }) {
  return (
    <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-medium', trustClasses(state))}>
      {formatLabel(state)}
    </span>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 px-3 py-2 dark:border-slate-800 dark:bg-slate-900/50">
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">{value}</dd>
    </div>
  )
}

function CaseFileCard({ state }: { state: ReevuWorkbenchState }) {
  const caseFile = state.caseFile

  if (!caseFile) {
    return (
      <PanelSection title="Advisory Case File" eyebrow="Persistent memory" icon={<Archive className="h-4 w-4" />}>
        <EmptyState>Start a REEVU conversation to open a scoped agricultural decision case.</EmptyState>
      </PanelSection>
    )
  }

  return (
    <PanelSection title="Advisory Case File" eyebrow="Persistent memory" icon={<Archive className="h-4 w-4" />}>
      <div className="space-y-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-semibold', statusClasses(caseFile.status))}>
              {formatLabel(caseFile.status)}
            </span>
            <span className="text-[10px] text-slate-400 dark:text-slate-500">
              {new Date(caseFile.updatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <p className="mt-2 line-clamp-2 text-sm font-medium leading-snug text-slate-900 dark:text-slate-100">
            {caseFile.title}
          </p>
        </div>

        <dl className="grid grid-cols-2 gap-2">
          <Metric label="Messages" value={caseFile.messageCount} />
          <Metric label="Runs" value={caseFile.runCount} />
          <Metric label="Evidence" value={caseFile.evidenceSnapshotCount} />
          <Metric label="Artifacts" value={caseFile.artifactCount} />
        </dl>

        <div className="rounded-xl border border-amber-200/80 bg-amber-50/70 px-3 py-2 text-xs leading-relaxed text-amber-800 dark:border-amber-900/70 dark:bg-amber-950/20 dark:text-amber-200">
          Case files are resumable summaries of the decision trail. User uploads stay task context until formally ingested.
        </div>
      </div>
    </PanelSection>
  )
}

function DomainLaneCard({ lane }: { lane: ReevuDomainExpertLane }) {
  return (
    <article className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{lane.label}</h3>
          <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
            {lane.description}
          </p>
        </div>
        <span className={cn('flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium', statusClasses(lane.status))}>
          <StatusIcon status={lane.status} />
          {formatLabel(lane.status)}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <TrustBadge state={lane.trustState} />
        <span className="rounded-full border border-slate-200 bg-white/80 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
          {lane.evidenceCount} records
        </span>
      </div>

      {lane.services.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {lane.services.slice(0, 3).map(service => (
            <span key={service} className="rounded-md bg-white px-1.5 py-0.5 text-[10px] text-slate-500 dark:bg-slate-950/60 dark:text-slate-400">
              {service}
            </span>
          ))}
        </div>
      )}

      {lane.missingReason && (
        <p className="mt-2 text-[11px] leading-relaxed text-amber-700 dark:text-amber-300">
          {lane.missingReason}
        </p>
      )}
    </article>
  )
}

function ToolCallCard({ tool }: { tool: ReevuToolCallCard }) {
  return (
    <article className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">{tool.displayName}</h3>
          <p className="mt-1 truncate text-[11px] text-slate-500 dark:text-slate-400">{tool.rawName}</p>
        </div>
        <span className={cn('flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium', statusClasses(tool.status))}>
          <StatusIcon status={tool.status} />
          {formatLabel(tool.status)}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
        <div className="rounded-lg bg-white/80 px-2 py-1.5 dark:bg-slate-950/60">
          <span className="text-slate-400">Duration</span>
          <div className="font-medium text-slate-700 dark:text-slate-200">{formatDuration(tool.durationMs)}</div>
        </div>
        <div className="rounded-lg bg-white/80 px-2 py-1.5 dark:bg-slate-950/60">
          <span className="text-slate-400">Records</span>
          <div className="font-medium text-slate-700 dark:text-slate-200">{tool.recordsTouched ?? 0}</div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <TrustBadge state={tool.trustState} />
        <span className="rounded-full border border-slate-200 bg-white/80 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
          {formatLabel(tool.authorityLevel)}
        </span>
        {tool.resultType && (
          <span className="rounded-full border border-slate-200 bg-white/80 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
            {formatLabel(tool.resultType)}
          </span>
        )}
      </div>
    </article>
  )
}

function ApprovalCard({ gate }: { gate: ReevuApprovalGate }) {
  const [localStatus, setLocalStatus] = useState(gate.status)

  return (
    <article className="rounded-xl border border-amber-200/80 bg-amber-50/70 p-3 dark:border-amber-900/70 dark:bg-amber-950/20">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-amber-950 dark:text-amber-100">{gate.title}</h3>
          <p className="mt-1 text-xs leading-relaxed text-amber-800 dark:text-amber-200">{gate.reason}</p>
        </div>
        <Lock className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-300" />
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className={cn('rounded-full border px-2 py-0.5 text-[10px] font-medium', statusClasses(localStatus))}>
          {formatLabel(localStatus)}
        </span>
        <span className="rounded-full border border-amber-200 bg-white/70 px-2 py-0.5 text-[10px] text-amber-800 dark:border-amber-900/70 dark:bg-slate-950/40 dark:text-amber-200">
          {formatLabel(gate.kind)}
        </span>
        <TrustBadge state={gate.trustState} />
      </div>
      {gate.toolDisplayName && (
        <p className="mt-2 font-mono text-[11px] text-amber-800/80 dark:text-amber-200/80">{gate.toolDisplayName}</p>
      )}
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => setLocalStatus('reviewed')}
          className="rounded-lg border border-emerald-200 bg-white/90 px-2 py-1.5 text-[11px] font-medium text-emerald-700 transition hover:bg-emerald-50 dark:border-emerald-900/70 dark:bg-slate-950/50 dark:text-emerald-300"
        >
          Mark reviewed
        </button>
        <button
          type="button"
          onClick={() => setLocalStatus('escalated')}
          className="rounded-lg border border-amber-300 bg-white/90 px-2 py-1.5 text-[11px] font-medium text-amber-800 transition hover:bg-amber-100 dark:border-amber-900/70 dark:bg-slate-950/50 dark:text-amber-200"
        >
          Escalate
        </button>
      </div>
    </article>
  )
}

function ArtifactRow({ artifact }: { artifact: ReevuArtifact }) {
  const Icon = artifact.source === 'user' ? Upload : FileText

  return (
    <article className="flex gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-slate-500 dark:bg-slate-950/60 dark:text-slate-300">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <h3 className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{artifact.title}</h3>
          <TrustBadge state={artifact.trustState} />
        </div>
        <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{artifact.detail}</p>
        <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-400 dark:text-slate-500">
          {formatLabel(artifact.kind)} / {formatLabel(artifact.source)}
        </p>
      </div>
    </article>
  )
}

function ToolRegistryRow({ tool }: { tool: ReevuToolDefinition }) {
  return (
    <article className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-mono text-xs font-semibold text-slate-900 dark:text-slate-100">{tool.displayName}</h3>
          <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{tool.description}</p>
        </div>
        <Database className="h-4 w-4 shrink-0 text-slate-400" />
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <TrustBadge state={tool.trustState} />
        <span className="rounded-full border border-slate-200 bg-white/80 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
          {formatLabel(tool.category)}
        </span>
        <span className="rounded-full border border-slate-200 bg-white/80 px-2 py-0.5 text-[10px] text-slate-500 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-400">
          {tool.permissions.join(', ')}
        </span>
      </div>
    </article>
  )
}

export function ReevuWorkbenchPanel({ state }: ReevuWorkbenchPanelProps) {
  const latestEnvelope = state.latestAssistant?.metadata?.evidence_envelope
  const safeFailure = state.latestAssistant?.metadata?.safe_failure
  const activeLanes = useMemo(
    () => state.domainLanes.filter(lane => lane.status !== 'idle'),
    [state.domainLanes],
  )

  return (
    <div className="space-y-4 p-4">
      <div className="rounded-[1.35rem] border border-emerald-200/70 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.16),_transparent_34%),linear-gradient(135deg,_rgba(255,255,255,0.94),_rgba(248,250,252,0.74))] p-4 shadow-sm dark:border-emerald-900/50 dark:bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.20),_transparent_34%),linear-gradient(135deg,_rgba(2,6,23,0.94),_rgba(15,23,42,0.74))]">
        <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-emerald-700 dark:text-emerald-300">
          REEVU Workbench
        </p>
        <h1 className="mt-2 text-lg font-semibold tracking-tight text-slate-950 dark:text-slate-50">
          Agentic command surface
        </h1>
        <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
          Conversation, expert lanes, tools, evidence, approvals, and artifacts stay visible as one scoped decision case.
        </p>
      </div>

      <CaseFileCard state={state} />

      <PanelSection title="Live Reasoning Timeline" eyebrow="ReevuRun protocol" icon={<Activity className="h-4 w-4" />}>
        {state.runEvents.length > 0 ? (
          <div className="[&>div]:mb-0">
            <ReevuRunTimelineCard events={state.runEvents} />
          </div>
        ) : (
          <EmptyState>Run events will appear here as REEVU plans, calls tools, validates evidence, and completes the turn.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="Domain Expert Lanes" eyebrow="Multi-expert synthesis" icon={<GitBranch className="h-4 w-4" />}>
        <div className="space-y-2">
          {(activeLanes.length > 0 ? activeLanes : state.domainLanes).map(lane => (
            <DomainLaneCard key={lane.id} lane={lane} />
          ))}
        </div>
      </PanelSection>

      <PanelSection title="Domain Tool Calls" eyebrow="Auditable connectors" icon={<Wrench className="h-4 w-4" />}>
        {state.toolCalls.length > 0 ? (
          <div className="space-y-2">
            {state.toolCalls.map(tool => <ToolCallCard key={tool.id} tool={tool} />)}
          </div>
        ) : (
          <EmptyState>No deterministic tool calls in the current turn yet.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="Approval Gates" eyebrow="Human control" icon={<ShieldCheck className="h-4 w-4" />}>
        {state.approvalGates.length > 0 ? (
          <div className="space-y-2">
            {state.approvalGates.map(gate => <ApprovalCard key={gate.id} gate={gate} />)}
          </div>
        ) : (
          <EmptyState>High-impact actions will request explicit review here before operational use.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="Evidence Packet" eyebrow="Traceable authority" icon={<Layers className="h-4 w-4" />}>
        {latestEnvelope ? (
          <div className="grid grid-cols-2 gap-2">
            <Metric label="Claims" value={latestEnvelope.claims.length} />
            <Metric label="Evidence refs" value={latestEnvelope.evidence_refs.length} />
            <Metric label="Calculations" value={latestEnvelope.calculation_steps.length} />
            <Metric label="Gaps" value={(latestEnvelope.missing_evidence_signals ?? []).length + (latestEnvelope.uncertainty?.missing_data?.length ?? 0)} />
          </div>
        ) : (
          <EmptyState>Evidence snapshots attach after synthesis and validation.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="Safe-Failure Panel" eyebrow="Guardrails" icon={<AlertTriangle className="h-4 w-4" />}>
        {safeFailure ? (
          <div className="space-y-3 text-xs leading-relaxed">
            <div className="rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-rose-800 dark:border-rose-900/70 dark:bg-rose-950/20 dark:text-rose-200">
              <p className="font-semibold">{formatLabel(safeFailure.error_category)}</p>
              <p className="mt-1">REEVU stopped instead of guessing because authority or context was incomplete.</p>
            </div>
            <div>
              <p className="font-semibold text-slate-700 dark:text-slate-200">Next steps</p>
              <ul className="mt-1 space-y-1 text-slate-500 dark:text-slate-400">
                {safeFailure.next_steps.map(step => <li key={step}>{step}</li>)}
              </ul>
            </div>
          </div>
        ) : (
          <EmptyState>No safe-failure active for the latest turn.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="Scoped Artifacts" eyebrow="Files and outputs" icon={<FileText className="h-4 w-4" />}>
        {state.artifacts.length > 0 ? (
          <div className="space-y-2">
            {state.artifacts.map(artifact => <ArtifactRow key={artifact.id} artifact={artifact} />)}
          </div>
        ) : (
          <EmptyState>Uploads, evidence packets, summaries, comparisons, drafts, and recommendations become scoped artifacts here.</EmptyState>
        )}
      </PanelSection>

      <PanelSection title="REEVU Playbooks" eyebrow="Domain workflows" icon={<Play className="h-4 w-4" />}>
        <div className="space-y-2">
          {state.playbooks.map(playbook => (
            <article key={playbook.id} className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{playbook.title}</h3>
                  <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{playbook.description}</p>
                </div>
                <TrustBadge state={playbook.trustState} />
              </div>
              <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">{playbook.triggerHint}</p>
            </article>
          ))}
        </div>
      </PanelSection>

      <PanelSection title="Connector Registry" eyebrow="Discoverable tools" icon={<Database className="h-4 w-4" />}>
        <div className="space-y-2">
          {state.toolRegistry.map(tool => <ToolRegistryRow key={tool.id} tool={tool} />)}
        </div>
      </PanelSection>

      <PanelSection title="Trust Labels" eyebrow="Authority map" icon={<Lock className="h-4 w-4" />}>
        <div className="space-y-2">
          {state.trustStates.map(entry => (
            <article key={entry.state} className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3 dark:border-slate-800 dark:bg-slate-900/50">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{entry.label}</h3>
                <TrustBadge state={entry.state} />
              </div>
              <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{entry.description}</p>
            </article>
          ))}
        </div>
      </PanelSection>

      <div className="rounded-2xl border border-slate-200/80 bg-white/70 p-3 text-[11px] leading-relaxed text-slate-500 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400">
        <Clock className="mr-1 inline h-3.5 w-3.5" />
        This panel is a live workbench view over the current conversation. Backend case persistence can replace local storage without changing the UI contract.
      </div>
    </div>
  )
}

export default ReevuWorkbenchPanel
