import type {
  DeveloperBoardAgentRole,
  DeveloperBoardLane,
  DeveloperBoardStatus,
  DeveloperMasterBoard,
} from './contracts/board'
import type {
  DeveloperBoardAutonomyAnalysis,
  DeveloperLaneAutonomyAnalysis,
  DeveloperLaneReadiness,
  DeveloperLaneStructuralWarning,
  DeveloperLaneStructuralWarningCode,
  DeveloperLaneStructuralWarningSeverity,
} from './contracts/autonomy'
import type { DeveloperLaneDispatchPacket } from './contracts/dispatch'

const STATUS_PRIORITY: Record<DeveloperBoardStatus, number> = {
  active: 40,
  completed: 5,
  planned: 30,
  watch: 10,
  blocked: 0,
}

function hasValues(values: string[]) {
  return values.some((value) => value.trim().length > 0)
}

function hasMeaningfulText(value: string | null | undefined) {
  return typeof value === 'string' && value.trim().length > 0
}

function createStructuralWarning(
  code: DeveloperLaneStructuralWarningCode,
  severity: DeveloperLaneStructuralWarningSeverity,
  message: string,
  remediation: string
): DeveloperLaneStructuralWarning {
  return {
    code,
    severity,
    message,
    remediation,
  }
}

function collectValidationEvidenceText(lane: DeveloperBoardLane) {
  return [
    ...lane.inputs,
    ...lane.outputs,
    ...lane.completion_criteria,
    ...(lane.closure?.evidence ?? []),
    lane.closure?.closure_summary ?? '',
  ].join(' ')
}

function hasExplicitValidationBasis(lane: DeveloperBoardLane) {
  if (lane.validation_basis) {
    return (
      hasMeaningfulText(lane.validation_basis.owner) &&
      hasMeaningfulText(lane.validation_basis.summary) &&
      hasValues(lane.validation_basis.evidence) &&
      hasMeaningfulText(lane.validation_basis.last_reviewed_at)
    )
  }

  return /(validation|validate|validated|verify|verified|verification|test|tests|evidence|qa|check|checks)/i.test(
    collectValidationEvidenceText(lane)
  )
}

function hasExplicitClosure(lane: DeveloperBoardLane) {
  if (!lane.closure) {
    return false
  }

  return (
    hasMeaningfulText(lane.closure.queue_job_id) &&
    hasMeaningfulText(lane.closure.queue_sha256) &&
    hasMeaningfulText(lane.closure.source_board_concurrency_token) &&
    hasMeaningfulText(lane.closure.closure_summary) &&
    hasValues(lane.closure.evidence) &&
    hasMeaningfulText(lane.closure.completed_at)
  )
}

function hasWatchRationale(lane: DeveloperBoardLane) {
  if (lane.dependencies.length > 0 || lane.subplans.length > 0) {
    return true
  }

  return /(watch|review|monitor|await|pending|later|follow-up)/i.test(
    [lane.objective, ...lane.inputs, ...lane.outputs, ...lane.completion_criteria].join(' ')
  )
}

function collectRegisteredAgentIds(board: DeveloperMasterBoard) {
  return new Set([
    board.control_plane.primary_orchestrator,
    ...board.agent_roles.map((role) => role.agent),
  ])
}

