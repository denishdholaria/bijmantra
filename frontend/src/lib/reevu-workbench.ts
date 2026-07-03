import type { EvidenceEnvelope } from '@/components/ai/EvidenceTraceCard'
import type {
  ReevuPlanExecutionStep,
  ReevuPlanExecutionSummary,
  ReevuRetrievalAudit,
  ReevuRunEvent,
} from '@/lib/reevu-chat-stream'
import type { ReevuSafeFailure } from '@/lib/reevu-safe-failure'
import type { ReevuAttachmentSummary } from '@/lib/reevu-ui-context'

export type ReevuTrustState =
  | 'trusted'
  | 'partial'
  | 'user_provided'
  | 'model_synthesis'
  | 'missing_authority'
  | 'requires_review'

export type ReevuWorkbenchLaneStatus = 'idle' | 'planned' | 'active' | 'completed' | 'missing'

export interface ReevuWorkbenchMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    proposal?: {
      id: number
      title: string
      status: string
      description: string
    }
    evidence_envelope?: EvidenceEnvelope
    retrieval_audit?: ReevuRetrievalAudit
    plan_execution_summary?: ReevuPlanExecutionSummary
    safe_failure?: ReevuSafeFailure
    attachments?: ReevuAttachmentSummary[]
    run_events?: ReevuRunEvent[]
  }
}

export interface ReevuToolDefinition {
  id: string
  displayName: string
  category: 'internal-db' | 'brapi' | 'weather' | 'document' | 'rust-compute' | 'workspace'
  description: string
  authorityLevel: string
  trustState: ReevuTrustState
  permissions: string[]
  auditEvent: string
}

export interface ReevuToolCallCard {
  id: string
  displayName: string
  rawName: string
  status: string
  trustState: ReevuTrustState
  authorityLevel: string
  durationMs?: number
  recordsTouched?: number
  resultType?: string | null
  success?: boolean | null
}

export interface ReevuApprovalGate {
  id: string
  kind: string
  title: string
  status: string
  reason: string
  trustState: ReevuTrustState
  toolDisplayName?: string
}

export interface ReevuArtifact {
  id: string
  kind:
    | 'uploaded_file'
    | 'csv'
    | 'pdf'
    | 'evidence_packet'
    | 'run_summary'
    | 'generated_table'
    | 'comparison'
    | 'map'
    | 'protocol_draft'
    | 'recommendation'
  title: string
  trustState: ReevuTrustState
  detail: string
  source: 'user' | 'reevu' | 'system'
}

export interface ReevuDomainExpertLane {
  id: string
  label: string
  description: string
  status: ReevuWorkbenchLaneStatus
  trustState: ReevuTrustState
  evidenceCount: number
  services: string[]
  missingReason?: string
}

export interface ReevuPlaybook {
  id: string
  title: string
  description: string
  lanes: string[]
  triggerHint: string
  trustState: ReevuTrustState
}

export interface ReevuAdvisoryCaseFile {
  id: string
  title: string
  status: 'open' | 'completed' | 'requires_review' | 'failed'
  messageCount: number
  runCount: number
  evidenceSnapshotCount: number
  artifactCount: number
  decisionCount: number
  updatedAt: string
}

export interface ReevuWorkbenchState {
  latestAssistant?: ReevuWorkbenchMessage
  latestUser?: ReevuWorkbenchMessage
  runEvents: ReevuRunEvent[]
  toolCalls: ReevuToolCallCard[]
  approvalGates: ReevuApprovalGate[]
  artifacts: ReevuArtifact[]
  domainLanes: ReevuDomainExpertLane[]
  playbooks: ReevuPlaybook[]
  toolRegistry: ReevuToolDefinition[]
  caseFile?: ReevuAdvisoryCaseFile
  trustStates: Array<{ state: ReevuTrustState; label: string; description: string }>
}

const CASE_FILE_STORAGE_KEY = 'reevu_advisory_case_files_v1'

