import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TabsContent } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

import type {
  DeveloperControlPlaneCloseoutReceiptResponse,
  DeveloperControlPlaneMissionDetailResponse,
  DeveloperControlPlaneMissionStateResponse,
  DeveloperControlPlaneOvernightQueueStatusResponse,
} from '../../api/activeBoard'
import type { DeveloperLaneAutonomyAnalysis } from '../../contracts/autonomy'
import type { DeveloperBoardAgentRole, DeveloperBoardLane } from '../../contracts/board'
import {
  buildReviewedDispatchPilotChecks,
  countBlockingReviewedDispatchPilotChecks,
} from '../../reviewedDispatch'
import type { DeveloperControlPlanePersistenceStatus } from '../../state/selectors'
import { getSelectedLaneMissionSummary } from '../missionLinking'
import { statusTone } from '../planner/shared'

type OrchestrationTabProps = {
  lanes: DeveloperBoardLane[]
  agentRoles: DeveloperBoardAgentRole[]
  operatingCadence: string[]
  persistenceStatus: DeveloperControlPlanePersistenceStatus
  selectedLane: DeveloperBoardLane | null
  selectedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null
  queueStatusState: 'idle' | 'loading' | 'ready' | 'error'
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null
  selectedLaneQueueJobId?: string | null
  closeoutReceiptState?: 'idle' | 'loading' | 'available' | 'missing' | 'error'
  closeoutReceiptRecord?: DeveloperControlPlaneCloseoutReceiptResponse | null
  missionStateState: 'idle' | 'loading' | 'ready' | 'error'
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
  missionStateError: string | null
  missionStateLastCheckedAt: string | null
  missionDetailState: 'idle' | 'loading' | 'ready' | 'error'
  missionDetailRecord: DeveloperControlPlaneMissionDetailResponse | null
  missionDetailError: string | null
  missionDetailLastCheckedAt: string | null
}

function reviewedDispatchTone(blockingCount: number) {
  return blockingCount === 0
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
}

function checkTone(passed: boolean) {
  return passed
    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
    : 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
}