export function analyzeDeveloperLane(
  lane: DeveloperBoardLane,
  laneMap: Map<string, DeveloperBoardLane>,
  registeredAgentIds: Set<string>
): DeveloperLaneAutonomyAnalysis {
  const missingFields: string[] = []
  const advisoryGaps: string[] = []
  const structuralWarnings: DeveloperLaneStructuralWarning[] = []

  if (!lane.title.trim()) {
    missingFields.push('title')
  }
  if (!lane.objective.trim()) {
    missingFields.push('objective')
  }
  if (!hasValues(lane.owners)) {
    missingFields.push('owners')
    structuralWarnings.push(
      createStructuralWarning(
        'missing-owners',
        'blocking',
        'This lane has no meaningful owner assignments.',
        'Assign at least one meaningful owner before dispatch or promotion.'
      )
    )
  }

  const unregisteredOwners = lane.owners.filter(
    (owner) => hasMeaningfulText(owner) && !registeredAgentIds.has(owner)
  )
  if (unregisteredOwners.length > 0) {
    structuralWarnings.push(
      createStructuralWarning(
        'unregistered-owners',
        'advisory',
        `This lane references owner labels without declared agent-role contracts: ${unregisteredOwners.join(', ')}`,
        'Reconcile owner labels with declared agent roles or keep them as operator-only owner notes before dispatch.'
      )
    )
  }
  if (!hasValues(lane.outputs)) {
    advisoryGaps.push('outputs')
    structuralWarnings.push(
      createStructuralWarning(
        'missing-outputs',
        'advisory',
        'This lane does not declare expected outputs.',
        'Declare the expected outputs so execution intent is inspectable.'
      )
    )
  }
  if (!hasValues(lane.completion_criteria)) {
    missingFields.push('completion criteria')
    structuralWarnings.push(
      createStructuralWarning(
        'missing-completion-criteria',
        'blocking',
        'This lane does not declare completion criteria.',
        'Define explicit completion criteria before forward execution decisions.'
      )
    )
  }

  if (!hasValues(lane.inputs)) {
    advisoryGaps.push('inputs')
  }
  if (lane.subplans.length === 0) {
    advisoryGaps.push('sub-plans')
  }

  const orphanedDependencies = lane.dependencies.filter((dependency) => !laneMap.has(dependency))
  if (orphanedDependencies.length > 0) {
    structuralWarnings.push(
      createStructuralWarning(
        'orphaned-dependencies',
        'blocking',
        `This lane references dependency ids that do not exist on the current board: ${orphanedDependencies.join(', ')}`,
        'Repair or remove invalid dependency references before dispatch.'
      )
    )
  }

  if (lane.status === 'watch' && !hasWatchRationale(lane)) {
    structuralWarnings.push(
      createStructuralWarning(
        'stale-watch-lane',
        'advisory',
        'This watch lane no longer carries a clear board-grounded reason for remaining in watch state.',
        'Document the continued watch rationale or reclassify the lane into planned, blocked, active, or completed.'
      )
    )
  }

  if (lane.status === 'active' && !hasExplicitValidationBasis(lane)) {
    structuralWarnings.push(
      createStructuralWarning(
        'active-without-validation-evidence',
        'advisory',
        'This active lane lacks explicit validation_basis evidence in current board state.',
        'Attach or reference current validation basis before relying on this lane as execution-ready.'
      )
    )
  }

  if (lane.status === 'completed' && !hasExplicitClosure(lane)) {
    structuralWarnings.push(
      createStructuralWarning(
        'completed-without-closure',
        'blocking',
        'This completed lane has no persisted closure evidence in canonical board state.',
        'Write reviewed completion evidence back through the explicit completion flow before treating this lane as closed.'
      )
    )
  }

  const unresolvedDependencies = lane.dependencies.filter((dependency) => {
    const dependencyLane = laneMap.get(dependency)
    return !dependencyLane || dependencyLane.status === 'blocked'
  })

  const blockingStructuralWarnings = structuralWarnings.filter(
    (warning) => warning.severity === 'blocking'
  )
  const advisoryStructuralWarnings = structuralWarnings.filter(
    (warning) => warning.severity === 'advisory'
  )

  const readiness: DeveloperLaneReadiness =
    lane.status === 'completed' && hasExplicitClosure(lane)
      ? 'completed'
      : lane.status === 'watch'
      ? 'watch'
      : lane.status === 'blocked' ||
          missingFields.length > 0 ||
          unresolvedDependencies.length > 0 ||
          blockingStructuralWarnings.length > 0
        ? 'blocked'
        : 'ready'

  const recommendations: string[] = []
  if (unresolvedDependencies.length > 0) {
    recommendations.push(`Clear unresolved dependencies: ${unresolvedDependencies.join(', ')}`)
  }
  if (missingFields.length > 0) {
    recommendations.push(`Fill missing execution contract fields: ${missingFields.join(', ')}`)
  }
  if (advisoryGaps.length > 0) {
    recommendations.push(`Strengthen lane detail: ${advisoryGaps.join(', ')}`)
  }
  for (const warning of structuralWarnings) {
    recommendations.push(`${warning.severity === 'blocking' ? 'Resolve blocking drift' : 'Review advisory drift'}: ${warning.remediation}`)
  }
  if (readiness === 'ready' && lane.status === 'planned') {
    recommendations.push('This lane is structurally ready and can be promoted to active when execution should begin')
  }
  if (readiness === 'ready' && lane.status === 'active') {
    recommendations.push('This lane is ready for active agent dispatch')
  }

  const score = Math.max(
    0,
    STATUS_PRIORITY[lane.status] +
      (readiness === 'ready' ? 25 : readiness === 'watch' ? 5 : 0) +
      (hasValues(lane.inputs) ? 5 : 0) +
      (hasValues(lane.outputs) ? 10 : 0) +
      (hasValues(lane.completion_criteria) ? 10 : 0) +
      (lane.subplans.length > 0 ? 5 : 0) -
      lane.dependencies.length * 5 -
      unresolvedDependencies.length * 20 -
      missingFields.length * 15 -
      advisoryStructuralWarnings.length * 5 -
      blockingStructuralWarnings.length * 20
  )

  return {
    laneId: lane.id,
    title: lane.title,
    status: lane.status,
    readiness,
    score,
    structuralWarnings,
    missingFields,
    advisoryGaps,
    unresolvedDependencies,
    recommendations,
  }
}

