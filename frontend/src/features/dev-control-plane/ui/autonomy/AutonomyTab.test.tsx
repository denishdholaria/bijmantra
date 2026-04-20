import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  defaultDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
} from '../../contracts/board'
import {
  createDeveloperLaneQueueCandidate,
  materializeDeveloperLaneQueueEntry,
} from '../../contracts/dispatch'
import { deriveDeveloperMasterBoardViewModel } from '../../state/selectors'
import { Tabs } from '@/components/ui/tabs'
import { AutonomyTab } from './AutonomyTab'

const decisionMemoryMocks = vi.hoisted(() => ({
  useDecisionMemory: vi.fn(),
}))

vi.mock('./useDecisionMemory', () => ({
  useDecisionMemory: decisionMemoryMocks.useDecisionMemory,
}))

beforeEach(() => {
  decisionMemoryMocks.useDecisionMemory.mockReturnValue({
    state: 'idle',
    record: null,
    error: null,
    lastCheckedAt: null,
    scope: {
      sourceLaneId: null,
      queueJobId: null,
      linkedMissionId: null,
    },
    resolution: {
      matchMode: 'none',
      fallbackUsed: false,
    },
  })
})

describe('AutonomyTab', () => {
  it('wires recommended-lane focus and selected-lane promotion through the container callbacks', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'planned'
    controlPlaneLane.outputs = []

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const onSelectLane = vi.fn()
    const onPromoteLane = vi.fn()
    const onCopyDispatchPacket = vi.fn()
    const onCopyQueueCandidate = vi.fn()
    const onCopyQueueEntry = vi.fn()
    const onRefreshQueueStatus = vi.fn()
    const onRefreshRecommendedTargets = vi.fn()
    const onRefreshAndRetryQueueWrite = vi.fn()
    const onCompletionClosureSummaryChange = vi.fn()
    const onCompletionEvidenceInputChange = vi.fn()
    const onDraftLaneCompletionFromCurrentState = vi.fn()
    const onDraftLaneCompletionForLane = vi.fn()
    const onRefreshAndRetryLaneCompletion = vi.fn()
    const onWriteLaneCompletion = vi.fn()
    const onWriteQueueEntry = vi.fn()
    const embeddedCompletionWritePreparation = {
      source_lane_id: 'control-plane',
      queue_job_id: 'overnight-lane-control-plane-token1',
      draft_source: 'stable-closeout-receipt' as const,
      queue_status: {
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-2',
        exists: true,
        job_count: 3,
        updated_at: '2026-03-18T11:31:00.000Z',
      },
      closeout_receipt: {
        exists: true,
        queue_job_id: 'overnight-lane-control-plane-token1',
        mission_id: 'runtime-mission-control-plane-token1',
        producer_key: 'openclaw-runtime',
        source_lane_id: 'control-plane',
        source_board_concurrency_token: 'token-control-1',
        runtime_profile_id: 'bijmantra-bca-local-verify',
        runtime_policy_sha256: 'policy-sha-1234',
        closeout_status: 'passed',
        state_refresh_required: true,
        receipt_recorded_at: '2026-03-18T11:33:00.000Z',
        started_at: '2026-03-18T11:32:30.000Z',
        finished_at: '2026-03-18T11:32:50.000Z',
        verification_evidence_ref:
          'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-2',
        closeout_commands: [],
        artifacts: [],
      },
      prepared_request: {
        source_board_concurrency_token: 'token-control-1',
        expected_queue_sha256: 'queue-sha-2',
        operator_intent: 'write-reviewed-lane-completion' as const,
        completion: {
          source_lane_id: 'control-plane',
          queue_job_id: 'overnight-lane-control-plane-token1',
          closure_summary:
            'Reviewed closeout receipt for lane control-plane (passed) after watchdog completion and canonical queue refresh.',
          evidence: [
            'Reviewed queue job overnight-lane-control-plane-token1 using watchdog closeout receipt before explicit board write-back.',
            'Watchdog closeout queue hash: queue-sha-2.',
          ],
          closeout_receipt: {
            queue_job_id: 'overnight-lane-control-plane-token1',
            artifact_paths: [],
            mission_id: 'runtime-mission-control-plane-token1',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'token-control-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-18T11:33:00.000Z',
            verification_evidence_ref:
              'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-2',
          },
        },
      },
    }
    decisionMemoryMocks.useDecisionMemory.mockReturnValue({
      state: 'ready',
      record: {
        total_count: 1,
        entries: [
          {
            learning_entry_id: 402,
            organization_id: 1,
            entry_type: 'verification-learning',
            source_classification: 'mission-state',
            title: 'Lane-scoped verification reminder',
            summary: 'Control-plane verification evidence should be refreshed before completion write-back.',
            confidence_score: 0.91,
            recorded_by_user_id: 1,
            recorded_by_email: 'ops@bijmantra.org',
            board_id: 'bijmantra-app-development-master-board',
            source_lane_id: 'control-plane',
            queue_job_id: 'overnight-lane-control-plane-token1',
            linked_mission_id: 'mission-runtime-job',
            approval_receipt_id: null,
            source_reference: 'mission:mission-runtime-job',
            evidence_refs: ['mission:mission-runtime-job'],
            summary_metadata: null,
            recorded_at: '2026-03-31T12:15:00.000Z',
          },
        ],
      },
      error: null,
      lastCheckedAt: '2026-04-05T11:13:00.000Z',
      scope: {
        sourceLaneId: 'control-plane',
        queueJobId: 'overnight-lane-control-plane-token1',
        linkedMissionId: 'mission-runtime-job',
      },
      resolution: {
        matchMode: 'exact-runtime',
        fallbackUsed: false,
      },
    })
    const queueCandidate = createDeveloperLaneQueueCandidate(view.dispatchPacket, 'token-1')
    const queueEntry = materializeDeveloperLaneQueueEntry(queueCandidate, {
      'platform-runtime': 'overnight-lane-platform-runtime-token1',
      'control-plane': 'overnight-lane-control-plane-token1',
      'delivery-lanes': 'overnight-lane-delivery-lanes-token1',
      'cross-domain-hub': 'overnight-lane-cross-domain-hub-token1',
    }).entry

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={queueCandidate}
          queueEntry={queueEntry}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-2',
            exists: true,
            job_count: 3,
            updated_at: '2026-03-18T11:31:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={{
            exists: true,
            queue_job_id: 'overnight-lane-control-plane-token1',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-18T11:33:00.000Z',
            started_at: '2026-03-18T11:32:30.000Z',
            finished_at: '2026-03-18T11:32:50.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-2',
            closeout_commands: [],
            artifacts: [],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          missionStateState="ready"
          missionStateRecord={{
            count: 1,
            missions: [
              {
                mission_id: 'mission-runtime-job',
                objective: 'Reviewed runtime closeout observed for control-plane lane',
                status: 'active',
                owner: 'OmShriMaatreNamaha',
                priority: 'p1',
                producer_key: 'openclaw-runtime',
                queue_job_id: 'runtime-job',
                source_lane_id: 'control-plane',
                source_board_concurrency_token: 'token-control-1',
                created_at: '2026-04-05T11:09:00.000Z',
                updated_at: '2026-04-05T11:10:00.000Z',
                subtask_total: 1,
                subtask_completed: 0,
                assignment_total: 1,
                evidence_count: 2,
                blocker_count: 0,
                escalation_needed: false,
                verification: {
                  passed: 1,
                  warned: 0,
                  failed: 0,
                  last_verified_at: '2026-04-05T11:09:30.000Z',
                },
                final_summary: 'Stable closeout receipt observed; awaiting explicit board closure write-back.',
              },
            ],
          }}
          runtimeAutonomyCycleState="ready"
          runtimeAutonomyCycleRecord={{
            exists: true,
            artifact_path:
              '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
            generated_at: '2026-04-05T11:10:24.399975+00:00',
            queue_path: '.agent/jobs/overnight-queue.json',
            window: 'nightly',
            max_jobs_per_run: 2,
            status_counts: { queued: 9 },
            selected_job_count: 1,
            blocked_job_count: 1,
            closeout_candidate_count: 1,
            next_action_count: 3,
            next_action_ordering_source: 'canonical-learning-exact-runtime',
            watchdog: {
              exists: true,
              state_path: 'runtime-artifacts/watchdog-state.json',
              last_check: '2026-04-05T10:00:00Z',
              gateway_healthy: false,
              state_is_stale: true,
              total_alerts: 2,
              job_errors: {
                'runtime-job': {
                  last_error: 'verification failed',
                  consecutive_errors: 3,
                },
              },
            },
            selected_jobs: [
              {
                job_id: 'closeout-follow-up',
                title: 'Closeout Follow Up',
                source_lane_id: 'platform-runtime',
                priority: 'p1',
                primary_agent: 'OmShriMaatreNamaha',
                trigger_reason: 'closeout-receipt:runtime-job:passed',
                source_task: '.ai/tasks/example.md',
              },
            ],
            blocked_jobs: [
              {
                job_id: 'watchdog-remediation',
                title: 'Watchdog Remediation',
                source_lane_id: 'cross-domain-hub',
                reason: 'trigger-disabled',
              },
            ],
            closeout_candidates: [
              {
                job_id: 'runtime-job',
                title: 'Runtime Job',
                source_lane_id: 'control-plane',
                queue_status: 'completed',
                closeout_status: 'passed',
                mission_id: 'mission-runtime-job',
                verification_evidence_ref:
                  'runtime-artifacts/mission-evidence/runtime-job/verification_1.json',
                path: 'runtime-artifacts/mission-evidence/runtime-job/closeout.json',
              },
            ],
            next_actions: [
              {
                action: 'prepare-completion-write-back',
                job_id: 'runtime-job',
                title: 'Runtime Job',
                source_lane_id: 'control-plane',
                reason: 'stable closeout ready for explicit board write-back',
                primary_agent: null,
                priority: null,
                mission_id: 'mission-runtime-job',
                receipt_path: 'runtime-artifacts/mission-evidence/runtime-job/closeout.json',
                state_path: null,
                detail: {
                  queueStatus: 'completed',
                  closeoutStatus: 'passed',
                  verificationEvidenceRef:
                    'runtime-artifacts/mission-evidence/runtime-job/verification_1.json',
                  completionWritePreparation: embeddedCompletionWritePreparation,
                },
              },
              {
                action: 'review-closeout-receipt',
                job_id: 'runtime-job',
                title: 'Runtime Job',
                source_lane_id: 'control-plane',
                reason: 'stable closeout receipt observed (passed)',
                primary_agent: null,
                priority: null,
                mission_id: 'mission-runtime-job',
                receipt_path: 'runtime-artifacts/mission-evidence/runtime-job/closeout.json',
                state_path: null,
                detail: null,
              },
              {
                action: 'dispatch-queue-job',
                job_id: 'closeout-follow-up',
                title: 'Closeout Follow Up',
                source_lane_id: 'platform-runtime',
                reason: 'closeout-receipt:runtime-job:passed',
                primary_agent: 'OmShriMaatreNamaha',
                priority: 'p1',
                mission_id: null,
                receipt_path: null,
                state_path: null,
                detail: null,
              },
            ],
          }}
          runtimeAutonomyCycleError={null}
          runtimeAutonomyCycleLastCheckedAt="2026-04-05T11:12:00.000Z"
          runtimeCompletionAssistState="ready"
          runtimeCompletionAssistRecord={{
            exists: true,
            artifact_path:
              '.github/docs/architecture/tracking/developer-control-plane-completion-assist.json',
            generated_at: '2026-04-06T12:05:00+00:00',
            status: 'staged',
            staged: true,
            explicit_write_required: true,
            message:
              'Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.',
            source: {
              endpoint:
                'http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle',
              autonomy_cycle_artifact_path:
                '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
              autonomy_cycle_generated_at: '2026-04-05T11:10:24.399975+00:00',
              next_action_ordering_source: 'canonical-learning-exact-runtime',
            },
            actionable_completion_write: {
              action: 'prepare-completion-write-back',
              actionIndex: 0,
              jobId: 'overnight-lane-control-plane-token1',
              sourceLaneId: 'control-plane',
              reason: 'stable closeout ready for explicit board write-back',
              missionId: 'runtime-mission-control-plane-token1',
              receiptPath: 'runtime-artifacts/mission-evidence/job/closeout.json',
              draftSource: 'stable-closeout-receipt',
              queueStatus: {
                queue_path: '.agent/jobs/overnight-queue.json',
                queue_sha256: 'queue-sha-2',
                exists: true,
                job_count: 3,
                updated_at: '2026-03-18T11:31:00.000Z',
              },
              closeoutReceipt: {
                exists: true,
                queue_job_id: 'overnight-lane-control-plane-token1',
                mission_id: 'runtime-mission-control-plane-token1',
                producer_key: 'openclaw-runtime',
                source_lane_id: 'control-plane',
                source_board_concurrency_token: 'token-control-1',
                runtime_profile_id: 'bijmantra-bca-local-verify',
                runtime_policy_sha256: 'policy-sha-1234',
                closeout_status: 'passed',
                state_refresh_required: true,
                receipt_recorded_at: '2026-03-18T11:33:00.000Z',
                started_at: '2026-03-18T11:32:30.000Z',
                finished_at: '2026-03-18T11:32:50.000Z',
                verification_evidence_ref:
                  'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
                queue_sha256_at_closeout: 'queue-sha-2',
                closeout_commands: [],
                artifacts: [],
              },
              preparedRequest: embeddedCompletionWritePreparation.prepared_request,
            },
          }}
          runtimeCompletionAssistError={null}
          runtimeCompletionAssistLastCheckedAt="2026-04-06T12:06:00+00:00"
          lastQueueWriteResult={{
            status: 'conflict',
            message: 'Queue write conflict; source board token is stale and must be refreshed',
            writtenJobId: null,
            previousQueueSha256: 'queue-sha-1',
            currentQueueSha256: 'queue-sha-2',
            queueUpdatedAt: '2026-03-18T11:31:00.000Z',
            approvalReceiptId: 41,
            approvalReceiptRecordedAt: '2026-03-18T11:31:05.000Z',
            conflictReason: 'stale-board-token',
            remediationMessage:
              'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.',
            refreshTargets: ['active-board'],
            retryPermittedAfterRefresh: true,
            currentBoardConcurrencyToken: 'token-2',
            conflictJobId: null,
          }}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'written',
            message:
              'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1. Approval receipt #52 recorded.',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'completed',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            approvalReceiptId: 52,
            approvalReceiptRecordedAt: '2026-03-18T11:32:05.000Z',
            conflictReason: null,
            remediationMessage: null,
            refreshTargets: [],
            retryPermittedAfterRefresh: null,
            currentBoardConcurrencyToken: 'token-3',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'completed',
            nextRecommendedLaneId: 'platform-runtime',
            nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
          }}
          onSelectLane={onSelectLane}
          onPromoteLane={onPromoteLane}
          onCopyDispatchPacket={onCopyDispatchPacket}
          onCopyQueueCandidate={onCopyQueueCandidate}
          onCopyQueueEntry={onCopyQueueEntry}
          onRefreshQueueStatus={onRefreshQueueStatus}
          onRefreshRecommendedTargets={onRefreshRecommendedTargets}
          onRefreshAndRetryQueueWrite={onRefreshAndRetryQueueWrite}
          onRefreshAndRetryLaneCompletion={onRefreshAndRetryLaneCompletion}
          onCompletionClosureSummaryChange={onCompletionClosureSummaryChange}
          onCompletionEvidenceInputChange={onCompletionEvidenceInputChange}
          onDraftLaneCompletionFromCurrentState={onDraftLaneCompletionFromCurrentState}
          onDraftLaneCompletionForLane={onDraftLaneCompletionForLane}
          onWriteLaneCompletion={onWriteLaneCompletion}
          onWriteQueueEntry={onWriteQueueEntry}
        />
      </Tabs>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Focus recommended lane' }))
    expect(onSelectLane).toHaveBeenCalledWith('platform-runtime')

    fireEvent.click(screen.getByRole('button', { name: 'Promote selected lane to active' }))
    expect(onPromoteLane).toHaveBeenCalledWith('control-plane')

    fireEvent.click(screen.getByRole('button', { name: 'Copy queue candidate' }))
    expect(onCopyQueueCandidate).toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Copy queue entry' }))
    expect(onCopyQueueEntry).toHaveBeenCalled()

    expect(screen.getAllByText(/Queue hash:/)).toHaveLength(3)
    expect(screen.getAllByText('queue-sha-2')).toHaveLength(4)
    expect(screen.getByText(/Job count:/)).toBeInTheDocument()
    expect(
      screen.getByText((content, element) => element?.textContent === 'Job count: 3')
    ).toBeInTheDocument()
    expect(screen.getByText('Queue write conflict; source board token is stale and must be refreshed')).toBeInTheDocument()
    expect(screen.getByText('Recommended refresh:')).toBeInTheDocument()
    expect(screen.getByText('Active board')).toBeInTheDocument()
    expect(screen.getByText('Retry after refresh:')).toBeInTheDocument()
    expect(screen.getByText('Permitted after review')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Refresh the shared board state, confirm the selected lane still materializes to the intended queue entry, then retry with the current board token.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('Structural Drift Warnings')).toBeInTheDocument()
    expect(screen.getByText('Reviewed Dispatch Pilot Preflight')).toBeInTheDocument()
    expect(screen.getByText('Current lane: control-plane. The first bounded pilot remains restricted to platform-runtime.')).toBeInTheDocument()
    expect(screen.getByText('Canonical learning context is visible')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Canonical learning ledger includes matching learnings for this scope. Recent learnings: Lane-scoped verification reminder.'
      )
    ).toBeInTheDocument()
    const [prepareWriteBackAction] = screen.getAllByText('prepare-completion-write-back')
    const reviewCloseoutAction = screen.getByText('review-closeout-receipt')
    const dispatchQueueAction = screen.getByText('dispatch-queue-job')
    expect(
      prepareWriteBackAction.compareDocumentPosition(dispatchQueueAction) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
    expect(
      reviewCloseoutAction.compareDocumentPosition(dispatchQueueAction) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
    expect(screen.getByText('Validation basis')).toBeInTheDocument()
    expect(screen.getByText('Completion closure')).toBeInTheDocument()
    expect(screen.getByText('No persisted closure for the selected lane yet.')).toBeInTheDocument()
    expect(screen.getByText('Autonomy Cycle')).toBeInTheDocument()
    expect(screen.getByText('Decision Memory')).toBeInTheDocument()
    expect(screen.getByText('memory-informed')).toBeInTheDocument()
    expect(screen.getByText('exact runtime match')).toBeInTheDocument()
    expect(screen.getByText('Lane-scoped verification reminder')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Control-plane verification evidence should be refreshed before completion write-back.'
      )
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Latest bounded next-action synthesis from queue, runtime watchdog, and closeout evidence.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('Completion Assist')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Headless reviewed completion assist derived from the hidden runtime autonomy-cycle response.'
      )
    ).toBeInTheDocument()
    expect(
      screen.getByText('Next-action ordering is biased by exact runtime-scope canonical learnings.')
    ).toBeInTheDocument()
    expect(screen.getByText('closeout-receipt:runtime-job:passed')).toBeInTheDocument()
    expect(
      screen.getAllByText('runtime-artifacts/mission-evidence/runtime-job/closeout.json').length
    ).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Focus lane platform-runtime' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Focus lane cross-domain-hub' })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Draft closeout for lane control-plane' })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Prepare board write-back for lane control-plane' })
    ).toBeInTheDocument()
    expect(screen.getByText('Mission alignment')).toBeInTheDocument()
    expect(screen.getAllByText('ready').length).toBeGreaterThan(0)
    expect(
      screen.getByText(
        'Durable mission mission-runtime-job is aligned to this queue job and lane and is still awaiting explicit board closure.'
      )
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Focus lane platform-runtime' }))
    expect(onSelectLane).toHaveBeenCalledWith('platform-runtime')
    fireEvent.click(
      screen.getByRole('button', { name: 'Prepare board write-back for lane control-plane' })
    )
    expect(onDraftLaneCompletionForLane).toHaveBeenNthCalledWith(
      1,
      'control-plane',
      embeddedCompletionWritePreparation
    )
    fireEvent.click(screen.getByRole('button', { name: 'Draft closeout for lane control-plane' }))
    expect(onDraftLaneCompletionForLane).toHaveBeenNthCalledWith(
      2,
      'control-plane',
      embeddedCompletionWritePreparation
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Draft from staged assist for lane control-plane' })
    )
    expect(onDraftLaneCompletionForLane).toHaveBeenNthCalledWith(
      3,
      'control-plane',
      embeddedCompletionWritePreparation
    )
    expect(screen.getByText('Closeout Receipt Source')).toBeInTheDocument()
    expect(screen.getByText('Stable closeout receipt found. Draft closeout will prefer watchdog evidence for this queue job.')).toBeInTheDocument()
    expect(screen.getAllByText('passed').length).toBeGreaterThan(0)
    expect(
      screen.getByText(
        'Focused control-plane contract and autonomy checkpoints remain the current execution-confidence basis for this lane.'
      )
    ).toBeInTheDocument()
    expect(screen.getAllByText('This lane does not declare expected outputs.').length).toBeGreaterThan(0)
    expect(
      screen.getByText(
        'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1. Approval receipt #52 recorded.'
      )
    ).toBeInTheDocument()
    expect(screen.getAllByText(/Approval receipt:/).length).toBeGreaterThan(1)
    expect(screen.getByText('#41')).toBeInTheDocument()
    expect(screen.getByText('#52')).toBeInTheDocument()
    expect(screen.getAllByText(/Approval recorded:/)).toHaveLength(2)
    expect(screen.getByText('Next recommended lane:')).toBeInTheDocument()
    expect(
      screen.getAllByText('App Runtime and Developer Surface Capabilities').length
    ).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: 'Refresh queue status' }))
    expect(onRefreshQueueStatus).toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Refresh recommended targets' }))
    expect(onRefreshRecommendedTargets).toHaveBeenCalledWith(['active-board'])

    fireEvent.click(screen.getByRole('button', { name: 'Refresh and retry queue write' }))
    expect(onRefreshAndRetryQueueWrite).toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Focus next recommended lane' }))
    expect(onSelectLane).toHaveBeenCalledWith('platform-runtime')
    expect(
      screen.queryByRole('button', { name: 'Promote next recommended lane' })
    ).not.toBeInTheDocument()

    expect(screen.getByRole('button', { name: 'Draft closeout from current state' })).toBeDisabled()

    expect(screen.getByRole('button', { name: 'Write completion to board' })).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Write queue entry' }))
    expect(onWriteQueueEntry).toHaveBeenCalled()
  })

  it('shows broader lane fallback when decision memory widens beyond exact runtime scope', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    decisionMemoryMocks.useDecisionMemory.mockReturnValue({
      state: 'ready',
      record: {
        total_count: 1,
        entries: [
          {
            learning_entry_id: 410,
            organization_id: 1,
            entry_type: 'pattern',
            source_classification: 'accepted-review',
            title: 'Accepted review enabled queue export for lane platform-runtime',
            summary:
              'Explicit spec_review and risk_review evidence supported queue export for lane platform-runtime.',
            confidence_score: 0.93,
            recorded_by_user_id: 1,
            recorded_by_email: 'ops@bijmantra.org',
            board_id: 'bijmantra-app-development-master-board',
            source_lane_id: 'platform-runtime',
            queue_job_id: null,
            linked_mission_id: null,
            approval_receipt_id: 77,
            source_reference: 'approval-receipt:77:accepted-review',
            evidence_refs: ['receipt:77'],
            summary_metadata: null,
            recorded_at: '2026-03-31T12:15:00.000Z',
          },
        ],
      },
      error: null,
      lastCheckedAt: '2026-04-05T12:10:00.000Z',
      scope: {
        sourceLaneId: 'platform-runtime',
        queueJobId: 'overnight-lane-platform-runtime-next-token',
        linkedMissionId: null,
      },
      resolution: {
        matchMode: 'lane-only',
        fallbackUsed: true,
      },
    })

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-platform-runtime-next-token"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-next',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-19T14:00:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-19T14:01:00.000Z"
          closeoutReceiptState="idle"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt={null}
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('broader lane fallback')).toBeInTheDocument()
    expect(
      screen.getByText(
        'No exact runtime-linked learning matched, so decision memory widened to broader lane scope.'
      )
    ).toBeInTheDocument()
  })

  it('keeps prepare-write-back gated until durable mission alignment is visible', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'planned'

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const onSelectLane = vi.fn()
    const onDraftLaneCompletionForLane = vi.fn()

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="runtime-job"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-04-05T11:12:00.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-04-05T11:12:00.000Z"
          missionStateState="ready"
          missionStateRecord={{ count: 0, missions: [] }}
          runtimeAutonomyCycleState="ready"
          runtimeAutonomyCycleRecord={{
            exists: true,
            artifact_path:
              '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
            generated_at: '2026-04-05T11:10:24.399975+00:00',
            queue_path: '.agent/jobs/overnight-queue.json',
            window: 'nightly',
            max_jobs_per_run: 2,
            status_counts: { queued: 1 },
            selected_job_count: 0,
            blocked_job_count: 0,
            closeout_candidate_count: 1,
            next_action_count: 1,
            next_action_ordering_source: 'artifact',
            watchdog: {
              exists: true,
              state_path: 'runtime-artifacts/watchdog-state.json',
              last_check: '2026-04-05T10:00:00Z',
              gateway_healthy: true,
              state_is_stale: false,
              total_alerts: 0,
              job_errors: {},
            },
            selected_jobs: [],
            blocked_jobs: [],
            closeout_candidates: [],
            next_actions: [
              {
                action: 'prepare-completion-write-back',
                job_id: 'runtime-job',
                title: 'Runtime Job',
                source_lane_id: 'control-plane',
                reason: 'stable closeout ready for explicit board write-back',
                primary_agent: null,
                priority: null,
                mission_id: 'mission-runtime-job',
                receipt_path: 'runtime-artifacts/mission-evidence/runtime-job/closeout.json',
                state_path: null,
                detail: {
                  queueStatus: 'completed',
                  closeoutStatus: 'passed',
                  verificationEvidenceRef:
                    'runtime-artifacts/mission-evidence/runtime-job/verification_1.json',
                },
              },
            ],
          }}
          runtimeAutonomyCycleError={null}
          runtimeAutonomyCycleLastCheckedAt="2026-04-05T11:12:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={onSelectLane}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onDraftLaneCompletionForLane={onDraftLaneCompletionForLane}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Mission alignment')).toBeInTheDocument()
    expect(screen.getAllByText('pending').length).toBeGreaterThan(0)
    expect(
      screen.getByText(
        'Stable closeout evidence exists, but no aligned durable mission snapshot is visible for this queue job and lane yet.'
      )
    ).toBeInTheDocument()

    const prepareButton = screen.getByRole('button', { name: 'Mission alignment required' })
    expect(prepareButton).toBeDisabled()

    expect(screen.getByRole('button', { name: 'Lane control-plane in focus' })).toBeDisabled()
    expect(onDraftLaneCompletionForLane).not.toHaveBeenCalled()
  })

  it('offers promote-next-lane action from completion handoff when the recommended lane is planned and ready', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')

    if (!controlPlaneLane || !platformRuntimeLane) {
      throw new Error('Expected default control-plane and platform-runtime lanes in board fixture')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-2',
      source_board_concurrency_token: 'token-3',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
    }
    platformRuntimeLane.status = 'planned'

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const onPromoteLane = vi.fn()

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="written"
          queueStatusState="ready"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'written',
            message: 'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1.',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'completed',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            conflictReason: null,
            remediationMessage: null,
            refreshTargets: [],
            retryPermittedAfterRefresh: null,
            currentBoardConcurrencyToken: 'token-3',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'completed',
            nextRecommendedLaneId: 'platform-runtime',
            nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
          }}
          onSelectLane={() => {}}
          onPromoteLane={onPromoteLane}
          onCopyDispatchPacket={() => {}}
          onCopyQueueCandidate={() => {}}
          onCopyQueueEntry={() => {}}
          onRefreshQueueStatus={() => {}}
          onCompletionClosureSummaryChange={() => {}}
          onCompletionEvidenceInputChange={() => {}}
          onDraftLaneCompletionFromCurrentState={() => {}}
          onWriteLaneCompletion={() => {}}
          onWriteQueueEntry={() => {}}
        />
      </Tabs>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Promote next recommended lane' }))
    expect(onPromoteLane).toHaveBeenCalledWith('platform-runtime')
    expect(
      screen.getByText('Promote this lane to active before staging the next reviewed queue entry.')
    ).toBeInTheDocument()
  })

  it('surfaces queue-staging-ready guidance from the completion handoff when the recommended lane is already active', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board fixture')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-2',
      source_board_concurrency_token: 'token-3',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
    }

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="written"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-2',
            exists: true,
            job_count: 3,
            updated_at: '2026-03-18T11:31:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'written',
            message: 'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1.',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'completed',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            conflictReason: null,
            remediationMessage: null,
            refreshTargets: [],
            retryPermittedAfterRefresh: null,
            currentBoardConcurrencyToken: 'token-3',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'completed',
            nextRecommendedLaneId: 'platform-runtime',
            nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
          }}
          onSelectLane={() => {}}
          onPromoteLane={() => {}}
          onCopyDispatchPacket={() => {}}
          onCopyQueueCandidate={() => {}}
          onCopyQueueEntry={() => {}}
          onRefreshQueueStatus={() => {}}
          onCompletionClosureSummaryChange={() => {}}
          onCompletionEvidenceInputChange={() => {}}
          onDraftLaneCompletionFromCurrentState={() => {}}
          onWriteLaneCompletion={() => {}}
          onWriteQueueEntry={() => {}}
        />
      </Tabs>
    )

    expect(
      screen.getByText('Reviewed queue staging is ready after you focus this lane.')
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Promote next recommended lane' })
    ).not.toBeInTheDocument()
  })

  it('offers a focused queue refresh action when the next recommended lane is only waiting on queue preflight state', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')

    if (!controlPlaneLane || !platformRuntimeLane) {
      throw new Error('Expected control-plane and platform-runtime lanes in default board fixture')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-2',
      source_board_concurrency_token: 'token-3',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
    }
    platformRuntimeLane.status = 'active'

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const onRefreshQueueStatus = vi.fn()

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="written"
          queueStatusState="idle"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt={null}
          closeoutReceiptState="available"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'written',
            message: 'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1.',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'completed',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            conflictReason: null,
            remediationMessage: null,
            refreshTargets: [],
            retryPermittedAfterRefresh: null,
            currentBoardConcurrencyToken: 'token-3',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'completed',
            nextRecommendedLaneId: 'platform-runtime',
            nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
          }}
          onSelectLane={() => {}}
          onPromoteLane={() => {}}
          onCopyDispatchPacket={() => {}}
          onCopyQueueCandidate={() => {}}
          onCopyQueueEntry={() => {}}
          onRefreshQueueStatus={onRefreshQueueStatus}
          onCompletionClosureSummaryChange={() => {}}
          onCompletionEvidenceInputChange={() => {}}
          onDraftLaneCompletionFromCurrentState={() => {}}
          onWriteLaneCompletion={() => {}}
          onWriteQueueEntry={() => {}}
        />
      </Tabs>
    )

    expect(
      screen.getByText(
        'Refresh queue status before staging the next reviewed queue entry so the preflight hash is explicit.'
      )
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Refresh queue status for next lane' }))
    expect(onRefreshQueueStatus).toHaveBeenCalled()
  })

  it('offers a focused active-board refresh action when the next recommended lane is only waiting on shared persistence sync', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')

    if (!controlPlaneLane || !platformRuntimeLane) {
      throw new Error('Expected control-plane and platform-runtime lanes in default board fixture')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-2',
      source_board_concurrency_token: 'token-3',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
    }
    platformRuntimeLane.status = 'active'

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const onRefreshRecommendedTargets = vi.fn()

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'fallback',
            label: 'Local fallback active',
            description: 'Backend persistence is unavailable; using local fallback state.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="written"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-2',
            exists: true,
            job_count: 3,
            updated_at: '2026-03-18T11:31:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'written',
            message: 'Lane control-plane marked completed from queue job overnight-lane-control-plane-token1.',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'completed',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            conflictReason: null,
            remediationMessage: null,
            refreshTargets: [],
            retryPermittedAfterRefresh: null,
            currentBoardConcurrencyToken: 'token-3',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'completed',
            nextRecommendedLaneId: 'platform-runtime',
            nextRecommendedLaneTitle: 'App Runtime and Developer Surface Capabilities',
          }}
          onSelectLane={() => {}}
          onPromoteLane={() => {}}
          onCopyDispatchPacket={() => {}}
          onCopyQueueCandidate={() => {}}
          onCopyQueueEntry={() => {}}
          onRefreshQueueStatus={() => {}}
          onRefreshRecommendedTargets={onRefreshRecommendedTargets}
          onCompletionClosureSummaryChange={() => {}}
          onCompletionEvidenceInputChange={() => {}}
          onDraftLaneCompletionFromCurrentState={() => {}}
          onWriteLaneCompletion={() => {}}
          onWriteQueueEntry={() => {}}
        />
      </Tabs>
    )

    expect(
      screen.getByText(
        'Shared canonical board must be active before staging the next reviewed queue entry.'
      )
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Refresh active board for next lane' }))
    expect(onRefreshRecommendedTargets).toHaveBeenCalledWith(['active-board'])
  })

  it('wires refresh-and-retry completion actions when conflict metadata permits retry', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'control-plane'
    )
    const onRefreshRecommendedTargets = vi.fn()
    const onRefreshAndRetryLaneCompletion = vi.fn()

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="conflict"
          queueStatusState="ready"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="missing"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary="Completion evidence was reviewed and accepted."
          completionEvidenceInput={'Focused tests passed\nQueue job completed'}
          lastCompletionWriteResult={{
            status: 'conflict',
            message:
              'Completion write-back conflict; source board token is stale and must be refreshed',
            noOp: false,
            laneId: 'control-plane',
            laneStatus: 'active',
            queueJobId: 'overnight-lane-control-plane-token1',
            queueSha256: 'queue-sha-2',
            conflictReason: 'stale-board-token',
            remediationMessage:
              'Refresh the shared board state and queue snapshot, confirm runtime evidence still matches, then retry completion write-back with the current board token.',
            refreshTargets: ['active-board', 'overnight-queue'],
            retryPermittedAfterRefresh: true,
            currentBoardConcurrencyToken: 'token-2',
            currentQueueSha256: 'queue-sha-2',
            currentLaneStatus: 'active',
          }}
          onSelectLane={() => {}}
          onPromoteLane={() => {}}
          onCopyDispatchPacket={() => {}}
          onCopyQueueCandidate={() => {}}
          onCopyQueueEntry={() => {}}
          onRefreshQueueStatus={() => {}}
          onRefreshRecommendedTargets={onRefreshRecommendedTargets}
          onRefreshAndRetryLaneCompletion={onRefreshAndRetryLaneCompletion}
          onCompletionClosureSummaryChange={() => {}}
          onCompletionEvidenceInputChange={() => {}}
          onDraftLaneCompletionFromCurrentState={() => {}}
          onWriteLaneCompletion={() => {}}
          onWriteQueueEntry={() => {}}
        />
      </Tabs>
    )

    fireEvent.click(screen.getByRole('button', { name: 'Refresh recommended targets' }))
    expect(onRefreshRecommendedTargets).toHaveBeenCalledWith([
      'active-board',
      'overnight-queue',
    ])

    fireEvent.click(screen.getByRole('button', { name: 'Refresh and retry completion write' }))
    expect(onRefreshAndRetryLaneCompletion).toHaveBeenCalled()
  })

  it('projects persisted completion closure for completed lanes', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-completed-1',
      source_board_concurrency_token: 'token-completed-1',
      closure_summary: 'Completion evidence was reviewed and accepted.',
      evidence: ['Focused tests passed', 'Queue job completed'],
      completed_at: '2026-03-18T11:32:00.000Z',
      closeout_receipt: {
        queue_job_id: 'overnight-lane-control-plane-token1',
        artifact_paths: ['metrics.json', 'confidential-docs/architecture/tracking/current-app-state.json'],
        mission_id: 'runtime-mission-control-plane-token1',
        producer_key: 'openclaw-runtime',
        source_lane_id: 'control-plane',
        source_board_concurrency_token: 'token-completed-1',
        runtime_profile_id: 'bijmantra-bca-local-verify',
        runtime_policy_sha256: 'policy-sha-1234',
        closeout_status: 'passed',
        state_refresh_required: true,
        receipt_recorded_at: '2026-03-18T11:33:00.000Z',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-completed-1',
      },
    }

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="idle"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt={null}
          closeoutReceiptState="idle"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt={null}
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Completion closure')).toBeInTheDocument()
    expect(screen.getByText('Completion evidence was reviewed and accepted.')).toBeInTheDocument()
    expect(screen.getAllByText('queue-sha-completed-1').length).toBeGreaterThan(0)
    expect(screen.getByText('token-completed-1')).toBeInTheDocument()
    expect(screen.getByText('Stable runtime provenance')).toBeInTheDocument()
    expect(screen.getByText('runtime-mission-control-plane-token1')).toBeInTheDocument()
    expect(screen.getByText('openclaw-runtime')).toBeInTheDocument()
    expect(screen.getByText('bijmantra-bca-local-verify')).toBeInTheDocument()
    expect(
      screen.getByText('runtime-artifacts/mission-evidence/control-plane/verification_1.json')
    ).toBeInTheDocument()
    expect(
      screen.getByText('metrics.json, confidential-docs/architecture/tracking/current-app-state.json')
    ).toBeInTheDocument()
  })

  it('disables queue writes when owner drift blocks the selected lane', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.owners = []

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )
    const queueCandidate = createDeveloperLaneQueueCandidate(view.dispatchPacket, 'token-1')
    const queueEntry = materializeDeveloperLaneQueueEntry(queueCandidate, {
      'platform-runtime': 'overnight-lane-platform-runtime-token1',
      'control-plane': 'overnight-lane-control-plane-token1',
      'delivery-lanes': 'overnight-lane-delivery-lanes-token1',
      'cross-domain-hub': 'overnight-lane-cross-domain-hub-token1',
    }).entry

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={queueCandidate}
          queueEntry={queueEntry}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="idle"
          queueStatusRecord={null}
          queueStatusError={null}
          queueStatusLastRefreshedAt={null}
          closeoutReceiptState="idle"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt={null}
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getAllByText('This lane has no meaningful owner assignments.').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Write queue entry' })).toBeDisabled()
  })

  it('surfaces queue fallback messaging when no stable closeout receipt exists yet', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'control-plane'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-2',
            exists: true,
            job_count: 3,
            updated_at: '2026-03-18T11:31:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-18T11:32:00.000Z"
          closeoutReceiptState="missing"
          closeoutReceiptRecord={{
            exists: false,
            queue_job_id: 'overnight-lane-control-plane-token1',
            closeout_status: null,
            state_refresh_required: null,
            receipt_recorded_at: null,
            started_at: null,
            finished_at: null,
            verification_evidence_ref: null,
            queue_sha256_at_closeout: null,
            closeout_commands: [],
            artifacts: [],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-18T11:34:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('No stable closeout receipt is present yet. Draft closeout will fall back to the refreshed queue snapshot.')).toBeInTheDocument()
    expect(screen.getByText('missing')).toBeInTheDocument()
  })

  it('shows a ready reviewed-dispatch preflight for platform-runtime when the pilot gates pass', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-platform-runtime-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-19T14:00:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-19T14:01:00.000Z"
          closeoutReceiptState="idle"
          closeoutReceiptRecord={null}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt={null}
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Reviewed Dispatch Pilot Preflight')).toBeInTheDocument()
    expect(screen.getByText('platform-runtime remains the first bounded reviewed-dispatch pilot lane.')).toBeInTheDocument()
    expect(screen.getByText('Queue hash queue-sha-platform-1 is loaded for reviewed preflight checks.')).toBeInTheDocument()
    expect(screen.getByText('No unresolved dependency lanes block this reviewed pilot entry.')).toBeInTheDocument()
    expect(screen.getByText('Autonomy analysis marks the selected lane as structurally ready.')).toBeInTheDocument()
  })

  it('surfaces a runtime evidence mismatch when watchdog reports verified completion without a closeout receipt', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-platform-runtime-token1234"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T08:29:26.506880+00:00',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T08:30:00.000Z"
          closeoutReceiptState="missing"
          closeoutReceiptRecord={{
            exists: false,
            queue_job_id: 'overnight-lane-platform-runtime-token1234',
            closeout_status: null,
            state_refresh_required: null,
            receipt_recorded_at: null,
            started_at: null,
            finished_at: null,
            verification_evidence_ref: null,
            queue_sha256_at_closeout: null,
            closeout_commands: [],
            artifacts: [],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-20T08:30:00.000Z"
          runtimeWatchdogState="ready"
          runtimeWatchdogRecord={{
            exists: true,
            state_path: 'runtime-artifacts/watchdog-state.json',
            auth_store_exists: false,
            auth_store_path: 'runtime-artifacts/agents/main/agent/auth-profiles.json',
            bootstrap_ready: false,
            bootstrap_status: 'auth-store-missing',
            mission_evidence_dir_exists: false,
            mission_evidence_dir_path: 'runtime-artifacts/mission-evidence',
            last_check: '2026-03-20T08:29:26.506880+00:00',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            completion_assist_advisory: {
              authority: 'advisory-only-derived',
              observed_from_path:
                '.github/docs/architecture/tracking/current-app-state.json',
              available: true,
              artifact_path:
                '.github/docs/architecture/tracking/developer-control-plane-completion-assist.json',
              status: 'staged',
              staged: true,
              explicit_write_required: true,
              message:
                'Staged reviewed completion assist for lane platform-runtime. This artifact does not perform explicit board write-back.',
              source_lane_id: 'platform-runtime',
              queue_job_id: 'overnight-lane-platform-runtime-token1234',
              draft_source: 'stable-closeout-receipt',
              receipt_path:
                'runtime-artifacts/mission-evidence/platform-runtime/closeout.json',
              source_endpoint:
                'http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle',
              autonomy_cycle_artifact_path:
                '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
              next_action_ordering_source: 'canonical-learning-exact-runtime',
              matched_selected_job_ids: [
                'overnight-lane-platform-runtime-token1234',
              ],
            },
            jobs: [
              {
                job_id: 'overnight-lane-platform-runtime-token1234',
                label: 'bijmantra:overnight-lane-platform-runtime-token1234',
                status: 'completed',
                started_at: '',
                duration_minutes: 0,
                last_error: '',
                consecutive_errors: 0,
                branch: 'auto/overnight-lane-platform-runtime-token1234',
                verification_passed: true,
              },
            ],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T08:30:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Runtime Watchdog')).toBeInTheDocument()
    expect(screen.getByText('Watchdog marked the selected queue job completed and verified, but the stable closeout receipt is still missing. Treat runtime closeout as incomplete until mission evidence is written.')).toBeInTheDocument()
    expect(screen.getByText('Runtime reports a verified completion, but the stable closeout receipt is absent. Do not treat the lane as trustworthily closed out until watchdog mission evidence is present.')).toBeInTheDocument()
    expect(
      screen.getAllByText(
        'Completion assist advisory is staged for lane platform-runtime and still needs explicit write-back review.'
      ).length
    ).toBeGreaterThan(0)
    expect(screen.getByText('Blocked: auth missing')).toBeInTheDocument()
    expect(
      screen.getByText(/runtime-artifacts\/agents\/main\/agent\/auth-profiles\.json/)
    ).toBeInTheDocument()
    expect(
      screen.getByText('.github/docs/architecture/tracking/current-app-state.json')
    ).toBeInTheDocument()
    expect(screen.getByText('Runtime bootstrap is blocked because the external auth store is missing. Seed runtime auth before expecting the reviewed dispatch pilot to project into execution.')).toBeInTheDocument()
    expect(screen.getByText('Autonomy Evidence Timeline')).toBeInTheDocument()
    expect(screen.getByText('Runtime watchdog reports verified completion, but stable receipt evidence is still missing.')).toBeInTheDocument()
    expect(screen.getByText('Stable closeout receipt is not available yet.')).toBeInTheDocument()
    expect(screen.getByText('Missing')).toBeInTheDocument()
    expect(screen.getByText('mismatch')).toBeInTheDocument()
  })

  it('surfaces stale runtime watchdog snapshots as non-current runtime truth', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-platform-runtime-token1234"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T08:30:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T08:30:00.000Z"
          closeoutReceiptState="missing"
          closeoutReceiptRecord={{
            exists: false,
            queue_job_id: 'overnight-lane-platform-runtime-token1234',
            closeout_status: null,
            state_refresh_required: null,
            receipt_recorded_at: null,
            started_at: null,
            finished_at: null,
            verification_evidence_ref: null,
            queue_sha256_at_closeout: null,
            closeout_commands: [],
            artifacts: [],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-20T08:30:00.000Z"
          runtimeWatchdogState="ready"
          runtimeWatchdogRecord={{
            exists: true,
            state_path: 'runtime-artifacts/watchdog-state.json',
            auth_store_exists: true,
            auth_store_path: 'runtime-artifacts/agents/main/agent/auth-profiles.json',
            bootstrap_ready: true,
            bootstrap_status: 'ready',
            mission_evidence_dir_exists: true,
            mission_evidence_dir_path: 'runtime-artifacts/mission-evidence',
            last_check: '2026-03-20T08:29:26.506880+00:00',
            state_is_stale: true,
            state_age_seconds: 900,
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [
              {
                job_id: 'overnight-lane-platform-runtime-token1234',
                label: 'bijmantra:overnight-lane-platform-runtime-token1234',
                status: 'completed',
                started_at: '',
                duration_minutes: 0,
                last_error: '',
                consecutive_errors: 0,
                branch: 'auto/overnight-lane-platform-runtime-token1234',
                verification_passed: true,
              },
            ],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T08:30:00.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('stale snapshot')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Runtime watchdog state is stale. Refresh or rerun the watchdog before trusting gateway health or selected queue-job status.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('Watchdog snapshot:')).toBeInTheDocument()
    expect(screen.getByText('Stale')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Runtime watchdog state is stale. Refresh or rerun the watchdog before treating gateway health or runtime job state as current truth.'
      )
    ).toBeInTheDocument()
  })

  it('shows receipt-observed durable mission-state before canonical closure write-back', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'active'

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-3',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T09:02:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T09:02:30.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={{
            exists: true,
            queue_job_id: 'overnight-lane-control-plane-token1',
            mission_id: 'runtime-mission-control-plane-token1',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'token-control-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-20T09:01:00.000Z',
            started_at: '2026-03-20T08:59:00.000Z',
            finished_at: '2026-03-20T09:00:30.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-3',
            closeout_commands: [],
            artifacts: [],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-20T09:02:30.000Z"
          missionStateState="ready"
          missionStateRecord={{
            count: 1,
            missions: [
              {
                mission_id: 'runtime-mission-control-plane-token1',
                objective: 'Reviewed runtime closeout observed for control-plane lane',
                status: 'active',
                owner: 'OmShriMaatreNamaha',
                priority: 'p1',
                producer_key: 'openclaw-runtime',
                queue_job_id: 'overnight-lane-control-plane-token1',
                source_lane_id: 'control-plane',
                source_board_concurrency_token: 'token-control-1',
                created_at: '2026-03-20T09:01:05.000Z',
                updated_at: '2026-03-20T09:01:30.000Z',
                subtask_total: 1,
                subtask_completed: 0,
                assignment_total: 1,
                evidence_count: 2,
                blocker_count: 0,
                escalation_needed: false,
                verification: {
                  passed: 1,
                  warned: 0,
                  failed: 0,
                  last_verified_at: '2026-03-20T09:01:15.000Z',
                },
                final_summary: 'Stable closeout receipt observed; awaiting explicit board closure write-back.',
              },
            ],
          }}
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Durable Mission Snapshot')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Stable receipt has already anchored an active durable mission. Canonical board closure is still pending.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('closure-pending')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Receipt observed. Durable mission runtime-mission-control-plane-token1 is active for overnight-lane-control-plane-token1, and canonical board closure is still pending.'
      )
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        'Stable receipt and durable mission snapshot are present, but explicit reviewed completion write-back is still the closure authority.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('Reviewed runtime closeout observed for control-plane lane')).toBeInTheDocument()
    expect(
      screen.getByText('Stable closeout receipt observed; awaiting explicit board closure write-back.')
    ).toBeInTheDocument()
  })

  it('shows a complete autonomy evidence chain when runtime receipt and board closure are aligned', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-3',
      source_board_concurrency_token: 'token-control-1',
      closure_summary: 'Reviewed closeout evidence was accepted.',
      evidence: ['Focused tests passed', 'Runtime receipt reviewed'],
      completed_at: '2026-03-20T09:00:00.000Z',
      closeout_receipt: {
        queue_job_id: 'overnight-lane-control-plane-token1',
        artifact_paths: ['metrics.json'],
        mission_id: 'runtime-mission-control-plane-token1',
        producer_key: 'openclaw-runtime',
        source_lane_id: 'control-plane',
        source_board_concurrency_token: 'token-control-1',
        runtime_profile_id: 'bijmantra-bca-local-verify',
        runtime_policy_sha256: 'policy-sha-1234',
        closeout_status: 'passed',
        state_refresh_required: true,
        receipt_recorded_at: '2026-03-20T09:01:00.000Z',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-3',
      },
    }

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="autonomy" onValueChange={() => {}}>
        <AutonomyTab
          jsonError={view.jsonError}
          autonomyAnalysis={view.autonomyAnalysis}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          recommendedLane={view.recommendedLane}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          dispatchPacket={view.dispatchPacket}
          queueCandidate={null}
          queueEntry={null}
          unresolvedQueueDependencyLaneIds={[]}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
          queueWriteState="idle"
          completionWriteState="idle"
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-3',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T09:02:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T09:02:30.000Z"
          closeoutReceiptState="available"
          closeoutReceiptRecord={{
            exists: true,
            queue_job_id: 'overnight-lane-control-plane-token1',
            mission_id: 'runtime-mission-control-plane-token1',
            producer_key: 'openclaw-runtime',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'token-control-1',
            runtime_profile_id: 'bijmantra-bca-local-verify',
            runtime_policy_sha256: 'policy-sha-1234',
            closeout_status: 'passed',
            state_refresh_required: true,
            receipt_recorded_at: '2026-03-20T09:01:00.000Z',
            started_at: '2026-03-20T08:59:00.000Z',
            finished_at: '2026-03-20T09:00:30.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-3',
            closeout_commands: [],
            artifacts: [
              {
                path: 'metrics.json',
                exists: true,
                sha256: 'abc123',
                modified_at: '2026-03-20T09:01:30.000Z',
              },
            ],
          }}
          closeoutReceiptError={null}
          closeoutReceiptLastCheckedAt="2026-03-20T09:02:30.000Z"
          runtimeWatchdogState="ready"
          runtimeWatchdogRecord={{
            exists: true,
            state_path: 'runtime-artifacts/watchdog-state.json',
            auth_store_exists: true,
            auth_store_path: 'runtime-artifacts/agents/main/agent/auth-profiles.json',
            bootstrap_ready: true,
            bootstrap_status: 'ready',
            mission_evidence_dir_exists: true,
            mission_evidence_dir_path: 'runtime-artifacts/mission-evidence',
            last_check: '2026-03-20T09:02:00.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [
              {
                job_id: 'overnight-lane-control-plane-token1',
                label: 'bijmantra:overnight-lane-control-plane-token1',
                status: 'completed',
                started_at: '2026-03-20T08:59:00.000Z',
                duration_minutes: 1.5,
                last_error: '',
                consecutive_errors: 0,
                branch: 'auto/overnight-lane-control-plane-token1',
                verification_passed: true,
              },
            ],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T09:02:30.000Z"
          lastQueueWriteResult={null}
          completionClosureSummary=""
          completionEvidenceInput=""
          lastCompletionWriteResult={null}
          onSelectLane={vi.fn()}
          onPromoteLane={vi.fn()}
          onCopyDispatchPacket={vi.fn()}
          onCopyQueueCandidate={vi.fn()}
          onCopyQueueEntry={vi.fn()}
          onRefreshQueueStatus={vi.fn()}
          onCompletionClosureSummaryChange={vi.fn()}
          onCompletionEvidenceInputChange={vi.fn()}
          onDraftLaneCompletionFromCurrentState={vi.fn()}
          onWriteLaneCompletion={vi.fn()}
          onWriteQueueEntry={vi.fn()}
        />
      </Tabs>
    )

    expect(screen.getByText('Autonomy Evidence Timeline')).toBeInTheDocument()
    expect(screen.getByText('Lane control-plane has persisted closure evidence in the canonical board.')).toBeInTheDocument()
    expect(screen.getByText('Queue queue-sha-3 is loaded for deterministic job overnight-lane-control-plane-token1.')).toBeInTheDocument()
    expect(screen.getByText('Watchdog verified runtime completion for overnight-lane-control-plane-token1.')).toBeInTheDocument()
    expect(screen.getByText('Stable receipt via bijmantra-bca-local-verify was recorded for overnight-lane-control-plane-token1.')).toBeInTheDocument()
    expect(screen.getByText('Canonical board closure persists reviewed runtime provenance for overnight-lane-control-plane-token1.')).toBeInTheDocument()
  })
})
