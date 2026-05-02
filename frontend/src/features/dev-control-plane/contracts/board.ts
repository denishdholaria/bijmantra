export type DeveloperBoardStatus = 'active' | 'planned' | 'blocked' | 'watch' | 'completed'

export type DeveloperBoardLaneCloseoutReceipt = {
  queue_job_id: string
  artifact_paths: string[]
  mission_id?: string
  producer_key?: string
  source_lane_id?: string
  source_board_concurrency_token?: string
  runtime_profile_id?: string
  runtime_policy_sha256?: string
  closeout_status?: string
  state_refresh_required?: boolean
  receipt_recorded_at?: string
  verification_evidence_ref?: string
  queue_sha256_at_closeout?: string
}

export type DeveloperBoardLaneClosure = {
  queue_job_id: string
  queue_sha256: string
  source_board_concurrency_token: string
  closure_summary: string
  evidence: string[]
  completed_at: string
  closeout_receipt?: DeveloperBoardLaneCloseoutReceipt
}

export type DeveloperBoardLaneValidationBasis = {
  owner: string
  summary: string
  evidence: string[]
  last_reviewed_at: string
}

export type DeveloperBoardLaneReviewGate = {
  reviewed_by: string
  summary: string
  evidence: string[]
  reviewed_at: string
}

export type DeveloperBoardLaneReviewState = {
  spec_review?: DeveloperBoardLaneReviewGate
  risk_review?: DeveloperBoardLaneReviewGate
  verification_evidence?: DeveloperBoardLaneReviewGate
}

export type DeveloperBoardSubplan = {
  id: string
  title: string
  objective: string
  status: DeveloperBoardStatus
  outputs: string[]
}

export type DeveloperBoardLane = {
  id: string
  title: string
  objective: string
  status: DeveloperBoardStatus
  owners: string[]
  inputs: string[]
  outputs: string[]
  dependencies: string[]
  completion_criteria: string[]
  validation_basis?: DeveloperBoardLaneValidationBasis
  review_state?: DeveloperBoardLaneReviewState
  closure?: DeveloperBoardLaneClosure
  subplans: DeveloperBoardSubplan[]
}

export type DeveloperBoardAgentRole = {
  agent: string
  role: string
  reads: string[]
  writes: string[]
  escalation: string[]
}

export type DeveloperMasterBoard = {
  version: string
  board_id: string
  title: string
  visibility: 'internal-superuser'
  intent: string
  continuous_operation_goal: string
  orchestration_contract: {
    canonical_inputs: string[]
    canonical_outputs: string[]
    execution_loop: string[]
    coordination_rules: string[]
  }
  lanes: DeveloperBoardLane[]
  agent_roles: DeveloperBoardAgentRole[]
  control_plane: {
    primary_orchestrator: string
    evidence_sources: string[]
    operating_cadence: string[]
  }
}

export const DEVELOPER_MASTER_BOARD_SCHEMA_VERSION = '1.2.0'
export const DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION = '1.0.0'
export const DEVELOPER_MASTER_BOARD_PREVIOUS_SCHEMA_VERSION = '1.1.0'

export const developerMasterBoardVersionPolicy = {
  exportVersion: DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
  currentVersion: DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
  supportedImportVersions: [
    DEVELOPER_MASTER_BOARD_LEGACY_SCHEMA_VERSION,
    DEVELOPER_MASTER_BOARD_PREVIOUS_SCHEMA_VERSION,
    DEVELOPER_MASTER_BOARD_SCHEMA_VERSION,
  ] as readonly string[],
  compatibilityMode: 'explicit-import-list',
} as const

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isStringArray(value: unknown) {
  return Array.isArray(value) && value.every((entry) => typeof entry === 'string')
}

function isOptionalBoolean(value: unknown): value is boolean | undefined {
  return value === undefined || typeof value === 'boolean'
}

function isBoardStatus(value: unknown): value is DeveloperBoardStatus {
  return (
    value === 'active' ||
    value === 'planned' ||
    value === 'blocked' ||
    value === 'watch' ||
    value === 'completed'
  )
}

