import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  activeBoardApiMocks,
  createCaptureLearningResponse,
  createCaptureMissionResponse,
  createMem0AddResponse,
  createMem0SearchResponse,
  mem0ApiMocks,
  resetMem0TestEnvironment,
  seedMem0BootstrapMocks,
  sonnerMocks,
} from './mem0TestHelpers'
import { useMem0TabController } from './useMem0TabController'

vi.mock('../../api/mem0', () => ({
  fetchDeveloperControlPlaneMem0Health: mem0ApiMocks.fetchDeveloperControlPlaneMem0Health,
  fetchDeveloperControlPlaneMem0Status: mem0ApiMocks.fetchDeveloperControlPlaneMem0Status,
  addDeveloperControlPlaneMem0Memory: mem0ApiMocks.addDeveloperControlPlaneMem0Memory,
  searchDeveloperControlPlaneMem0Memory: mem0ApiMocks.searchDeveloperControlPlaneMem0Memory,
  captureDeveloperControlPlaneMem0Learning: mem0ApiMocks.captureDeveloperControlPlaneMem0Learning,
  captureDeveloperControlPlaneMem0Mission: mem0ApiMocks.captureDeveloperControlPlaneMem0Mission,
  getDeveloperControlPlaneMem0ErrorMessage: mem0ApiMocks.getDeveloperControlPlaneMem0ErrorMessage,
}))

vi.mock('../../api/activeBoard', () => ({
  fetchDeveloperControlPlaneLearnings: activeBoardApiMocks.fetchDeveloperControlPlaneLearnings,
  fetchDeveloperControlPlaneMissionState: activeBoardApiMocks.fetchDeveloperControlPlaneMissionState,
}))

vi.mock('sonner', () => ({
  toast: sonnerMocks,
}))

