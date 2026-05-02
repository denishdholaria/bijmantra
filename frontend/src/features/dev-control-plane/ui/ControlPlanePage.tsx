import { AlertTriangle, Activity, GitBranch, Orbit, Shield, Sparkles, Workflow } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OverviewTab } from './overview/OverviewTab'
import { IndigenousTab } from './indigenous/IndigenousTab'
import { PlannerTab } from './planner/PlannerTab'
import { AutonomyTab } from './autonomy/AutonomyTab'
import { ArielmaTab } from './arielma/ArielmaTab'
import { JsonTab } from './json/JsonTab'
import { Mem0Tab } from './mem0/Mem0Tab'
import { OrchestrationTab } from './orchestration/OrchestrationTab'
import { useControlPlaneController } from './useControlPlaneController'

function persistenceTone(tone: 'loading' | 'fallback' | 'warning' | 'synced') {
  if (tone === 'warning') {
    return 'text-amber-700 dark:text-amber-300'
  }

  if (tone === 'synced') {
    return 'text-emerald-700 dark:text-emerald-300'
  }

  if (tone === 'loading') {
    return 'text-sky-700 dark:text-sky-300'
  }

  return 'text-slate-700 dark:text-slate-300'
}

const tabLabelByValue: Record<string, string> = {
  overview: 'Overview',
  indigenous: 'Indigenous Brain',
  planner: 'Planner',
  autonomy: 'Autonomy',
  mem0: 'Mem0',
  arielma: 'Diagram',
  json: 'JSON',
  orchestration: 'Orchestration',
}

