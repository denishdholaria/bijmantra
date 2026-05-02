import { ApiError } from '@/lib/api-errors'
import { apiClient } from '@/lib/api-client'

export type DeveloperControlPlaneMem0Service = {
  enabled: boolean
  configured: boolean
  host: string
  project_scoped: boolean
  org_project_pair_valid: boolean
  is_optional: boolean
  is_canonical_authority: boolean
}

export type DeveloperControlPlaneMem0StatusResponse = {
  service: DeveloperControlPlaneMem0Service
  purpose: string
  detail: string
}

export type DeveloperControlPlaneMem0HealthResponse = {
  scope: DeveloperControlPlaneMem0Scope
  reachable: boolean
  checked_at: string
  latency_ms: number | null
  result_count: number | null
  detail: string
}

export type DeveloperControlPlaneMem0Scope = {
  user_id: string
  app_id: string
  run_id: string | null
}

export type DeveloperControlPlaneMem0AddRequest = {
  text: string
  user_id?: string | null
  app_id?: string
  run_id?: string | null
  category?: string | null
  metadata?: Record<string, unknown> | null
}

export type DeveloperControlPlaneMem0AddResponse = {
  scope: DeveloperControlPlaneMem0Scope
  result: Record<string, unknown>
}

export type DeveloperControlPlaneMem0SearchRequest = {
  query: string
  user_id?: string | null
  app_id?: string
  run_id?: string | null
  limit?: number
  filters?: Record<string, unknown> | null
}

export type DeveloperControlPlaneMem0SearchResponse = {
  query: string
  scope: DeveloperControlPlaneMem0Scope
  limit: number
  result: Record<string, unknown>
}

export type DeveloperControlPlaneMem0LearningSource = {
  learning_entry_id: number
  entry_type: string
  source_classification: string
  title: string
  summary: string
  source_lane_id: string | null
  queue_job_id: string | null
  linked_mission_id: string | null
  source_reference: string | null
}

export type DeveloperControlPlaneMem0CaptureLearningRequest = {
  user_id?: string | null
  app_id?: string
  run_id?: string | null
}

export type DeveloperControlPlaneMem0CaptureLearningResponse = {
  scope: DeveloperControlPlaneMem0Scope
  source: DeveloperControlPlaneMem0LearningSource
  memory_text: string
  result: Record<string, unknown>
}

export type DeveloperControlPlaneMem0MissionSource = {
  mission_id: string
  objective: string
  status: string
  owner: string
  priority: string
  producer_key: string | null
  queue_job_id: string | null
  source_lane_id: string | null
  evidence_count: number
  blocker_count: number
  final_summary: string | null
}

export type DeveloperControlPlaneMem0MissionCloseout = {
  exists: boolean
  queue_job_id: string | null
  closeout_status: string | null
  verification_evidence_ref: string | null
  artifact_count: number
  command_count: number
}

export type DeveloperControlPlaneMem0CaptureMissionRequest = {
  user_id?: string | null
  app_id?: string
  run_id?: string | null
}

export type DeveloperControlPlaneMem0CaptureMissionResponse = {
  scope: DeveloperControlPlaneMem0Scope
  source: DeveloperControlPlaneMem0MissionSource
  closeout_receipt: DeveloperControlPlaneMem0MissionCloseout | null
  memory_text: string
  result: Record<string, unknown>
}

export async function fetchDeveloperControlPlaneMem0Status() {
  return apiClient.get<DeveloperControlPlaneMem0StatusResponse>(
    '/api/v2/developer-control-plane/mem0/status'
  )
}

export async function fetchDeveloperControlPlaneMem0Health(query: {
  userId?: string | null
  appId?: string
  runId?: string | null
} = {}) {
  const searchParams = new URLSearchParams()
  if (query.userId) {
    searchParams.set('user_id', query.userId)
  }
  if (query.appId) {
    searchParams.set('app_id', query.appId)
  }
  if (query.runId) {
    searchParams.set('run_id', query.runId)
  }

  const suffix = searchParams.size > 0 ? `?${searchParams.toString()}` : ''

  return apiClient.get<DeveloperControlPlaneMem0HealthResponse>(
    `/api/v2/developer-control-plane/mem0/health${suffix}`
  )
}

export async function addDeveloperControlPlaneMem0Memory(
  payload: DeveloperControlPlaneMem0AddRequest
) {
  return apiClient.post<DeveloperControlPlaneMem0AddResponse>(
    '/api/v2/developer-control-plane/mem0/memories',
    payload
  )
}

export async function searchDeveloperControlPlaneMem0Memory(
  payload: DeveloperControlPlaneMem0SearchRequest
) {
  return apiClient.post<DeveloperControlPlaneMem0SearchResponse>(
    '/api/v2/developer-control-plane/mem0/search',
    payload
  )
}

export async function captureDeveloperControlPlaneMem0Learning(
  learningEntryId: number,
  payload: DeveloperControlPlaneMem0CaptureLearningRequest
) {
  return apiClient.post<DeveloperControlPlaneMem0CaptureLearningResponse>(
    `/api/v2/developer-control-plane/mem0/learnings/${encodeURIComponent(String(learningEntryId))}/capture`,
    payload
  )
}

export async function captureDeveloperControlPlaneMem0Mission(
  missionId: string,
  payload: DeveloperControlPlaneMem0CaptureMissionRequest
) {
  return apiClient.post<DeveloperControlPlaneMem0CaptureMissionResponse>(
    `/api/v2/developer-control-plane/mem0/missions/${encodeURIComponent(missionId)}/capture`,
    payload
  )
}

export function getDeveloperControlPlaneMem0ErrorMessage(error: unknown) {
  if (!(error instanceof Error)) {
    return 'Developer Mem0 request failed'
  }

  if (error instanceof ApiError) {
    const detail = (error.responseData as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') {
      return detail
    }
    return error.getUserMessage()
  }

  return error.message || 'Developer Mem0 request failed'
}