function assertDeveloperBoardLaneClosure(
  value: unknown,
  index: number
): asserts value is DeveloperBoardLaneClosure {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: lanes[${index}].closure must be an object`)
  }

  if (
    typeof value.queue_job_id !== 'string' ||
    typeof value.queue_sha256 !== 'string' ||
    typeof value.source_board_concurrency_token !== 'string' ||
    typeof value.closure_summary !== 'string' ||
    typeof value.completed_at !== 'string'
  ) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].closure is missing required text fields`
    )
  }

  if (!isStringArray(value.evidence)) {
    throw new Error(`Invalid developer master board: lanes[${index}].closure evidence must be a string array`)
  }

  if (value.closeout_receipt !== undefined) {
    assertDeveloperBoardLaneCloseoutReceipt(value.closeout_receipt, index)
  }
}

function assertDeveloperBoardLaneCloseoutReceipt(
  value: unknown,
  index: number
): asserts value is DeveloperBoardLaneCloseoutReceipt {
  if (!isRecord(value)) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].closure.closeout_receipt must be an object`
    )
  }

  if (typeof value.queue_job_id !== 'string') {
    throw new Error(
      `Invalid developer master board: lanes[${index}].closure.closeout_receipt queue_job_id must be a string`
    )
  }

  if (!isStringArray(value.artifact_paths)) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].closure.closeout_receipt artifact_paths must be a string array`
    )
  }

  if (
    (value.mission_id !== undefined && typeof value.mission_id !== 'string') ||
    (value.producer_key !== undefined && typeof value.producer_key !== 'string') ||
    (value.source_lane_id !== undefined && typeof value.source_lane_id !== 'string') ||
    (value.source_board_concurrency_token !== undefined &&
      typeof value.source_board_concurrency_token !== 'string') ||
    (value.runtime_profile_id !== undefined && typeof value.runtime_profile_id !== 'string') ||
    (value.runtime_policy_sha256 !== undefined && typeof value.runtime_policy_sha256 !== 'string') ||
    (value.closeout_status !== undefined && typeof value.closeout_status !== 'string') ||
    !isOptionalBoolean(value.state_refresh_required) ||
    (value.receipt_recorded_at !== undefined && typeof value.receipt_recorded_at !== 'string') ||
    (value.verification_evidence_ref !== undefined &&
      typeof value.verification_evidence_ref !== 'string') ||
    (value.queue_sha256_at_closeout !== undefined &&
      typeof value.queue_sha256_at_closeout !== 'string')
  ) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].closure.closeout_receipt has unsupported field types`
    )
  }
}

function assertDeveloperBoardLaneValidationBasis(
  value: unknown,
  index: number
): asserts value is DeveloperBoardLaneValidationBasis {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: lanes[${index}].validation_basis must be an object`)
  }

  if (
    typeof value.owner !== 'string' ||
    typeof value.summary !== 'string' ||
    typeof value.last_reviewed_at !== 'string'
  ) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].validation_basis is missing required text fields`
    )
  }

  if (!isStringArray(value.evidence)) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].validation_basis evidence must be a string array`
    )
  }
}

function assertDeveloperBoardLaneReviewGate(
  value: unknown,
  index: number,
  fieldName: keyof DeveloperBoardLaneReviewState
): asserts value is DeveloperBoardLaneReviewGate {
  if (!isRecord(value)) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].review_state.${fieldName} must be an object`
    )
  }

  if (
    typeof value.reviewed_by !== 'string' ||
    typeof value.summary !== 'string' ||
    typeof value.reviewed_at !== 'string'
  ) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].review_state.${fieldName} is missing required text fields`
    )
  }

  if (!isStringArray(value.evidence)) {
    throw new Error(
      `Invalid developer master board: lanes[${index}].review_state.${fieldName} evidence must be a string array`
    )
  }
}

