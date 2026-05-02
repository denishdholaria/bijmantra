import { motion } from 'framer-motion'
import {
  Activity,
  ArrowRight,
  GitBranch,
  Radar,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TabsContent } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

import type {
  DeveloperControlPlaneAutonomyCycleResponse,
  DeveloperControlPlaneCloseoutReceiptResponse,
  DeveloperControlPlaneLearningEntryType,
  DeveloperControlPlaneLearningLedgerResponse,
  DeveloperControlPlaneMissionStateResponse,
  DeveloperControlPlaneOvernightQueueStatusResponse,
  DeveloperControlPlaneSilentMonitor,
  DeveloperControlPlaneSilentMonitorsResponse,
  DeveloperControlPlaneWatchdogStatusResponse,
} from '../../api/activeBoard'
import type {
  DeveloperBoardAutonomyAnalysis,
  DeveloperLaneAutonomyAnalysis,
} from '../../contracts/autonomy'
import type { DeveloperBoardLane } from '../../contracts/board'
import type { DeveloperControlPlanePersistenceStatus } from '../../state/selectors'
import { getSelectedLaneMissionSummary } from '../missionLinking'

type OverviewTabProps = {
  lanes: DeveloperBoardLane[]
  autonomyAnalysis: DeveloperBoardAutonomyAnalysis | null
  selectedLane: DeveloperBoardLane | null
  recommendedLane: DeveloperBoardLane | null
  persistenceStatus: DeveloperControlPlanePersistenceStatus
  lastUpdatedAt: string
  primaryOrchestrator: string | null
  agentRoleCount: number
  queueStatusState: 'idle' | 'loading' | 'ready' | 'error'
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null
  queueStatusError: string | null
  queueStatusLastRefreshedAt: string | null
  selectedLaneQueueJobId?: string | null
  closeoutReceiptState?: 'idle' | 'loading' | 'available' | 'missing' | 'error'
  closeoutReceiptRecord?: DeveloperControlPlaneCloseoutReceiptResponse | null
  runtimeWatchdogState: 'idle' | 'loading' | 'ready' | 'error'
  runtimeWatchdogRecord: DeveloperControlPlaneWatchdogStatusResponse | null
  runtimeWatchdogError: string | null
  runtimeWatchdogLastCheckedAt: string | null
  runtimeAutonomyCycleState?: 'idle' | 'loading' | 'ready' | 'missing' | 'error'
  runtimeAutonomyCycleRecord?: DeveloperControlPlaneAutonomyCycleResponse | null
  runtimeAutonomyCycleLastCheckedAt?: string | null
  silentMonitorsState?: 'idle' | 'loading' | 'ready' | 'error'
  silentMonitorsRecord?: DeveloperControlPlaneSilentMonitorsResponse | null
  silentMonitorsError?: string | null
  silentMonitorsLastCheckedAt?: string | null
  missionStateState: 'idle' | 'loading' | 'ready' | 'error'
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
  missionStateError: string | null
  missionStateLastCheckedAt: string | null
  learningLedgerState?: 'idle' | 'loading' | 'ready' | 'error'
  learningLedgerRecord?: DeveloperControlPlaneLearningLedgerResponse | null
  learningLedgerError?: string | null
  learningLedgerLastCheckedAt?: string | null
  learningLedgerQuery?: OverviewLearningLedgerQuery
  onRefreshQueueStatus: () => Promise<unknown> | void
  onRefreshLearnings?: (query?: OverviewLearningLedgerQuery) => Promise<unknown> | void
  onSetActiveTab: (value: string) => void
  onSelectLane: (laneId: string) => void
}

type OverviewLearningLedgerQuery = {
  limit?: number
  entryType?: DeveloperControlPlaneLearningEntryType | null
  sourceClassification?: string | null
  sourceLaneId?: string | null
  queueJobId?: string | null
  linkedMissionId?: string | null
}

type ClusterStatus = DeveloperBoardLane['status']
type SourceTruthKind = 'shared-backend' | 'tracked-artifact' | 'browser-fallback'

const STATUS_ORDER: ClusterStatus[] = ['active', 'planned', 'watch', 'blocked', 'completed']

const SOURCE_TRUTH_META: Record<
  SourceTruthKind,
  {
    label: string
    className: string
  }
> = {
  'shared-backend': {
    label: 'Shared backend',
    className: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
  },
  'tracked-artifact': {
    label: 'Tracked artifact',
    className: 'border-cyan-300/25 bg-cyan-300/10 text-cyan-100',
  },
  'browser-fallback': {
    label: 'Browser fallback',
    className: 'border-amber-300/25 bg-amber-300/10 text-amber-100',
  },
}

const STATUS_META: Record<
  ClusterStatus,
  {
    label: string
    description: string
    chipClassName: string
    accentClassName: string
    glowClassName: string
  }
> = {
  active: {
    label: 'Active cluster',
    description: 'Execution lanes currently moving with live ownership.',
    chipClassName: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-100',
    accentClassName: 'from-emerald-300 via-cyan-300 to-sky-400',
    glowClassName: 'bg-emerald-300/25',
  },
  planned: {
    label: 'Planned cluster',
    description: 'Defined lanes queued for activation and dispatch.',
    chipClassName: 'border-sky-400/30 bg-sky-400/10 text-sky-100',
    accentClassName: 'from-sky-300 via-cyan-300 to-blue-400',
    glowClassName: 'bg-sky-300/25',
  },
  watch: {
    label: 'Watch cluster',
    description: 'Lanes being monitored for the next valid window.',
    chipClassName: 'border-amber-300/30 bg-amber-300/10 text-amber-50',
    accentClassName: 'from-amber-200 via-orange-300 to-yellow-300',
    glowClassName: 'bg-amber-300/25',
  },
  blocked: {
    label: 'Blocked cluster',
    description: 'Dependency or contract drift is stopping movement.',
    chipClassName: 'border-rose-400/30 bg-rose-400/10 text-rose-100',
    accentClassName: 'from-rose-300 via-fuchsia-300 to-orange-300',
    glowClassName: 'bg-rose-300/25',
  },
  completed: {
    label: 'Completed cluster',
    description: 'Closed lanes with recorded completion state.',
    chipClassName: 'border-violet-400/30 bg-violet-400/10 text-violet-100',
    accentClassName: 'from-violet-300 via-indigo-300 to-sky-300',
    glowClassName: 'bg-violet-300/25',
  },
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'Not sampled yet'
  }

  return new Date(value).toLocaleString()
}

function formatCompactState(state: 'idle' | 'loading' | 'ready' | 'error') {
  if (state === 'ready') {
    return 'Live'
  }

  if (state === 'loading') {
    return 'Refreshing'
  }

  if (state === 'error') {
    return 'Attention'
  }

  return 'Standby'
}

