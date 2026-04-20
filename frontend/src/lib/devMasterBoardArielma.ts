import type { DeveloperMasterBoard, DeveloperBoardAgentRole, DeveloperBoardLane, DeveloperBoardStatus } from '@/features/dev-control-plane/contracts/board'

export type DeveloperMasterBoardArielmaLens = 'system-topology' | 'dependency-flow' | 'agent-ownership'

type ArielmaLensOption = {
  value: DeveloperMasterBoardArielmaLens
  label: string
  description: string
}

export const developerMasterBoardArielmaLensOptions: ArielmaLensOption[] = [
  {
    value: 'system-topology',
    label: 'System topology',
    description: 'Board, orchestrator, evidence sources, lanes, and sub-plans in one bounded control-plane map.',
  },
  {
    value: 'dependency-flow',
    label: 'Dependency flow',
    description: 'Lane-level unblock paths so operators can see what holds execution back.',
  },
  {
    value: 'agent-ownership',
    label: 'Agent ownership',
    description: 'Primary orchestrator, agent roles, and the lanes they currently own or influence.',
  },
] as const

function sanitizeId(value: string) {
  const sanitized = value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
  return sanitized ? `n_${sanitized}` : 'n_node'
}

function sanitizeLabel(value: string) {
  return value.replace(/"/g, "'").replace(/\n/g, ' ').trim()
}

function diagramNode(id: string, label: string) {
  return `${id}["${sanitizeLabel(label)}"]`
}

function diagramClass(status: DeveloperBoardStatus) {
  if (status === 'active') return 'statusActive'
  if (status === 'blocked') return 'statusBlocked'
  if (status === 'watch') return 'statusWatch'
  if (status === 'completed') return 'statusCompleted'
  return 'statusPlanned'
}

function commonClassDefs() {
  return [
    'classDef board fill:#082f6b,stroke:#bfdbfe,color:#eff6ff,stroke-width:2px;',
    'classDef metadata fill:#0f766e,stroke:#99f6e4,color:#ecfeff,stroke-width:1.5px;',
    'classDef lane fill:#172554,stroke:#93c5fd,color:#eff6ff,stroke-width:1.5px;',
    'classDef subplan fill:#1e3a8a,stroke:#bfdbfe,color:#eff6ff;',
    'classDef agent fill:#3f6212,stroke:#bef264,color:#f7fee7,stroke-width:1.5px;',
    'classDef statusActive fill:#065f46,stroke:#6ee7b7,color:#ecfdf5,stroke-width:1.5px;',
    'classDef statusPlanned fill:#1d4ed8,stroke:#93c5fd,color:#eff6ff,stroke-width:1.5px;',
    'classDef statusBlocked fill:#991b1b,stroke:#fca5a5,color:#fef2f2,stroke-width:1.5px;',
    'classDef statusWatch fill:#854d0e,stroke:#fde68a,color:#fffbeb,stroke-width:1.5px;',
    'classDef statusCompleted fill:#166534,stroke:#86efac,color:#f0fdf4,stroke-width:1.5px;',
  ]
}

function laneLabel(lane: DeveloperBoardLane) {
  return `${lane.title}\n${lane.status.toUpperCase()} · ${lane.subplans.length} sub-plans`
}

function buildSystemTopology(board: DeveloperMasterBoard) {
  const lines = ['flowchart LR']
  const boardId = 'n_board'
  const orchestratorId = 'n_orchestrator'
  const evidenceId = 'n_evidence'
  const cadenceId = 'n_cadence'
  const contractId = 'n_contract'

  lines.push(`    ${diagramNode(boardId, `${board.title}\n${board.visibility}`)}`)
  lines.push(`    ${diagramNode(orchestratorId, `Primary orchestrator\n${board.control_plane.primary_orchestrator}`)}`)
  lines.push(`    ${diagramNode(evidenceId, `Evidence sources\n${board.control_plane.evidence_sources.length} sources`)}`)
  lines.push(`    ${diagramNode(cadenceId, `Operating cadence\n${board.control_plane.operating_cadence.length} steps`)}`)
  lines.push(`    ${diagramNode(contractId, `Orchestration contract\n${board.orchestration_contract.coordination_rules.length} rules`)}`)
  lines.push(`    ${boardId} --> ${orchestratorId}`)
  lines.push(`    ${boardId} --> ${evidenceId}`)
  lines.push(`    ${boardId} --> ${cadenceId}`)
  lines.push(`    ${boardId} --> ${contractId}`)

  for (const lane of board.lanes) {
    const laneId = sanitizeId(`lane_${lane.id}`)
    lines.push(`    ${diagramNode(laneId, laneLabel(lane))}`)
    lines.push(`    ${boardId} --> ${laneId}`)

    for (const subplan of lane.subplans) {
      const subplanId = sanitizeId(`subplan_${lane.id}_${subplan.id}`)
      lines.push(`    ${diagramNode(subplanId, `${subplan.title}\n${subplan.status.toUpperCase()}`)}`)
      lines.push(`    ${laneId} --> ${subplanId}`)
      lines.push(`    class ${subplanId} subplan,${diagramClass(subplan.status)};`)
    }

    lines.push(`    class ${laneId} lane,${diagramClass(lane.status)};`)
  }

  lines.push(`    class ${boardId} board;`)
  lines.push(`    class ${orchestratorId},${evidenceId},${cadenceId},${contractId} metadata;`)
  lines.push(...commonClassDefs().map((line) => `    ${line}`))
  return `${lines.join('\n')}\n`
}

function buildDependencyFlow(board: DeveloperMasterBoard) {
  const lines = ['flowchart LR']
  const rootId = 'n_execution_root'
  lines.push(`    ${diagramNode(rootId, `${board.title}\nExecution dependencies`)}`)

  for (const lane of board.lanes) {
    const laneId = sanitizeId(`lane_${lane.id}`)
    lines.push(`    ${diagramNode(laneId, `${lane.title}\n${lane.status.toUpperCase()} · ${lane.dependencies.length} deps`)}`)
    lines.push(`    class ${laneId} lane,${diagramClass(lane.status)};`)

    if (lane.dependencies.length === 0) {
      lines.push(`    ${rootId} -->|ready surface| ${laneId}`)
      continue
    }

    for (const dependencyId of lane.dependencies) {
      const dependencyLane = board.lanes.find((candidate) => candidate.id === dependencyId)
      const dependencyNodeId = sanitizeId(`lane_${dependencyId}`)
      if (dependencyLane) {
        lines.push(`    ${diagramNode(dependencyNodeId, `${dependencyLane.title}\n${dependencyLane.status.toUpperCase()}`)}`)
        lines.push(`    ${dependencyNodeId} -->|unblocks| ${laneId}`)
        lines.push(`    class ${dependencyNodeId} lane,${diagramClass(dependencyLane.status)};`)
      } else {
        lines.push(`    ${diagramNode(dependencyNodeId, `Missing dependency\n${dependencyId}`)}`)
        lines.push(`    ${dependencyNodeId} -.-> ${laneId}`)
        lines.push(`    class ${dependencyNodeId} statusBlocked;`)
      }
    }
  }

  lines.push(`    class ${rootId} board;`)
  lines.push(...commonClassDefs().map((line) => `    ${line}`))
  return `${lines.join('\n')}\n`
}

function lanesForAgent(board: DeveloperMasterBoard, role: DeveloperBoardAgentRole) {
  return board.lanes.filter((lane) => lane.owners.includes(role.agent))
}

function buildAgentOwnership(board: DeveloperMasterBoard) {
  const lines = ['flowchart LR']
  const rootId = 'n_agent_root'
  lines.push(`    ${diagramNode(rootId, `${board.control_plane.primary_orchestrator}\nPrimary orchestrator`)}`)

  for (const role of board.agent_roles) {
    const agentId = sanitizeId(`agent_${role.agent}`)
    const ownedLanes = lanesForAgent(board, role)
    lines.push(`    ${diagramNode(agentId, `${role.agent}\n${ownedLanes.length} owned lanes`)}`)
    lines.push(`    ${rootId} -->|coordinates| ${agentId}`)
    lines.push(`    class ${agentId} agent;`)

    for (const lane of ownedLanes) {
      const laneId = sanitizeId(`lane_${lane.id}`)
      lines.push(`    ${diagramNode(laneId, `${lane.title}\n${lane.status.toUpperCase()}`)}`)
      lines.push(`    ${agentId} -->|owns| ${laneId}`)
      lines.push(`    class ${laneId} lane,${diagramClass(lane.status)};`)
    }
  }

  lines.push(`    class ${rootId} board;`)
  lines.push(...commonClassDefs().map((line) => `    ${line}`))
  return `${lines.join('\n')}\n`
}

export function createDeveloperMasterBoardArielma(
  board: DeveloperMasterBoard,
  lens: DeveloperMasterBoardArielmaLens
) {
  if (lens === 'dependency-flow') {
    return buildDependencyFlow(board)
  }

  if (lens === 'agent-ownership') {
    return buildAgentOwnership(board)
  }

  return buildSystemTopology(board)
}