function missionStateTone(
  state: OrchestrationTabProps['missionStateState'],
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
) {
  if (state === 'error') {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (state === 'loading') {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  if (state === 'ready' && (missionStateRecord?.count ?? 0) > 0) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  if (state === 'ready') {
    return 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
  }

  return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function missionDetailTone(
  state: OrchestrationTabProps['missionDetailState'],
  missionDetailRecord: DeveloperControlPlaneMissionDetailResponse | null
) {
  if (state === 'error') {
    return 'bg-rose-500/15 text-rose-700 dark:text-rose-300'
  }

  if (state === 'loading') {
    return 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
  }

  if (state === 'ready' && missionDetailRecord) {
    return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
  }

  return 'bg-slate-500/15 text-slate-700 dark:text-slate-300'
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

export function OrchestrationTab({
  lanes,
  agentRoles,
  operatingCadence,
  persistenceStatus,
  selectedLane,
  selectedLaneAnalysis,
  queueStatusState,
  queueStatusRecord,
  selectedLaneQueueJobId = null,
  closeoutReceiptState = 'idle',
  closeoutReceiptRecord = null,
  missionStateState,
  missionStateRecord,
  missionStateError,
  missionStateLastCheckedAt,
  missionDetailState,
  missionDetailRecord,
  missionDetailError,
  missionDetailLastCheckedAt,
}: OrchestrationTabProps) {
  const reviewedDispatchChecks = buildReviewedDispatchPilotChecks(
    persistenceStatus,
    selectedLane,
    selectedLaneAnalysis,
    queueStatusState,
    queueStatusRecord
  )
  const blockingReviewedDispatchChecks = countBlockingReviewedDispatchPilotChecks(
    reviewedDispatchChecks
  )
  const selectedLaneMissionId =
    closeoutReceiptRecord?.mission_id ?? selectedLane?.closure?.closeout_receipt?.mission_id ?? null
  const selectedLaneMissionSummary = getSelectedLaneMissionSummary({
    selectedLane,
    missionStateRecord,
    closeoutReceiptRecord,
    selectedLaneQueueJobId,
  })
  const selectedLaneMissionDetailAligned =
    selectedLaneMissionSummary?.mission_id != null &&
    missionDetailRecord?.mission_id === selectedLaneMissionSummary.mission_id
  const selectedLaneMissionClosurePending =
    selectedLaneMissionSummary !== null &&
    !selectedLane?.closure &&
    closeoutReceiptState === 'available' &&
    closeoutReceiptRecord?.exists === true

  return (
    <TabsContent value="orchestration" className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Lane Matrix</CardTitle>
            <CardDescription>
              Explicit lanes, dependencies, outputs, and sub-plans for coordinated execution.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {lanes.map((lane) => (
              <div key={lane.id} className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.26em] text-muted-foreground">{lane.id}</div>
                    <h3 className="mt-1 text-lg font-semibold">{lane.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground">{lane.objective}</p>
                  </div>
                  <span className={cn('rounded-full px-3 py-1 text-xs font-medium capitalize', statusTone(lane.status))}>
                    {lane.status}
                  </span>
                </div>

                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Owners</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {lane.owners.map((owner) => (
                        <span key={owner} className="rounded-full border border-border/70 px-2.5 py-1 text-xs">
                          {owner}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Dependencies</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {lane.dependencies.length > 0 ? lane.dependencies.map((dependency) => (
                        <span key={dependency} className="rounded-full border border-border/70 px-2.5 py-1 text-xs">
                          {dependency}
                        </span>
                      )) : <span className="text-sm text-muted-foreground">Independent lane</span>}
                    </div>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Inputs</div>
                    <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                      {lane.inputs.map((input) => <div key={input}>{input}</div>)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Outputs</div>
                    <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                      {lane.outputs.map((output) => <div key={output}>{output}</div>)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Completion Criteria</div>
                    <div className="mt-2 space-y-2 text-sm text-muted-foreground">
                      {lane.completion_criteria.map((criterion) => <div key={criterion}>{criterion}</div>)}
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Sub-Plans</div>
                  <div className="mt-2 grid gap-3 md:grid-cols-2">
                    {lane.subplans.map((subplan) => (
                      <div key={subplan.id} className="rounded-xl border border-border/70 bg-background/70 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-sm font-medium">{subplan.title}</div>
                          <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-medium capitalize', statusTone(subplan.status))}>
                            {subplan.status}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">{subplan.objective}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Reviewed Dispatch Readiness</CardTitle>
              <CardDescription>
                Read-only projection of the first bounded pilot gate using the shared reviewed-dispatch contract.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Selected Pilot Lane</div>
                  <div className="mt-1 font-medium text-foreground">{selectedLane?.id ?? 'No lane selected'}</div>
                </div>
                <span className={cn('rounded-full px-3 py-1 text-xs font-medium capitalize', reviewedDispatchTone(blockingReviewedDispatchChecks))}>
                  {blockingReviewedDispatchChecks === 0 ? 'ready' : 'blocked'}
                </span>
              </div>

              <div className="space-y-3 text-sm text-muted-foreground">
                {reviewedDispatchChecks.map((check) => (
                  <div key={check.id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-medium capitalize', checkTone(check.passed))}>
                        {check.passed ? 'pass' : 'blocking'}
                      </span>
                      <span className="font-medium text-foreground">{check.label}</span>
                    </div>
                    <div className="mt-2">{check.detail}</div>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Selected Lane Closure</div>
                {selectedLane?.closure ? (
                  <div className="mt-3 space-y-3 text-sm text-muted-foreground">
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div>
                        Queue job id:{' '}
                        <span className="font-mono text-foreground">{selectedLane.closure.queue_job_id}</span>
                      </div>
                      <div>
                        Completed at:{' '}
                        <span className="text-foreground">{formatTimestamp(selectedLane.closure.completed_at)}</span>
                      </div>
                    </div>
                    <div>{selectedLane.closure.closure_summary}</div>
                    {selectedLane.closure.closeout_receipt ? (
                      <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                        <div className="font-medium text-foreground">Stable runtime provenance</div>
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          <div>
                            Mission id:{' '}
                            <span className="font-mono text-foreground">
                              {selectedLane.closure.closeout_receipt.mission_id ?? 'Not available'}
                            </span>
                          </div>
                          <div>
                            Producer:{' '}
                            <span className="text-foreground">
                              {selectedLane.closure.closeout_receipt.producer_key ?? 'Not available'}
                            </span>
                          </div>
                          <div>
                            Runtime profile:{' '}
                            <span className="font-mono text-foreground">
                              {selectedLane.closure.closeout_receipt.runtime_profile_id ?? 'Not available'}
                            </span>
                          </div>
                          <div>
                            Receipt recorded:{' '}
                            <span className="text-foreground">
                              {formatTimestamp(selectedLane.closure.closeout_receipt.receipt_recorded_at ?? null)}
                            </span>
                          </div>
                        </div>
                        <div className="mt-2">
                          Verification evidence:{' '}
                          <span className="font-mono text-foreground break-all">
                            {selectedLane.closure.closeout_receipt.verification_evidence_ref ?? 'Not available'}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="rounded-xl border border-amber-300/50 bg-amber-50/60 p-3 text-amber-700 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-300">
                        Selected lane has persisted closure evidence, but no stable runtime closeout receipt subset was recorded.
                      </div>
                    )}
                  </div>
                ) : selectedLane?.status === 'completed' ? (
                  <div className="mt-3 text-sm text-rose-700 dark:text-rose-300">
                    Selected lane is completed but has no persisted closure evidence.
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-muted-foreground">
                    No persisted closure is recorded for the selected lane.
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Selected Lane Mission Link</div>
                {selectedLaneMissionSummary ? (
                  <div className="mt-3 space-y-3 text-sm text-muted-foreground">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="font-medium text-foreground">{selectedLaneMissionSummary.objective}</div>
                        <div className="mt-1 font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground">
                          {selectedLaneMissionSummary.mission_id}
                        </div>
                      </div>
                      <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-medium capitalize', statusTone(selectedLaneMissionSummary.status as DeveloperBoardLane['status']))}>
                        {selectedLaneMissionSummary.status}
                      </span>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div>
                        Producer: <span className="text-foreground">{selectedLaneMissionSummary.producer_key ?? 'Unknown'}</span>
                      </div>
                      <div>
                        Evidence items: <span className="text-foreground">{selectedLaneMissionSummary.evidence_count}</span>
                      </div>
                      <div>
                        Queue job: <span className="font-mono text-foreground">{selectedLaneMissionSummary.queue_job_id ?? 'Not available'}</span>
                      </div>
                      <div>
                        Source lane: <span className="font-mono text-foreground">{selectedLaneMissionSummary.source_lane_id ?? 'Not available'}</span>
                      </div>
                    </div>
                    {selectedLaneMissionSummary.source_board_concurrency_token ? (
                      <div>
                        Board token:{' '}
                        <span className="font-mono text-foreground">
                          {selectedLaneMissionSummary.source_board_concurrency_token}
                        </span>
                      </div>
                    ) : null}
                    <div>
                      {selectedLaneMissionClosurePending
                        ? selectedLaneMissionDetailAligned
                          ? 'Stable receipt observed. Durable mission detail is aligned, and canonical board closure is still pending.'
                          : 'Stable receipt observed. Durable mission snapshot is active before canonical board closure.'
                        : selectedLaneMissionDetailAligned
                          ? 'Durable mission detail is aligned to the selected lane receipt mission.'
                          : selectedLaneMissionId
                            ? 'Durable mission summary is linked, but detailed mission inspection is still loading or pointed at another snapshot.'
                            : 'Durable mission summary is linked by selected lane and queue context before canonical closure is written.'}
                    </div>
                  </div>
                ) : selectedLaneMissionId ? (
                  <div className="mt-3 rounded-xl border border-amber-300/50 bg-amber-50/60 p-3 text-sm text-amber-700 dark:border-amber-700/40 dark:bg-amber-950/20 dark:text-amber-300">
                    No durable mission snapshot is currently linked to runtime mission {selectedLaneMissionId}.
                  </div>
                ) : selectedLane?.closure?.closeout_receipt ? (
                  <div className="mt-3 text-sm text-muted-foreground">
                    Selected lane closure includes runtime provenance, but no stable mission id was recorded.
                  </div>
                ) : selectedLane?.closure ? (
                  <div className="mt-3 text-sm text-muted-foreground">
                    Selected lane closure has no stable runtime receipt, so no durable mission link can be resolved yet.
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-muted-foreground">
                    Select or complete a lane with reviewed runtime provenance to resolve durable mission linkage.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Orchestrator Mission State</CardTitle>
              <CardDescription>
                Read-only durable mission-state summaries for OmShriMaatreNamaha and current internal orchestrator producers.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-3 rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Mission Feed</div>
                  <div className="mt-1 font-medium text-foreground">{missionStateRecord?.count ?? 0} mission snapshot{(missionStateRecord?.count ?? 0) === 1 ? '' : 's'}</div>
                </div>
                <span className={cn('rounded-full px-3 py-1 text-xs font-medium capitalize', missionStateTone(missionStateState, missionStateRecord))}>
                  {missionStateState === 'ready'
                    ? (missionStateRecord?.count ?? 0) > 0
                      ? 'active'
                      : 'empty'
                    : missionStateState}
                </span>
              </div>

              <div className="space-y-3 text-sm text-muted-foreground">
                <div>Last checked: <span className="text-foreground">{formatTimestamp(missionStateLastCheckedAt)}</span></div>
                {missionStateState === 'ready' && missionStateRecord && missionStateRecord.count > 0 ? (
                  missionStateRecord.missions.map((mission) => (
                    <div key={mission.mission_id} className="rounded-xl border border-border/70 bg-muted/20 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <div className="font-medium text-foreground">{mission.objective}</div>
                          <div className="mt-1 text-xs uppercase tracking-[0.22em] text-muted-foreground">{mission.mission_id}</div>
                        </div>
                        <span className={cn('rounded-full px-2.5 py-1 text-[11px] font-medium capitalize', statusTone(mission.status as DeveloperBoardLane['status']))}>
                          {mission.status}
                        </span>
                      </div>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        <div>Producer: <span className="text-foreground">{mission.producer_key ?? 'Unknown'}</span></div>
                        <div>Priority: <span className="text-foreground">{mission.priority}</span></div>
                        <div>Queue job: <span className="font-mono text-foreground">{mission.queue_job_id ?? 'Not available'}</span></div>
                        <div>Source lane: <span className="font-mono text-foreground">{mission.source_lane_id ?? 'Not available'}</span></div>
                        <div>Subtasks: <span className="text-foreground">{mission.subtask_completed}/{mission.subtask_total}</span></div>
                        <div>Assignments: <span className="text-foreground">{mission.assignment_total}</span></div>
                        <div>Evidence items: <span className="text-foreground">{mission.evidence_count}</span></div>
                        <div>Blockers: <span className="text-foreground">{mission.blocker_count}</span></div>
                      </div>
                      {mission.source_board_concurrency_token ? (
                        <div className="mt-2">
                          Board token:{' '}
                          <span className="font-mono text-foreground">
                            {mission.source_board_concurrency_token}
                          </span>
                        </div>
                      ) : null}
                      <div className="mt-3">Verification: <span className="text-foreground">{mission.verification.passed} passed, {mission.verification.warned} warned, {mission.verification.failed} failed</span></div>
                      {mission.final_summary && (
                        <div className="mt-2 text-muted-foreground">{mission.final_summary}</div>
                      )}
                    </div>
                  ))
                ) : missionStateState === 'error' ? (
                  <div className="rounded-xl border border-rose-300/50 bg-rose-50/60 p-3 text-rose-700 dark:border-rose-700/40 dark:bg-rose-950/20 dark:text-rose-300">
                    {missionStateError ?? 'Mission-state inspection is unavailable.'}
                  </div>
                ) : (
                  <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
                    {(missionStateRecord?.count ?? 0) === 0
                      ? 'No durable OmShriMaatreNamaha mission snapshots are recorded for this organization yet.'
                      : 'Mission-state inspection will appear here after the first refresh.'}
                  </div>
                )}

                <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Mission Detail</div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        Expanded read-only audit detail for the selected linked mission when available, otherwise the latest durable OmShriMaatreNamaha snapshot.
                      </div>
                    </div>
                    <span className={cn('rounded-full px-3 py-1 text-xs font-medium capitalize', missionDetailTone(missionDetailState, missionDetailRecord))}>
                      {missionDetailState === 'ready' ? 'loaded' : missionDetailState}
                    </span>
                  </div>

                  <div className="mt-3 text-sm text-muted-foreground">
                    Last checked: <span className="text-foreground">{formatTimestamp(missionDetailLastCheckedAt)}</span>
                  </div>

                  {missionDetailState === 'ready' && missionDetailRecord ? (
                    <div className="mt-4 space-y-4 text-sm text-muted-foreground">
                      <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                        <div className="font-medium text-foreground">{missionDetailRecord.objective}</div>
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          <div>Mission id: <span className="font-mono text-foreground">{missionDetailRecord.mission_id}</span></div>
                          <div>Escalation needed: <span className="text-foreground">{missionDetailRecord.escalation_needed ? 'Yes' : 'No'}</span></div>
                        </div>
                      </div>

                      <div className="grid gap-3 xl:grid-cols-2">
                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Subtasks</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.subtasks.length > 0 ? missionDetailRecord.subtasks.map((subtask) => (
                              <div key={subtask.id}>
                                <div className="text-foreground">{subtask.title}</div>
                                <div>Status: <span className="text-foreground">{subtask.status}</span></div>
                                <div>Owner: <span className="text-foreground">{subtask.owner_role}</span></div>
                              </div>
                            )) : <div>No subtasks recorded.</div>}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Assignments</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.assignments.length > 0 ? missionDetailRecord.assignments.map((assignment) => (
                              <div key={assignment.id}>
                                <div className="text-foreground">{assignment.assigned_role}</div>
                                <div>{assignment.handoff_reason}</div>
                              </div>
                            )) : <div>No assignments recorded.</div>}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Evidence</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.evidence_items.length > 0 ? missionDetailRecord.evidence_items.map((item) => (
                              <div key={item.id}>
                                <div className="text-foreground">{item.kind}</div>
                                <div>{item.summary}</div>
                                <div>Source: <span className="font-mono text-foreground">{item.source_path}</span></div>
                              </div>
                            )) : <div>No evidence recorded.</div>}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Verification</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.verification_runs.length > 0 ? missionDetailRecord.verification_runs.map((verification) => (
                              <div key={verification.id}>
                                <div className="text-foreground">{verification.verification_type}</div>
                                <div>Result: <span className="text-foreground">{verification.result}</span></div>
                                <div>Evidence ref: <span className="font-mono text-foreground">{verification.evidence_ref ?? 'Not available'}</span></div>
                              </div>
                            )) : <div>No verification runs recorded.</div>}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Decision Notes</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.decision_notes.length > 0 ? missionDetailRecord.decision_notes.map((note) => (
                              <div key={note.id}>
                                <div className="text-foreground">{note.decision_class}</div>
                                <div>Authority: <span className="text-foreground">{note.authority_source}</span></div>
                              </div>
                            )) : <div>No decision notes recorded.</div>}
                          </div>
                        </div>

                        <div className="rounded-xl border border-border/70 bg-background/70 p-3">
                          <div className="font-medium text-foreground">Blockers</div>
                          <div className="mt-3 space-y-3">
                            {missionDetailRecord.blockers.length > 0 ? missionDetailRecord.blockers.map((blocker) => (
                              <div key={blocker.id}>
                                <div className="text-foreground">{blocker.blocker_type}</div>
                                <div>{blocker.impact}</div>
                              </div>
                            )) : <div>No blockers recorded.</div>}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : missionDetailState === 'error' ? (
                    <div className="mt-4 rounded-xl border border-rose-300/50 bg-rose-50/60 p-3 text-rose-700 dark:border-rose-700/40 dark:bg-rose-950/20 dark:text-rose-300">
                      {missionDetailError ?? 'Mission detail is unavailable.'}
                    </div>
                  ) : (
                    <div className="mt-4 rounded-xl border border-border/70 bg-background/70 p-3 text-sm text-muted-foreground">
                      Mission detail will appear here after the first durable snapshot is refreshed.
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agent Contract</CardTitle>
              <CardDescription>Roles that should read from and write back to the board.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {agentRoles.map((role) => (
                <div key={role.agent} className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                  <div className="font-medium">{role.agent}</div>
                  <p className="mt-1 text-sm text-muted-foreground">{role.role}</p>
                  <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                    <div><span className="font-medium text-foreground">Reads:</span> {role.reads.join(', ')}</div>
                    <div><span className="font-medium text-foreground">Writes:</span> {role.writes.join(', ')}</div>
                    <div><span className="font-medium text-foreground">Escalates:</span> {role.escalation.join(', ')}</div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Control Plane Cadence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              {operatingCadence.map((step) => (
                <div key={step} className="rounded-xl border border-border/70 bg-muted/20 px-3 py-2">
                  {step}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </TabsContent>
  )
}