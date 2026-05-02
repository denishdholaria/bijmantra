import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { Tabs } from '@/components/ui/tabs'

import {
  activeBoardApiMocks,
  clipboardWriteText,
  createCaptureLearningResponse,
  createCaptureMissionResponse,
  createLearningLedgerResponse,
  createMem0AddResponse,
  createMem0HealthResponse,
  createMem0SearchResponse,
  createMem0StatusResponse,
  createMissionStateResponse,
  mem0ApiMocks,
  resetMem0TestEnvironment,
  seedMem0BootstrapMocks,
  sonnerMocks,
} from './mem0TestHelpers'
import { Mem0Tab } from './Mem0Tab'

vi.mock('../../api/mem0', () => mem0ApiMocks)
vi.mock('../../api/activeBoard', () => ({
  fetchDeveloperControlPlaneLearnings: activeBoardApiMocks.fetchDeveloperControlPlaneLearnings,
  fetchDeveloperControlPlaneMissionState: activeBoardApiMocks.fetchDeveloperControlPlaneMissionState,
}))
vi.mock('sonner', () => ({
  toast: sonnerMocks,
}))

beforeEach(() => {
  resetMem0TestEnvironment()
})

describe('Mem0Tab', () => {
  it('loads status, adds a memory, and searches memory', async () => {
    seedMem0BootstrapMocks()
    mem0ApiMocks.fetchDeveloperControlPlaneMem0Status.mockResolvedValue(createMem0StatusResponse())
    mem0ApiMocks.fetchDeveloperControlPlaneMem0Health.mockResolvedValue(createMem0HealthResponse())
    mem0ApiMocks.addDeveloperControlPlaneMem0Memory.mockResolvedValue(createMem0AddResponse())
    mem0ApiMocks.searchDeveloperControlPlaneMem0Memory.mockResolvedValue(createMem0SearchResponse())
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockResolvedValue(
      createLearningLedgerResponse()
    )
    mem0ApiMocks.captureDeveloperControlPlaneMem0Learning.mockResolvedValue(
      createCaptureLearningResponse()
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue(
      createMissionStateResponse()
    )
    mem0ApiMocks.captureDeveloperControlPlaneMem0Mission.mockResolvedValue(
      createCaptureMissionResponse()
    )

    render(
      <Tabs value="mem0" onValueChange={() => {}}>
        <Mem0Tab />
      </Tabs>
    )

    await waitFor(() => {
      expect(screen.getByText('Mem0')).toBeInTheDocument()
      expect(screen.getByText('Ready')).toBeInTheDocument()
      expect(screen.getByText('Cloud Reachable')).toBeInTheDocument()
      expect(screen.getByText('12.5 ms')).toBeInTheDocument()
      expect(screen.getByText('Recent Session Trail')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'All Entries (0)' })).toBeInTheDocument()
      expect(
        screen.getByText('No successful Mem0 writes have been recorded in this session yet.')
      ).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Copy Visible Summaries' })).toBeDisabled()
      expect(screen.getByRole('button', { name: 'Clear Trail' })).toBeDisabled()
      expect(screen.getByText('Capture Canonical Learnings')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Capture to Mem0' })).toBeInTheDocument()
      expect(screen.getByText('Capture Mission Outcomes')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Capture Mission to Mem0' })).toBeInTheDocument()
    })

    fireEvent.change(
      screen.getByPlaceholderText(
        'Example: Keep Mem0 separate from REEVU and use it only for developer micro-memory.'
      ),
      { target: { value: 'Keep Mem0 separate from REEVU.' } }
    )
    fireEvent.click(screen.getByRole('button', { name: 'Add Memory' }))

    await waitFor(() => {
      expect(mem0ApiMocks.addDeveloperControlPlaneMem0Memory).toHaveBeenCalledWith({
        text: 'Keep Mem0 separate from REEVU.',
        user_id: 'bijmantra-dev',
        app_id: 'bijmantra-dev',
        run_id: null,
        category: 'note',
      })
      expect(screen.getByRole('button', { name: 'Copy Visible Summaries' })).toBeEnabled()
      expect(screen.getByRole('button', { name: 'Clear Trail' })).toBeEnabled()
      expect(screen.getByText('Manual Note')).toBeInTheDocument()
      expect(screen.getByText('Manual note: note')).toBeInTheDocument()
      expect(screen.getByText('mem-1')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'All Entries (1)' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Manual Notes (1)' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Copy Summary' }))

    await waitFor(() => {
      expect(clipboardWriteText).toHaveBeenCalledWith(
        expect.stringContaining('Mem0 Manual Note')
      )
      expect(clipboardWriteText).toHaveBeenCalledWith(
        expect.stringContaining('Title: Manual note: note')
      )
      expect(sonnerMocks.success).toHaveBeenCalledWith('Mem0 capture summary copied.')
    })

    fireEvent.change(screen.getByPlaceholderText('Example: How should Mem0 relate to REEVU?'), {
      target: { value: 'Mem0 separate from REEVU' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Search Memory' }))

    await waitFor(() => {
      expect(mem0ApiMocks.searchDeveloperControlPlaneMem0Memory).toHaveBeenCalledWith({
        query: 'Mem0 separate from REEVU',
        user_id: 'bijmantra-dev',
        app_id: 'bijmantra-dev',
        run_id: null,
        limit: 5,
      })
      expect(screen.getAllByText(/Keep Mem0 separate from REEVU/).length).toBeGreaterThan(0)
    })

    fireEvent.click(screen.getByRole('button', { name: 'Capture to Mem0' }))

    await waitFor(() => {
      expect(mem0ApiMocks.captureDeveloperControlPlaneMem0Learning).toHaveBeenCalledWith(42, {
        user_id: 'bijmantra-dev',
        app_id: 'bijmantra-dev',
        run_id: null,
      })
      expect(screen.getAllByText(/mem-learn-1/).length).toBeGreaterThan(0)
      expect(screen.getByText('Learning Capture')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Capture Mission to Mem0' }))

    await waitFor(() => {
      expect(mem0ApiMocks.captureDeveloperControlPlaneMem0Mission).toHaveBeenCalledWith('mission-1', {
        user_id: 'bijmantra-dev',
        app_id: 'bijmantra-dev',
        run_id: null,
      })
      expect(screen.getAllByText(/mem-mission-1/).length).toBeGreaterThan(0)
      expect(screen.getByText('Mission Capture')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'All Entries (3)' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Learning Captures (1)' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Mission Captures (1)' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Learning Captures (1)' }))

    await waitFor(() => {
      expect(screen.queryByText('Manual note: note')).not.toBeInTheDocument()
      expect(screen.queryAllByRole('button', { name: 'Copy Summary' })).toHaveLength(1)
      expect(screen.getByText('Learning Capture')).toBeInTheDocument()
    })

    clipboardWriteText.mockClear()
    sonnerMocks.success.mockClear()

    fireEvent.click(screen.getByRole('button', { name: 'Copy Visible Summaries' }))

    await waitFor(() => {
      expect(clipboardWriteText).toHaveBeenCalledTimes(1)
      expect(sonnerMocks.success).toHaveBeenCalledWith('Visible Mem0 summaries copied.')
    })

    const copiedText = String(clipboardWriteText.mock.calls[0]?.[0] ?? '')
    expect(copiedText).toContain('Mem0 Learning Captures')
    expect(copiedText).toContain('mem-learn-1')
    expect(copiedText).not.toContain('Manual note: note')
    expect(copiedText).not.toContain('mem-mission-1')

    fireEvent.click(screen.getByRole('button', { name: 'All Entries (3)' }))

    await waitFor(() => {
      expect(screen.getByText('Manual note: note')).toBeInTheDocument()
      expect(screen.queryAllByRole('button', { name: 'Copy Summary' })).toHaveLength(3)
    })

    fireEvent.click(screen.getByRole('button', { name: 'Clear Trail' }))

    await waitFor(() => {
      expect(
        screen.getByText('No successful Mem0 writes have been recorded in this session yet.')
      ).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Clear Trail' })).toBeDisabled()
    })
  })

  it('rehydrates the recent session trail from sessionStorage', async () => {
    window.sessionStorage.setItem(
      'developer-control-plane-mem0-activity-trail',
      JSON.stringify([
        {
          id: 'manual-note-seeded',
          kind: 'manual-note',
          title: 'Manual note: architecture',
          summary: 'Keep Mem0 separate from REEVU.',
          scopeLabel: 'bijmantra-dev · bijmantra-dev',
          resultId: 'mem-seeded-1',
          recordedAt: '2026-04-05T10:40:00.000Z',
        },
      ])
    )

    mem0ApiMocks.fetchDeveloperControlPlaneMem0Status.mockResolvedValue(createMem0StatusResponse())
    mem0ApiMocks.fetchDeveloperControlPlaneMem0Health.mockResolvedValue(createMem0HealthResponse())
    activeBoardApiMocks.fetchDeveloperControlPlaneLearnings.mockResolvedValue(
      createLearningLedgerResponse([])
    )
    activeBoardApiMocks.fetchDeveloperControlPlaneMissionState.mockResolvedValue(
      createMissionStateResponse([])
    )

    render(
      <Tabs value="mem0" onValueChange={() => {}}>
        <Mem0Tab />
      </Tabs>
    )

    await waitFor(() => {
      expect(screen.getByText('Manual Note')).toBeInTheDocument()
      expect(screen.getByText('Manual note: architecture')).toBeInTheDocument()
      expect(screen.getByText('mem-seeded-1')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Clear Trail' })).toBeEnabled()
    })
  })
})