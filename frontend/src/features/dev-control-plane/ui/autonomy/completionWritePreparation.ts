import type {
  DeveloperControlPlaneAutonomyCycleAction,
  DeveloperControlPlaneAutonomyCycleResponse,
  DeveloperControlPlaneCompletionWritePreparationResponse,
  DeveloperControlPlaneRuntimeCompletionAssistResponse,
} from '../../api/activeBoard'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function coerceCompletionWritePreparation(
  preparation: unknown
): DeveloperControlPlaneCompletionWritePreparationResponse | null {
  if (!isRecord(preparation)) {
    return null
  }

  const queueStatus = preparation.queue_status
  const closeoutReceipt = preparation.closeout_receipt
  const preparedRequest = preparation.prepared_request
  if (
    typeof preparation.source_lane_id !== 'string' ||
    typeof preparation.queue_job_id !== 'string' ||
    (preparation.draft_source !== 'queue-snapshot' &&
      preparation.draft_source !== 'stable-closeout-receipt') ||
    !isRecord(queueStatus) ||
    typeof queueStatus.queue_path !== 'string' ||
    typeof queueStatus.queue_sha256 !== 'string' ||
    typeof queueStatus.exists !== 'boolean' ||
    typeof queueStatus.job_count !== 'number' ||
    !isRecord(closeoutReceipt) ||
    typeof closeoutReceipt.exists !== 'boolean' ||
    !isRecord(preparedRequest) ||
    typeof preparedRequest.source_board_concurrency_token !== 'string' ||
    typeof preparedRequest.expected_queue_sha256 !== 'string' ||
    preparedRequest.operator_intent !== 'write-reviewed-lane-completion'
  ) {
    return null
  }

  const completion = preparedRequest.completion
  if (
    !isRecord(completion) ||
    typeof completion.source_lane_id !== 'string' ||
    typeof completion.queue_job_id !== 'string' ||
    typeof completion.closure_summary !== 'string' ||
    !isStringArray(completion.evidence)
  ) {
    return null
  }

  return preparation as DeveloperControlPlaneCompletionWritePreparationResponse
}

export function getAutonomyActionCompletionWritePreparation(
  action: DeveloperControlPlaneAutonomyCycleAction
): DeveloperControlPlaneCompletionWritePreparationResponse | null {
  if (!isRecord(action.detail)) {
    return null
  }

  return coerceCompletionWritePreparation(action.detail.completionWritePreparation)
}

export function findAutonomyCycleCompletionWritePreparationForLane(
  record: DeveloperControlPlaneAutonomyCycleResponse | null | undefined,
  laneId: string
): DeveloperControlPlaneCompletionWritePreparationResponse | null {
  for (const action of record?.next_actions ?? []) {
    if (
      action.action === 'prepare-completion-write-back' &&
      action.source_lane_id === laneId
    ) {
      const preparation = getAutonomyActionCompletionWritePreparation(action)
      if (preparation) {
        return preparation
      }
    }
  }

  return null
}

export function findCompletionAssistPreparationForLane(
  record: DeveloperControlPlaneRuntimeCompletionAssistResponse | null | undefined,
  laneId: string
): DeveloperControlPlaneCompletionWritePreparationResponse | null {
  const actionable = record?.actionable_completion_write
  if (!actionable || actionable.sourceLaneId !== laneId) {
    return null
  }

  return coerceCompletionWritePreparation({
    source_lane_id: actionable.sourceLaneId,
    queue_job_id: actionable.jobId,
    draft_source: actionable.draftSource,
    queue_status: actionable.queueStatus,
    closeout_receipt: actionable.closeoutReceipt,
    prepared_request: actionable.preparedRequest,
  })
}