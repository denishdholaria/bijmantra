import { useEffect, useState } from 'react'

import {
  addDeveloperControlPlaneMem0Memory,
  captureDeveloperControlPlaneMem0Learning,
  captureDeveloperControlPlaneMem0Mission,
  fetchDeveloperControlPlaneMem0Health,
  fetchDeveloperControlPlaneMem0Status,
  getDeveloperControlPlaneMem0ErrorMessage,
  searchDeveloperControlPlaneMem0Memory,
  type DeveloperControlPlaneMem0AddResponse,
  type DeveloperControlPlaneMem0CaptureLearningResponse,
  type DeveloperControlPlaneMem0CaptureMissionResponse,
  type DeveloperControlPlaneMem0HealthResponse,
  type DeveloperControlPlaneMem0SearchResponse,
  type DeveloperControlPlaneMem0StatusResponse,
} from '../../api/mem0'
import {
  fetchDeveloperControlPlaneLearnings,
  fetchDeveloperControlPlaneMissionState,
  type DeveloperControlPlaneLearningLedgerResponse,
  type DeveloperControlPlaneMissionStateResponse,
} from '../../api/activeBoard'
import { extractFirstResultId, formatScopeLabel } from './activityTrail'
import { useMem0ActivityTrail } from './useMem0ActivityTrail'

export type Mem0TabState = 'idle' | 'loading' | 'ready' | 'error'
export type Mem0ActionState = 'idle' | 'submitting' | 'success' | 'error'
export type LearningTabState = 'idle' | 'loading' | 'ready' | 'error'

const DEFAULT_USER_ID = 'bijmantra-dev'
const DEFAULT_APP_ID = 'bijmantra-dev'

