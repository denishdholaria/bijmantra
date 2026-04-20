import type { DeveloperBoardAgentRole, DeveloperBoardStatus } from './board'
import type { DeveloperLaneAutonomyAnalysis } from './autonomy'

export type DeveloperLaneDispatchPacket = {
  generatedAt: string
  boardId: string
  boardTitle: string
  primaryOrchestrator: string
  lane: {
    id: string
    title: string
    status: DeveloperBoardStatus
    objective: string
    owners: string[]
    inputs: string[]
    outputs: string[]
    dependencies: string[]
    completionCriteria: string[]
    subplans: Array<{
      id: string
      title: string
      status: DeveloperBoardStatus
      objective: string
      outputs: string[]
    }>
  }
  autonomy: DeveloperLaneAutonomyAnalysis
  agentRoles: DeveloperBoardAgentRole[]
}

export type DeveloperLaneQueueCandidate = {
  candidateVersion: '1.0.0'
  exportedAt: string
  boardId: string
  boardTitle: string
  sourceBoardConcurrencyToken: string
  sourceLaneId: string
  title: string
  primaryAgent: string
  supportAgents: string[]
  goal: string
  successCriteria: string[]
  lane: {
    objective: string
    inputs: string[]
    outputs: string[]
    dependencies: string[]
    completion_criteria: string[]
  }
  precedence: {
    canonicalPlanningSource: 'active-board'
    derivedExecutionSurface: 'overnight-queue'
    exportDisposition: 'manual-candidate-only'
    conflictResolution: 'board-wins-no-silent-overwrite'
    staleIfSourceBoardChanges: true
  }
}

export type DeveloperLaneQueueEntryProvenance = {
  candidateVersion: '1.0.0'
  exportedAt: string
  boardId: string
  boardTitle: string
  sourceBoardConcurrencyToken: string
  sourceLaneId: string
  precedence: {
    canonicalPlanningSource: 'active-board'
    derivedExecutionSurface: 'overnight-queue'
    exportDisposition: 'manual-candidate-only'
    conflictResolution: 'board-wins-no-silent-overwrite'
    staleIfSourceBoardChanges: true
  }
}

export type DeveloperLaneQueueEntry = {
  jobId: string
  title: string
  status: 'queued'
  priority: 'p2'
  primaryAgent: string
  supportAgents: string[]
  executionMode: 'same-control-plane'
  autonomousTrigger: {
    type: 'overnight-window'
    window: 'nightly'
    enabled: true
  }
  dependsOn: string[]
  goal: string
  provenance: DeveloperLaneQueueEntryProvenance
  lane: {
    objective: string
    inputs: string[]
    outputs: string[]
    dependencies: string[]
    completion_criteria: string[]
  }
  successCriteria: string[]
  verification: {
    commands: string[]
    stateRefreshRequired: true
  }
}

export type DeveloperLaneQueueEntryMaterialization = {
  entry: DeveloperLaneQueueEntry | null
  unresolvedDependencyLaneIds: string[]
}

function queueTokenSuffix(sourceBoardConcurrencyToken: string) {
  const normalized = sourceBoardConcurrencyToken
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
    .slice(0, 8)

  return normalized || 'unknown000'
}

export function createDeveloperLaneQueueJobId(
  sourceLaneId: string,
  sourceBoardConcurrencyToken: string
) {
  return `overnight-lane-${sourceLaneId}-${queueTokenSuffix(sourceBoardConcurrencyToken)}`
}

