import type {
  DeveloperControlPlaneLearningLedgerResponse,
  DeveloperControlPlaneOvernightQueueStatusResponse,
} from './api/activeBoard'
import type { DeveloperLaneAutonomyAnalysis } from './contracts/autonomy'
import type { DeveloperBoardLane, DeveloperBoardLaneReviewGate } from './contracts/board'
import type { DeveloperControlPlanePersistenceStatus } from './state/selectors'

export type ReviewedDispatchPilotCheck = {
  id: string
  label: string
  passed: boolean
  detail: string
  blocking: boolean
}

export type ReviewedDispatchDecisionMemory = {
  state: 'idle' | 'loading' | 'ready' | 'error'
  record: DeveloperControlPlaneLearningLedgerResponse | null
  error: string | null
}

function hasCompleteReviewGate(reviewGate: DeveloperBoardLaneReviewGate | null | undefined) {
  return Boolean(
    reviewGate &&
      reviewGate.reviewed_by.trim().length > 0 &&
      reviewGate.summary.trim().length > 0 &&
      reviewGate.reviewed_at.trim().length > 0 &&
      reviewGate.evidence.length > 0
  )
}

export function hasReviewedDispatchReviewGates(selectedLane: DeveloperBoardLane | null) {
  return Boolean(
    selectedLane &&
      hasCompleteReviewGate(selectedLane.review_state?.spec_review) &&
      hasCompleteReviewGate(selectedLane.review_state?.risk_review)
  )
}

export function hasReviewedCompletionVerificationEvidence(selectedLane: DeveloperBoardLane | null) {
  return Boolean(selectedLane && hasCompleteReviewGate(selectedLane.review_state?.verification_evidence))
}

export function hasReviewedDispatchValidationBasis(selectedLane: DeveloperBoardLane | null) {
  return hasReviewedDispatchReviewGates(selectedLane)
}

function buildReviewedDispatchLearningCheck(
  decisionMemory: ReviewedDispatchDecisionMemory
): ReviewedDispatchPilotCheck | null {
  if (decisionMemory.state === 'idle') {
    return null
  }

  const entries = decisionMemory.record?.entries ?? []
  const learningTitles = entries
    .slice(0, 2)
    .map((entry) => entry.title)
    .filter((title) => title.trim().length > 0)
  const hasReviewedCompletionLearning = entries.some(
    (entry) => entry.source_classification === 'reviewed-completion-writeback'
  )
  const hasAcceptedReviewLearning = entries.some(
    (entry) => entry.source_classification === 'accepted-review'
  )

  if (decisionMemory.state === 'loading') {
    return {
      id: 'canonical-learning-context',
      label: 'Canonical learning context is loading',
      passed: false,
      detail:
        'Scoped canonical learnings are loading for this lane. Reviewed-dispatch preflight should still rely on current board and queue evidence until matching learnings are visible.',
      blocking: false,
    }
  }

  if (decisionMemory.state === 'error') {
    return {
      id: 'canonical-learning-context',
      label: 'Canonical learning context is unavailable',
      passed: false,
      detail: decisionMemory.error
        ? `Canonical learning lookup failed: ${decisionMemory.error}`
        : 'Canonical learning lookup failed. Reviewed-dispatch preflight should rely on current board and queue evidence until learnings are visible again.',
      blocking: false,
    }
  }

  if (entries.length === 0) {
    return {
      id: 'canonical-learning-context',
      label: 'Canonical learning context is visible',
      passed: false,
      detail:
        'No scoped canonical learnings are linked to this lane yet. The pilot may proceed from current board gates, and the next explicit completion write-back should record one.',
      blocking: false,
    }
  }

  let detail = 'Canonical learning ledger includes matching learnings for this scope.'
  if (hasReviewedCompletionLearning) {
    detail =
      'Canonical learning ledger includes prior reviewed completion write-back evidence for this scope.'
  } else if (hasAcceptedReviewLearning) {
    detail =
      'Canonical learning ledger includes prior accepted-review evidence for this scope.'
  }

  if (learningTitles.length > 0) {
    detail = `${detail} Recent learnings: ${learningTitles.join('; ')}.`
  }

  return {
    id: 'canonical-learning-context',
    label: 'Canonical learning context is visible',
    passed: true,
    detail,
    blocking: false,
  }
}