function formatWatchdogCompletionAssistSummary(
  advisory: DeveloperControlPlaneWatchdogStatusResponse['completion_assist_advisory']
) {
  if (!advisory) {
    return null
  }

  if (advisory.available && advisory.staged) {
    return advisory.source_lane_id
      ? `Completion assist advisory is staged for lane ${advisory.source_lane_id} and still needs explicit write-back review.`
      : 'Completion assist advisory is staged and still needs explicit write-back review.'
  }

  if (advisory.available) {
    return 'Completion assist advisory is present but not staged for write-back.'
  }

  return 'Completion assist advisory is currently idle.'
}

function formatLearningEntryTypeLabel(entryType: DeveloperControlPlaneLearningEntryType) {
  if (entryType === 'verification-learning') {
    return 'Verification'
  }

  if (entryType === 'pitfall') {
    return 'Pitfall'
  }

  if (entryType === 'incident') {
    return 'Incident'
  }

  return 'Pattern'
}

function formatLearningSourceLabel(sourceClassification: string) {
  return sourceClassification
    .split('-')
    .filter(Boolean)
    .map((segment) => segment[0]?.toUpperCase() + segment.slice(1))
    .join(' ')
}

function formatLearningConfidence(score: number | null) {
  if (score === null) {
    return null
  }

  const normalizedScore = score <= 1 ? Math.round(score * 100) : Math.round(score)
  return `${normalizedScore}% confidence`
}

function describeLearningLedgerScope(
  query: OverviewLearningLedgerQuery,
  selectedLane: DeveloperBoardLane | null,
  selectedLaneQueueJobId: string | null
) {
  if (query.queueJobId) {
    return query.queueJobId === selectedLaneQueueJobId
      ? 'Selected queue job'
      : `Queue job ${query.queueJobId}`
  }

  if (query.sourceLaneId) {
    return query.sourceLaneId === selectedLane?.id
      ? 'Selected lane'
      : `Lane ${query.sourceLaneId}`
  }

  if (query.entryType) {
    return `${formatLearningEntryTypeLabel(query.entryType)} only`
  }

  if (query.sourceClassification) {
    return formatLearningSourceLabel(query.sourceClassification)
  }

  return 'Recent all'
}

function isLearningQueryActive(
  currentQuery: OverviewLearningLedgerQuery,
  expectedQuery: OverviewLearningLedgerQuery
) {
  return (
    (currentQuery.entryType ?? null) === (expectedQuery.entryType ?? null) &&
    (currentQuery.sourceClassification ?? null) ===
      (expectedQuery.sourceClassification ?? null) &&
    (currentQuery.sourceLaneId ?? null) === (expectedQuery.sourceLaneId ?? null) &&
    (currentQuery.queueJobId ?? null) === (expectedQuery.queueJobId ?? null) &&
    (currentQuery.linkedMissionId ?? null) === (expectedQuery.linkedMissionId ?? null)
  )
}

function laneScore(analysis: DeveloperLaneAutonomyAnalysis | null | undefined) {
  return Math.max(0, Math.min(100, analysis?.score ?? 0))
}

function signalTone(state: 'idle' | 'loading' | 'ready' | 'error', healthy = true) {
  if (state === 'ready' && healthy) {
    return 'border-emerald-400/25 bg-emerald-400/10 text-emerald-50'
  }

  if (state === 'loading') {
    return 'border-sky-400/25 bg-sky-400/10 text-sky-50'
  }

  if (state === 'error' || !healthy) {
    return 'border-rose-400/25 bg-rose-400/10 text-rose-50'
  }

  return 'border-white/12 bg-white/6 text-slate-100'
}

function clusterNodePosition(index: number, total: number) {
  const normalizedTotal = Math.max(total, 1)
  const angle = (Math.PI * 2 * index) / normalizedTotal
  const radiusX = total === 1 ? 0 : 31
  const radiusY = total === 1 ? 0 : 23

  return {
    left: `${50 + Math.cos(angle) * radiusX}%`,
    top: `${50 + Math.sin(angle) * radiusY}%`,
  }
}

function readinessBadgeTone(readiness: DeveloperLaneAutonomyAnalysis['readiness']) {
  if (readiness === 'ready') {
    return 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100'
  }

  if (readiness === 'completed') {
    return 'border-violet-400/20 bg-violet-400/10 text-violet-100'
  }

  if (readiness === 'watch') {
    return 'border-amber-300/20 bg-amber-300/10 text-amber-50'
  }

  return 'border-rose-400/20 bg-rose-400/10 text-rose-100'
}

function silentMonitorTone(state: DeveloperControlPlaneSilentMonitor['state']) {
  if (state === 'healthy') {
    return 'border-emerald-400/25 bg-emerald-400/10 text-emerald-50'
  }

  if (state === 'watch') {
    return 'border-amber-300/25 bg-amber-300/10 text-amber-50'
  }

  if (state === 'missing') {
    return 'border-white/15 bg-white/6 text-slate-100'
  }

  return 'border-rose-400/25 bg-rose-400/10 text-rose-50'
}

function silentMonitorBadgeTone(state: DeveloperControlPlaneSilentMonitor['state']) {
  if (state === 'healthy') {
    return 'border-emerald-400/25 bg-emerald-400/10 text-emerald-100'
  }

  if (state === 'watch') {
    return 'border-amber-300/25 bg-amber-300/10 text-amber-50'
  }

  if (state === 'missing') {
    return 'border-white/15 bg-white/6 text-slate-100'
  }

  return 'border-rose-400/25 bg-rose-400/10 text-rose-100'
}

function formatSilentMonitorState(state: DeveloperControlPlaneSilentMonitor['state']) {
  if (state === 'healthy') {
    return 'Quiet'
  }

  if (state === 'watch') {
    return 'Watch'
  }

  if (state === 'missing') {
    return 'Missing'
  }

  return 'Alert'
}

function formatSilentMonitorOverallState(state: 'idle' | 'loading' | 'ready' | 'error', overallState: string | null) {
  if (state === 'loading') {
    return 'Refreshing'
  }

  if (state === 'error') {
    return 'Attention'
  }

  if (overallState === 'healthy') {
    return 'Quiet'
  }

  if (overallState === 'watch') {
    return 'Watching'
  }

  if (overallState === 'missing') {
    return 'Missing evidence'
  }

  if (overallState === 'alert') {
    return 'Emitting'
  }

  return 'Standby'
}

function uniqueSourceTruthKinds(sources: SourceTruthKind[]) {
  return Array.from(new Set(sources))
}

