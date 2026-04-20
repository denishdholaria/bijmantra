import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Tabs } from '@/components/ui/tabs'
import { OrchestrationTab } from './OrchestrationTab'

import {
  defaultDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
} from '../../contracts/board'
import { deriveDeveloperMasterBoardViewModel } from '../../state/selectors'

describe('OrchestrationTab', () => {
  it('renders lane matrix, agent contract, and cadence as a projection of canonical board state', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="orchestration" onValueChange={() => {}}>
        <OrchestrationTab
          lanes={defaultDeveloperMasterBoard.lanes}
          agentRoles={defaultDeveloperMasterBoard.agent_roles}
          operatingCadence={defaultDeveloperMasterBoard.control_plane.operating_cadence}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:00:00.000Z',
          }}
          missionStateState="ready"
          missionStateRecord={{
            count: 1,
            missions: [
              {
                mission_id: 'mission-1',
                objective: 'Control-plane reviewed dispatch runtime inspection',
                status: 'completed',
                owner: 'OmShriMaatreNamaha',
                priority: 'p1',
                producer_key: 'chaitanya',
                queue_job_id: null,
                source_lane_id: null,
                source_board_concurrency_token: null,
                created_at: '2026-03-20T00:00:00.000Z',
                updated_at: '2026-03-20T00:05:00.000Z',
                subtask_total: 1,
                subtask_completed: 1,
                assignment_total: 1,
                evidence_count: 1,
                blocker_count: 1,
                escalation_needed: true,
                verification: {
                  passed: 1,
                  warned: 0,
                  failed: 0,
                  last_verified_at: '2026-03-20T00:04:00.000Z',
                },
                final_summary: 'Runtime watchdog and durable mission-state inspection recorded.',
              },
            ],
          }}
          missionStateError={null}
          missionStateLastCheckedAt="2026-03-20T00:06:00.000Z"
          missionDetailState="ready"
          missionDetailRecord={{
            mission_id: 'mission-1',
            objective: 'Control-plane reviewed dispatch runtime inspection',
            status: 'completed',
            owner: 'OmShriMaatreNamaha',
            priority: 'p1',
            producer_key: 'chaitanya',
            queue_job_id: null,
            source_lane_id: null,
            source_board_concurrency_token: null,
            created_at: '2026-03-20T00:00:00.000Z',
            updated_at: '2026-03-20T00:05:00.000Z',
            subtask_total: 1,
            subtask_completed: 1,
            assignment_total: 1,
            evidence_count: 1,
            blocker_count: 1,
            escalation_needed: true,
            verification: {
              passed: 1,
              warned: 0,
              failed: 0,
              last_verified_at: '2026-03-20T00:04:00.000Z',
            },
            final_summary: 'Runtime watchdog and durable mission-state inspection recorded.',
            subtasks: [
              {
                id: 'subtask-1',
                title: 'Inspect watchdog and mission evidence alignment',
                status: 'completed',
                owner_role: 'OmVishnaveNamah',
                depends_on: [],
                updated_at: '2026-03-20T00:03:00.000Z',
              },
            ],
            assignments: [
              {
                id: 'assignment-1',
                subtask_id: 'subtask-1',
                assigned_role: 'OmVishnaveNamah',
                handoff_reason: 'Validate runtime truth before pilot closeout',
                started_at: '2026-03-20T00:01:00.000Z',
                completed_at: '2026-03-20T00:02:00.000Z',
              },
            ],
            evidence_items: [
              {
                id: 'evidence-1',
                mission_id: 'mission-1',
                subtask_id: 'subtask-1',
                kind: 'runtime_watchdog',
                evidence_class: 'runtime-status',
                summary: 'Watchdog completed the reviewed queue job.',
                source_path: 'runtime-artifacts/watchdog-state.json',
                recorded_at: '2026-03-20T00:03:30.000Z',
              },
            ],
            verification_runs: [
              {
                id: 'verification-1',
                subject_id: 'subtask-1',
                verification_type: 'runtime_watchdog',
                result: 'passed',
                evidence_ref: 'evidence-1',
                executed_at: '2026-03-20T00:04:00.000Z',
              },
            ],
            decision_notes: [
              {
                id: 'decision-1',
                decision_class: 'reviewed_dispatch',
                authority_source: 'OmShriMaatreNamaha',
                recorded_at: '2026-03-20T00:04:30.000Z',
              },
            ],
            blockers: [
              {
                id: 'blocker-1',
                mission_id: 'mission-1',
                subtask_id: null,
                blocker_type: 'missing_closeout_receipt',
                impact: 'Stable runtime closeout receipt is not yet present.',
                escalation_needed: true,
                recorded_at: '2026-03-20T00:04:45.000Z',
              },
            ],
          }}
          missionDetailError={null}
          missionDetailLastCheckedAt="2026-03-20T00:06:30.000Z"
        />
      </Tabs>
    )

    expect(screen.getByText('Lane Matrix')).toBeInTheDocument()
    expect(screen.getByText('Control Plane and Agent Orchestration')).toBeInTheDocument()
    expect(screen.getByText('Reviewed Dispatch Readiness')).toBeInTheDocument()
    expect(screen.getByText('platform-runtime remains the first bounded reviewed-dispatch pilot lane.')).toBeInTheDocument()
    expect(screen.getByText('Orchestrator Mission State')).toBeInTheDocument()
    expect(screen.getAllByText('Control-plane reviewed dispatch runtime inspection').length).toBe(2)
    expect(screen.getByText('Producer:')).toBeInTheDocument()
    expect(screen.getByText('Mission Detail')).toBeInTheDocument()
    expect(screen.getByText('Inspect watchdog and mission evidence alignment')).toBeInTheDocument()
    expect(screen.getByText('runtime-artifacts/watchdog-state.json')).toBeInTheDocument()
    expect(screen.getByText('missing_closeout_receipt')).toBeInTheDocument()
    expect(screen.getByText('Agent Contract')).toBeInTheDocument()
    expect(screen.getByText('Control Plane Cadence')).toBeInTheDocument()
    expect(screen.getByText('inspect board before work begins')).toBeInTheDocument()
    expect(
      screen.getByText('translate human vision and optional constraints into executable objectives before dispatch')
    ).toBeInTheDocument()
  })

  it('surfaces persisted selected-lane runtime provenance when closure evidence exists', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-control-1',
      source_board_concurrency_token: 'token-control-1',
      closure_summary: 'Reviewed closeout evidence was accepted for the control plane lane.',
      evidence: ['Focused tests passed', 'Closeout receipt reviewed'],
      completed_at: '2026-03-20T00:10:00.000Z',
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
        receipt_recorded_at: '2026-03-20T00:11:00.000Z',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-control-1',
      },
    }

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="orchestration" onValueChange={() => {}}>
        <OrchestrationTab
          lanes={view.parsedBoard?.lanes ?? []}
          agentRoles={view.parsedBoard?.agent_roles ?? []}
          operatingCadence={view.parsedBoard?.control_plane.operating_cadence ?? []}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          missionStateState="idle"
          missionStateRecord={null}
          missionStateError={null}
          missionStateLastCheckedAt={null}
          missionDetailState="idle"
          missionDetailRecord={null}
          missionDetailError={null}
          missionDetailLastCheckedAt={null}
        />
      </Tabs>
    )

    expect(screen.getByText('Selected Lane Closure')).toBeInTheDocument()
    expect(screen.getByText('Reviewed closeout evidence was accepted for the control plane lane.')).toBeInTheDocument()
    expect(screen.getByText('Stable runtime provenance')).toBeInTheDocument()
    expect(screen.getByText('runtime-mission-control-plane-token1')).toBeInTheDocument()
    expect(screen.getByText('openclaw-runtime')).toBeInTheDocument()
    expect(screen.getByText('bijmantra-bca-local-verify')).toBeInTheDocument()
    expect(
      screen.getByText('runtime-artifacts/mission-evidence/control-plane/verification_1.json')
    ).toBeInTheDocument()
  })

  it('shows the selected lane mission linkage when durable mission-state matches the runtime receipt mission id', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.status = 'completed'
    controlPlaneLane.closure = {
      queue_job_id: 'overnight-lane-control-plane-token1',
      queue_sha256: 'queue-sha-control-1',
      source_board_concurrency_token: 'token-control-1',
      closure_summary: 'Reviewed closeout evidence was accepted for the control plane lane.',
      evidence: ['Focused tests passed', 'Closeout receipt reviewed'],
      completed_at: '2026-03-20T00:10:00.000Z',
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
        receipt_recorded_at: '2026-03-20T00:11:00.000Z',
        verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
        queue_sha256_at_closeout: 'queue-sha-control-1',
      },
    }

    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(board),
      'control-plane'
    )

    render(
      <Tabs value="orchestration" onValueChange={() => {}}>
        <OrchestrationTab
          lanes={view.parsedBoard?.lanes ?? []}
          agentRoles={view.parsedBoard?.agent_roles ?? []}
          operatingCadence={view.parsedBoard?.control_plane.operating_cadence ?? []}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          missionStateState="ready"
          missionStateRecord={{
            count: 1,
            missions: [
              {
                mission_id: 'runtime-mission-control-plane-token1',
                objective: 'Reviewed closeout persistence for lane Control Plane Lane',
                status: 'completed',
                owner: 'OmShriMaatreNamaha',
                priority: 'p1',
                producer_key: 'openclaw-runtime',
                queue_job_id: 'overnight-lane-control-plane-token1',
                source_lane_id: 'control-plane',
                source_board_concurrency_token: 'token-control-1',
                created_at: '2026-03-20T00:12:30.000Z',
                updated_at: '2026-03-20T00:13:00.000Z',
                subtask_total: 1,
                subtask_completed: 1,
                assignment_total: 1,
                evidence_count: 2,
                blocker_count: 0,
                escalation_needed: false,
                verification: {
                  passed: 1,
                  warned: 0,
                  failed: 0,
                  last_verified_at: '2026-03-20T00:12:45.000Z',
                },
                final_summary:
                  'Canonical board closure persisted reviewed runtime provenance for lane control-plane.',
              },
            ],
          }}
          missionStateError={null}
          missionStateLastCheckedAt="2026-03-20T00:13:10.000Z"
          missionDetailState="ready"
          missionDetailRecord={{
            mission_id: 'runtime-mission-control-plane-token1',
            objective: 'Reviewed closeout persistence for lane Control Plane Lane',
            status: 'completed',
            owner: 'OmShriMaatreNamaha',
            priority: 'p1',
            producer_key: 'openclaw-runtime',
            queue_job_id: 'overnight-lane-control-plane-token1',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'token-control-1',
            created_at: '2026-03-20T00:12:30.000Z',
            updated_at: '2026-03-20T00:13:00.000Z',
            subtask_total: 1,
            subtask_completed: 1,
            assignment_total: 1,
            evidence_count: 2,
            blocker_count: 0,
            escalation_needed: false,
            verification: {
              passed: 1,
              warned: 0,
              failed: 0,
              last_verified_at: '2026-03-20T00:12:45.000Z',
            },
            final_summary:
              'Canonical board closure persisted reviewed runtime provenance for lane control-plane.',
            subtasks: [],
            assignments: [],
            evidence_items: [],
            verification_runs: [],
            decision_notes: [],
            blockers: [],
          }}
          missionDetailError={null}
          missionDetailLastCheckedAt="2026-03-20T00:13:12.000Z"
        />
      </Tabs>
    )

    expect(screen.getByText('Selected Lane Mission Link')).toBeInTheDocument()
    expect(screen.getAllByText('Reviewed closeout persistence for lane Control Plane Lane').length).toBe(
      3
    )
    expect(screen.getAllByText('runtime-mission-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('overnight-lane-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('control-plane').length).toBeGreaterThan(0)
    expect(screen.getAllByText('token-control-1').length).toBeGreaterThan(0)
    expect(screen.getByText('Durable mission detail is aligned to the selected lane receipt mission.')).toBeInTheDocument()
  })

  it('shows receipt-observed durable mission linkage before canonical closure exists', () => {
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
      <Tabs value="orchestration" onValueChange={() => {}}>
        <OrchestrationTab
          lanes={view.parsedBoard?.lanes ?? []}
          agentRoles={view.parsedBoard?.agent_roles ?? []}
          operatingCadence={view.parsedBoard?.control_plane.operating_cadence ?? []}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          selectedLane={view.selectedLane}
          selectedLaneAnalysis={view.selectedLaneAnalysis}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
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
            receipt_recorded_at: '2026-03-20T00:11:00.000Z',
            started_at: '2026-03-20T00:09:00.000Z',
            finished_at: '2026-03-20T00:10:30.000Z',
            verification_evidence_ref: 'runtime-artifacts/mission-evidence/control-plane/verification_1.json',
            queue_sha256_at_closeout: 'queue-sha-control-1',
            closeout_commands: [],
            artifacts: [],
          }}
          missionStateState="ready"
          missionStateRecord={{
            count: 1,
            missions: [
              {
                mission_id: 'runtime-mission-control-plane-token1',
                objective: 'Reviewed closeout receipt observed for lane Control Plane',
                status: 'active',
                owner: 'OmShriMaatreNamaha',
                priority: 'p1',
                producer_key: 'openclaw-runtime',
                queue_job_id: 'overnight-lane-control-plane-token1',
                source_lane_id: 'control-plane',
                source_board_concurrency_token: 'token-control-1',
                created_at: '2026-03-20T00:12:30.000Z',
                updated_at: '2026-03-20T00:13:00.000Z',
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
                  last_verified_at: '2026-03-20T00:12:45.000Z',
                },
                final_summary: 'Stable receipt observed; waiting for explicit board closure write-back.',
              },
            ],
          }}
          missionStateError={null}
          missionStateLastCheckedAt="2026-03-20T00:13:10.000Z"
          missionDetailState="ready"
          missionDetailRecord={{
            mission_id: 'runtime-mission-control-plane-token1',
            objective: 'Reviewed closeout receipt observed for lane Control Plane',
            status: 'active',
            owner: 'OmShriMaatreNamaha',
            priority: 'p1',
            producer_key: 'openclaw-runtime',
            queue_job_id: 'overnight-lane-control-plane-token1',
            source_lane_id: 'control-plane',
            source_board_concurrency_token: 'token-control-1',
            created_at: '2026-03-20T00:12:30.000Z',
            updated_at: '2026-03-20T00:13:00.000Z',
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
              last_verified_at: '2026-03-20T00:12:45.000Z',
            },
            final_summary: 'Stable receipt observed; waiting for explicit board closure write-back.',
            subtasks: [],
            assignments: [],
            evidence_items: [],
            verification_runs: [],
            decision_notes: [],
            blockers: [],
          }}
          missionDetailError={null}
          missionDetailLastCheckedAt="2026-03-20T00:13:12.000Z"
        />
      </Tabs>
    )

    expect(screen.getByText('Selected Lane Mission Link')).toBeInTheDocument()
    expect(screen.getAllByText('Reviewed closeout receipt observed for lane Control Plane').length).toBe(
      3
    )
    expect(
      screen.getByText(
        'Stable receipt observed. Durable mission detail is aligned, and canonical board closure is still pending.'
      )
    ).toBeInTheDocument()
    expect(screen.getAllByText('runtime-mission-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('overnight-lane-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('control-plane').length).toBeGreaterThan(0)
  })
})