export function useMem0TabController() {
  const [statusState, setStatusState] = useState<Mem0TabState>('idle')
  const [statusRecord, setStatusRecord] = useState<DeveloperControlPlaneMem0StatusResponse | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [statusLastCheckedAt, setStatusLastCheckedAt] = useState<string | null>(null)
  const [healthState, setHealthState] = useState<Mem0TabState>('idle')
  const [healthRecord, setHealthRecord] = useState<DeveloperControlPlaneMem0HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [userId, setUserId] = useState(DEFAULT_USER_ID)
  const [appId, setAppId] = useState(DEFAULT_APP_ID)
  const [runId, setRunId] = useState('')
  const [category, setCategory] = useState('note')
  const [memoryText, setMemoryText] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const [addState, setAddState] = useState<Mem0ActionState>('idle')
  const [addError, setAddError] = useState<string | null>(null)
  const [lastAddResult, setLastAddResult] =
    useState<DeveloperControlPlaneMem0AddResponse | null>(null)

  const [searchState, setSearchState] = useState<Mem0ActionState>('idle')
  const [searchError, setSearchError] = useState<string | null>(null)
  const [lastSearchResult, setLastSearchResult] =
    useState<DeveloperControlPlaneMem0SearchResponse | null>(null)

  const [learningState, setLearningState] = useState<LearningTabState>('idle')
  const [learningRecord, setLearningRecord] =
    useState<DeveloperControlPlaneLearningLedgerResponse | null>(null)
  const [learningError, setLearningError] = useState<string | null>(null)
  const [captureState, setCaptureState] = useState<Mem0ActionState>('idle')
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [capturingLearningId, setCapturingLearningId] = useState<number | null>(null)
  const [lastCaptureResult, setLastCaptureResult] =
    useState<DeveloperControlPlaneMem0CaptureLearningResponse | null>(null)

  const [missionState, setMissionState] = useState<LearningTabState>('idle')
  const [missionRecord, setMissionRecord] =
    useState<DeveloperControlPlaneMissionStateResponse | null>(null)
  const [missionError, setMissionError] = useState<string | null>(null)
  const [captureMissionState, setCaptureMissionState] = useState<Mem0ActionState>('idle')
  const [captureMissionError, setCaptureMissionError] = useState<string | null>(null)
  const [capturingMissionId, setCapturingMissionId] = useState<string | null>(null)
  const [lastMissionCaptureResult, setLastMissionCaptureResult] =
    useState<DeveloperControlPlaneMem0CaptureMissionResponse | null>(null)

  const activityTrailController = useMem0ActivityTrail()

  const refreshStatus = async () => {
    setStatusState('loading')
    setStatusError(null)
    try {
      const record = await fetchDeveloperControlPlaneMem0Status()
      setStatusRecord(record)
      setStatusState('ready')
      setStatusLastCheckedAt(new Date().toISOString())
    } catch (error) {
      setStatusRecord(null)
      setStatusState('error')
      setStatusError(getDeveloperControlPlaneMem0ErrorMessage(error))
      setStatusLastCheckedAt(new Date().toISOString())
    }
  }

  const refreshHealth = async () => {
    setHealthState('loading')
    setHealthError(null)
    try {
      const record = await fetchDeveloperControlPlaneMem0Health({
        userId,
        appId,
        runId: runId || null,
      })
      setHealthRecord(record)
      setHealthState('ready')
    } catch (error) {
      setHealthRecord(null)
      setHealthState('error')
      setHealthError(getDeveloperControlPlaneMem0ErrorMessage(error))
    }
  }

  const refreshDiagnostics = async () => {
    await Promise.allSettled([refreshStatus(), refreshHealth()])
  }

  const refreshLearnings = async () => {
    setLearningState('loading')
    setLearningError(null)
    try {
      const record = await fetchDeveloperControlPlaneLearnings({ limit: 6 })
      setLearningRecord(record)
      setLearningState('ready')
    } catch (error) {
      setLearningRecord(null)
      setLearningState('error')
      setLearningError(getDeveloperControlPlaneMem0ErrorMessage(error))
    }
  }

  const refreshMissions = async () => {
    setMissionState('loading')
    setMissionError(null)
    try {
      const record = await fetchDeveloperControlPlaneMissionState({ limit: 6 })
      setMissionRecord(record)
      setMissionState('ready')
    } catch (error) {
      setMissionRecord(null)
      setMissionState('error')
      setMissionError(getDeveloperControlPlaneMem0ErrorMessage(error))
    }
  }

  useEffect(() => {
    void refreshStatus()
  }, [])

  useEffect(() => {
    void refreshHealth()
  }, [])

  useEffect(() => {
    void refreshLearnings()
  }, [])

  useEffect(() => {
    void refreshMissions()
  }, [])

  const handleAddMemory = async () => {
    setAddState('submitting')
    setAddError(null)
    try {
      const result = await addDeveloperControlPlaneMem0Memory({
        text: memoryText,
        user_id: userId,
        app_id: appId,
        run_id: runId || null,
        category: category || null,
      })
      setLastAddResult(result)
      setAddState('success')
      activityTrailController.recordActivity({
        kind: 'manual-note',
        title: category ? `Manual note: ${category}` : 'Manual note',
        summary: memoryText,
        scopeLabel: formatScopeLabel(result.scope),
        resultId: extractFirstResultId(result.result),
      })
    } catch (error) {
      setAddState('error')
      setAddError(getDeveloperControlPlaneMem0ErrorMessage(error))
    }
  }

  const handleSearch = async () => {
    setSearchState('submitting')
    setSearchError(null)
    try {
      const result = await searchDeveloperControlPlaneMem0Memory({
        query: searchQuery,
        user_id: userId,
        app_id: appId,
        run_id: runId || null,
        limit: 5,
      })
      setLastSearchResult(result)
      setSearchState('success')
    } catch (error) {
      setSearchState('error')
      setSearchError(getDeveloperControlPlaneMem0ErrorMessage(error))
    }
  }

  const handleCaptureLearning = async (learningEntryId: number) => {
    setCaptureState('submitting')
    setCaptureError(null)
    setCapturingLearningId(learningEntryId)
    try {
      const result = await captureDeveloperControlPlaneMem0Learning(learningEntryId, {
        user_id: userId,
        app_id: appId,
        run_id: runId || null,
      })
      setLastCaptureResult(result)
      setCaptureState('success')
      activityTrailController.recordActivity({
        kind: 'learning-capture',
        title: result.source.title,
        summary: result.source.summary,
        scopeLabel: formatScopeLabel(result.scope),
        resultId: extractFirstResultId(result.result),
      })
    } catch (error) {
      setCaptureState('error')
      setCaptureError(getDeveloperControlPlaneMem0ErrorMessage(error))
    } finally {
      setCapturingLearningId(null)
    }
  }

  const handleCaptureMission = async (missionId: string) => {
    setCaptureMissionState('submitting')
    setCaptureMissionError(null)
    setCapturingMissionId(missionId)
    try {
      const result = await captureDeveloperControlPlaneMem0Mission(missionId, {
        user_id: userId,
        app_id: appId,
        run_id: runId || null,
      })
      setLastMissionCaptureResult(result)
      setCaptureMissionState('success')
      activityTrailController.recordActivity({
        kind: 'mission-capture',
        title: result.source.objective,
        summary:
          result.source.final_summary ??
          `Mission ${result.source.mission_id} captured with status ${result.source.status}.`,
        scopeLabel: formatScopeLabel(result.scope),
        resultId: extractFirstResultId(result.result),
      })
    } catch (error) {
      setCaptureMissionState('error')
      setCaptureMissionError(getDeveloperControlPlaneMem0ErrorMessage(error))
    } finally {
      setCapturingMissionId(null)
    }
  }

  return {
    statusState,
    statusRecord,
    statusError,
    statusLastCheckedAt,
    healthState,
    healthRecord,
    healthError,
    userId,
    setUserId,
    appId,
    setAppId,
    runId,
    setRunId,
    category,
    setCategory,
    memoryText,
    setMemoryText,
    searchQuery,
    setSearchQuery,
    addState,
    addError,
    lastAddResult,
    searchState,
    searchError,
    lastSearchResult,
    learningState,
    learningRecord,
    learningError,
    captureState,
    captureError,
    capturingLearningId,
    lastCaptureResult,
    missionState,
    missionRecord,
    missionError,
    captureMissionState,
    captureMissionError,
    capturingMissionId,
    lastMissionCaptureResult,
    refreshDiagnostics,
    refreshLearnings,
    refreshMissions,
    handleAddMemory,
    handleSearch,
    handleCaptureLearning,
    handleCaptureMission,
    ...activityTrailController,
  }
}