export function selectReadyDeveloperLaneAnalyses(
  laneAnalyses: DeveloperLaneAutonomyAnalysis[]
) {
  return laneAnalyses.filter((lane) => lane.readiness === 'ready')
}

export function selectBlockedDeveloperLaneAnalyses(
  laneAnalyses: DeveloperLaneAutonomyAnalysis[]
) {
  return laneAnalyses.filter((lane) => lane.readiness === 'blocked')
}

export function selectAdvisoryGapDeveloperLaneAnalyses(
  laneAnalyses: DeveloperLaneAutonomyAnalysis[]
) {
  return laneAnalyses.filter((lane) => lane.advisoryGaps.length > 0)
}

export function selectNextRecommendedDeveloperLaneId(
  laneAnalyses: DeveloperLaneAutonomyAnalysis[]
) {
  return (
    [...laneAnalyses]
      .filter((lane) => lane.readiness === 'ready' && lane.status !== 'watch')
      .sort((left, right) => right.score - left.score)[0]?.laneId ?? null
  )
}

export function buildDeveloperBoardSystemRecommendations(
  laneAnalyses: DeveloperLaneAutonomyAnalysis[],
  nextRecommendedLaneId: string | null
) {
  const systemRecommendations: string[] = []
  const blockedLaneAnalyses = selectBlockedDeveloperLaneAnalyses(laneAnalyses)
  const driftedLaneAnalyses = laneAnalyses.filter((lane) => lane.structuralWarnings.length > 0)
  const activatablePlannedLanes = laneAnalyses.filter(
    (lane) => lane.readiness === 'ready' && lane.status === 'planned'
  )
  const advisoryGapLaneAnalyses = selectAdvisoryGapDeveloperLaneAnalyses(laneAnalyses)
  const blockingStructuralWarningCount = laneAnalyses.reduce(
    (count, lane) => count + lane.structuralWarnings.filter((warning) => warning.severity === 'blocking').length,
    0
  )
  const advisoryStructuralWarningCount = laneAnalyses.reduce(
    (count, lane) => count + lane.structuralWarnings.filter((warning) => warning.severity === 'advisory').length,
    0
  )

  if (nextRecommendedLaneId) {
    const recommendedLane = laneAnalyses.find((lane) => lane.laneId === nextRecommendedLaneId)
    if (recommendedLane) {
      systemRecommendations.push(`Next recommended lane: ${recommendedLane.title}`)
    }
  } else {
    systemRecommendations.push('No lane is fully ready for autonomous dispatch yet; clear structural blockers first')
  }

  if (blockedLaneAnalyses.length > 0) {
    systemRecommendations.push(
      `${blockedLaneAnalyses.length} lane(s) have structural or dependency blockers that will cause drift if ignored`
    )
  }

  if (activatablePlannedLanes.length > 0) {
    systemRecommendations.push(
      `${activatablePlannedLanes.length} planned lane(s) are structurally ready to promote to active`
    )
  }

  if (advisoryGapLaneAnalyses.length > 0) {
    systemRecommendations.push(
      `${advisoryGapLaneAnalyses.length} lane(s) have advisory gaps; bounded slices will improve continuity`
    )
  }

  if (driftedLaneAnalyses.length > 0) {
    systemRecommendations.push(
      `${driftedLaneAnalyses.length} lane(s) carry explicit structural drift warnings (${blockingStructuralWarningCount} blocking, ${advisoryStructuralWarningCount} advisory)`
    )
  }

  return systemRecommendations
}