const TRUST_STATE_DESCRIPTIONS: Record<ReevuTrustState, string> = {
  trusted: 'Backed by the locked first-wave REEVU authority map or deterministic evidence.',
  partial: 'Usable as dependent enrichment, but not promoted to canonical authority.',
  user_provided: 'Provided by the user as task context; not trusted evidence until ingested.',
  model_synthesis: 'Generated synthesis that must stay attached to evidence and uncertainty.',
  missing_authority: 'Authority or evidence is absent; REEVU must safe-fail or ask for scope.',
  requires_review: 'Human review is required before operational action or recommendation use.',
}

export const REEVU_TRUST_STATES = Object.entries(TRUST_STATE_DESCRIPTIONS).map(([state, description]) => ({
  state: state as ReevuTrustState,
  label: formatLabel(state),
  description,
}))

export const REEVU_TOOL_REGISTRY: ReevuToolDefinition[] = [
  {
    id: 'breeding.search',
    displayName: 'breeding.search',
    category: 'internal-db',
    description: 'Search germplasm, varieties, and breeding records.',
    authorityLevel: 'canonical_reevu_trusted_surface',
    trustState: 'trusted',
    permissions: ['breeding:read'],
    auditEvent: 'reevu.tool.breeding_search',
  },
  {
    id: 'trial.rank',
    displayName: 'trial.rank',
    category: 'brapi',
    description: 'Resolve trial summaries and rank trial performance.',
    authorityLevel: 'canonical_reevu_trusted_surface',
    trustState: 'trusted',
    permissions: ['trials:read'],
    auditEvent: 'reevu.tool.trial_rank',
  },
  {
    id: 'phenotype.compare',
    displayName: 'phenotype.compare',
    category: 'internal-db',
    description: 'Compare trait and phenotype evidence across germplasm.',
    authorityLevel: 'canonical_reevu_trusted_surface',
    trustState: 'trusted',
    permissions: ['phenotyping:read'],
    auditEvent: 'reevu.tool.phenotype_compare',
  },
  {
    id: 'weather.enrich',
    displayName: 'weather.enrich',
    category: 'weather',
    description: 'Attach coordinate-grounded weather enrichment when provider authority is available.',
    authorityLevel: 'partial_dependent_enrichment',
    trustState: 'partial',
    permissions: ['environment:read'],
    auditEvent: 'reevu.tool.weather_enrich',
  },
  {
    id: 'gblup.compute',
    displayName: 'gblup.compute',
    category: 'rust-compute',
    description: 'Run deterministic breeding-value compute over scoped evidence.',
    authorityLevel: 'canonical_reevu_trusted_surface',
    trustState: 'trusted',
    permissions: ['breeding:compute'],
    auditEvent: 'reevu.tool.gblup_compute',
  },
  {
    id: 'artifact.export',
    displayName: 'artifact.export',
    category: 'document',
    description: 'Export generated or retrieved artifacts after review.',
    authorityLevel: 'human_reviewed_export_surface',
    trustState: 'requires_review',
    permissions: ['artifacts:export'],
    auditEvent: 'reevu.tool.artifact_export',
  },
  {
    id: 'workspace.navigate',
    displayName: 'workspace.navigate',
    category: 'workspace',
    description: 'Navigate the BijMantra shell without changing data.',
    authorityLevel: 'workspace_utility_surface',
    trustState: 'model_synthesis',
    permissions: ['workspace:navigate'],
    auditEvent: 'reevu.tool.workspace_navigate',
  },
]