function assertDeveloperBoardLaneReviewState(
  value: unknown,
  index: number
): asserts value is DeveloperBoardLaneReviewState {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: lanes[${index}].review_state must be an object`)
  }

  if (value.spec_review !== undefined) {
    assertDeveloperBoardLaneReviewGate(value.spec_review, index, 'spec_review')
  }

  if (value.risk_review !== undefined) {
    assertDeveloperBoardLaneReviewGate(value.risk_review, index, 'risk_review')
  }

  if (value.verification_evidence !== undefined) {
    assertDeveloperBoardLaneReviewGate(value.verification_evidence, index, 'verification_evidence')
  }
}

function assertSupportedDeveloperMasterBoardVersion(version: unknown) {
  if (typeof version !== 'string') {
    throw new Error('Invalid developer master board: version must be a string')
  }

  if (developerMasterBoardVersionPolicy.supportedImportVersions.includes(version)) {
    return
  }

  throw new Error(
    `Invalid developer master board: unsupported schema version ${JSON.stringify(version)}; supported import versions: ${developerMasterBoardVersionPolicy.supportedImportVersions.join(', ')}; current export version: ${developerMasterBoardVersionPolicy.exportVersion}`
  )
}

function assertDeveloperBoardSubplan(value: unknown, index: number): asserts value is DeveloperBoardSubplan {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: lanes[${index}].subplans entry must be an object`)
  }

  if (typeof value.id !== 'string' || typeof value.title !== 'string' || typeof value.objective !== 'string') {
    throw new Error(`Invalid developer master board: lanes[${index}].subplans entry is missing required text fields`)
  }

  if (!isBoardStatus(value.status)) {
    throw new Error(`Invalid developer master board: lanes[${index}].subplans entry has an unsupported status`)
  }

  if (!isStringArray(value.outputs)) {
    throw new Error(`Invalid developer master board: lanes[${index}].subplans entry outputs must be a string array`)
  }
}

