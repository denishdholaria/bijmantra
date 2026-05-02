import { vi } from 'vitest'

import type {
  DeveloperControlPlaneMem0AddResponse,
  DeveloperControlPlaneMem0CaptureLearningResponse,
  DeveloperControlPlaneMem0CaptureMissionResponse,
  DeveloperControlPlaneMem0HealthResponse,
  DeveloperControlPlaneMem0SearchResponse,
  DeveloperControlPlaneMem0StatusResponse,
} from '../../api/mem0'
import type {
  DeveloperControlPlaneLearningLedgerResponse,
  DeveloperControlPlaneMissionStateResponse,
} from '../../api/activeBoard'

type Mem0Scope = DeveloperControlPlaneMem0HealthResponse['scope']
type LearningEntry = DeveloperControlPlaneLearningLedgerResponse['entries'][number]
type MissionRecord = DeveloperControlPlaneMissionStateResponse['missions'][number]

export const clipboardWriteText = vi.fn()

export const sonnerMocks = {
  success: vi.fn(),
  error: vi.fn(),
}

export const mem0ApiMocks = {
  fetchDeveloperControlPlaneMem0Health: vi.fn(),
  fetchDeveloperControlPlaneMem0Status: vi.fn(),
  addDeveloperControlPlaneMem0Memory: vi.fn(),
  searchDeveloperControlPlaneMem0Memory: vi.fn(),
  captureDeveloperControlPlaneMem0Learning: vi.fn(),
  captureDeveloperControlPlaneMem0Mission: vi.fn(),
  getDeveloperControlPlaneMem0ErrorMessage: vi.fn((error: unknown) =>
    error instanceof Error ? error.message : 'Mem0 error'
  ),
}

export const activeBoardApiMocks = {
  fetchDeveloperControlPlaneLearnings: vi.fn(),
  fetchDeveloperControlPlaneMissionState: vi.fn(),
}

export function installClipboardMock() {
  Object.defineProperty(window.navigator, 'clipboard', {
    configurable: true,
    value: {
      writeText: clipboardWriteText,
    },
  })
}

export function resetMem0TestEnvironment() {
  window.sessionStorage.clear()
  vi.clearAllMocks()
  installClipboardMock()
  clipboardWriteText.mockResolvedValue(undefined)
}

export function createMem0Scope(overrides: Partial<Mem0Scope> = {}): Mem0Scope {
  return {
    user_id: 'bijmantra-dev',
    app_id: 'bijmantra-dev',
    run_id: null,
    ...overrides,
  }
}

export function createMem0StatusResponse(
  overrides: Partial<DeveloperControlPlaneMem0StatusResponse> = {}
): DeveloperControlPlaneMem0StatusResponse {
  return {
    service: {
      enabled: true,
      configured: true,
      host: 'https://api.mem0.ai',
      project_scoped: false,
      org_project_pair_valid: true,
      is_optional: true,
      is_canonical_authority: false,
      ...(overrides.service ?? {}),
    },
    purpose: 'Developer-only cloud memory for short project recall.',
    detail: 'Mem0 is ready for developer memory with global app-level scoping.',
    ...overrides,
  }
}

export function createMem0HealthResponse(
  overrides: Partial<DeveloperControlPlaneMem0HealthResponse> = {}
): DeveloperControlPlaneMem0HealthResponse {
  return {
    scope: createMem0Scope(overrides.scope ?? {}),
    reachable: true,
    checked_at: '2026-04-05T10:20:00.000Z',
    latency_ms: 12.5,
    result_count: 0,
    detail: 'Mem0 cloud probe succeeded with the configured backend credentials.',
    ...overrides,
  }
}

export function createLearningEntry(overrides: Partial<LearningEntry> = {}): LearningEntry {
  return {
    learning_entry_id: 42,
    organization_id: 1,
    entry_type: 'pattern',
    source_classification: 'mission-state',
    title: 'Keep Mem0 separate from REEVU',
    summary: 'Developer cloud recall should remain separate from REEVU runtime memory.',
    confidence_score: 0.95,
    recorded_by_user_id: 1,
    recorded_by_email: 'admin@example.com',
    board_id: 'bijmantra-app-development-master-board',
    source_lane_id: 'control-plane',
    queue_job_id: 'job-1',
    linked_mission_id: 'mission-1',
    approval_receipt_id: null,
    source_reference: '.ai/tasks/mem0.md',
    evidence_refs: [],
    summary_metadata: null,
    recorded_at: '2026-04-05T10:30:00.000Z',
    ...overrides,
  }
}

export function createLearningLedgerResponse(
  entries: LearningEntry[] = [createLearningEntry()],
  overrides: Partial<DeveloperControlPlaneLearningLedgerResponse> = {}
): DeveloperControlPlaneLearningLedgerResponse {
  return {
    total_count: entries.length,
    entries,
    ...overrides,
  }
}