export function analyzeDeveloperMasterBoard(board: DeveloperMasterBoard): DeveloperBoardAutonomyAnalysis {
  const laneMap = new Map(board.lanes.map((lane) => [lane.id, lane]))
  const registeredAgentIds = collectRegisteredAgentIds(board)
  const laneAnalyses = board.lanes.map((lane) => analyzeDeveloperLane(lane, laneMap, registeredAgentIds))
  const readyLaneIds = selectReadyDeveloperLaneAnalyses(laneAnalyses).map((lane) => lane.laneId)
  const blockedLaneIds = selectBlockedDeveloperLaneAnalyses(laneAnalyses).map((lane) => lane.laneId)
  const driftedLaneIds = laneAnalyses
    .filter((lane) => lane.structuralWarnings.length > 0)
    .map((lane) => lane.laneId)
  const nextRecommendedLaneId = selectNextRecommendedDeveloperLaneId(laneAnalyses)
  const systemRecommendations = buildDeveloperBoardSystemRecommendations(
    laneAnalyses,
    nextRecommendedLaneId
  )
  const blockingStructuralWarningCount = laneAnalyses.reduce(
    (count, lane) => count + lane.structuralWarnings.filter((warning) => warning.severity === 'blocking').length,
    0
  )
  const advisoryStructuralWarningCount = laneAnalyses.reduce(
    (count, lane) => count + lane.structuralWarnings.filter((warning) => warning.severity === 'advisory').length,
    0
  )

  return {
    laneAnalyses,
    readyLaneIds,
    blockedLaneIds,
    driftedLaneIds,
    blockingStructuralWarningCount,
    advisoryStructuralWarningCount,
    nextRecommendedLaneId,
    systemRecommendations,
  }
}

export function createDeveloperLaneDispatchPacket(
  board: DeveloperMasterBoard,
  laneId?: string | null,
  generatedAt = new Date().toISOString()
): DeveloperLaneDispatchPacket | null {
  const autonomy = analyzeDeveloperMasterBoard(board)
  const targetLaneId = laneId ?? autonomy.nextRecommendedLaneId
  if (!targetLaneId) {
    return null
  }

  const lane = board.lanes.find((entry) => entry.id === targetLaneId)
  const laneAnalysis = autonomy.laneAnalyses.find((entry) => entry.laneId === targetLaneId)
  if (!lane || !laneAnalysis) {
    return null
  }

  const ownedAgents = new Set(lane.owners)
  const agentRoles = board.agent_roles.filter(
    (role) => ownedAgents.has(role.agent) || role.agent === board.control_plane.primary_orchestrator
  )

  return {
    generatedAt,
    boardId: board.board_id,
    boardTitle: board.title,
    primaryOrchestrator: board.control_plane.primary_orchestrator,
    lane: {
      id: lane.id,
      title: lane.title,
      status: lane.status,
      objective: lane.objective,
      owners: lane.owners,
      inputs: lane.inputs,
      outputs: lane.outputs,
      dependencies: lane.dependencies,
      completionCriteria: lane.completion_criteria,
      subplans: lane.subplans.map((subplan) => ({
        id: subplan.id,
        title: subplan.title,
        status: subplan.status,
        objective: subplan.objective,
        outputs: subplan.outputs,
      })),
    },
    autonomy: laneAnalysis,
    agentRoles,
  }
}