describe('useMem0TabController', () => {
  beforeEach(() => {
    resetMem0TestEnvironment()
    seedMem0BootstrapMocks()
  })

  it('bootstraps state, refreshes diagnostics for the current scope, and records successful actions', async () => {
    mem0ApiMocks.addDeveloperControlPlaneMem0Memory.mockResolvedValue(
      createMem0AddResponse({
        scope: {
          user_id: 'agri-architect',
          app_id: 'bijmantra-mem0',
          run_id: 'session-1',
        },
      })
    )
    mem0ApiMocks.searchDeveloperControlPlaneMem0Memory.mockResolvedValue(
      createMem0SearchResponse({
        scope: {
          user_id: 'agri-architect',
          app_id: 'bijmantra-mem0',
          run_id: 'session-1',
        },
      })
    )
    mem0ApiMocks.captureDeveloperControlPlaneMem0Learning.mockResolvedValue(
      createCaptureLearningResponse({
        scope: {
          user_id: 'agri-architect',
          app_id: 'bijmantra-mem0',
          run_id: 'session-1',
        },
      })
    )
    mem0ApiMocks.captureDeveloperControlPlaneMem0Mission.mockResolvedValue(
      createCaptureMissionResponse({
        scope: {
          user_id: 'agri-architect',
          app_id: 'bijmantra-mem0',
          run_id: 'session-1',
        },
      })
    )

    const { result } = renderHook(() => useMem0TabController())

    await waitFor(() => {
      expect(result.current.statusState).toBe('ready')
      expect(result.current.healthState).toBe('ready')
      expect(result.current.learningState).toBe('ready')
      expect(result.current.missionState).toBe('ready')
    })

    expect(mem0ApiMocks.fetchDeveloperControlPlaneMem0Status).toHaveBeenCalledTimes(1)
    expect(mem0ApiMocks.fetchDeveloperControlPlaneMem0Health).toHaveBeenCalledWith({
      userId: 'bijmantra-dev',
      appId: 'bijmantra-dev',
      runId: null,
    })

    act(() => {
      result.current.setUserId('agri-architect')
      result.current.setAppId('bijmantra-mem0')
      result.current.setRunId('session-1')
      result.current.setCategory('decision')
      result.current.setMemoryText('Keep Mem0 separate from REEVU.')
      result.current.setSearchQuery('Mem0 separate from REEVU')
    })

    await act(async () => {
      await result.current.refreshDiagnostics()
    })

    expect(mem0ApiMocks.fetchDeveloperControlPlaneMem0Health).toHaveBeenLastCalledWith({
      userId: 'agri-architect',
      appId: 'bijmantra-mem0',
      runId: 'session-1',
    })

    await act(async () => {
      await result.current.handleAddMemory()
    })

    expect(mem0ApiMocks.addDeveloperControlPlaneMem0Memory).toHaveBeenCalledWith({
      text: 'Keep Mem0 separate from REEVU.',
      user_id: 'agri-architect',
      app_id: 'bijmantra-mem0',
      run_id: 'session-1',
      category: 'decision',
    })
    expect(result.current.addState).toBe('success')
    expect(result.current.activityTrail).toHaveLength(1)
    expect(result.current.activityTrail[0]).toMatchObject({
      kind: 'manual-note',
      title: 'Manual note: decision',
      resultId: 'mem-1',
    })

    await act(async () => {
      await result.current.handleSearch()
    })

    expect(mem0ApiMocks.searchDeveloperControlPlaneMem0Memory).toHaveBeenCalledWith({
      query: 'Mem0 separate from REEVU',
      user_id: 'agri-architect',
      app_id: 'bijmantra-mem0',
      run_id: 'session-1',
      limit: 5,
    })
    expect(result.current.searchState).toBe('success')
    expect(result.current.lastSearchResult?.result.results[0]?.id).toBe('mem-1')

    await act(async () => {
      await result.current.handleCaptureLearning(42)
    })

    expect(mem0ApiMocks.captureDeveloperControlPlaneMem0Learning).toHaveBeenCalledWith(42, {
      user_id: 'agri-architect',
      app_id: 'bijmantra-mem0',
      run_id: 'session-1',
    })
    expect(result.current.captureState).toBe('success')
    expect(result.current.activityTrail.map((entry) => entry.kind)).toEqual([
      'learning-capture',
      'manual-note',
    ])

    await act(async () => {
      await result.current.handleCaptureMission('mission-1')
    })

    expect(mem0ApiMocks.captureDeveloperControlPlaneMem0Mission).toHaveBeenCalledWith('mission-1', {
      user_id: 'agri-architect',
      app_id: 'bijmantra-mem0',
      run_id: 'session-1',
    })
    expect(result.current.captureMissionState).toBe('success')
    expect(result.current.activityTrail.map((entry) => entry.kind)).toEqual([
      'mission-capture',
      'learning-capture',
      'manual-note',
    ])
    expect(result.current.filteredActivityTrail).toHaveLength(3)

    const persistedTrail = JSON.parse(
      window.sessionStorage.getItem('developer-control-plane-mem0-activity-trail') ?? '[]'
    )
    expect(persistedTrail).toHaveLength(3)
  })

  it('surfaces action failures without recording activity entries', async () => {
    mem0ApiMocks.addDeveloperControlPlaneMem0Memory.mockRejectedValue(
      new Error('Unable to write developer memory')
    )
    mem0ApiMocks.captureDeveloperControlPlaneMem0Mission.mockRejectedValue(
      new Error('Mission capture failed')
    )

    const { result } = renderHook(() => useMem0TabController())

    await waitFor(() => {
      expect(result.current.statusState).toBe('ready')
      expect(result.current.missionState).toBe('ready')
    })

    act(() => {
      result.current.setMemoryText('This write should fail.')
    })

    await act(async () => {
      await result.current.handleAddMemory()
    })

    expect(result.current.addState).toBe('error')
    expect(result.current.addError).toBe('Unable to write developer memory')
    expect(result.current.activityTrail).toHaveLength(0)

    await act(async () => {
      await result.current.handleCaptureMission('mission-1')
    })

    expect(result.current.captureMissionState).toBe('error')
    expect(result.current.captureMissionError).toBe('Mission capture failed')
    expect(result.current.capturingMissionId).toBeNull()
    expect(result.current.activityTrail).toHaveLength(0)
  })
})