export const REEVU_PLAYBOOKS: ReevuPlaybook[] = [
  {
    id: 'compare-varieties',
    title: 'Compare Varieties',
    description: 'Compare variety performance with trait, trial, and evidence trace lanes.',
    lanes: ['breeding', 'phenotyping', 'seed_operations'],
    triggerHint: 'Compare two or more varieties for yield, disease, or release readiness.',
    trustState: 'trusted',
  },
  {
    id: 'diagnose-trial-failure',
    title: 'Diagnose Trial Failure',
    description: 'Inspect trial design, phenotype signals, agronomy, weather, and pathology risks.',
    lanes: ['phenotyping', 'agronomy', 'climate', 'pathology'],
    triggerHint: 'Why did this trial underperform?',
    trustState: 'requires_review',
  },
  {
    id: 'plan-cross',
    title: 'Plan Cross',
    description: 'Evaluate parents, traits, genetic gain, and downstream nursery constraints.',
    lanes: ['breeding', 'phenotyping', 'economics'],
    triggerHint: 'Plan a cross for disease resistance and yield.',
    trustState: 'requires_review',
  },
  {
    id: 'validate-recommendation',
    title: 'Validate Recommendation',
    description: 'Pressure-test assumptions, evidence, uncertainty, and authority gaps.',
    lanes: ['breeding', 'agronomy', 'climate', 'economics'],
    triggerHint: 'Validate this recommendation before I act.',
    trustState: 'requires_review',
  },
  {
    id: 'prepare-release-dossier',
    title: 'Prepare Release Dossier',
    description: 'Assemble trial, quality, provenance, and decision evidence for review.',
    lanes: ['breeding', 'phenotyping', 'seed_operations', 'economics'],
    triggerHint: 'Prepare a release dossier for this candidate.',
    trustState: 'requires_review',
  },
  {
    id: 'seed-inventory-risk',
    title: 'Seed Inventory Risk',
    description: 'Assess inventory availability, viability, dispatch risk, and replenishment needs.',
    lanes: ['seed_operations', 'economics'],
    triggerHint: 'Assess seed inventory risk for the next dispatch window.',
    trustState: 'requires_review',
  },
]

const BASE_LANES: Array<Omit<ReevuDomainExpertLane, 'status' | 'evidenceCount' | 'services' | 'missingReason'>> = [
  {
    id: 'breeding',
    label: 'Breeding',
    description: 'Genetics, parentage, germplasm, selection, and crossing logic.',
    trustState: 'trusted',
  },
  {
    id: 'phenotyping',
    label: 'Phenotyping',
    description: 'Trait observations, trial measurements, and comparison evidence.',
    trustState: 'trusted',
  },
  {
    id: 'agronomy',
    label: 'Agronomy',
    description: 'Crop management, field operations, and seasonal context.',
    trustState: 'model_synthesis',
  },
  {
    id: 'pathology',
    label: 'Pathology',
    description: 'Disease pressure, resistance claims, and crop-protection signals.',
    trustState: 'requires_review',
  },
  {
    id: 'climate',
    label: 'Climate',
    description: 'Weather and climate enrichment; partial unless live authority succeeds.',
    trustState: 'partial',
  },
  {
    id: 'economics',
    label: 'Economics',
    description: 'Cost, market, supply-chain, and release tradeoffs.',
    trustState: 'requires_review',
  },
  {
    id: 'seed_operations',
    label: 'Seed Operations',
    description: 'Seed inventory, viability, processing, dispatch, and operational risk.',
    trustState: 'requires_review',
  },
]

const FUNCTION_TOOL_ALIASES: Record<string, string> = {
  search_germplasm: 'breeding.search',
  get_germplasm_details: 'breeding.detail',
  compare_germplasm: 'phenotype.compare',
  get_trait_summary: 'phenotype.summarize',
  get_marker_associations: 'genomics.qtl.lookup',
  cross_domain_query: 'reevu.cross_domain.synthesize',
  search_trials: 'trial.search',
  get_trial_results: 'trial.rank',
  propose_create_trial: 'trial.proposal.create',
  search_crosses: 'cross.search',
  predict_cross: 'cross.predict',
  propose_create_cross: 'cross.proposal.create',
  propose_record_observation: 'phenotype.observation.proposal',
  get_observations: 'phenotype.observations',
  get_trait_distribution: 'phenotype.distribution',
  calculate_breeding_value: 'gblup.compute',
  analyze_gxe: 'gxe.analyze',
  calculate_genetic_diversity: 'population.diversity.compute',
  search_accessions: 'seed_bank.accession.search',
  search_seedlots: 'seed_ops.seedlot.search',
  get_seed_inventory: 'seed_ops.inventory.read',
  check_seed_viability: 'seed_bank.viability.check',
  search_locations: 'location.search',
  get_field_info: 'field.info',
  get_crop_calendar: 'agronomy.crop_calendar',
  get_weather_forecast: 'weather.enrich',
  export_data: 'artifact.export',
  navigate_to: 'workspace.navigate',
}

function formatLabel(value: string): string {
  return value
    .replace(/[._-]/g, ' ')
    .replace(/\b\w/g, character => character.toUpperCase())
}