function SourceTruthBadges({
  sources,
  compact = false,
}: {
  sources: SourceTruthKind[]
  compact?: boolean
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {uniqueSourceTruthKinds(sources).map((source) => (
        <Badge
          key={source}
          className={cn(
            'border font-medium',
            compact ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-[11px]',
            SOURCE_TRUTH_META[source].className
          )}
        >
          {SOURCE_TRUTH_META[source].label}
        </Badge>
      ))}
    </div>
  )
}

export function OverviewTab({
  lanes,
  autonomyAnalysis,
  selectedLane,
  recommendedLane,
  persistenceStatus,
  lastUpdatedAt,
  primaryOrchestrator,
  agentRoleCount,
  queueStatusState,
  queueStatusRecord,
  queueStatusError,
  queueStatusLastRefreshedAt,
  selectedLaneQueueJobId = null,
  closeoutReceiptState = 'idle',
  closeoutReceiptRecord = null,
  runtimeWatchdogState,
  runtimeWatchdogRecord,
  runtimeWatchdogError,
  runtimeWatchdogLastCheckedAt,
  runtimeAutonomyCycleState = 'idle',
  runtimeAutonomyCycleRecord = null,
  runtimeAutonomyCycleLastCheckedAt = null,
  silentMonitorsState = 'idle',
  silentMonitorsRecord = null,
  silentMonitorsError = null,
  silentMonitorsLastCheckedAt = null,
  missionStateState,
  missionStateRecord,
  missionStateError,
  missionStateLastCheckedAt,
  learningLedgerState = 'idle',
  learningLedgerRecord = null,
  learningLedgerError = null,
  learningLedgerLastCheckedAt = null,
  learningLedgerQuery = { limit: 6 },
  onRefreshQueueStatus,
  onRefreshLearnings = () => {},
  onSetActiveTab,
  onSelectLane,
}: OverviewTabProps) {
  const analysisMap = new Map(
    (autonomyAnalysis?.laneAnalyses ?? []).map((analysis) => [analysis.laneId, analysis])
  )

  const totalSubplans = lanes.reduce((count, lane) => count + lane.subplans.length, 0)
  const totalDependencies = lanes.reduce((count, lane) => count + lane.dependencies.length, 0)
  const statusClusters = STATUS_ORDER.map((status) => {
    const clusterLanes = lanes.filter((lane) => lane.status === status)
    const clusterAnalyses = clusterLanes
      .map((lane) => analysisMap.get(lane.id) ?? null)
      .filter((analysis): analysis is DeveloperLaneAutonomyAnalysis => analysis !== null)

    return {
      status,
      meta: STATUS_META[status],
      lanes: clusterLanes,
      count: clusterLanes.length,
      subplans: clusterLanes.reduce((count, lane) => count + lane.subplans.length, 0),
      readyCount: clusterAnalyses.filter((analysis) => analysis.readiness === 'ready').length,
      blockingWarnings: clusterAnalyses.reduce(
        (count, analysis) =>
          count +
          analysis.structuralWarnings.filter((warning) => warning.severity === 'blocking').length,
        0
      ),
    }
  })

  const ownerConstellations = Array.from(
    lanes.reduce(
      (map, lane) => {
        for (const owner of lane.owners) {
          const current = map.get(owner) ?? {
            owner,
            laneIds: [] as string[],
            titles: [] as string[],
            activeCount: 0,
          }
          current.laneIds.push(lane.id)
          current.titles.push(lane.title)
          if (lane.status === 'active') {
            current.activeCount += 1
          }
          map.set(owner, current)
        }
        return map
      },
      new Map<string, { owner: string; laneIds: string[]; titles: string[]; activeCount: number }>()
    ).values()
  )
    .sort((left, right) => {
      if (right.laneIds.length !== left.laneIds.length) {
        return right.laneIds.length - left.laneIds.length
      }
      return left.owner.localeCompare(right.owner)
    })
    .slice(0, 6)

  const developmentThread = [...(autonomyAnalysis?.laneAnalyses ?? [])]
    .sort((left, right) => right.score - left.score)
    .slice(0, 6)
    .map((analysis) => ({
      analysis,
      lane: lanes.find((lane) => lane.id === analysis.laneId) ?? null,
    }))
    .filter((entry): entry is { analysis: DeveloperLaneAutonomyAnalysis; lane: DeveloperBoardLane } => entry.lane !== null)

  const highlightedLane = recommendedLane ?? selectedLane
  const boardSourceTruth: SourceTruthKind =
    persistenceStatus.tone === 'synced' ? 'shared-backend' : 'browser-fallback'
  const boardAndMissionSources: SourceTruthKind[] =
    boardSourceTruth === 'shared-backend'
      ? ['shared-backend']
      : ['browser-fallback', 'shared-backend']
  const signalProvenanceSources: SourceTruthKind[] =
    boardSourceTruth === 'shared-backend'
      ? ['shared-backend', 'tracked-artifact']
      : ['browser-fallback', 'shared-backend', 'tracked-artifact']
  const autonomyCycleWatchdog = runtimeAutonomyCycleRecord?.watchdog ?? null
  const autonomyCycleWatchdogJobErrorCount = autonomyCycleWatchdog
    ? Object.keys(autonomyCycleWatchdog.job_errors).length
    : 0
  const runtimeWatchdogTelemetrySource = runtimeWatchdogRecord
    ? 'watchdog'
    : autonomyCycleWatchdog?.exists
      ? 'autonomy-cycle'
      : 'none'
  const runtimeStateIsStale =
    runtimeWatchdogRecord?.state_is_stale ?? autonomyCycleWatchdog?.state_is_stale ?? false
  const runtimeGatewayHealthy =
    runtimeWatchdogRecord?.gateway_healthy ?? autonomyCycleWatchdog?.gateway_healthy ?? null
  const runtimeHealthy = !runtimeStateIsStale && runtimeGatewayHealthy === true
  const runtimeBootstrapReady = runtimeWatchdogRecord?.bootstrap_ready ?? null
  const runtimeOperationallyReady = runtimeHealthy && (runtimeBootstrapReady !== false)
  const runtimeCompletionAssistSummary = formatWatchdogCompletionAssistSummary(
    runtimeWatchdogRecord?.completion_assist_advisory ?? null
  )
  const runtimeWatchdogDisplayCount =
    runtimeWatchdogRecord?.job_count ??
    (runtimeWatchdogTelemetrySource === 'autonomy-cycle' ? autonomyCycleWatchdogJobErrorCount : 0)
  const runtimeWatchdogDisplayTimestamp =
    runtimeWatchdogLastCheckedAt ??
    runtimeAutonomyCycleLastCheckedAt ??
    runtimeAutonomyCycleRecord?.generated_at ??
    null
  const runtimeWatchdogSummary = runtimeWatchdogRecord
    ? !runtimeBootstrapReady
      ? 'Bootstrap blocked by missing auth'
      : runtimeStateIsStale
        ? 'Watchdog snapshot stale'
        : runtimeHealthy
          ? 'Gateway healthy'
          : 'Gateway requires attention'
    : runtimeWatchdogTelemetrySource === 'autonomy-cycle'
      ? runtimeStateIsStale
        ? 'Autonomy-cycle watchdog stale'
        : runtimeHealthy
          ? 'Autonomy-cycle watchdog fallback'
          : 'Autonomy-cycle signals attention'
      : runtimeAutonomyCycleState === 'loading'
        ? 'Refreshing fallback telemetry'
        : formatCompactState(runtimeWatchdogState)
  const silentMonitorCards = silentMonitorsRecord?.monitors ?? []
  const emittingSilentMonitorCount = silentMonitorCards.filter((monitor) => monitor.should_emit).length
  const silentMonitorOverallState = silentMonitorsRecord?.overall_state ?? null
  const missionCount = missionStateRecord?.count ?? 0
  const queueJobCount = queueStatusRecord?.job_count ?? 0
  const learningEntries = learningLedgerRecord?.entries ?? []
  const activeLaneCount = lanes.filter((lane) => lane.status === 'active').length
  const readyLaneCount = autonomyAnalysis?.readyLaneIds.length ?? 0
  const blockedLaneCount = autonomyAnalysis?.blockedLaneIds.length ?? 0
  const learningCounts = learningEntries.reduce(
    (counts, entry) => {
      if (entry.entry_type === 'verification-learning') {
        counts.verification += 1
        return counts
      }

      counts[entry.entry_type] += 1
      return counts
    },
    {
      pattern: 0,
      pitfall: 0,
      incident: 0,
      verification: 0,
    }
  )
  const learningScopeLabel = describeLearningLedgerScope(
    learningLedgerQuery,
    selectedLane,
    selectedLaneQueueJobId
  )
  const selectedLaneMissionSummary = getSelectedLaneMissionSummary({
    selectedLane,
    missionStateRecord,
    closeoutReceiptRecord,
    selectedLaneQueueJobId,
  })
  const selectedLaneMissionClosurePending =
    selectedLaneMissionSummary !== null &&
    !selectedLane?.closure &&
    closeoutReceiptState === 'available' &&
    closeoutReceiptRecord?.exists === true

  return (
    <TabsContent value="overview" className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-cyan-300/15 bg-[linear-gradient(135deg,rgba(2,6,23,0.98),rgba(8,15,41,0.96)_45%,rgba(10,37,64,0.94))] p-6 text-slate-50 shadow-[0_30px_120px_rgba(2,6,23,0.42)] sm:p-8">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <motion.div
            className="absolute -left-12 top-0 h-56 w-56 rounded-full bg-cyan-300/12 blur-3xl"
            animate={{ x: [0, 26, 0], y: [0, 22, 0], opacity: [0.4, 0.7, 0.4] }}
            transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute right-0 top-10 h-72 w-72 rounded-full bg-fuchsia-300/10 blur-3xl"
            animate={{ x: [0, -24, 0], y: [0, 26, 0], opacity: [0.25, 0.55, 0.25] }}
            transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-emerald-300/8 blur-3xl"
            animate={{ scale: [1, 1.14, 1], opacity: [0.18, 0.34, 0.18] }}
            transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
          />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.18),transparent_0.6rem)] bg-[length:2.8rem_2.8rem] opacity-[0.08]" />
        </div>

        <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.12fr)_minmax(360px,0.88fr)]">
          <div className="space-y-5">
            <Badge className="w-fit border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-cyan-100">
              Live Internal Command Deck
            </Badge>
            <div className="space-y-3">
              <h2
                className="text-3xl font-semibold tracking-[-0.04em] text-white sm:text-5xl [font-family:'Space_Grotesk',var(--prakruti-font-display)]"
              >
                Interstellar Development Lattice
              </h2>
              <p className="max-w-3xl text-sm leading-7 text-slate-200/82 sm:text-base">
                This route now opens on a live cosmic control surface. Every cluster, thread, and signal below is derived from the real developer control-plane board, overnight queue telemetry, watchdog state, and durable mission snapshots instead of mock planning chrome.
              </p>
            </div>

            <div className="flex flex-wrap gap-3 text-xs text-slate-200/80">
              <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1.5">
                Route: /admin/developer/master-board
              </span>
              <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1.5">
                Orchestrator: {primaryOrchestrator ?? 'OmShriMaatreNamaha'}
              </span>
              <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1.5">
                Persistence: {persistenceStatus.label}
              </span>
              <span className="rounded-full border border-white/12 bg-white/6 px-3 py-1.5">
                Last board write: {formatTimestamp(lastUpdatedAt)}
              </span>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                size="sm"
                className="border border-cyan-300/20 bg-white text-slate-950 hover:bg-slate-100"
                onClick={() => void onRefreshQueueStatus()}
              >
                <RefreshCw className="h-4 w-4" />
                Refresh live signals
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white"
                onClick={() => onSetActiveTab('planner')}
              >
                <Workflow className="h-4 w-4" />
                Open planner
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white"
                onClick={() => onSetActiveTab('autonomy')}
              >
                <Radar className="h-4 w-4" />
                Open autonomy
              </Button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className={cn(
                'rounded-[1.6rem] border p-4 backdrop-blur-xl',
                signalTone(queueStatusState, queueStatusState === 'ready')
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-slate-300/80">Overnight queue</div>
                  <div className="mt-2">
                    <SourceTruthBadges sources={['tracked-artifact']} compact />
                  </div>
                  <div className="mt-2 text-3xl font-semibold text-white">{queueJobCount}</div>
                </div>
                <GitBranch className="h-5 w-5 text-cyan-200" />
              </div>
              <div className="mt-3 text-sm text-slate-200/76">{formatCompactState(queueStatusState)} queue sample</div>
              <div className="mt-1 text-xs text-slate-300/70">{formatTimestamp(queueStatusLastRefreshedAt)}</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.04 }}
              className={cn(
                'rounded-[1.6rem] border p-4 backdrop-blur-xl',
                signalTone(runtimeWatchdogState, runtimeOperationallyReady)
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-slate-300/80">Runtime watchdog</div>
                  <div className="mt-2">
                    <SourceTruthBadges sources={['tracked-artifact']} compact />
                  </div>
                  <div className="mt-2 text-3xl font-semibold text-white">{runtimeWatchdogDisplayCount}</div>
                </div>
                <ShieldCheck className="h-5 w-5 text-emerald-200" />
              </div>
              <div className="mt-3 text-sm text-slate-200/76">{runtimeWatchdogSummary}</div>
              <div className="mt-1 text-xs text-slate-300/70">
                {formatTimestamp(runtimeWatchdogDisplayTimestamp)}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.54, delay: 0.08 }}
              className={cn(
                'rounded-[1.6rem] border p-4 backdrop-blur-xl',
                signalTone(missionStateState, missionStateState === 'ready')
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-slate-300/80">Mission feed</div>
                  <div className="mt-2">
                    <SourceTruthBadges sources={['shared-backend']} compact />
                  </div>
                  <div className="mt-2 text-3xl font-semibold text-white">{missionCount}</div>
                </div>
                <Rocket className="h-5 w-5 text-fuchsia-200" />
              </div>
              <div className="mt-3 text-sm text-slate-200/76">Durable orchestrator snapshots</div>
              <div className="mt-1 text-xs text-slate-300/70">{formatTimestamp(missionStateLastCheckedAt)}</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.58, delay: 0.12 }}
              className={cn(
                'rounded-[1.6rem] border p-4 backdrop-blur-xl',
                signalTone(
                  silentMonitorsState,
                  silentMonitorsState === 'ready' && silentMonitorOverallState === 'healthy'
                )
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.28em] text-slate-300/80">Silent monitors</div>
                  <div className="mt-2">
                    <SourceTruthBadges sources={['tracked-artifact']} compact />
                  </div>
                  <div className="mt-2 text-3xl font-semibold text-white">{emittingSilentMonitorCount}</div>
                </div>
                <Sparkles className="h-5 w-5 text-amber-100" />
              </div>
              <div className="mt-3 text-sm text-slate-200/76">
                {formatSilentMonitorOverallState(silentMonitorsState, silentMonitorOverallState)} across{' '}
                {silentMonitorCards.length} evidence tracks
              </div>
              <div className="mt-1 text-xs text-slate-300/70">
                {formatTimestamp(silentMonitorsLastCheckedAt)}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(360px,0.82fr)]">
        <Card className="overflow-hidden border-slate-900/80 bg-[linear-gradient(180deg,rgba(8,15,41,0.98),rgba(2,6,23,0.98))] text-slate-50 shadow-[0_24px_100px_rgba(2,6,23,0.34)]">
          <CardHeader className="pb-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="text-xl text-white">Development Clusters</CardTitle>
                <CardDescription className="text-slate-300">
                  Live lane clustering by status, with every node bound to the canonical board rather than a static design mock.
                </CardDescription>
              </div>
              <SourceTruthBadges sources={[boardSourceTruth]} />
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-2">
            {statusClusters.map((cluster, clusterIndex) => (
              <motion.div
                key={cluster.status}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.42, delay: clusterIndex * 0.05 }}
                className="relative overflow-hidden rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4"
              >
                <div className={cn('absolute inset-x-5 top-0 h-px bg-gradient-to-r opacity-80', cluster.meta.accentClassName)} />
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-slate-400">{cluster.meta.label}</div>
                    <div className="mt-1 text-lg font-semibold text-white">{cluster.count} lane{cluster.count === 1 ? '' : 's'}</div>
                    <div className="mt-2 text-sm text-slate-300/80">{cluster.meta.description}</div>
                  </div>
                  <Badge className={cn('border', cluster.meta.chipClassName)}>{cluster.status}</Badge>
                </div>

                <div className="relative mt-5 h-32 overflow-hidden rounded-[1.4rem] border border-white/8 bg-slate-950/70">
                  <motion.div
                    className="absolute inset-4 rounded-full border border-white/10"
                    animate={{ rotate: [0, 360] }}
                    transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
                  />
                  <motion.div
                    className="absolute inset-8 rounded-full border border-white/6"
                    animate={{ rotate: [0, -360] }}
                    transition={{ duration: 32, repeat: Infinity, ease: 'linear' }}
                  />
                  <div className={cn('absolute left-1/2 top-1/2 h-12 w-12 -translate-x-1/2 -translate-y-1/2 rounded-full blur-xl', cluster.meta.glowClassName)} />
                  <div className="absolute left-1/2 top-1/2 z-10 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/14 bg-white/8 text-sm font-semibold text-white backdrop-blur-md">
                    {cluster.count}
                  </div>

                  {cluster.lanes.slice(0, 8).map((lane, laneIndex) => {
                    const position = clusterNodePosition(laneIndex, cluster.lanes.length)
                    return (
                      <motion.button
                        key={lane.id}
                        type="button"
                        className="absolute z-20 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/40 bg-white shadow-[0_0_18px_rgba(255,255,255,0.45)]"
                        style={position}
                        animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
                        transition={{ duration: 3 + laneIndex * 0.35, repeat: Infinity, ease: 'easeInOut' }}
                        onClick={() => onSelectLane(lane.id)}
                        aria-label={`Focus lane ${lane.title}`}
                      />
                    )
                  })}
                </div>

                <div className="mt-4 grid gap-2 text-xs text-slate-300/75 sm:grid-cols-3">
                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
                    <div className="uppercase tracking-[0.22em] text-slate-500">Subplans</div>
                    <div className="mt-1 text-base font-semibold text-white">{cluster.subplans}</div>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
                    <div className="uppercase tracking-[0.22em] text-slate-500">Ready</div>
                    <div className="mt-1 text-base font-semibold text-white">{cluster.readyCount}</div>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2">
                    <div className="uppercase tracking-[0.22em] text-slate-500">Blocking drift</div>
                    <div className="mt-1 text-base font-semibold text-white">{cluster.blockingWarnings}</div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {cluster.lanes.slice(0, 4).map((lane) => (
                    <button
                      key={lane.id}
                      type="button"
                      className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-left text-xs text-slate-200 transition hover:bg-white/[0.08]"
                      onClick={() => onSelectLane(lane.id)}
                    >
                      {lane.title}
                    </button>
                  ))}
                  {cluster.count > 4 && (
                    <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">
                      +{cluster.count - 4} more
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="overflow-hidden border-cyan-300/15 bg-[linear-gradient(180deg,rgba(9,20,52,0.98),rgba(4,10,28,0.98))] text-slate-50 shadow-[0_22px_80px_rgba(3,7,18,0.3)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Launch Window</CardTitle>
                  <CardDescription className="text-slate-300">
                    The next recommended or selected lane, surfaced as a real development target instead of a decorative hero callout.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={[boardSourceTruth]} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {highlightedLane ? (
                (() => {
                  const highlightedAnalysis = analysisMap.get(highlightedLane.id) ?? null

                  return (
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.05] p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">{highlightedLane.id}</div>
                          <h3 className="mt-2 text-2xl font-semibold text-white">{highlightedLane.title}</h3>
                        </div>
                        <Badge className={cn('border', STATUS_META[highlightedLane.status].chipClassName)}>
                          {highlightedLane.status}
                        </Badge>
                      </div>

                      <p className="mt-3 text-sm leading-6 text-slate-300/85">{highlightedLane.objective}</p>

                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-2xl border border-white/8 bg-slate-950/50 px-4 py-3 text-sm text-slate-300">
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Owners</div>
                          <div className="mt-2 text-white">{highlightedLane.owners.join(', ')}</div>
                        </div>
                        <div className="rounded-2xl border border-white/8 bg-slate-950/50 px-4 py-3 text-sm text-slate-300">
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Execution score</div>
                          <div className="mt-2 text-white">{laneScore(highlightedAnalysis)} / 100</div>
                        </div>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {highlightedLane.completion_criteria.slice(0, 3).map((criterion) => (
                          <span key={criterion} className="rounded-full border border-cyan-300/14 bg-cyan-300/10 px-3 py-1 text-xs text-cyan-100">
                            {criterion}
                          </span>
                        ))}
                      </div>

                      <div className="mt-5 flex flex-wrap gap-3">
                        <Button
                          size="sm"
                          className="bg-white text-slate-950 hover:bg-slate-100"
                          onClick={() => {
                            onSelectLane(highlightedLane.id)
                            onSetActiveTab('planner')
                          }}
                        >
                          Focus in planner
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white"
                          onClick={() => {
                            onSelectLane(highlightedLane.id)
                            onSetActiveTab('autonomy')
                          }}
                        >
                          Inspect readiness
                        </Button>
                      </div>
                    </div>
                  )
                })()
              ) : (
                <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-300">
                  No lane is currently selected or recommended. Add or activate a lane in the planner to project it here.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(8,18,44,0.98),rgba(3,8,24,0.98))] text-slate-50 shadow-[0_18px_70px_rgba(3,7,18,0.28)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Learning Ledger</CardTitle>
                  <CardDescription className="text-slate-300">
                    Read-only typed learnings surfaced from approval receipts, queue conflicts, stable closeout receipts, and mission verification evidence.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={['shared-backend']} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className={cn(
                    'border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white',
                    isLearningQueryActive(learningLedgerQuery, {}) &&
                      'border-cyan-300/30 bg-cyan-300/12 text-cyan-100'
                  )}
                  onClick={() => void onRefreshLearnings({ limit: 6 })}
                >
                  Recent all
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!selectedLane}
                  className={cn(
                    'border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white',
                    selectedLane &&
                      isLearningQueryActive(learningLedgerQuery, {
                        sourceLaneId: selectedLane.id,
                      }) &&
                      'border-cyan-300/30 bg-cyan-300/12 text-cyan-100'
                  )}
                  onClick={() => {
                    if (!selectedLane) {
                      return
                    }

                    void onRefreshLearnings({
                      limit: 6,
                      sourceLaneId: selectedLane.id,
                    })
                  }}
                >
                  Selected lane
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!selectedLaneQueueJobId}
                  className={cn(
                    'border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white',
                    selectedLaneQueueJobId &&
                      isLearningQueryActive(learningLedgerQuery, {
                        queueJobId: selectedLaneQueueJobId,
                      }) &&
                      'border-cyan-300/30 bg-cyan-300/12 text-cyan-100'
                  )}
                  onClick={() => {
                    if (!selectedLaneQueueJobId) {
                      return
                    }

                    void onRefreshLearnings({
                      limit: 6,
                      queueJobId: selectedLaneQueueJobId,
                    })
                  }}
                >
                  Selected job
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className={cn(
                    'border-white/12 bg-white/6 text-slate-50 hover:bg-white/10 hover:text-white',
                    isLearningQueryActive(learningLedgerQuery, {
                      entryType: 'verification-learning',
                    }) && 'border-cyan-300/30 bg-cyan-300/12 text-cyan-100'
                  )}
                  onClick={() =>
                    void onRefreshLearnings({
                      limit: 6,
                      entryType: 'verification-learning',
                    })
                  }
                >
                  Verification only
                </Button>
              </div>

              <div className={cn('rounded-[1.4rem] border p-4', signalTone(learningLedgerState, learningLedgerState === 'ready'))}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-slate-400">Loaded scope</div>
                    <div className="mt-2 text-lg font-semibold text-white">{learningScopeLabel}</div>
                  </div>
                  <div className="text-right text-xs text-slate-300/72">
                    <div>{formatCompactState(learningLedgerState)}</div>
                    <div className="mt-1">{formatTimestamp(learningLedgerLastCheckedAt)}</div>
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-300/78">
                  {learningLedgerRecord
                    ? `${learningLedgerRecord.total_count} typed learning entr${learningLedgerRecord.total_count === 1 ? 'y' : 'ies'} available in the current view.`
                    : learningLedgerError ?? 'Learning ledger is standing by.'}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Patterns</div>
                  <div className="mt-2 text-2xl font-semibold text-white">{learningCounts.pattern}</div>
                </div>
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Pitfalls</div>
                  <div className="mt-2 text-2xl font-semibold text-white">{learningCounts.pitfall}</div>
                </div>
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Incidents</div>
                  <div className="mt-2 text-2xl font-semibold text-white">{learningCounts.incident}</div>
                </div>
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                  <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Verification</div>
                  <div className="mt-2 text-2xl font-semibold text-white">{learningCounts.verification}</div>
                </div>
              </div>

              {learningEntries.length > 0 ? (
                <div className="space-y-3">
                  {learningEntries.slice(0, 4).map((entry) => {
                    const confidenceLabel = formatLearningConfidence(entry.confidence_score)

                    return (
                      <div
                        key={entry.learning_entry_id}
                        className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="text-xs uppercase tracking-[0.22em] text-slate-500">
                              {formatLearningSourceLabel(entry.source_classification)}
                            </div>
                            <div className="mt-2 text-sm font-medium text-white">{entry.title}</div>
                          </div>
                          <Badge className="border border-cyan-300/20 bg-cyan-300/10 text-cyan-100">
                            {formatLearningEntryTypeLabel(entry.entry_type)}
                          </Badge>
                        </div>
                        <div className="mt-3 text-sm leading-6 text-slate-300/82">{entry.summary}</div>
                        <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-400">
                          {entry.source_lane_id ? (
                            <span className="rounded-full border border-white/10 px-2.5 py-1">
                              Lane {entry.source_lane_id}
                            </span>
                          ) : null}
                          {entry.queue_job_id ? (
                            <span className="rounded-full border border-white/10 px-2.5 py-1">
                              Job {entry.queue_job_id}
                            </span>
                          ) : null}
                          {confidenceLabel ? (
                            <span className="rounded-full border border-white/10 px-2.5 py-1">
                              {confidenceLabel}
                            </span>
                          ) : null}
                          <span className="rounded-full border border-white/10 px-2.5 py-1">
                            {formatTimestamp(entry.recorded_at)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-300">
                  No typed learning entries are projected for the current view yet.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(5,12,34,0.98),rgba(2,6,23,0.98))] text-slate-50 shadow-[0_18px_70px_rgba(3,7,18,0.28)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Owner Constellations</CardTitle>
                  <CardDescription className="text-slate-300">
                    Agent and operator clustering from real lane ownership.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={[boardSourceTruth]} />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {ownerConstellations.length > 0 ? (
                ownerConstellations.map((cluster, clusterIndex) => (
                  <motion.div
                    key={cluster.owner}
                    initial={{ opacity: 0, x: 14 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.35, delay: clusterIndex * 0.05 }}
                    className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-white">{cluster.owner}</div>
                        <div className="mt-1 text-xs text-slate-400">{cluster.laneIds.length} lane assignment{cluster.laneIds.length === 1 ? '' : 's'}</div>
                      </div>
                      <div className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1 text-xs text-slate-200">
                        {cluster.activeCount} active
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {cluster.titles.slice(0, 3).map((title) => (
                        <span key={title} className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-slate-300">
                          {title}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4 text-sm text-slate-300">
                  Owner assignments will cluster here once lanes carry owners.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.06fr)_minmax(360px,0.94fr)]">
        <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(3,8,24,0.98),rgba(8,15,41,0.98))] text-slate-50 shadow-[0_18px_80px_rgba(2,6,23,0.3)]">
          <CardHeader className="pb-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="text-xl text-white">Development Thread</CardTitle>
                <CardDescription className="text-slate-300">
                  Highest-priority movement lanes, ordered from the real autonomy score and structural readiness model.
                </CardDescription>
              </div>
              <SourceTruthBadges sources={[boardSourceTruth]} />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {developmentThread.length > 0 ? (
              developmentThread.map((entry, threadIndex) => {
                const isHighlighted = highlightedLane?.id === entry.lane.id

                return (
                  <motion.button
                    key={entry.lane.id}
                    type="button"
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.38, delay: threadIndex * 0.05 }}
                    className={cn(
                      'group relative w-full overflow-hidden rounded-[1.6rem] border p-4 text-left transition hover:border-cyan-300/30 hover:bg-white/[0.06]',
                      isHighlighted
                        ? 'border-cyan-300/25 bg-cyan-300/10'
                        : 'border-white/10 bg-white/[0.04]'
                    )}
                    onClick={() => onSelectLane(entry.lane.id)}
                  >
                    <div className="absolute left-5 top-5 bottom-5 w-px bg-gradient-to-b from-cyan-300/0 via-cyan-300/35 to-fuchsia-300/0" />
                    <div className="pl-6">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Thread {threadIndex + 1}</div>
                          <div className="mt-1 text-lg font-semibold text-white">{entry.lane.title}</div>
                          <div className="mt-2 text-sm text-slate-300/80">{entry.lane.objective}</div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge className={cn('border', STATUS_META[entry.lane.status].chipClassName)}>
                            {entry.lane.status}
                          </Badge>
                          <Badge className={cn('border', readinessBadgeTone(entry.analysis.readiness))}>
                            {entry.analysis.readiness}
                          </Badge>
                        </div>
                      </div>

                      <div className="mt-4">
                        <div className="flex items-center justify-between text-xs uppercase tracking-[0.22em] text-slate-500">
                          <span>Autonomy score</span>
                          <span>{laneScore(entry.analysis)} / 100</span>
                        </div>
                        <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-white/8">
                          <motion.div
                            className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-sky-300 to-fuchsia-300"
                            initial={{ width: 0 }}
                            animate={{ width: `${laneScore(entry.analysis)}%` }}
                            transition={{ duration: 0.7, delay: 0.15 + threadIndex * 0.06 }}
                          />
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 sm:grid-cols-3 text-sm text-slate-300/76">
                        <div>
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Owners</div>
                          <div className="mt-2 text-white">{entry.lane.owners.join(', ')}</div>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Dependencies</div>
                          <div className="mt-2 text-white">{entry.lane.dependencies.length}</div>
                        </div>
                        <div>
                          <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Completion criteria</div>
                          <div className="mt-2 text-white">{entry.lane.completion_criteria.length}</div>
                        </div>
                      </div>
                    </div>
                  </motion.button>
                )
              })
            ) : (
              <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4 text-sm text-slate-300">
                The development thread will materialize here once the control-plane board contains analyzable lanes.
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(8,18,46,0.98),rgba(2,6,23,0.98))] text-slate-50 shadow-[0_18px_70px_rgba(3,7,18,0.28)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Silent Monitors</CardTitle>
                  <CardDescription className="text-slate-300">
                    Evidence-only readiness and drift monitors. They surface issues here, but they do not mutate the board, queue, or REEVU trust surfaces.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={['tracked-artifact']} />
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {silentMonitorCards.length > 0 ? (
                silentMonitorCards.map((monitor) => (
                  <div
                    key={monitor.monitor_key}
                    className={cn('rounded-[1.4rem] border p-4', silentMonitorTone(monitor.state))}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-medium text-white">{monitor.label}</div>
                        <div className="mt-1 text-slate-300/78">{monitor.summary}</div>
                      </div>
                      <Badge className={cn('border', silentMonitorBadgeTone(monitor.state))}>
                        {formatSilentMonitorState(monitor.state)}
                      </Badge>
                    </div>
                    {monitor.detail ? (
                      <div className="mt-2 text-xs leading-6 text-slate-200/76">{monitor.detail}</div>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-300/72">
                      <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1">
                        Cadence: {monitor.refresh_cadence}
                      </span>
                      <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1">
                        Artifact: {monitor.output_artifact}
                      </span>
                      {monitor.evidence_sources[0]?.path ? (
                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1">
                          Source: {monitor.evidence_sources[0].path}
                        </span>
                      ) : null}
                    </div>
                    {monitor.findings.length > 0 ? (
                      <div className="mt-2 text-xs text-slate-300/72">
                        Signals: {monitor.findings.slice(0, 3).join(', ')}
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] p-4 text-slate-300/78">
                  {silentMonitorsError ?? 'Evidence-only silent monitors are standing by.'}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(6,14,38,0.98),rgba(2,6,23,0.98))] text-slate-50 shadow-[0_18px_70px_rgba(3,7,18,0.28)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Signal Provenance</CardTitle>
                  <CardDescription className="text-slate-300">
                    Direct operational sources backing this surface right now.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={signalProvenanceSources} />
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className={cn('rounded-[1.4rem] border p-4', signalTone(queueStatusState, queueStatusState === 'ready'))}>
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium text-white">Canonical board persistence</div>
                    <div className="mt-1 text-slate-300/78">{persistenceStatus.description}</div>
                  </div>
                  <SourceTruthBadges sources={[boardSourceTruth]} compact />
                  <Activity className="h-4 w-4 text-cyan-200" />
                </div>
              </div>
              <div className={cn('rounded-[1.4rem] border p-4', signalTone(queueStatusState, queueStatusState === 'ready'))}>
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-white">Overnight queue file</div>
                  <SourceTruthBadges sources={['tracked-artifact']} compact />
                </div>
                <div className="mt-1 text-slate-300/78">
                  {queueStatusRecord ? `${queueStatusRecord.queue_path} with ${queueStatusRecord.job_count} jobs.` : queueStatusError ?? 'Queue telemetry is standing by.'}
                </div>
              </div>
              <div className={cn('rounded-[1.4rem] border p-4', signalTone(runtimeWatchdogState, runtimeOperationallyReady))}>
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-white">Runtime watchdog state</div>
                  <SourceTruthBadges sources={['tracked-artifact']} compact />
                </div>
                <div className="mt-1 text-slate-300/78">
                  {runtimeWatchdogRecord
                    ? `${runtimeWatchdogRecord.job_count} runtime jobs observed; ${!runtimeBootstrapReady ? 'bootstrap blocked because runtime auth is missing' : runtimeStateIsStale ? 'watchdog snapshot stale' : runtimeHealthy ? 'gateway healthy' : 'gateway requires attention'}.`
                    : runtimeWatchdogTelemetrySource === 'autonomy-cycle'
                      ? `${autonomyCycleWatchdogJobErrorCount} watchdog job error${autonomyCycleWatchdogJobErrorCount === 1 ? '' : 's'} inferred from the autonomy-cycle artifact; ${runtimeStateIsStale ? 'fallback snapshot stale' : runtimeHealthy ? 'gateway healthy in fallback snapshot' : `${autonomyCycleWatchdog?.total_alerts ?? 0} alert(s) need attention`}.`
                    : runtimeWatchdogError ?? 'Watchdog state is standing by.'}
                </div>
                {runtimeWatchdogRecord && runtimeCompletionAssistSummary ? (
                  <div className="mt-2 text-xs text-slate-300/68">
                    {runtimeCompletionAssistSummary}
                  </div>
                ) : null}
              </div>
              <div className={cn('rounded-[1.4rem] border p-4', signalTone(missionStateState, missionStateState === 'ready'))}>
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-white">Durable mission ledger</div>
                  <SourceTruthBadges sources={['shared-backend']} compact />
                </div>
                <div className="mt-1 text-slate-300/78">
                  {missionStateRecord
                    ? `${missionStateRecord.count} durable mission snapshot${missionStateRecord.count === 1 ? '' : 's'} available for inspection.`
                    : missionStateError ?? 'Mission-state snapshots are standing by.'}
                </div>
              </div>
              <div className={cn('rounded-[1.4rem] border p-4', signalTone(missionStateState, Boolean(selectedLaneMissionSummary)))}>
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-white">Selected lane execution chain</div>
                  <SourceTruthBadges sources={['shared-backend', 'tracked-artifact']} compact />
                </div>
                {selectedLaneMissionSummary ? (
                  <div className="mt-2 space-y-2 text-slate-300/78">
                    <div>
                      Lane <span className="font-mono text-white">{selectedLaneMissionSummary.source_lane_id ?? selectedLane?.id ?? 'Not available'}</span> is linked to queue job{' '}
                      <span className="font-mono text-white">{selectedLaneMissionSummary.queue_job_id ?? closeoutReceiptRecord?.queue_job_id ?? selectedLaneQueueJobId ?? selectedLane?.closure?.queue_job_id ?? 'Not available'}</span> and durable mission{' '}
                      <span className="font-mono text-white">{selectedLaneMissionSummary.mission_id}</span>.
                    </div>
                    <div className="text-white">{selectedLaneMissionSummary.objective}</div>
                    {selectedLaneMissionClosurePending ? (
                      <div>
                        Stable receipt is present and the durable mission is active, but canonical board closure is still pending.
                      </div>
                    ) : null}
                    {selectedLaneMissionSummary.source_board_concurrency_token ? (
                      <div>
                        Board token <span className="font-mono text-white">{selectedLaneMissionSummary.source_board_concurrency_token}</span>
                      </div>
                    ) : null}
                  </div>
                ) : selectedLane?.closure || (closeoutReceiptState === 'available' && closeoutReceiptRecord?.exists) ? (
                  <div className="mt-1 text-slate-300/78">
                    {selectedLane?.closure
                      ? 'This lane has closure evidence, but no durable mission linkage is currently projected in the live feed.'
                      : 'Stable receipt is present for the selected lane, but the durable mission linkage is not yet projected in the live feed.'}
                  </div>
                ) : (
                  <div className="mt-1 text-slate-300/78">
                    Select a lane with reviewed runtime provenance to project its queue-to-mission chain here.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-900/80 bg-[linear-gradient(180deg,rgba(7,15,39,0.98),rgba(2,6,23,0.98))] text-slate-50 shadow-[0_18px_70px_rgba(3,7,18,0.28)]">
            <CardHeader className="pb-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl text-white">Board Field Metrics</CardTitle>
                  <CardDescription className="text-slate-300">
                    A compact real-state snapshot of the control plane that powers the planner, autonomy, diagram, and orchestration tabs.
                  </CardDescription>
                </div>
                <SourceTruthBadges sources={boardAndMissionSources} />
              </div>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Agent roles</div>
                <div className="mt-2 text-2xl font-semibold text-white">{agentRoleCount}</div>
              </div>
              <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Lanes ready</div>
                <div className="mt-2 text-2xl font-semibold text-white">{readyLaneCount}</div>
              </div>
              <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Dependencies</div>
                <div className="mt-2 text-2xl font-semibold text-white">{totalDependencies}</div>
              </div>
              <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.05] p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-slate-500">Last live mission check</div>
                <div className="mt-2 text-sm font-medium text-white">{formatTimestamp(missionStateLastCheckedAt)}</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </TabsContent>
  )
}

export default OverviewTab