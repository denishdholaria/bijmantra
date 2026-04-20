import type {
  DeveloperControlPlaneCloseoutReceiptResponse,
  DeveloperControlPlaneMissionStateResponse,
  DeveloperControlPlaneMissionSummary,
} from '../api/activeBoard'
import type { DeveloperBoardLane } from '../contracts/board'

type SelectedLaneMissionSummaryInput = {
  selectedLane: DeveloperBoardLane | null
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
  closeoutReceiptRecord?: DeveloperControlPlaneCloseoutReceiptResponse | null
  selectedLaneQueueJobId?: string | null
}

type MissionRuntimeLinkageInput = {
  missionStateRecord: DeveloperControlPlaneMissionStateResponse | null
  missionId?: string | null
  sourceLaneId?: string | null
  queueJobId?: string | null
}

export function getMissionSummaryForRuntimeLinkage({
  missionStateRecord,
  missionId = null,
  sourceLaneId = null,
  queueJobId = null,
}: MissionRuntimeLinkageInput): DeveloperControlPlaneMissionSummary | null {
  if (!missionStateRecord) {
    return null
  }

  if (missionId) {
    const exactMatch = missionStateRecord.missions.find((mission) => mission.mission_id === missionId)
    if (exactMatch) {
      return exactMatch
    }
  }

  if (!queueJobId && !sourceLaneId) {
    return null
  }

  const matchingMissions = missionStateRecord.missions.filter(
    (mission) =>
      (queueJobId !== null && mission.queue_job_id === queueJobId) ||
      (sourceLaneId !== null && mission.source_lane_id === sourceLaneId)
  )

  if (matchingMissions.length === 0) {
    return null
  }

  return (
    matchingMissions.find(
      (mission) =>
        (queueJobId === null || mission.queue_job_id === queueJobId) &&
        (sourceLaneId === null || mission.source_lane_id === sourceLaneId)
    ) ?? matchingMissions[0]
  )
}

export function getSelectedLaneMissionSummary({
  selectedLane,
  missionStateRecord,
  closeoutReceiptRecord = null,
  selectedLaneQueueJobId = null,
}: SelectedLaneMissionSummaryInput): DeveloperControlPlaneMissionSummary | null {
  const missionId =
    closeoutReceiptRecord?.mission_id ?? selectedLane?.closure?.closeout_receipt?.mission_id ?? null

  const queueJobId =
    closeoutReceiptRecord?.queue_job_id ??
    selectedLane?.closure?.queue_job_id ??
    selectedLaneQueueJobId ??
    null
  const laneId =
    closeoutReceiptRecord?.source_lane_id ??
    selectedLane?.closure?.closeout_receipt?.source_lane_id ??
    selectedLane?.id ??
    null

  return getMissionSummaryForRuntimeLinkage({
    missionStateRecord,
    missionId,
    sourceLaneId: laneId,
    queueJobId,
  })
}