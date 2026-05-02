import type {
  BacklogItem,
  GovernanceRule,
  Initiative,
  Kpi,
  Milestone,
  PhaseSummary,
  Risk,
  Workstream,
} from './models'

const phaseSummaries: PhaseSummary[] = [
  { phaseId: 'explore', label: 'Explore', description: 'Map frontier opportunities and constraints.', status: 'active' },
  { phaseId: 'seek', label: 'Seek', description: 'Focus high-value mission threads into execution lanes.', status: 'active' },
  { phaseId: 'go', label: 'Go', description: 'Convert validated lanes into delivered systems.', status: 'planned' },
  { phaseId: 'transcend', label: 'Transcend', description: 'Turn execution learning into durable platform leverage.', status: 'planned' },
]

const initiatives: Initiative[] = [
  {
    id: 'or-sensing-mesh',
    phaseId: 'explore',
    title: 'Distributed Sensing Mesh',
    mission: 'Unify field, storage, and lab telemetry into one decision surface.',
    modelLeap: 'From siloed dashboards to lane-aware operational sensing.',
    narrative: 'The sensing mesh aligns environment, vault, and field signals with action-oriented alerts.',
    northStarSignals: ['coverage density', 'alert quality', 'cross-domain traceability'],
  },
  {
    id: 'or-decision-loop',
    phaseId: 'seek',
    title: 'Closed Loop Decision Engine',
    mission: 'Tie prediction, planning, and execution proof into one workflow loop.',
    modelLeap: 'From isolated models to evidence-backed operational loops.',
    narrative: 'Decision loops combine planning assumptions, outputs, and corrective follow-through.',
    northStarSignals: ['assumption coverage', 'response time', 'operator trust'],
  },
  {
    id: 'or-crop-systems',
    phaseId: 'go',
    title: 'Crop Systems Control Plane',
    mission: 'Operationalize crop intelligence, soil, irrigation, and protection as one modular surface.',
    modelLeap: 'From exploratory feature buckets to owned domain modules.',
    narrative: 'This lane aligns the newly promoted crop-system divisions around canonical routing and registry truth.',
    northStarSignals: ['route integrity', 'module ownership', 'validation coverage'],
  },
  {
    id: 'or-autonomy',
    phaseId: 'transcend',
    title: 'Autonomous Execution Fabric',
    mission: 'Continuously route work with evidence, validation, and recovery built in.',
    modelLeap: 'From manual coordination to supervised autonomy.',
    narrative: 'Autonomy remains grounded in canonical state and verified closures.',
    northStarSignals: ['closure rate', 'rework avoided', 'state freshness'],
  },
]

const workstreams: Workstream[] = [
  { id: 'ws-telemetry', phaseId: 'explore', initiativeId: 'or-sensing-mesh', title: 'Telemetry contract alignment', owner: 'Sensors', priority: 'high', status: 'in-progress' },
  { id: 'ws-vault-links', phaseId: 'explore', initiativeId: 'or-sensing-mesh', title: 'Vault to environment link map', owner: 'Seed Bank', priority: 'medium', status: 'pending' },
  { id: 'ws-evidence', phaseId: 'seek', initiativeId: 'or-decision-loop', title: 'Evidence capture trail', owner: 'Platform', priority: 'high', status: 'in-progress' },
  { id: 'ws-recalibration', phaseId: 'seek', initiativeId: 'or-decision-loop', title: 'Prediction recalibration', owner: 'Plant Sciences', priority: 'medium', status: 'pending' },
  { id: 'ws-crop-routing', phaseId: 'go', initiativeId: 'or-crop-systems', title: 'Canonical crop-system routing', owner: 'Frontend', priority: 'high', status: 'in-progress' },
  { id: 'ws-registry-truth', phaseId: 'go', initiativeId: 'or-crop-systems', title: 'Registry truth convergence', owner: 'Frontend', priority: 'high', status: 'in-progress' },
  { id: 'ws-state-refresh', phaseId: 'transcend', initiativeId: 'or-autonomy', title: 'State refresh automation', owner: 'Control Plane', priority: 'medium', status: 'pending' },
  { id: 'ws-recovery', phaseId: 'transcend', initiativeId: 'or-autonomy', title: 'Operator recovery surfaces', owner: 'Platform', priority: 'medium', status: 'pending' },
]

const milestones: Milestone[] = [
  { id: 'ms-observe', phaseId: 'explore', title: 'Baseline signal atlas exported', dueDate: '2026-04-10', status: 'in-progress' },
  { id: 'ms-loop', phaseId: 'seek', title: 'Evidence loop validated', dueDate: '2026-04-18', status: 'pending' },
  { id: 'ms-crop-promote', phaseId: 'go', title: 'Crop-system divisions promoted', dueDate: '2026-03-21', status: 'completed' },
  { id: 'ms-autonomy', phaseId: 'transcend', title: 'Autonomy overlay stabilized', dueDate: '2026-05-01', status: 'pending' },
]

const risks: Risk[] = [
  { id: 'risk-drift', phaseId: 'go', title: 'Registry and route drift', severity: 'high', mitigation: 'Derive navigation truth from owned route manifests.' },
  { id: 'risk-fragment', phaseId: 'seek', title: 'Evidence fragments across features', severity: 'medium', mitigation: 'Require provenance for state transitions.' },
  { id: 'risk-noise', phaseId: 'explore', title: 'Telemetry noise overwhelms operators', severity: 'medium', mitigation: 'Tighten alert thresholds and rollups.' },
  { id: 'risk-staleness', phaseId: 'transcend', title: 'Exported state lags repo truth', severity: 'low', mitigation: 'Run state refresh at meaningful closeout points.' },
]

const backlog: BacklogItem[] = [
  { id: 'backlog-shell', phaseId: 'go', title: 'Collapse duplicate route shell wrappers', owner: 'Frontend', status: 'ready' },
  { id: 'backlog-compat', phaseId: 'go', title: 'Decide permanent alias policy', owner: 'Frontend', status: 'queued' },
  { id: 'backlog-proof', phaseId: 'seek', title: 'Attach proof receipts to decisions', owner: 'Platform', status: 'blocked' },
]

const kpis: Kpi[] = [
  { id: 'kpi-coverage', phaseId: 'explore', name: 'Signal Coverage', current: 68, target: 90, unit: '%' },
  { id: 'kpi-evidence', phaseId: 'seek', name: 'Evidence Closure', current: 54, target: 85, unit: '%' },
  { id: 'kpi-modularity', phaseId: 'go', name: 'Route Integrity', current: 82, target: 100, unit: '%' },
  { id: 'kpi-autonomy', phaseId: 'transcend', name: 'Autonomous Closure', current: 36, target: 70, unit: '%' },
]

const governanceRules: GovernanceRule[] = [
  { id: 'gov-no-mock', title: 'No Mock Operational Data', description: 'Live operational surfaces must not fabricate production records.' },
  { id: 'gov-provenance', title: 'Provenance Required', description: 'Decisions and derived outputs must carry traceable provenance.' },
  { id: 'gov-route-truth', title: 'Single Route Authority', description: 'Navigation surfaces must derive from canonical route ownership.' },
]

export const OUTER_RIMS_DATASET = {
  updatedAt: '2026-03-21T00:00:00.000Z',
  phaseSummaries,
  initiatives,
  workstreams,
  milestones,
  risks,
  backlog,
  kpis,
  governanceRules,
}