function normalizeTrustState(value: unknown, fallback: ReevuTrustState): ReevuTrustState {
  return typeof value === 'string' && value in TRUST_STATE_DESCRIPTIONS
    ? value as ReevuTrustState
    : fallback
}

function latestMessage(messages: ReevuWorkbenchMessage[], role: ReevuWorkbenchMessage['role']) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === role) {
      return messages[index]
    }
  }
  return undefined
}

function latestAssistantWithRun(messages: ReevuWorkbenchMessage[]) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]
    if (message.role === 'assistant' && (message.metadata?.run_events?.length ?? 0) > 0) {
      return message
    }
  }
  return latestMessage(messages, 'assistant')
}

function toolDefinitionFor(displayName: string | undefined, rawName: string | undefined) {
  const alias = rawName ? FUNCTION_TOOL_ALIASES[rawName] : undefined
  const id = displayName || alias
  return REEVU_TOOL_REGISTRY.find(tool => tool.id === id || tool.displayName === id)
}

function buildToolCalls(events: ReevuRunEvent[]): ReevuToolCallCard[] {
  const toolEvents = events.filter(event => event.tool_name && event.event.startsWith('tool.'))
  const grouped = new Map<string, ReevuRunEvent[]>()

  for (const event of toolEvents) {
    const key = event.tool_name || event.tool_display_name || event.event
    grouped.set(key, [...(grouped.get(key) ?? []), event])
  }

  return Array.from(grouped.entries()).map(([rawName, groupedEvents], index) => {
    const latestEvent = groupedEvents[groupedEvents.length - 1]
    const definition = toolDefinitionFor(latestEvent.tool_display_name, rawName)
    const displayName = latestEvent.tool_display_name
      || definition?.displayName
      || FUNCTION_TOOL_ALIASES[rawName]
      || rawName

    return {
      id: `${rawName}-${index}`,
      displayName,
      rawName,
      status: latestEvent.status,
      trustState: normalizeTrustState(latestEvent.trust_state, definition?.trustState ?? 'model_synthesis'),
      authorityLevel: latestEvent.authority_level || definition?.authorityLevel || 'tool_registry_surface',
      durationMs: latestEvent.duration_ms,
      recordsTouched: latestEvent.records_touched,
      resultType: latestEvent.result_type,
      success: latestEvent.success,
    }
  })
}

function buildApprovalGates(events: ReevuRunEvent[], latestAssistant?: ReevuWorkbenchMessage): ReevuApprovalGate[] {
  const gates = events
    .filter(event => event.event === 'approval.requested')
    .map((event, index) => ({
      id: event.approval_id || event.event_id || `approval-${index}`,
      kind: event.approval_kind || 'human_review',
      title: event.title || 'Human approval requested',
      status: event.approval_status || event.status,
      reason: event.approval_reason || event.detail || 'Human review is required before operational use.',
      trustState: normalizeTrustState(event.trust_state, 'requires_review'),
      toolDisplayName: event.tool_display_name || event.tool_name,
    }))

  if (latestAssistant?.metadata?.proposal && gates.length === 0) {
    gates.push({
      id: `proposal-${latestAssistant.metadata.proposal.id}`,
      kind: 'proposal_creation',
      title: 'Proposal awaiting review',
      status: latestAssistant.metadata.proposal.status || 'pending_review',
      reason: latestAssistant.metadata.proposal.description,
      trustState: 'requires_review',
      toolDisplayName: 'proposal.review',
    })
  }

  return gates
}

function artifactKindForAttachment(attachment: ReevuAttachmentSummary): ReevuArtifact['kind'] {
  const name = attachment.name.toLowerCase()
  if (name.endsWith('.csv') || name.endsWith('.tsv') || attachment.mime_type.includes('csv')) return 'csv'
  if (name.endsWith('.pdf') || attachment.mime_type.includes('pdf')) return 'pdf'
  return 'uploaded_file'
}

function artifactKindForGeneratedId(id: string): ReevuArtifact['kind'] {
  const normalized = id.toLowerCase()
  if (normalized.includes('map')) return 'map'
  if (normalized.includes('comparison')) return 'comparison'
  if (normalized.includes('table') || normalized.includes('csv')) return 'generated_table'
  if (normalized.includes('protocol')) return 'protocol_draft'
  if (normalized.includes('recommend')) return 'recommendation'
  if (normalized.includes('evidence')) return 'evidence_packet'
  return 'run_summary'
}

