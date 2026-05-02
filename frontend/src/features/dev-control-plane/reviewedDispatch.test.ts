import { describe, expect, it } from 'vitest'

import { defaultDeveloperMasterBoard } from './contracts/board'
import { analyzeDeveloperMasterBoard } from './autonomy'
import {
  buildReviewedDispatchPilotChecks,
  countBlockingReviewedDispatchPilotChecks,
  hasReviewedCompletionVerificationEvidence,
  hasReviewedDispatchReviewGates,
} from './reviewedDispatch'

describe('reviewedDispatch', () => {
  it('recognizes explicit reviewed-dispatch gates on the allowlisted pilot lane', () => {
    const platformRuntimeLane = defaultDeveloperMasterBoard.lanes.find((lane) => lane.id === 'platform-runtime')

    expect(hasReviewedDispatchReviewGates(platformRuntimeLane ?? null)).toBe(true)
    expect(hasReviewedCompletionVerificationEvidence(platformRuntimeLane ?? null)).toBe(true)
  })

  it('builds a fully passing reviewed-dispatch preflight for platform-runtime', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const selectedLane = board.lanes.find((lane) => lane.id === 'platform-runtime') ?? null
    const autonomyAnalysis = analyzeDeveloperMasterBoard(board)
    const selectedLaneAnalysis = autonomyAnalysis.laneAnalyses.find((lane) => lane.laneId === 'platform-runtime') ?? null

    const checks = buildReviewedDispatchPilotChecks(
      {
        tone: 'synced',
        label: 'Shared backend persistence active',
        description: 'Shared backend persistence is active for this hidden surface.',
      },
      selectedLane,
      selectedLaneAnalysis,
      'ready',
      {
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-platform-1',
        exists: true,
        job_count: 1,
        updated_at: '2026-03-20T00:00:00.000Z',
      }
    )

    expect(countBlockingReviewedDispatchPilotChecks(checks)).toBe(0)
    expect(checks.every((check) => check.passed)).toBe(true)
  })

  it('adds a non-blocking canonical-learning check when scoped learnings are available', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const selectedLane = board.lanes.find((lane) => lane.id === 'platform-runtime') ?? null
    const autonomyAnalysis = analyzeDeveloperMasterBoard(board)
    const selectedLaneAnalysis =
      autonomyAnalysis.laneAnalyses.find((lane) => lane.laneId === 'platform-runtime') ?? null

    const checks = buildReviewedDispatchPilotChecks(
      {
        tone: 'synced',
        label: 'Shared backend persistence active',
        description: 'Shared backend persistence is active for this hidden surface.',
      },
      selectedLane,
      selectedLaneAnalysis,
      'ready',
      {
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-platform-1',
        exists: true,
        job_count: 1,
        updated_at: '2026-03-20T00:00:00.000Z',
      },
      {
        state: 'ready',
        record: {
          total_count: 1,
          entries: [
            {
              learning_entry_id: 91,
              organization_id: 1,
              entry_type: 'pattern',
              source_classification: 'reviewed-completion-writeback',
              title: 'Reviewed completion write-back closed lane platform-runtime',
              summary:
                'Explicit reviewed completion write-back persisted canonical closure for lane platform-runtime.',
              confidence_score: 0.94,
              recorded_by_user_id: 1,
              recorded_by_email: 'ops@bijmantra.org',
              board_id: 'bijmantra-app-development-master-board',
              source_lane_id: 'platform-runtime',
              queue_job_id: 'overnight-lane-platform-runtime-token1',
              linked_mission_id: 'mission-platform-runtime-token1',
              approval_receipt_id: 77,
              source_reference:
                'approval-receipt:77:reviewed-completion-writeback',
              evidence_refs: ['receipt:77'],
              summary_metadata: null,
              recorded_at: '2026-03-31T12:15:00.000Z',
            },
          ],
        },
        error: null,
      }
    )

    const learningCheck = checks.find((check) => check.id === 'canonical-learning-context')
    expect(learningCheck).toMatchObject({
      passed: true,
      blocking: false,
      label: 'Canonical learning context is visible',
    })
    expect(learningCheck?.detail).toBe(
      'Canonical learning ledger includes prior reviewed completion write-back evidence for this scope. Recent learnings: Reviewed completion write-back closed lane platform-runtime.'
    )
    expect(countBlockingReviewedDispatchPilotChecks(checks)).toBe(0)
  })

  it('blocks the preflight when the selected lane is not the allowlisted pilot', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const selectedLane = board.lanes.find((lane) => lane.id === 'control-plane') ?? null
    const autonomyAnalysis = analyzeDeveloperMasterBoard(board)
    const selectedLaneAnalysis = autonomyAnalysis.laneAnalyses.find((lane) => lane.laneId === 'control-plane') ?? null

    const checks = buildReviewedDispatchPilotChecks(
      {
        tone: 'synced',
        label: 'Shared backend persistence active',
        description: 'Shared backend persistence is active for this hidden surface.',
      },
      selectedLane,
      selectedLaneAnalysis,
      'ready',
      {
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-control-1',
        exists: true,
        job_count: 1,
        updated_at: '2026-03-20T00:00:00.000Z',
      }
    )

    expect(checks.find((check) => check.id === 'allowlisted-lane')?.passed).toBe(false)
    expect(countBlockingReviewedDispatchPilotChecks(checks)).toBeGreaterThan(0)
  })

  it('blocks the preflight when explicit spec or risk reviews are missing', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const selectedLane = board.lanes.find((lane) => lane.id === 'platform-runtime') ?? null

    if (!selectedLane?.review_state) {
      throw new Error('Expected reviewed platform-runtime fixture state')
    }

    delete selectedLane.review_state.risk_review

    const autonomyAnalysis = analyzeDeveloperMasterBoard(board)
    const selectedLaneAnalysis = autonomyAnalysis.laneAnalyses.find((lane) => lane.laneId === 'platform-runtime') ?? null

    const checks = buildReviewedDispatchPilotChecks(
      {
        tone: 'synced',
        label: 'Shared backend persistence active',
        description: 'Shared backend persistence is active for this hidden surface.',
      },
      selectedLane,
      selectedLaneAnalysis,
      'ready',
      {
        queue_path: '.agent/jobs/overnight-queue.json',
        queue_sha256: 'queue-sha-platform-1',
        exists: true,
        job_count: 1,
        updated_at: '2026-03-20T00:00:00.000Z',
      }
    )

    expect(hasReviewedDispatchReviewGates(selectedLane)).toBe(false)
    expect(checks.find((check) => check.id === 'review-gates')?.passed).toBe(false)
    expect(countBlockingReviewedDispatchPilotChecks(checks)).toBeGreaterThan(0)
  })
})