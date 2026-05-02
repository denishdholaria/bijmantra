import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createDefaultDeveloperMasterBoardJson } from '@/features/dev-control-plane/contracts/board'

describe('useDevMasterBoardStore persistence contract', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('formats, persists, and resets the internal master board JSON', async () => {
    const { useDevMasterBoardStore } = await import('./devMasterBoardStore')

    expect(useDevMasterBoardStore.getState().hasHydrated).toBe(true)
    expect(useDevMasterBoardStore.getState().storageAvailable).toBe(true)

    const reorderedBoardJson = JSON.stringify({
      title: 'Compact Board',
      board_id: 'bijmantra-app-development-master-board',
      version: '1.0.0',
      visibility: 'internal-superuser',
      continuous_operation_goal: 'Goal',
      intent: 'Intent',
      control_plane: {
        operating_cadence: [],
        evidence_sources: [],
        primary_orchestrator: 'OmShriMaatreNamaha',
      },
      agent_roles: [],
      lanes: [],
      orchestration_contract: {
        coordination_rules: [],
        execution_loop: [],
        canonical_outputs: [],
        canonical_inputs: [],
      },
    })

    useDevMasterBoardStore.getState().replaceBoardJson(reorderedBoardJson)
    expect(useDevMasterBoardStore.getState().rawBoardJson).toBe(reorderedBoardJson)

    useDevMasterBoardStore.getState().formatBoardJson()
    expect(useDevMasterBoardStore.getState().rawBoardJson).toBe(`{
  "version": "1.0.0",
  "board_id": "bijmantra-app-development-master-board",
  "title": "Compact Board",
  "visibility": "internal-superuser",
  "intent": "Intent",
  "continuous_operation_goal": "Goal",
  "orchestration_contract": {
    "canonical_inputs": [],
    "canonical_outputs": [],
    "execution_loop": [],
    "coordination_rules": []
  },
  "lanes": [],
  "agent_roles": [],
  "control_plane": {
    "primary_orchestrator": "OmShriMaatreNamaha",
    "evidence_sources": [],
    "operating_cadence": []
  }
}\n`)

    useDevMasterBoardStore.getState().resetBoard()
    expect(useDevMasterBoardStore.getState().rawBoardJson).toBe(createDefaultDeveloperMasterBoardJson())

    const persistedState = JSON.parse(localStorage.getItem('bijmantra-dev-master-board-storage') ?? '{}')
    expect(persistedState.state).toMatchObject({
      rawBoardJson: expect.any(String),
      lastUpdatedAt: expect.any(String),
    })
    expect(persistedState.state.hasHydrated).toBeUndefined()
    expect(persistedState.state.storageAvailable).toBeUndefined()
  })

  it('keeps the legacy store import path as a feature-state shim', async () => {
    const legacyModule = await import('./devMasterBoardStore')
    const featureModule = await import('@/features/dev-control-plane/state')

    expect(legacyModule.useDevMasterBoardStore).toBe(featureModule.useDevMasterBoardStore)
  })
})