function buildArtifacts(
  messages: ReevuWorkbenchMessage[],
  latestAssistant?: ReevuWorkbenchMessage,
): ReevuArtifact[] {
  const artifacts: ReevuArtifact[] = []

  for (const message of messages) {
    for (const attachment of message.metadata?.attachments ?? []) {
      artifacts.push({
        id: `upload-${attachment.id}`,
        kind: artifactKindForAttachment(attachment),
        title: attachment.name,
        trustState: 'user_provided',
        detail: 'User-uploaded task context; not trusted evidence until formally ingested.',
        source: 'user',
      })
    }
  }

  if (latestAssistant?.metadata?.evidence_envelope) {
    const envelope = latestAssistant.metadata.evidence_envelope
    artifacts.push({
      id: `evidence-${latestAssistant.id}`,
      kind: 'evidence_packet',
      title: 'Evidence Packet',
      trustState: envelope.evidence_refs.length > 0 ? 'trusted' : 'partial',
      detail: `${envelope.evidence_refs.length} refs, ${envelope.calculation_steps.length} calculations, ${(envelope.missing_evidence_signals ?? []).length} gaps.`,
      source: 'reevu',
    })
  }

  if (latestAssistant?.metadata?.plan_execution_summary) {
    artifacts.push({
      id: `run-summary-${latestAssistant.id}`,
      kind: 'run_summary',
      title: 'Run Summary',
      trustState: 'model_synthesis',
      detail: `${latestAssistant.metadata.plan_execution_summary.steps.length} execution steps captured for this turn.`,
      source: 'system',
    })
  }

  const generatedArtifactIds = new Set<string>()
  for (const event of latestAssistant?.metadata?.run_events ?? []) {
    for (const artifactId of event.artifact_ids ?? []) {
      generatedArtifactIds.add(artifactId)
    }
  }

  for (const artifactId of generatedArtifactIds) {
    artifacts.push({
      id: `generated-${artifactId}`,
      kind: artifactKindForGeneratedId(artifactId),
      title: formatLabel(artifactId),
      trustState: 'model_synthesis',
      detail: 'Generated REEVU artifact scoped to this run; review authority before operational use.',
      source: 'reevu',
    })
  }

  if (latestAssistant?.metadata?.proposal) {
    artifacts.push({
      id: `recommendation-${latestAssistant.metadata.proposal.id}`,
      kind: 'recommendation',
      title: latestAssistant.metadata.proposal.title,
      trustState: 'requires_review',
      detail: latestAssistant.metadata.proposal.description,
      source: 'reevu',
    })
  }

  return artifacts
}

function normalizeDomain(domain: string): string {
  const normalized = domain.toLowerCase()
  if (normalized.includes('trial') || normalized.includes('phenotype')) return 'phenotyping'
  if (normalized.includes('weather') || normalized.includes('climate') || normalized.includes('environment')) return 'climate'
  if (normalized.includes('seed')) return 'seed_operations'
  if (normalized.includes('patholog') || normalized.includes('disease')) return 'pathology'
  if (normalized.includes('economic') || normalized.includes('commerce')) return 'economics'
  if (normalized.includes('agron')) return 'agronomy'
  return normalized
}

function stepEvidenceCount(step: ReevuPlanExecutionStep): number {
  return Object.values(step.output_counts ?? {}).reduce((total, value) => total + value, 0)
}