function assertDeveloperBoardLane(value: unknown, index: number): asserts value is DeveloperBoardLane {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: lanes[${index}] must be an object`)
  }

  if (typeof value.id !== 'string' || typeof value.title !== 'string' || typeof value.objective !== 'string') {
    throw new Error(`Invalid developer master board: lanes[${index}] is missing required text fields`)
  }

  if (!isBoardStatus(value.status)) {
    throw new Error(`Invalid developer master board: lanes[${index}] has an unsupported status`)
  }

  if (!isStringArray(value.owners) || !isStringArray(value.inputs) || !isStringArray(value.outputs)) {
    throw new Error(`Invalid developer master board: lanes[${index}] owners, inputs, and outputs must be string arrays`)
  }

  if (!isStringArray(value.dependencies) || !isStringArray(value.completion_criteria)) {
    throw new Error(`Invalid developer master board: lanes[${index}] dependencies and completion criteria must be string arrays`)
  }

  if (value.validation_basis !== undefined) {
    assertDeveloperBoardLaneValidationBasis(value.validation_basis, index)
  }

  if (value.review_state !== undefined) {
    assertDeveloperBoardLaneReviewState(value.review_state, index)
  }

  if (value.closure !== undefined) {
    assertDeveloperBoardLaneClosure(value.closure, index)
  }

  if (!Array.isArray(value.subplans)) {
    throw new Error(`Invalid developer master board: lanes[${index}].subplans must be an array`)
  }

  value.subplans.forEach((subplan, subplanIndex) => assertDeveloperBoardSubplan(subplan, subplanIndex))
}

function assertDeveloperBoardAgentRole(value: unknown, index: number): asserts value is DeveloperBoardAgentRole {
  if (!isRecord(value)) {
    throw new Error(`Invalid developer master board: agent_roles[${index}] must be an object`)
  }

  if (typeof value.agent !== 'string' || typeof value.role !== 'string') {
    throw new Error(`Invalid developer master board: agent_roles[${index}] is missing required text fields`)
  }

  if (!isStringArray(value.reads) || !isStringArray(value.writes) || !isStringArray(value.escalation)) {
    throw new Error(`Invalid developer master board: agent_roles[${index}] reads, writes, and escalation must be string arrays`)
  }
}

function assertDeveloperMasterBoard(value: unknown): asserts value is DeveloperMasterBoard {
  if (!isRecord(value)) {
    throw new Error('Invalid developer master board: root value must be an object')
  }

  assertSupportedDeveloperMasterBoardVersion(value.version)

  if (
    typeof value.board_id !== 'string' ||
    typeof value.title !== 'string' ||
    typeof value.intent !== 'string' ||
    typeof value.continuous_operation_goal !== 'string'
  ) {
    throw new Error('Invalid developer master board: missing required root text fields')
  }

  if (value.visibility !== 'internal-superuser') {
    throw new Error('Invalid developer master board: visibility must be internal-superuser')
  }

  if (!isRecord(value.orchestration_contract)) {
    throw new Error('Invalid developer master board: orchestration_contract must be an object')
  }

  if (
    !isStringArray(value.orchestration_contract.canonical_inputs) ||
    !isStringArray(value.orchestration_contract.canonical_outputs) ||
    !isStringArray(value.orchestration_contract.execution_loop) ||
    !isStringArray(value.orchestration_contract.coordination_rules)
  ) {
    throw new Error('Invalid developer master board: orchestration_contract fields must be string arrays')
  }

  if (!Array.isArray(value.lanes)) {
    throw new Error('Invalid developer master board: lanes must be an array')
  }

  value.lanes.forEach((lane, index) => assertDeveloperBoardLane(lane, index))

  if (!Array.isArray(value.agent_roles)) {
    throw new Error('Invalid developer master board: agent_roles must be an array')
  }

  value.agent_roles.forEach((role, index) => assertDeveloperBoardAgentRole(role, index))

  if (!isRecord(value.control_plane)) {
    throw new Error('Invalid developer master board: control_plane must be an object')
  }

  if (typeof value.control_plane.primary_orchestrator !== 'string') {
    throw new Error('Invalid developer master board: control_plane.primary_orchestrator must be a string')
  }

  if (
    !isStringArray(value.control_plane.evidence_sources) ||
    !isStringArray(value.control_plane.operating_cadence)
  ) {
    throw new Error('Invalid developer master board: control_plane fields must be string arrays')
  }
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export const defaultDeveloperMasterBoard: DeveloperMasterBoard = {
  version: developerMasterBoardVersionPolicy.currentVersion,
  board_id: 'bijmantra-app-development-master-board',
  title: 'BijMantra Developer Control Plane',
  visibility: 'internal-superuser',
  intent:
    'Keep BijMantra development planning, sub-plans, orchestration context, and the Zero Human Intervention Autonomous Execution Protocol inside the product instead of a separate planning app.',
  continuous_operation_goal:
    'Allow internal agents to turn human vision and optional constraints into executable objectives, validated changes, and continuous improvement from one canonical JSON board.',
  orchestration_contract: {
    canonical_inputs: [
      'human vision',
      'optional constraints',
      'repo state',
      'architecture decisions',
      'active tasks',
      'validation evidence',
      'runtime findings',
    ],
    canonical_outputs: [
      'interpreted system objectives',
      'execution lanes',
      'sub-plan updates',
      'decision state',
      'verification evidence',
      'handoff summaries',
      'known limitations',
    ],
    execution_loop: [
      'interpret vision into concrete system objectives',
      'choose the safest viable architecture move: refactor, rebuild, or extend',
      'decompose work into bounded atomic tasks',
      'observe repo and app state',
      'prioritize the next valid lane',
      'execute changes in bounded slices',
      'verify outcomes with tests or live evidence',
      'write back explicit completion evidence to the board',
      'monitor runtime and board drift for the next improvement cycle',
    ],
    coordination_rules: [
      'human input is limited to vision and optional constraints',
      'one canonical board for control-plane planning and sub-plans',
      'agents read JSON first before acting',
      'dependencies must be explicit before parallel work starts',
      'completion criteria must be machine-readable where possible',
      'under uncertainty, choose the safest non-destructive path and preserve rollback capability',
    ],
  },
  lanes: [
    {
      id: 'control-plane',
      title: 'Control Plane and Agent Orchestration',
      objective:
        'Give OmShriMaatreNamaha and supporting agents a stable control-plane view of vision translation, plans, dependencies, safety constraints, and closure criteria.',
      status: 'active',
      owners: ['OmShriMaatreNamaha', 'OmVishnaveNamah'],
      inputs: ['metrics.json', '.ai/ decisions and tasks', '.agent/jobs queue', 'developer control plane'],
      outputs: ['prioritized lanes', 'dispatch plans', 'completed closure evidence'],
      dependencies: ['platform-runtime'],
      completion_criteria: [
        'all active lanes have explicit objective, dependencies, and completion criteria',
        'board state can be exported and reloaded without loss',
        'autonomous execution rules stay inspectable without additional human clarification',
      ],
      validation_basis: {
        owner: 'OmVishnaveNamah',
        summary:
          'Focused control-plane contract and autonomy checkpoints remain the current execution-confidence basis for this lane.',
        evidence: [
          'frontend/src/features/dev-control-plane/contracts/board.test.ts',
          'frontend/src/features/dev-control-plane/autonomy.test.ts',
        ],
        last_reviewed_at: '2026-03-18T19:10:00.000Z',
      },
      review_state: {
        spec_review: {
          reviewed_by: 'OmVishnaveNamah',
          summary:
            'Control-plane contract scope and board-first authority were reviewed for the current execution slice.',
          evidence: [
            'frontend/src/features/dev-control-plane/contracts/board.test.ts',
            'AGENTS.md',
          ],
          reviewed_at: '2026-03-31T08:00:00.000Z',
        },
        risk_review: {
          reviewed_by: 'OmKlimKalikayeiNamah',
          summary:
            'No destructive control-plane mutation path was introduced for the current lane slice.',
          evidence: [
            '.github/skills/developer-board-overnight-queue-sync/SKILL.md',
            'frontend/src/features/dev-control-plane/reviewedDispatch.test.ts',
          ],
          reviewed_at: '2026-03-31T08:05:00.000Z',
        },
        verification_evidence: {
          reviewed_by: 'OmVishnaveNamah',
          summary:
            'Focused control-plane contract and autonomy checks remain the current verification evidence for this lane.',
          evidence: [
            'frontend/src/features/dev-control-plane/autonomy.test.ts',
            'frontend/src/features/dev-control-plane/contracts/board.test.ts',
          ],
          reviewed_at: '2026-03-31T08:10:00.000Z',
        },
      },
      subplans: [
        {
          id: 'hidden-board-surface',
          title: 'Hidden board surface',
          objective: 'Host the developer control plane inside BijMantra on a hidden internal route.',
          status: 'active',
          outputs: ['internal route', 'persisted JSON board'],
        },
        {
          id: 'agent-contract',
          title: 'Agent contract view',
          objective: 'Expose machine-readable agent responsibilities and escalation rules.',
          status: 'planned',
          outputs: ['agent role map', 'coordination contract'],
        },
        {
          id: 'vision-translation',
          title: 'Vision translation protocol',
          objective: 'Convert high-level vision and optional constraints into executable system objectives and safety-bounded tasks.',
          status: 'active',
          outputs: ['objective map', 'execution-ready task graph'],
        },
      ],
    },
    {
      id: 'platform-runtime',
      title: 'App Runtime and Developer Surface Capabilities',
      objective:
        'Use internal developer surfaces to inspect control-plane state, runtime evidence, and adaptive signals without a separate tool.',
      status: 'completed',
      owners: ['OmNamahShivaya', 'OmShreemMahalakshmiyeiNamaha'],
      inputs: ['json graph canvas', 'system routes', 'developer route wrapper'],
      outputs: ['developer tooling', 'board visualizations', 'runtime state maps'],
      dependencies: [],
      completion_criteria: [
        'developer can read and edit board JSON inside BijMantra',
        'graph mode renders the board without leaving the app',
        'runtime telemetry can inform whether autonomous execution should adapt or retry',
      ],
      validation_basis: {
        owner: 'OmVishnaveNamah',
        summary:
          'Graph-surface and hidden-route review remain the explicit execution-confidence basis for runtime developer tooling.',
        evidence: [
          'frontend/src/features/dev-control-plane/ui/graph/GraphTab.test.tsx',
          'frontend/src/features/dev-control-plane/ui/ControlPlanePage.test.tsx',
        ],
        last_reviewed_at: '2026-03-18T19:10:00.000Z',
      },
      review_state: {
        spec_review: {
          reviewed_by: 'OmVishnaveNamah',
          summary:
            'The reviewed dispatch pilot scope remains bounded to platform-runtime and hidden developer surfaces.',
          evidence: [
            'frontend/src/features/dev-control-plane/reviewedDispatch.test.ts',
            'frontend/src/features/dev-control-plane/ui/orchestration/OrchestrationTab.tsx',
          ],
          reviewed_at: '2026-03-31T08:20:00.000Z',
        },
        risk_review: {
          reviewed_by: 'OmKlimKalikayeiNamah',
          summary:
            'The reviewed dispatch pilot still preserves board-wins precedence and keeps the overnight queue derived.',
          evidence: [
            '.agent/jobs/README.md',
            'frontend/src/features/dev-control-plane/contracts/dispatch.ts',
          ],
          reviewed_at: '2026-03-31T08:25:00.000Z',
        },
        verification_evidence: {
          reviewed_by: 'OmVishnaveNamah',
          summary:
            'Graph and control-plane runtime checks remain the current verification evidence for this pilot lane.',
          evidence: [
            'frontend/src/features/dev-control-plane/ui/graph/GraphTab.test.tsx',
            'frontend/src/features/dev-control-plane/ui/ControlPlanePage.test.tsx',
          ],
          reviewed_at: '2026-03-31T08:30:00.000Z',
        },
      },
      subplans: [
        {
          id: 'json-graph-reuse',
          title: 'JSON graph reuse',
          objective: 'Reuse the native graph canvas for planning JSON and orchestration maps.',
          status: 'active',
          outputs: ['graph tab', 'visual dependency map'],
        },
        {
          id: 'observability-loop',
          title: 'Observability loop',
          objective: 'Surface runtime findings, error states, and execution drift so the next autonomous slice can adapt safely.',
          status: 'planned',
          outputs: ['runtime evidence view', 'adaptation triggers'],
        },
      ],
    },
    {
      id: 'delivery-lanes',
      title: 'Feature Delivery and Verification',
      objective:
        'Drive implementation lanes from the same board so planning, execution, verification, and autonomous improvement stay synchronized.',
      status: 'watch',
      owners: ['OmSaraswatiBrahmayeNamah', 'OmKlimKalikayeiNamah'],
      inputs: ['active board lanes', 'repo evidence', 'test results'],
      outputs: ['completed features', 'verified evidence trails', 'risk notes'],
      dependencies: ['control-plane'],
      completion_criteria: [
        'lanes can move from planned to active to completed using explicit closure evidence',
        'validated improvements can be queued without requiring fresh human clarification',
      ],
      subplans: [
        {
          id: 'overnight-automation',
          title: 'Overnight automation',
          objective: 'Use the same developer control plane as a planning source for autonomous overnight slices.',
          status: 'planned',
          outputs: ['queue-ready lanes', 'handoff state'],
        },
        {
          id: 'continuous-improvement',
          title: 'Continuous improvement loop',
          objective: 'Batch or immediately fix bottlenecks, technical debt, and UX friction once evidence confirms the safer path.',
          status: 'planned',
          outputs: ['improvement backlog', 'validated optimizations'],
        },
      ],
    },
  ],
  agent_roles: [
    {
      agent: 'OmShriMaatreNamaha',
      role: 'Primary orchestrator and control-plane owner',
      reads: ['board JSON', 'queue state', 'repo evidence', 'verification results'],
      writes: ['lane priority', 'closure summaries', 'dispatch state'],
      escalation: ['conflicting evidence', 'destructive actions', 'cross-lane deadlock'],
    },
    {
      agent: 'OmNamahShivaya',
      role: 'Transformation and simplification owner',
      reads: ['architecture drift', 'obsolete surfaces', 'lane dependencies'],
      writes: ['refactor proposals', 'simplified execution paths'],
      escalation: ['high-risk migration', 'data model breakage'],
    },
    {
      agent: 'OmVishnaveNamah',
      role: 'Correctness and validation owner',
      reads: ['completion criteria', 'tests', 'runtime findings'],
      writes: ['validation verdicts', 'evidence-backed risk notes'],
      escalation: ['unverified critical changes', 'contract drift'],
    },
  ],
  control_plane: {
    primary_orchestrator: 'OmShriMaatreNamaha',
    evidence_sources: [
      'metrics.json',
      '.ai/tasks',
      '.ai/decisions',
      '.agent/jobs/overnight-queue.json',
      'frontend and backend verification results',
    ],
    operating_cadence: [
      'inspect board before work begins',
      'translate human vision and optional constraints into executable objectives before dispatch',
      'update lane state after each validated slice',
      'prefer the safest non-destructive path whenever uncertainty is high',
      'use the board as the canonical handoff surface for autonomous continuity',
    ],
  },
}

function normalizeDeveloperBoardSubplan(subplan: DeveloperBoardSubplan): DeveloperBoardSubplan {
  return {
    id: subplan.id,
    title: subplan.title,
    objective: subplan.objective,
    status: subplan.status,
    outputs: [...subplan.outputs],
  }
}

function normalizeDeveloperBoardLane(lane: DeveloperBoardLane): DeveloperBoardLane {
  return {
    id: lane.id,
    title: lane.title,
    objective: lane.objective,
    status: lane.status,
    owners: [...lane.owners],
    inputs: [...lane.inputs],
    outputs: [...lane.outputs],
    dependencies: [...lane.dependencies],
    completion_criteria: [...lane.completion_criteria],
    validation_basis: lane.validation_basis
      ? {
          owner: lane.validation_basis.owner,
          summary: lane.validation_basis.summary,
          evidence: [...lane.validation_basis.evidence],
          last_reviewed_at: lane.validation_basis.last_reviewed_at,
        }
      : undefined,
    review_state: lane.review_state
      ? {
          spec_review: lane.review_state.spec_review
            ? {
                reviewed_by: lane.review_state.spec_review.reviewed_by,
                summary: lane.review_state.spec_review.summary,
                evidence: [...lane.review_state.spec_review.evidence],
                reviewed_at: lane.review_state.spec_review.reviewed_at,
              }
            : undefined,
          risk_review: lane.review_state.risk_review
            ? {
                reviewed_by: lane.review_state.risk_review.reviewed_by,
                summary: lane.review_state.risk_review.summary,
                evidence: [...lane.review_state.risk_review.evidence],
                reviewed_at: lane.review_state.risk_review.reviewed_at,
              }
            : undefined,
          verification_evidence: lane.review_state.verification_evidence
            ? {
                reviewed_by: lane.review_state.verification_evidence.reviewed_by,
                summary: lane.review_state.verification_evidence.summary,
                evidence: [...lane.review_state.verification_evidence.evidence],
                reviewed_at: lane.review_state.verification_evidence.reviewed_at,
              }
            : undefined,
        }
      : undefined,
    closure: lane.closure
      ? {
          queue_job_id: lane.closure.queue_job_id,
          queue_sha256: lane.closure.queue_sha256,
          source_board_concurrency_token: lane.closure.source_board_concurrency_token,
          closure_summary: lane.closure.closure_summary,
          evidence: [...lane.closure.evidence],
          completed_at: lane.closure.completed_at,
          closeout_receipt: lane.closure.closeout_receipt
            ? {
                queue_job_id: lane.closure.closeout_receipt.queue_job_id,
                artifact_paths: [...lane.closure.closeout_receipt.artifact_paths],
                mission_id: lane.closure.closeout_receipt.mission_id,
                producer_key: lane.closure.closeout_receipt.producer_key,
                source_lane_id: lane.closure.closeout_receipt.source_lane_id,
                source_board_concurrency_token:
                  lane.closure.closeout_receipt.source_board_concurrency_token,
                runtime_profile_id: lane.closure.closeout_receipt.runtime_profile_id,
                runtime_policy_sha256: lane.closure.closeout_receipt.runtime_policy_sha256,
                closeout_status: lane.closure.closeout_receipt.closeout_status,
                state_refresh_required: lane.closure.closeout_receipt.state_refresh_required,
                receipt_recorded_at: lane.closure.closeout_receipt.receipt_recorded_at,
                verification_evidence_ref:
                  lane.closure.closeout_receipt.verification_evidence_ref,
                queue_sha256_at_closeout:
                  lane.closure.closeout_receipt.queue_sha256_at_closeout,
              }
            : undefined,
        }
      : undefined,
    subplans: lane.subplans.map((subplan) => normalizeDeveloperBoardSubplan(subplan)),
  }
}

function normalizeDeveloperBoardAgentRole(role: DeveloperBoardAgentRole): DeveloperBoardAgentRole {
  return {
    agent: role.agent,
    role: role.role,
    reads: [...role.reads],
    writes: [...role.writes],
    escalation: [...role.escalation],
  }
}

export function normalizeDeveloperMasterBoard(board: DeveloperMasterBoard): DeveloperMasterBoard {
  return {
    version: board.version,
    board_id: board.board_id,
    title: board.title,
    visibility: board.visibility,
    intent: board.intent,
    continuous_operation_goal: board.continuous_operation_goal,
    orchestration_contract: {
      canonical_inputs: [...board.orchestration_contract.canonical_inputs],
      canonical_outputs: [...board.orchestration_contract.canonical_outputs],
      execution_loop: [...board.orchestration_contract.execution_loop],
      coordination_rules: [...board.orchestration_contract.coordination_rules],
    },
    lanes: board.lanes.map((lane) => normalizeDeveloperBoardLane(lane)),
    agent_roles: board.agent_roles.map((role) => normalizeDeveloperBoardAgentRole(role)),
    control_plane: {
      primary_orchestrator: board.control_plane.primary_orchestrator,
      evidence_sources: [...board.control_plane.evidence_sources],
      operating_cadence: [...board.control_plane.operating_cadence],
    },
  }
}

export function createDefaultDeveloperMasterBoardJson() {
  return serializeDeveloperMasterBoard(defaultDeveloperMasterBoard)
}

export function parseDeveloperMasterBoard(rawBoardJson: string) {
  const parsed = JSON.parse(rawBoardJson) as unknown
  assertDeveloperMasterBoard(parsed)
  return parsed
}

export function serializeDeveloperMasterBoard(board: DeveloperMasterBoard) {
  return `${JSON.stringify(normalizeDeveloperMasterBoard(board), null, 2)}\n`
}

export function canonicalizeDeveloperMasterBoardJson(rawBoardJson: string) {
  return serializeDeveloperMasterBoard(parseDeveloperMasterBoard(rawBoardJson))
}

function createTemplateId(label: string) {
  const suffix =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID().slice(0, 8)
      : Math.random().toString(36).slice(2, 10)

  return `${slugify(label)}-${suffix}`
}

export function createDeveloperLaneTemplate(index: number): DeveloperBoardLane {
  const label = `New Lane ${index}`

  return {
    id: createTemplateId(label),
    title: label,
    objective: 'Describe the outcome this lane owns.',
    status: 'planned',
    owners: ['OmShriMaatreNamaha'],
    inputs: [],
    outputs: [],
    dependencies: [],
    completion_criteria: [],
    subplans: [],
  }
}

export function createDeveloperSubplanTemplate(index: number): DeveloperBoardSubplan {
  const label = `Subplan ${index}`

  return {
    id: createTemplateId(label),
    title: label,
    objective: 'Describe the bounded sub-plan outcome.',
    status: 'planned',
    outputs: [],
  }
}
