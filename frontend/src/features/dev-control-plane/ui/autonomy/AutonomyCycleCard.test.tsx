import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { DeveloperControlPlaneAutonomyCycleResponse } from '../../api/activeBoard'
import { AutonomyCycleCard } from './AutonomyCycleCard'

describe('AutonomyCycleCard', () => {
  it('renders backend-authoritative canonical-learning ordering when present', () => {
    const record: DeveloperControlPlaneAutonomyCycleResponse = {
      exists: true,
      artifact_path: '.github/docs/architecture/tracking/developer-control-plane-autonomy-cycle.json',
      generated_at: '2026-04-05T11:10:24.399975+00:00',
      queue_path: '.agent/jobs/overnight-queue.json',
      window: 'nightly',
      max_jobs_per_run: 2,
      status_counts: { queued: 1 },
      selected_job_count: 0,
      blocked_job_count: 0,
      closeout_candidate_count: 1,
      next_action_count: 2,
      next_action_ordering_source: 'canonical-learning-exact-runtime',
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
          },
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
    }

    render(
      <AutonomyCycleCard state="ready" record={record} />
    )

    const prepareWriteBackAction = screen.getByText('prepare-completion-write-back')
    const dispatchQueueAction = screen.getByText('dispatch-queue-job')

    expect(
      prepareWriteBackAction.compareDocumentPosition(dispatchQueueAction) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
    expect(
      screen.getByText('Next-action ordering is biased by exact runtime-scope canonical learnings.')
    ).toBeInTheDocument()
  })
})