export function createMissionRecord(overrides: Partial<MissionRecord> = {}): MissionRecord {
  return {
    mission_id: 'mission-1',
    objective: 'Capture canonical mission outcomes into Mem0 explicitly',
    status: 'completed',
    owner: 'OmShriMaatreNamaha',
    priority: 'high',
    producer_key: 'OmShriMaatreNamaha',
    queue_job_id: 'job-1',
    source_lane_id: 'control-plane',
    source_board_concurrency_token: 'token-1',
    created_at: '2026-04-05T10:00:00.000Z',
    updated_at: '2026-04-05T10:30:00.000Z',
    subtask_total: 3,
    subtask_completed: 3,
    assignment_total: 3,
    evidence_count: 2,
    blocker_count: 0,
    escalation_needed: false,
    verification: {
      passed: 2,
      warned: 0,
      failed: 0,
      last_verified_at: '2026-04-05T10:25:00.000Z',
    },
    final_summary: 'Mission closeout evidence is now available for explicit developer recall.',
    ...overrides,
  }
}

export function createMissionStateResponse(
  missions: MissionRecord[] = [createMissionRecord()],
  overrides: Partial<DeveloperControlPlaneMissionStateResponse> = {}
): DeveloperControlPlaneMissionStateResponse {
  return {
    count: missions.length,
    missions,
    ...overrides,
  }
}

export function createMem0AddResponse(options: {
  scope?: Partial<Mem0Scope>
  resultId?: string
} = {}): DeveloperControlPlaneMem0AddResponse {
  return {
    scope: createMem0Scope(options.scope),
    result: {
      results: [{ id: options.resultId ?? 'mem-1' }],
    },
  }
}

export function createMem0SearchResponse(options: {
  query?: string
  scope?: Partial<Mem0Scope>
  limit?: number
  resultId?: string
  memory?: string
} = {}): DeveloperControlPlaneMem0SearchResponse {
  return {
    query: options.query ?? 'Mem0 separate from REEVU',
    scope: createMem0Scope(options.scope),
    limit: options.limit ?? 5,
    result: {
      results: [
        {
          id: options.resultId ?? 'mem-1',
          memory: options.memory ?? 'Keep Mem0 separate from REEVU',
        },
      ],
    },
  }
}

export function createCaptureLearningResponse(options: {
  scope?: Partial<Mem0Scope>
  source?: Partial<DeveloperControlPlaneMem0CaptureLearningResponse['source']>
  resultId?: string
} = {}): DeveloperControlPlaneMem0CaptureLearningResponse {
  return {
    scope: createMem0Scope(options.scope),
    source: {
      learning_entry_id: 42,
      entry_type: 'pattern',
      source_classification: 'mission-state',
      title: 'Keep Mem0 separate from REEVU',
      summary: 'Developer cloud recall should remain separate from REEVU runtime memory.',
      source_lane_id: 'control-plane',
      queue_job_id: 'job-1',
      linked_mission_id: 'mission-1',
      source_reference: '.ai/tasks/mem0.md',
      ...(options.source ?? {}),
    },
    memory_text: 'Developer control plane learning [pattern] Keep Mem0 separate from REEVU.',
    result: {
      results: [{ id: options.resultId ?? 'mem-learn-1' }],
    },
  }
}

export function createCaptureMissionResponse(options: {
  scope?: Partial<Mem0Scope>
  source?: Partial<DeveloperControlPlaneMem0CaptureMissionResponse['source']>
  resultId?: string
} = {}): DeveloperControlPlaneMem0CaptureMissionResponse {
  return {
    scope: createMem0Scope(options.scope),
    source: {
      mission_id: 'mission-1',
      objective: 'Capture canonical mission outcomes into Mem0 explicitly',
      status: 'completed',
      owner: 'OmShriMaatreNamaha',
      priority: 'high',
      producer_key: 'OmShriMaatreNamaha',
      queue_job_id: 'job-1',
      source_lane_id: 'control-plane',
      evidence_count: 2,
      blocker_count: 0,
      final_summary: 'Mission closeout evidence is now available for explicit developer recall.',
      ...(options.source ?? {}),
    },
    closeout_receipt: {
      exists: true,
      queue_job_id: 'job-1',
      closeout_status: 'succeeded',
      verification_evidence_ref: '.agent/runtime/missions/job-1/verify.json',
      artifact_count: 1,
      command_count: 1,
    },
    memory_text: 'Developer control plane mission outcome [completed] Capture canonical mission outcomes into Mem0 explicitly.',
    result: {
      results: [{ id: options.resultId ?? 'mem-mission-1' }],
    },
  }
}

export function seedMem0BootstrapMocks() {
  mem0ApiMocks.fetchDeveloperControlPlaneMem0Status.mockResolvedValue(createMem0StatusResponse())
  mem0ApiMocks.fetchDeveloperControlPlaneMem0Health.mockResolvedValue(createMem0HealthResponse())
  activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockResolvedValue(
    createLearningLedgerResponse()
  )
  activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue(
    createMissionStateResponse()
  )
}