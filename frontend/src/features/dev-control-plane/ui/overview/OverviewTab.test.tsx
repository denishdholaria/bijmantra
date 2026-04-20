import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Tabs } from '@/components/ui/tabs'

import { defaultDeveloperMasterBoard, serializeDeveloperMasterBoard } from '../../contracts/board'
import { deriveDeveloperMasterBoardViewModel } from '../../state/selectors'
import { OverviewTab } from './OverviewTab'

describe('OverviewTab', () => {
  it('projects the selected lane queue-to-mission execution chain when durable linkage exists', () => {
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
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
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
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('Selected lane execution chain')).toBeInTheDocument()
    expect(
      screen.getAllByText(
        (_, node) =>
          node instanceof HTMLElement &&
          node.textContent?.includes('Lane control-plane is linked to queue job') === true &&
          node.textContent?.includes('runtime-mission-control-plane-token1') === true
      ).length
    ).toBeGreaterThan(0)
    expect(screen.getAllByText('overnight-lane-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('runtime-mission-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getByText('Reviewed closeout persistence for lane Control Plane Lane')).toBeInTheDocument()
    expect(screen.getByText(/Board token/i)).toBeInTheDocument()
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
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
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
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('Selected lane execution chain')).toBeInTheDocument()
    expect(
      screen.getAllByText(
        (_, node) =>
          node instanceof HTMLElement &&
          node.textContent?.includes('Lane control-plane is linked to queue job') === true &&
          node.textContent?.includes('runtime-mission-control-plane-token1') === true
      ).length
    ).toBeGreaterThan(0)
    expect(
      screen.getByText(
        'Stable receipt is present and the durable mission is active, but canonical board closure is still pending.'
      )
    ).toBeInTheDocument()
    expect(screen.getAllByText('overnight-lane-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('runtime-mission-control-plane-token1').length).toBeGreaterThan(0)
    expect(screen.getByText('Reviewed closeout receipt observed for lane Control Plane')).toBeInTheDocument()
  })

  it('surfaces the runtime auth bootstrap blocker in the signal summary', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 0,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
          missionStateState="idle"
          missionStateRecord={null}
          missionStateError={null}
          missionStateLastCheckedAt={null}
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('Bootstrap blocked by missing auth')).toBeInTheDocument()
    expect(
      screen.getByText('0 runtime jobs observed; bootstrap blocked because runtime auth is missing.')
    ).toBeInTheDocument()
    expect(screen.getAllByText('Tracked artifact').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Shared backend').length).toBeGreaterThan(0)
  })

  it('labels board-derived panels as browser fallback when shared persistence is not synced', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'fallback',
            label: 'Backend unavailable; local fallback active',
            description:
              'Shared backend persistence could not be reached, so this hidden control-plane surface is still running from the browser-local fallback board.',
          }}
          lastUpdatedAt="2026-04-08T17:24:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 3,
            updated_at: '2026-04-08T17:24:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-04-08T17:24:00.000Z"
          runtimeWatchdogState="idle"
          runtimeWatchdogRecord={null}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt={null}
          missionStateState="idle"
          missionStateRecord={null}
          missionStateError={null}
          missionStateLastCheckedAt={null}
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getAllByText('Browser fallback').length).toBeGreaterThan(0)
  })

  it('marks stale runtime watchdog snapshots as stale instead of healthy', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            state_is_stale: true,
            state_age_seconds: 900,
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
          missionStateState="idle"
          missionStateRecord={null}
          missionStateError={null}
          missionStateLastCheckedAt={null}
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('1 runtime jobs observed; watchdog snapshot stale.')).toBeInTheDocument()
  })

  it('falls back to autonomy-cycle watchdog telemetry when the direct watchdog endpoint is degraded', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'platform-runtime'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-04-08T17:11:49.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-platform-1',
            exists: true,
            job_count: 9,
            updated_at: '2026-04-08T17:11:48.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-04-08T17:11:48.000Z"
          runtimeWatchdogState="error"
          runtimeWatchdogRecord={null}
          runtimeWatchdogError="HTTP 500"
          runtimeWatchdogLastCheckedAt="2026-04-08T17:11:48.000Z"
          runtimeAutonomyCycleState="ready"
          runtimeAutonomyCycleRecord={{
            exists: true,
            artifact_path: '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
            generated_at: '2026-04-08T16:19:40.000Z',
            queue_path: '.agent/jobs/overnight-queue.json',
            window: 'nightly',
            max_jobs_per_run: 2,
            status_counts: { queued: 9 },
            selected_job_count: 2,
            blocked_job_count: 6,
            closeout_candidate_count: 1,
            next_action_count: 4,
            next_action_ordering_source: 'artifact',
            watchdog: {
              exists: true,
              state_path: 'runtime-artifacts/watchdog-state.json',
              last_check: '2026-04-08T17:11:49.000Z',
              gateway_healthy: false,
              state_is_stale: false,
              total_alerts: 4,
              job_errors: {
                'overnight-lane-b-chaitanya-permission-hardening': {
                  last_error: 'rate limit',
                  consecutive_errors: 1,
                },
                'overnight-lane-platform-runtime-1116c613': {
                  last_error: 'rate limit',
                  consecutive_errors: 2,
                },
              },
            },
            selected_jobs: [],
            blocked_jobs: [],
            closeout_candidates: [],
            next_actions: [],
            first_actionable_completion_write: null,
          }}
          runtimeAutonomyCycleLastCheckedAt="2026-04-08T17:11:49.000Z"
          missionStateState="ready"
          missionStateRecord={{ count: 0, missions: [] }}
          missionStateError={null}
          missionStateLastCheckedAt="2026-04-08T17:11:49.000Z"
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('Autonomy-cycle signals attention')).toBeInTheDocument()
    expect(
      screen.getByText(/watchdog job errors inferred from the autonomy-cycle artifact/i)
    ).toBeInTheDocument()
  })

  it('renders staged completion assist advisory from runtime watchdog state', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'control-plane'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 2,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
            completion_assist_advisory: {
              authority: 'advisory-only-derived',
              observed_from_path: '.github/docs/architecture/tracking/current-app-state.json',
              available: true,
              artifact_path:
                '.github/docs/architecture/tracking/developer-control-plane-completion-assist.json',
              status: 'staged',
              staged: true,
              explicit_write_required: true,
              message:
                'Staged reviewed completion assist for lane control-plane. This artifact does not perform explicit board write-back.',
              source_lane_id: 'control-plane',
              queue_job_id: 'overnight-lane-control-plane-token1234',
              draft_source: 'stable-closeout-receipt',
              receipt_path: 'runtime-artifacts/mission-evidence/control-plane/closeout.json',
              source_endpoint:
                'http://127.0.0.1:8000/api/v2/developer-control-plane/runtime/autonomy-cycle',
              autonomy_cycle_artifact_path:
                '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
              next_action_ordering_source: 'canonical-learning-exact-runtime',
              matched_selected_job_ids: ['overnight-lane-control-plane-token1234'],
            },
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
          missionStateState="idle"
          missionStateRecord={null}
          missionStateError={null}
          missionStateLastCheckedAt={null}
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(
      screen.getByText(
        'Completion assist advisory is staged for lane control-plane and still needs explicit write-back review.'
      )
    ).toBeInTheDocument()
  })

  it('renders the learning ledger summary and issues scoped refresh queries', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'control-plane'
    )
    const onRefreshLearnings = vi.fn()

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
          selectedLaneQueueJobId="overnight-lane-control-plane-token1"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
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
          learningLedgerState="ready"
          learningLedgerRecord={{
            total_count: 2,
            entries: [
              {
                learning_entry_id: 401,
                organization_id: 1,
                entry_type: 'pattern',
                source_classification: 'approval-receipt',
                title: 'Reviewed queue export pattern',
                summary:
                  'Accepted approval receipts can be reused as canonical queue-export evidence.',
                confidence_score: 0.86,
                recorded_by_user_id: 1,
                recorded_by_email: 'ops@bijmantra.org',
                board_id: 'bijmantra-app-development-master-board',
                source_lane_id: 'control-plane',
                queue_job_id: 'overnight-lane-control-plane-token1',
                linked_mission_id: null,
                approval_receipt_id: 44,
                source_reference: 'approval-receipt-44',
                evidence_refs: ['receipt:44'],
                summary_metadata: null,
                recorded_at: '2026-03-31T12:10:00.000Z',
              },
              {
                learning_entry_id: 402,
                organization_id: 1,
                entry_type: 'verification-learning',
                source_classification: 'mission-state',
                title: 'Lane-scoped verification reminder',
                summary:
                  'Control-plane verification evidence should be refreshed before completion write-back.',
                confidence_score: 0.91,
                recorded_by_user_id: 1,
                recorded_by_email: 'ops@bijmantra.org',
                board_id: 'bijmantra-app-development-master-board',
                source_lane_id: 'control-plane',
                queue_job_id: null,
                linked_mission_id: 'runtime-mission-control-plane-token1',
                approval_receipt_id: null,
                source_reference: 'mission:runtime-mission-control-plane-token1',
                evidence_refs: ['mission:runtime-mission-control-plane-token1'],
                summary_metadata: null,
                recorded_at: '2026-03-31T12:15:00.000Z',
              },
            ],
          }}
          learningLedgerError={null}
          learningLedgerLastCheckedAt="2026-03-31T12:16:00.000Z"
          learningLedgerQuery={{
            limit: 6,
            sourceLaneId: 'control-plane',
          }}
          onRefreshQueueStatus={() => {}}
          onRefreshLearnings={onRefreshLearnings}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getByText('Learning Ledger')).toBeInTheDocument()
    expect(screen.getByText('Reviewed queue export pattern')).toBeInTheDocument()
    expect(screen.getByText('Lane-scoped verification reminder')).toBeInTheDocument()
    expect(screen.getAllByText('Selected lane').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: 'Selected job' }))

    expect(onRefreshLearnings).toHaveBeenCalledWith({
      limit: 6,
      queueJobId: 'overnight-lane-control-plane-token1',
    })
  })

  it('renders evidence-only silent monitors without promoting them into planner authority', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      serializeDeveloperMasterBoard(defaultDeveloperMasterBoard),
      'control-plane'
    )

    render(
      <Tabs value="overview" onValueChange={() => {}}>
        <OverviewTab
          lanes={view.parsedBoard?.lanes ?? []}
          autonomyAnalysis={view.autonomyAnalysis}
          selectedLane={view.selectedLane}
          recommendedLane={view.recommendedLane}
          persistenceStatus={{
            tone: 'synced',
            label: 'Shared backend persistence active',
            description: 'Shared backend persistence is active for this hidden surface.',
          }}
          lastUpdatedAt="2026-03-20T00:14:00.000Z"
          primaryOrchestrator="OmShriMaatreNamaha"
          agentRoleCount={view.availableAgents.length}
          queueStatusState="ready"
          queueStatusRecord={{
            queue_path: '.agent/jobs/overnight-queue.json',
            queue_sha256: 'queue-sha-control-1',
            exists: true,
            job_count: 1,
            updated_at: '2026-03-20T00:12:00.000Z',
          }}
          queueStatusError={null}
          queueStatusLastRefreshedAt="2026-03-20T00:12:00.000Z"
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
            last_check: '2026-03-20T00:12:30.000Z',
            gateway_healthy: true,
            total_checks: 1,
            total_alerts: 0,
            job_count: 1,
            jobs: [],
          }}
          runtimeWatchdogError={null}
          runtimeWatchdogLastCheckedAt="2026-03-20T00:12:30.000Z"
          silentMonitorsState="ready"
          silentMonitorsRecord={{
            generated_at: '2026-03-31T12:20:00.000Z',
            overall_state: 'alert',
            should_emit: true,
            monitors: [
              {
                monitor_key: 'queue-staleness',
                label: 'Queue staleness',
                state: 'healthy',
                should_emit: false,
                summary: 'The overnight queue snapshot looks fresh for the current nightly cadence.',
                detail: 'Queue hash queue-sha-control-1; 1 sampled jobs; age 0.1h.',
                observed_at: '2026-03-31T12:12:00.000Z',
                refresh_cadence: 'Nightly and immediately after each reviewed queue export',
                output_artifact: 'developer-control-plane.runtime.silent-monitors.queue-staleness',
                mutates_authority_surfaces: false,
                evidence_sources: [
                  {
                    label: 'Overnight queue status',
                    path: '.agent/jobs/overnight-queue.json',
                    observed_at: '2026-03-31T12:12:00.000Z',
                  },
                ],
                findings: [],
              },
              {
                monitor_key: 'reevu-readiness',
                label: 'REEVU readiness',
                state: 'alert',
                should_emit: true,
                summary: 'REEVU readiness is degraded for the current local evidence set.',
                detail:
                  '3/14 real-question cases passed; runtime status blocked; benchmark-ready local orgs 0; gap status no_benchmark_ready_local_org; blockers: observations.empty, bio_gwas_runs.empty, bio_qtls.missing_or_inaccessible.',
                observed_at: '2026-03-31T12:20:00.000Z',
                refresh_cadence:
                  'After REEVU readiness census, benchmark, or authority-gap regeneration',
                output_artifact: 'developer-control-plane.runtime.silent-monitors.reevu-readiness',
                mutates_authority_surfaces: false,
                evidence_sources: [
                  {
                    label: 'REEVU authority gap report',
                    path: 'backend/test_reports/reevu_authority_gap_report.json',
                    observed_at: '2026-03-31T12:20:00.000Z',
                  },
                ],
                findings: [
                  'observations.empty',
                  'bio_gwas_runs.empty',
                  'bio_qtls.missing_or_inaccessible',
                ],
              },
            ],
          }}
          silentMonitorsError={null}
          silentMonitorsLastCheckedAt="2026-03-31T12:20:00.000Z"
          missionStateState="ready"
          missionStateRecord={{
            count: 0,
            missions: [],
          }}
          missionStateError={null}
          missionStateLastCheckedAt="2026-03-20T00:13:10.000Z"
          onRefreshQueueStatus={() => {}}
          onSetActiveTab={() => {}}
          onSelectLane={() => {}}
        />
      </Tabs>
    )

    expect(screen.getAllByText('Silent Monitors').length).toBeGreaterThan(0)
    expect(screen.getByText('REEVU readiness')).toBeInTheDocument()
    expect(
      screen.getByText('REEVU readiness is degraded for the current local evidence set.')
    ).toBeInTheDocument()
    expect(screen.getByText(/Signals: observations\.empty/)).toBeInTheDocument()
    expect(
      screen.getByText(
        'Evidence-only readiness and drift monitors. They surface issues here, but they do not mutate the board, queue, or REEVU trust surfaces.'
      )
    ).toBeInTheDocument()
  })
})