function buildDomainLanes(latestAssistant?: ReevuWorkbenchMessage): ReevuDomainExpertLane[] {
  const plan = latestAssistant?.metadata?.plan_execution_summary
  const servicesByLane = new Map<string, Set<string>>()
  const evidenceByLane = new Map<string, number>()
  const missingReasonByLane = new Map<string, string>()
  const statusByLane = new Map<string, ReevuWorkbenchLaneStatus>()

  for (const step of plan?.steps ?? []) {
    const laneId = normalizeDomain(step.domain)
    const services = servicesByLane.get(laneId) ?? new Set<string>()
    for (const service of step.services ?? []) {
      services.add(service)
    }
    servicesByLane.set(laneId, services)
    evidenceByLane.set(laneId, (evidenceByLane.get(laneId) ?? 0) + stepEvidenceCount(step))

    const status = (step.status ?? '').toLowerCase()
    if (status === 'missing' || step.missing_reason) {
      statusByLane.set(laneId, 'missing')
      if (step.missing_reason) {
        missingReasonByLane.set(laneId, step.missing_reason)
      }
    } else if (step.completed || status === 'completed') {
      statusByLane.set(laneId, statusByLane.get(laneId) === 'missing' ? 'missing' : 'completed')
    } else {
      statusByLane.set(laneId, 'planned')
    }
  }

  return BASE_LANES.map(lane => ({
    ...lane,
    status: statusByLane.get(lane.id) ?? 'idle',
    evidenceCount: evidenceByLane.get(lane.id) ?? 0,
    services: Array.from(servicesByLane.get(lane.id) ?? []),
    missingReason: missingReasonByLane.get(lane.id),
  }))
}

function buildCaseFile(
  messages: ReevuWorkbenchMessage[],
  runEvents: ReevuRunEvent[],
  artifacts: ReevuArtifact[],
  approvalGates: ReevuApprovalGate[],
  latestAssistant?: ReevuWorkbenchMessage,
  latestUser?: ReevuWorkbenchMessage,
): ReevuAdvisoryCaseFile | undefined {
  if (messages.length === 0) {
    return undefined
  }

  const runId = runEvents[0]?.run_id || latestAssistant?.id || messages[0].id
  const failed = runEvents.some(event => event.event === 'run.failed')
  const completed = runEvents.some(event => event.event === 'run.completed')
  const requiresReview = approvalGates.length > 0 || Boolean(latestAssistant?.metadata?.safe_failure)

  return {
    id: `reevu-case-${runId}`,
    title: latestUser?.content.slice(0, 72) || 'REEVU advisory case',
    status: failed ? 'failed' : requiresReview ? 'requires_review' : completed ? 'completed' : 'open',
    messageCount: messages.length,
    runCount: new Set(runEvents.map(event => event.run_id).filter(Boolean)).size || (runEvents.length ? 1 : 0),
    evidenceSnapshotCount: messages.filter(message => message.metadata?.evidence_envelope).length,
    artifactCount: artifacts.length,
    decisionCount: approvalGates.length + (latestAssistant?.metadata?.proposal ? 1 : 0),
    updatedAt: new Date().toISOString(),
  }
}

export function buildReevuWorkbenchState(messages: ReevuWorkbenchMessage[]): ReevuWorkbenchState {
  const latestAssistant = latestAssistantWithRun(messages)
  const latestUser = latestMessage(messages, 'user')
  const runEvents = latestAssistant?.metadata?.run_events ?? []
  const toolCalls = buildToolCalls(runEvents)
  const approvalGates = buildApprovalGates(runEvents, latestAssistant)
  const artifacts = buildArtifacts(messages, latestAssistant)
  const domainLanes = buildDomainLanes(latestAssistant)
  const caseFile = buildCaseFile(messages, runEvents, artifacts, approvalGates, latestAssistant, latestUser)

  return {
    latestAssistant,
    latestUser,
    runEvents,
    toolCalls,
    approvalGates,
    artifacts,
    domainLanes,
    playbooks: REEVU_PLAYBOOKS,
    toolRegistry: REEVU_TOOL_REGISTRY,
    caseFile,
    trustStates: REEVU_TRUST_STATES,
  }
}

export function loadReevuAdvisoryCaseFiles(storage: Storage = localStorage): ReevuAdvisoryCaseFile[] {
  const raw = storage.getItem(CASE_FILE_STORAGE_KEY)
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function persistReevuAdvisoryCaseFile(
  caseFile: ReevuAdvisoryCaseFile | undefined,
  storage: Storage = localStorage,
): void {
  if (!caseFile) {
    return
  }

  const cases = loadReevuAdvisoryCaseFiles(storage)
  const withoutCurrent = cases.filter(entry => entry.id !== caseFile.id)
  storage.setItem(CASE_FILE_STORAGE_KEY, JSON.stringify([caseFile, ...withoutCurrent].slice(0, 25)))
}
