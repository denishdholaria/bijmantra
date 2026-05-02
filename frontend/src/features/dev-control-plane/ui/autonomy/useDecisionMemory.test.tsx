import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const activeBoardApiMocks = vi.hoisted(() => ({
  fetchDeveloperControlPlaneLearnings: vi.fn(),
  getDeveloperControlPlanePersistenceErrorMessage: vi.fn(),
}))

vi.mock('../../api/activeBoard', () => ({
  fetchDeveloperControlPlaneLearnings: activeBoardApiMocks.fetchDeveloperControlPlaneLearnings,
  getDeveloperControlPlanePersistenceErrorMessage:
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage,
}))

import { useDecisionMemory } from './useDecisionMemory'

describe('useDecisionMemory', () => {
  beforeEach(() => {
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockReset()
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReset()
    activeBoardApiMocks.getDeveloperControlPlanePersistenceErrorMessage.mockReturnValue(
      'Learning ledger request failed'
    )
  })

  it('loads scoped canonical learnings for the selected lane, queue job, and mission', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockResolvedValue({
      total_count: 1,
      entries: [
        {
          learning_entry_id: 402,
          organization_id: 1,
          entry_type: 'verification-learning',
          source_classification: 'mission-state',
          title: 'Lane-scoped verification reminder',
          summary:
            'Control-plane verification evidence should be refreshed before completion write-back.',
          confidence_score: 0.91,
          recorded_by_user_id: 1,
          recorded_by_email: 'ops@bijmantra.org',
          board_id: 'bijmantra-app-development-master-board',
          source_lane_id: 'control-plane',
          queue_job_id: 'overnight-lane-control-plane-token1',
          linked_mission_id: 'mission-runtime-job',
          approval_receipt_id: null,
          source_reference: 'mission:mission-runtime-job',
          evidence_refs: ['mission:mission-runtime-job'],
          summary_metadata: null,
          recorded_at: '2026-03-31T12:15:00.000Z',
        },
      ],
    })

    const { result } = renderHook(() =>
      useDecisionMemory({
        enabled: true,
        sourceLaneId: 'control-plane',
        queueJobId: 'overnight-lane-control-plane-token1',
        linkedMissionId: 'mission-runtime-job',
      })
    )

    await waitFor(() => {
      expect(result.current.state).toBe('ready')
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenCalledWith({
      limit: 3,
      sourceLaneId: 'control-plane',
      queueJobId: 'overnight-lane-control-plane-token1',
      linkedMissionId: 'mission-runtime-job',
    })
    expect(result.current.record?.entries[0]?.title).toBe('Lane-scoped verification reminder')
    expect(result.current.scope).toEqual({
      sourceLaneId: 'control-plane',
      queueJobId: 'overnight-lane-control-plane-token1',
      linkedMissionId: 'mission-runtime-job',
    })
    expect(result.current.resolution).toEqual({
      matchMode: 'exact-runtime',
      fallbackUsed: false,
    })
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenCalledTimes(1)
  })

  it('falls back to broader lane scope when exact queue linkage has no canonical learnings yet', async () => {
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings
      .mockResolvedValueOnce({
        total_count: 0,
        entries: [],
      })
      .mockResolvedValueOnce({
        total_count: 1,
        entries: [
          {
            learning_entry_id: 410,
            organization_id: 1,
            entry_type: 'pattern',
            source_classification: 'accepted-review',
            title: 'Accepted review enabled queue export for lane control-plane',
            summary:
              'Explicit spec_review and risk_review evidence supported queue export for lane control-plane.',
            confidence_score: 0.93,
            recorded_by_user_id: 1,
            recorded_by_email: 'ops@bijmantra.org',
            board_id: 'bijmantra-app-development-master-board',
            source_lane_id: 'control-plane',
            queue_job_id: null,
            linked_mission_id: null,
            approval_receipt_id: 52,
            source_reference: 'approval-receipt:52:accepted-review',
            evidence_refs: ['receipt:52'],
            summary_metadata: null,
            recorded_at: '2026-03-31T12:15:00.000Z',
          },
        ],
      })

    const { result } = renderHook(() =>
      useDecisionMemory({
        enabled: true,
        sourceLaneId: 'control-plane',
        queueJobId: 'overnight-lane-control-plane-next-token',
        linkedMissionId: null,
      })
    )

    await waitFor(() => {
      expect(result.current.state).toBe('ready')
    })

    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenNthCalledWith(1, {
      limit: 3,
      sourceLaneId: 'control-plane',
      queueJobId: 'overnight-lane-control-plane-next-token',
    })
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).toHaveBeenNthCalledWith(2, {
      limit: 3,
      sourceLaneId: 'control-plane',
    })
    expect(result.current.record?.entries[0]?.title).toBe(
      'Accepted review enabled queue export for lane control-plane'
    )
    expect(result.current.resolution).toEqual({
      matchMode: 'lane-only',
      fallbackUsed: true,
    })
  })

  it('stays idle when no decision scope is available', () => {
    const { result } = renderHook(() =>
      useDecisionMemory({
        enabled: true,
        sourceLaneId: null,
        queueJobId: null,
        linkedMissionId: null,
      })
    )

    expect(result.current.state).toBe('idle')
    expect(result.current.record).toBeNull()
    expect(result.current.resolution).toEqual({
      matchMode: 'none',
      fallbackUsed: false,
    })
    expect(activeBoardApiMocks.fetchDeveloperControlPlaneLearnings).not.toHaveBeenCalled()
  })
})