export function createDeveloperLaneQueueCandidate(
  dispatchPacket: DeveloperLaneDispatchPacket | null,
  sourceBoardConcurrencyToken: string | null
): DeveloperLaneQueueCandidate | null {
  if (!dispatchPacket || !sourceBoardConcurrencyToken) {
    return null
  }

  return {
    candidateVersion: '1.0.0',
    exportedAt: dispatchPacket.generatedAt,
    boardId: dispatchPacket.boardId,
    boardTitle: dispatchPacket.boardTitle,
    sourceBoardConcurrencyToken,
    sourceLaneId: dispatchPacket.lane.id,
    title: dispatchPacket.lane.title,
    primaryAgent: dispatchPacket.primaryOrchestrator,
    supportAgents: Array.from(
      new Set(
        dispatchPacket.lane.owners.filter((owner) => owner !== dispatchPacket.primaryOrchestrator)
      )
    ),
    goal: dispatchPacket.lane.objective,
    successCriteria: [...dispatchPacket.lane.completionCriteria],
    lane: {
      objective: dispatchPacket.lane.objective,
      inputs: [...dispatchPacket.lane.inputs],
      outputs: [...dispatchPacket.lane.outputs],
      dependencies: [...dispatchPacket.lane.dependencies],
      completion_criteria: [...dispatchPacket.lane.completionCriteria],
    },
    precedence: {
      canonicalPlanningSource: 'active-board',
      derivedExecutionSurface: 'overnight-queue',
      exportDisposition: 'manual-candidate-only',
      conflictResolution: 'board-wins-no-silent-overwrite',
      staleIfSourceBoardChanges: true,
    },
  }
}

export function materializeDeveloperLaneQueueEntry(
  queueCandidate: DeveloperLaneQueueCandidate | null,
  laneIdToQueueJobId: Record<string, string>
): DeveloperLaneQueueEntryMaterialization {
  if (!queueCandidate) {
    return {
      entry: null,
      unresolvedDependencyLaneIds: [],
    }
  }

  const unresolvedDependencyLaneIds = queueCandidate.lane.dependencies.filter(
    (laneId) => !laneIdToQueueJobId[laneId]
  )

  if (unresolvedDependencyLaneIds.length > 0) {
    return {
      entry: null,
      unresolvedDependencyLaneIds,
    }
  }

  return {
    entry: {
      jobId: createDeveloperLaneQueueJobId(
        queueCandidate.sourceLaneId,
        queueCandidate.sourceBoardConcurrencyToken
      ),
      title: queueCandidate.title,
      status: 'queued',
      priority: 'p2',
      primaryAgent: queueCandidate.primaryAgent,
      supportAgents: [...queueCandidate.supportAgents],
      executionMode: 'same-control-plane',
      autonomousTrigger: {
        type: 'overnight-window',
        window: 'nightly',
        enabled: true,
      },
      dependsOn: queueCandidate.lane.dependencies.map((laneId) => laneIdToQueueJobId[laneId]),
      goal: queueCandidate.goal,
      provenance: {
        candidateVersion: queueCandidate.candidateVersion,
        exportedAt: queueCandidate.exportedAt,
        boardId: queueCandidate.boardId,
        boardTitle: queueCandidate.boardTitle,
        sourceBoardConcurrencyToken: queueCandidate.sourceBoardConcurrencyToken,
        sourceLaneId: queueCandidate.sourceLaneId,
        precedence: {
          canonicalPlanningSource: queueCandidate.precedence.canonicalPlanningSource,
          derivedExecutionSurface: queueCandidate.precedence.derivedExecutionSurface,
          exportDisposition: queueCandidate.precedence.exportDisposition,
          conflictResolution: queueCandidate.precedence.conflictResolution,
          staleIfSourceBoardChanges: queueCandidate.precedence.staleIfSourceBoardChanges,
        },
      },
      lane: {
        objective: queueCandidate.lane.objective,
        inputs: [...queueCandidate.lane.inputs],
        outputs: [...queueCandidate.lane.outputs],
        dependencies: [...queueCandidate.lane.dependencies],
        completion_criteria: [...queueCandidate.lane.completion_criteria],
      },
      successCriteria: [...queueCandidate.successCriteria],
      verification: {
        commands: [],
        stateRefreshRequired: true,
      },
    },
    unresolvedDependencyLaneIds: [],
  }
}