export function buildReviewedDispatchPilotChecks(
  persistenceStatus: DeveloperControlPlanePersistenceStatus,
  selectedLane: DeveloperBoardLane | null,
  selectedLaneAnalysis: DeveloperLaneAutonomyAnalysis | null,
  queueStatusState: 'idle' | 'loading' | 'ready' | 'error',
  queueStatusRecord: DeveloperControlPlaneOvernightQueueStatusResponse | null,
  decisionMemory: ReviewedDispatchDecisionMemory | null = null
): ReviewedDispatchPilotCheck[] {
  const laneId = selectedLane?.id ?? null
  const laneStatus = selectedLane?.status ?? null
  const hasReviewGates = hasReviewedDispatchReviewGates(selectedLane)
  const checks: ReviewedDispatchPilotCheck[] = [
    {
      id: 'shared-board',
      label: 'Shared canonical board is active',
      passed: persistenceStatus.tone === 'synced',
      detail:
        persistenceStatus.tone === 'synced'
          ? persistenceStatus.label
          : `${persistenceStatus.label}. The reviewed pilot should not start from browser-local fallback only.`,
      blocking: true,
    },
    {
      id: 'allowlisted-lane',
      label: 'Allowlisted pilot lane selected',
      passed: laneId === 'platform-runtime',
      detail:
        laneId === 'platform-runtime'
          ? 'platform-runtime remains the first bounded reviewed-dispatch pilot lane.'
          : laneId
            ? `Current lane: ${laneId}. The first bounded pilot remains restricted to platform-runtime.`
            : 'Select platform-runtime before staging the reviewed pilot queue entry.',
      blocking: true,
    },
    {
      id: 'lane-active',
      label: 'Selected lane is active',
      passed: laneStatus === 'active',
      detail:
        laneStatus === 'active'
          ? 'The selected lane is still active and eligible for reviewed dispatch.'
          : laneStatus
            ? `Current lane status is ${laneStatus}. The first pilot must begin from an active lane.`
            : 'No lane selected yet.',
      blocking: true,
    },
    {
      id: 'dependencies-empty',
      label: 'Selected lane has no dependencies',
      passed: selectedLane ? selectedLane.dependencies.length === 0 : false,
      detail:
        selectedLane?.dependencies.length === 0
          ? 'No unresolved dependency lanes block this reviewed pilot entry.'
          : selectedLane
            ? `Dependencies still declared: ${selectedLane.dependencies.join(', ')}.`
            : 'No lane selected yet.',
      blocking: true,
    },
    {
      id: 'review-gates',
      label: 'Spec and risk reviews are present',
      passed: hasReviewGates,
      detail: hasReviewGates
        ? 'Canonical lane review_state includes explicit spec_review and risk_review evidence.'
        : 'Add explicit spec_review and risk_review evidence before using this lane for the first bounded pilot.',
      blocking: true,
    },
    {
      id: 'no-blocking-drift',
      label: 'No blocking drift remains',
      passed: selectedLaneAnalysis?.readiness === 'ready',
      detail:
        selectedLaneAnalysis?.readiness === 'ready'
          ? 'Autonomy analysis marks the selected lane as structurally ready.'
          : selectedLaneAnalysis
            ? `Current readiness is ${selectedLaneAnalysis.readiness}; clear blocking drift before continuing.`
            : 'Autonomy analysis is not available for the selected lane.',
      blocking: true,
    },
    {
      id: 'queue-refreshed',
      label: 'Queue snapshot has been refreshed',
      passed: queueStatusState === 'ready' && queueStatusRecord !== null,
      detail:
        queueStatusState === 'ready' && queueStatusRecord
          ? `Queue hash ${queueStatusRecord.queue_sha256} is loaded for reviewed preflight checks.`
          : 'Refresh queue status before writing the reviewed queue entry so the preflight hash is explicit.',
      blocking: true,
    },
  ]

  const learningCheck = decisionMemory
    ? buildReviewedDispatchLearningCheck(decisionMemory)
    : null
  if (learningCheck) {
    checks.splice(5, 0, learningCheck)
  }

  return checks
}

export function countBlockingReviewedDispatchPilotChecks(checks: ReviewedDispatchPilotCheck[]) {
  return checks.filter((check) => !check.passed && check.blocking).length
}