export function ControlPlanePage() {
  const {
    fileInputRef,
    rawBoardJson,
    lastUpdatedAt,
    activeTab,
    extraOwnersInput,
    parsedBoard,
    jsonError,
    lanes,
    activeLaneCount,
    blockedLaneCount,
    subplanCount,
    dependencyCount,
    selectedLane,
    availableAgents,
    autonomyAnalysis,
    selectedLaneAnalysis,
    recommendedLane,
    persistenceStatus,
    dispatchPacket,
    queueCandidate,
    queueEntryMaterialization,
    selectedLaneQueueJobId,
    queueWriteState,
    completionWriteState,
    boardVersionsState,
    boardVersionsRecord,
    boardVersionsError,
    boardVersionsLastCheckedAt,
    boardRestoreState,
    lastBoardRestoreResult,
    queueStatusState,
    queueStatusRecord,
    queueStatusError,
    queueStatusLastRefreshedAt,
    closeoutReceiptState,
    closeoutReceiptRecord,
    closeoutReceiptError,
    closeoutReceiptLastCheckedAt,
    runtimeWatchdogState,
    runtimeWatchdogRecord,
    runtimeWatchdogError,
    runtimeWatchdogLastCheckedAt,
    runtimeAutonomyCycleState,
    runtimeAutonomyCycleRecord,
    runtimeAutonomyCycleError,
    runtimeAutonomyCycleLastCheckedAt,
    runtimeCompletionAssistState,
    runtimeCompletionAssistRecord,
    runtimeCompletionAssistError,
    runtimeCompletionAssistLastCheckedAt,
    silentMonitorsState,
    silentMonitorsRecord,
    silentMonitorsError,
    silentMonitorsLastCheckedAt,
    missionStateState,
    missionStateRecord,
    missionStateError,
    missionStateLastCheckedAt,
    missionDetailState,
    missionDetailRecord,
    missionDetailError,
    missionDetailLastCheckedAt,
    indigenousBrainState,
    indigenousBrainBrief,
    indigenousBrainError,
    indigenousBrainLastCheckedAt,
    learningLedgerState,
    learningLedgerRecord,
    learningLedgerError,
    learningLedgerLastCheckedAt,
    learningLedgerQuery,
    lastQueueWriteResult,
    completionClosureSummary,
    completionEvidenceInput,
    lastCompletionWriteResult,
    replaceBoardJson,
    formatBoardJson,
    resetBoard,
    setActiveTab,
    setSelectedLaneId,
    setExtraOwnersInput,
    handleUpdateBoardTextField,
    updateLaneField,
    updateValidationBasisField,
    updateReviewStateField,
    handleCreateLane,
    handleDeleteLane,
    handleToggleOwner,
    handleAddExtraOwners,
    handleAddSubplan,
    handleUpdateSubplan,
    handleDeleteSubplan,
    handlePromoteLane,
    handleCopyDispatchPacket,
    handleCopyQueueCandidate,
    handleCopyQueueEntry,
    handleRefreshRecommendedTargets,
    handleRefreshAndRetryQueueWrite,
    handleRefreshAndRetryLaneCompletion,
    loadBoardVersions,
    handleRestoreBoardVersion,
    refreshQueueStatus,
    loadLearnings,
    refreshIndigenousBrain,
    setCompletionClosureSummary,
    setCompletionEvidenceInput,
    handleDraftLaneCompletionFromCurrentState,
    handleDraftLaneCompletionForLane,
    handleWriteLaneCompletion,
    handleWriteQueueEntry,
    handleExport,
    triggerImport,
    handleImport,
  } = useControlPlaneController()

  const primaryOrchestrator = parsedBoard?.control_plane.primary_orchestrator ?? 'OmShriMaatreNamaha'
  const activeTabLabel = tabLabelByValue[activeTab] ?? activeTab
  const runtimeSignalsHaveErrors =
    queueStatusState === 'error' ||
    runtimeWatchdogState === 'error' ||
    runtimeAutonomyCycleState === 'error' ||
    silentMonitorsState === 'error' ||
    missionStateState === 'error'
  const runtimeSignalsRefreshing =
    queueStatusState === 'loading' ||
    runtimeWatchdogState === 'loading' ||
    runtimeAutonomyCycleState === 'loading' ||
    silentMonitorsState === 'loading' ||
    missionStateState === 'loading'
  const runtimeSignalsLive =
    queueStatusState === 'ready' &&
    (runtimeWatchdogState === 'ready' || runtimeAutonomyCycleState === 'ready') &&
    silentMonitorsState === 'ready'
  const runtimePostureLabel = runtimeSignalsHaveErrors
    ? 'partial telemetry'
    : runtimeSignalsLive
      ? 'signals live'
      : runtimeSignalsRefreshing
        ? 'refreshing'
        : 'awaiting refresh'

  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-[2rem] border border-slate-200/70 bg-[radial-gradient(circle_at_top_left,rgba(34,197,94,0.16),transparent_28%),radial-gradient(circle_at_top_right,rgba(59,130,246,0.18),transparent_26%),linear-gradient(135deg,#f8fafc,rgba(240,249,255,0.92))] p-8 shadow-sm dark:border-slate-800 dark:bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.16),transparent_26%),radial-gradient(circle_at_top_right,rgba(244,114,182,0.14),transparent_28%),linear-gradient(135deg,rgba(2,6,23,0.98),rgba(8,15,41,0.95)_48%,rgba(15,23,42,0.96))]">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.14),transparent_0.65rem)] bg-[length:3rem_3rem] opacity-[0.08] dark:opacity-[0.12]" />
          <div className="absolute -left-16 top-10 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl dark:bg-cyan-400/14" />
          <div className="absolute right-0 top-0 h-64 w-64 rounded-full bg-fuchsia-400/8 blur-3xl dark:bg-fuchsia-400/12" />
        </div>

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl space-y-4">
            <Badge className="w-fit border border-slate-950/10 bg-slate-950 text-white dark:border-white/10 dark:bg-white/10 dark:text-white">
              Internal Superuser Surface
            </Badge>
            <div>
              <h1
                className="text-3xl font-semibold tracking-[-0.04em] text-slate-950 dark:text-slate-50 sm:text-4xl [font-family:'Space_Grotesk',var(--prakruti-font-display)]"
              >
                BijMantra Developer Control Plane
              </h1>
              <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-300">
                This surface now opens as a live development command deck. It still preserves the planner, autonomy, diagram, JSON, and orchestration tools, but the first view emphasizes real board state, execution clustering, and runtime telemetry instead of a flat admin shell.
              </p>
            </div>

            <div className="flex flex-wrap gap-2 text-xs text-slate-700 dark:text-slate-300">
              <span className="rounded-full border border-slate-300/80 bg-white/70 px-3 py-1.5 dark:border-white/10 dark:bg-white/5">
                Primary orchestrator: {primaryOrchestrator}
              </span>
              <span className="rounded-full border border-slate-300/80 bg-white/70 px-3 py-1.5 dark:border-white/10 dark:bg-white/5">
                Route: /admin/developer/master-board
              </span>
              <span className="rounded-full border border-slate-300/80 bg-white/70 px-3 py-1.5 dark:border-white/10 dark:bg-white/5">
                Persistence: {persistenceStatus.label}
              </span>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
                <CardContent className="flex items-center gap-3 p-4">
                  <Workflow className="h-5 w-5 text-emerald-600" />
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Active Lanes</div>
                    <div className="text-2xl font-semibold">{activeLaneCount}</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
                <CardContent className="flex items-center gap-3 p-4">
                  <GitBranch className="h-5 w-5 text-sky-600" />
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Sub-Plans</div>
                    <div className="text-2xl font-semibold">{subplanCount}</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
                <CardContent className="flex items-center gap-3 p-4">
                  <Sparkles className="h-5 w-5 text-violet-600" />
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Agent Roles</div>
                    <div className="text-2xl font-semibold">{parsedBoard?.agent_roles.length ?? 0}</div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-white/60 bg-white/85 dark:border-white/10 dark:bg-white/[0.04]">
                <CardContent className="flex items-center gap-3 p-4">
                  <Shield className="h-5 w-5 text-amber-600" />
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Dependencies</div>
                    <div className="text-2xl font-semibold">{dependencyCount}</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <Card className="w-full max-w-md border-white/60 bg-white/90 dark:border-white/10 dark:bg-white/[0.05]">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Operating Model</CardTitle>
              <CardDescription>
                Continuous internal control-plane surface for coordinated planning, telemetry inspection, and bounded developer execution.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                Route: <span className="font-mono text-foreground">/admin/developer/master-board</span>
              </p>
              <p>Visibility: hidden from workspace registry and normal navigation.</p>
              <p>
                Persistence: <span className={persistenceTone(persistenceStatus.tone)}>{persistenceStatus.label}</span>
              </p>
              <p>{persistenceStatus.description}</p>
              <p>
                Last updated: <span className="text-foreground">{new Date(lastUpdatedAt).toLocaleString()}</span>
              </p>
              <p>
                Live surfaces: active board persistence, overnight queue status, runtime watchdog state, and durable mission snapshots.
              </p>
              <div className="grid gap-2 pt-1 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 dark:border-white/10 dark:bg-slate-950/50">
                  <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Current view</div>
                  <div className="mt-1 flex items-center gap-2 text-foreground">
                    <Orbit className="h-4 w-4 text-sky-500" />
                    {activeTabLabel}
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-3 py-2 dark:border-white/10 dark:bg-slate-950/50">
                  <div className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Runtime posture</div>
                  <div className="mt-1 flex items-center gap-2 text-foreground">
                    <Activity className="h-4 w-4 text-emerald-500" />
                    {runtimePostureLabel}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="h-auto flex-wrap justify-start gap-2 rounded-[1.4rem] border border-slate-200/80 bg-white/85 p-2 shadow-sm dark:border-slate-800 dark:bg-slate-950/70">
          <TabsTrigger value="overview" className="rounded-xl px-4 py-2 data-[state=active]:bg-slate-950 data-[state=active]:text-white dark:data-[state=active]:bg-white dark:data-[state=active]:text-slate-950">
            Overview
          </TabsTrigger>
          <TabsTrigger value="indigenous">Indigenous Brain</TabsTrigger>
          <TabsTrigger value="planner">Planner</TabsTrigger>
          <TabsTrigger value="autonomy">Autonomy</TabsTrigger>
          <TabsTrigger value="mem0">Mem0</TabsTrigger>
          <TabsTrigger value="arielma">Diagram</TabsTrigger>
          <TabsTrigger value="json">JSON</TabsTrigger>
          <TabsTrigger value="orchestration">Orchestration</TabsTrigger>
        </TabsList>

        <OverviewTab
          lanes={lanes}
          autonomyAnalysis={autonomyAnalysis}
          selectedLane={selectedLane}
          recommendedLane={recommendedLane}
          persistenceStatus={persistenceStatus}
          lastUpdatedAt={lastUpdatedAt}
          primaryOrchestrator={parsedBoard?.control_plane.primary_orchestrator ?? null}
          agentRoleCount={parsedBoard?.agent_roles.length ?? 0}
          queueStatusState={queueStatusState}
          queueStatusRecord={queueStatusRecord}
          queueStatusError={queueStatusError}
          queueStatusLastRefreshedAt={queueStatusLastRefreshedAt}
          selectedLaneQueueJobId={selectedLaneQueueJobId}
          closeoutReceiptState={closeoutReceiptState}
          closeoutReceiptRecord={closeoutReceiptRecord}
          runtimeWatchdogState={runtimeWatchdogState}
          runtimeWatchdogRecord={runtimeWatchdogRecord}
          runtimeWatchdogError={runtimeWatchdogError}
          runtimeWatchdogLastCheckedAt={runtimeWatchdogLastCheckedAt}
          runtimeAutonomyCycleState={runtimeAutonomyCycleState}
          runtimeAutonomyCycleRecord={runtimeAutonomyCycleRecord}
          runtimeAutonomyCycleLastCheckedAt={runtimeAutonomyCycleLastCheckedAt}
          silentMonitorsState={silentMonitorsState}
          silentMonitorsRecord={silentMonitorsRecord}
          silentMonitorsError={silentMonitorsError}
          silentMonitorsLastCheckedAt={silentMonitorsLastCheckedAt}
          missionStateState={missionStateState}
          missionStateRecord={missionStateRecord}
          missionStateError={missionStateError}
          missionStateLastCheckedAt={missionStateLastCheckedAt}
          learningLedgerState={learningLedgerState}
          learningLedgerRecord={learningLedgerRecord}
          learningLedgerError={learningLedgerError}
          learningLedgerLastCheckedAt={learningLedgerLastCheckedAt}
          learningLedgerQuery={learningLedgerQuery}
          onRefreshQueueStatus={refreshQueueStatus}
          onRefreshLearnings={loadLearnings}
          onSetActiveTab={setActiveTab}
          onSelectLane={setSelectedLaneId}
        />

        <IndigenousTab
          indigenousBrainState={indigenousBrainState}
          indigenousBrainBrief={indigenousBrainBrief}
          indigenousBrainError={indigenousBrainError}
          indigenousBrainLastCheckedAt={indigenousBrainLastCheckedAt}
          onRefresh={refreshIndigenousBrain}
        />

        <PlannerTab
          jsonError={jsonError}
          parsedBoard={parsedBoard}
          lanes={lanes}
          selectedLane={selectedLane}
          availableAgents={availableAgents}
          extraOwnersInput={extraOwnersInput}
          boardVersionsState={boardVersionsState}
          boardVersionsRecord={boardVersionsRecord}
          boardVersionsError={boardVersionsError}
          boardVersionsLastCheckedAt={boardVersionsLastCheckedAt}
          boardRestoreState={boardRestoreState}
          lastBoardRestoreResult={lastBoardRestoreResult}
          onSetActiveTab={setActiveTab}
          onSelectLane={setSelectedLaneId}
          onSetExtraOwnersInput={setExtraOwnersInput}
          onResetBoard={resetBoard}
          onCreateLane={handleCreateLane}
          onDeleteLane={handleDeleteLane}
          onToggleOwner={handleToggleOwner}
          onAddExtraOwners={handleAddExtraOwners}
          onAddSubplan={handleAddSubplan}
          onUpdateBoardTextField={handleUpdateBoardTextField}
          onUpdateLaneField={updateLaneField}
          onUpdateValidationBasisField={updateValidationBasisField}
          onUpdateReviewStateField={updateReviewStateField}
          onUpdateSubplan={handleUpdateSubplan}
          onDeleteSubplan={handleDeleteSubplan}
          onRefreshBoardVersions={loadBoardVersions}
          onRestoreBoardVersion={handleRestoreBoardVersion}
          onExport={handleExport}
          onTriggerImport={triggerImport}
        />

        <AutonomyTab
          jsonError={jsonError}
          autonomyAnalysis={autonomyAnalysis}
          persistenceStatus={persistenceStatus}
          recommendedLane={recommendedLane}
          selectedLane={selectedLane}
          selectedLaneAnalysis={selectedLaneAnalysis}
          dispatchPacket={dispatchPacket}
          queueCandidate={queueCandidate}
          queueEntry={queueEntryMaterialization.entry}
          unresolvedQueueDependencyLaneIds={queueEntryMaterialization.unresolvedDependencyLaneIds}
          selectedLaneQueueJobId={selectedLaneQueueJobId}
          queueWriteState={queueWriteState}
          completionWriteState={completionWriteState}
          queueStatusState={queueStatusState}
          queueStatusRecord={queueStatusRecord}
          queueStatusError={queueStatusError}
          queueStatusLastRefreshedAt={queueStatusLastRefreshedAt}
          closeoutReceiptState={closeoutReceiptState}
          closeoutReceiptRecord={closeoutReceiptRecord}
          closeoutReceiptError={closeoutReceiptError}
          closeoutReceiptLastCheckedAt={closeoutReceiptLastCheckedAt}
          missionStateState={missionStateState}
          missionStateRecord={missionStateRecord}
          runtimeWatchdogState={runtimeWatchdogState}
          runtimeWatchdogRecord={runtimeWatchdogRecord}
          runtimeWatchdogError={runtimeWatchdogError}
          runtimeWatchdogLastCheckedAt={runtimeWatchdogLastCheckedAt}
          runtimeAutonomyCycleState={runtimeAutonomyCycleState}
          runtimeAutonomyCycleRecord={runtimeAutonomyCycleRecord}
          runtimeAutonomyCycleError={runtimeAutonomyCycleError}
          runtimeAutonomyCycleLastCheckedAt={runtimeAutonomyCycleLastCheckedAt}
          runtimeCompletionAssistState={runtimeCompletionAssistState}
          runtimeCompletionAssistRecord={runtimeCompletionAssistRecord}
          runtimeCompletionAssistError={runtimeCompletionAssistError}
          runtimeCompletionAssistLastCheckedAt={runtimeCompletionAssistLastCheckedAt}
          lastQueueWriteResult={lastQueueWriteResult}
          completionClosureSummary={completionClosureSummary}
          completionEvidenceInput={completionEvidenceInput}
          lastCompletionWriteResult={lastCompletionWriteResult}
          onSelectLane={setSelectedLaneId}
          onPromoteLane={handlePromoteLane}
          onCopyDispatchPacket={handleCopyDispatchPacket}
          onCopyQueueCandidate={handleCopyQueueCandidate}
          onCopyQueueEntry={handleCopyQueueEntry}
          onRefreshQueueStatus={refreshQueueStatus}
          onRefreshRecommendedTargets={handleRefreshRecommendedTargets}
          onRefreshAndRetryQueueWrite={handleRefreshAndRetryQueueWrite}
          onRefreshAndRetryLaneCompletion={handleRefreshAndRetryLaneCompletion}
          onCompletionClosureSummaryChange={setCompletionClosureSummary}
          onCompletionEvidenceInputChange={setCompletionEvidenceInput}
          onDraftLaneCompletionFromCurrentState={handleDraftLaneCompletionFromCurrentState}
          onDraftLaneCompletionForLane={handleDraftLaneCompletionForLane}
          onWriteLaneCompletion={handleWriteLaneCompletion}
          onWriteQueueEntry={handleWriteQueueEntry}
        />

  <Mem0Tab />

        <ArielmaTab parsedBoard={parsedBoard} jsonError={jsonError} />

        <JsonTab
          jsonError={jsonError}
          rawBoardJson={rawBoardJson}
          onRawBoardJsonChange={replaceBoardJson}
          onFormatJson={formatBoardJson}
          onExport={handleExport}
          onTriggerImport={triggerImport}
          onResetBoard={resetBoard}
          persistenceStatus={persistenceStatus}
        />

        <OrchestrationTab
          lanes={lanes}
          agentRoles={parsedBoard?.agent_roles ?? []}
          operatingCadence={parsedBoard?.control_plane.operating_cadence ?? []}
          persistenceStatus={persistenceStatus}
          selectedLane={selectedLane}
          selectedLaneAnalysis={selectedLaneAnalysis}
          queueStatusState={queueStatusState}
          queueStatusRecord={queueStatusRecord}
          selectedLaneQueueJobId={selectedLaneQueueJobId}
          closeoutReceiptState={closeoutReceiptState}
          closeoutReceiptRecord={closeoutReceiptRecord}
          missionStateState={missionStateState}
          missionStateRecord={missionStateRecord}
          missionStateError={missionStateError}
          missionStateLastCheckedAt={missionStateLastCheckedAt}
          missionDetailState={missionDetailState}
          missionDetailRecord={missionDetailRecord}
          missionDetailError={missionDetailError}
          missionDetailLastCheckedAt={missionDetailLastCheckedAt}
        />
      </Tabs>

      <input
        ref={fileInputRef}
        type="file"
        accept="application/json"
        className="hidden"
        aria-label="Import developer control-plane board JSON"
        onChange={(event) => void handleImport(event)}
      />

      {blockedLaneCount > 0 && (
        <Card className="border-amber-300/50 bg-amber-50 dark:border-amber-700/50 dark:bg-amber-950/30">
          <CardContent className="flex items-start gap-3 p-4 text-sm text-amber-900 dark:text-amber-200">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              {blockedLaneCount} blocked lane{blockedLaneCount === 1 ? '' : 's'} detected in the canonical board. Use the planner to clear dependencies and then let agents read the updated JSON contract.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ControlPlanePage
