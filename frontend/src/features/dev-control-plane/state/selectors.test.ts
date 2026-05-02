import { describe, expect, it } from 'vitest'

import {
  createDefaultDeveloperMasterBoardJson,
  defaultDeveloperMasterBoard,
  serializeDeveloperMasterBoard,
} from '../contracts/board'
import {
  deriveDeveloperMasterBoardViewModel,
  deriveDeveloperControlPlanePersistenceStatus,
  selectBlockedDeveloperLanes,
  selectDeveloperAdvisoryGapAnalyses,
  selectRecommendedDeveloperLane,
  selectReadyDeveloperLanes,
} from './selectors'

describe('Developer master board state selectors', () => {
  it('derives the current board view from canonical JSON and selected lane', () => {
    const view = deriveDeveloperMasterBoardViewModel(
      createDefaultDeveloperMasterBoardJson(),
      'control-plane'
    )

    expect(view.jsonError).toBeNull()
    expect(view.parsedBoard).toEqual(defaultDeveloperMasterBoard)
    expect(view.selectedLane?.id).toBe('control-plane')
    expect(view.recommendedLane?.id).toBe('control-plane')
    expect(view.readyLanes.map((lane) => lane.id)).toEqual(['control-plane', 'platform-runtime'])
    expect(view.blockedLanes).toEqual([])
    expect(view.advisoryGapAnalyses).toEqual([])
    expect(view.dispatchPacket?.lane.id).toBe('control-plane')
    expect(view.availableAgents).toEqual(
      expect.arrayContaining(['OmNamahShivaya', 'OmShriMaatreNamaha', 'OmVishnaveNamah'])
    )
  })

  it('derives recommendation, blocked lanes, and advisory gaps from autonomy selectors', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')
    const deliveryLane = board.lanes.find((lane) => lane.id === 'delivery-lanes')
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!platformRuntimeLane || !deliveryLane || !controlPlaneLane) {
      throw new Error('Expected default control-plane lanes in board fixture')
    }

    platformRuntimeLane.dependencies = ['missing-runtime']
    controlPlaneLane.inputs = []
    controlPlaneLane.subplans = []
    deliveryLane.status = 'planned'
    deliveryLane.dependencies = []

    const view = deriveDeveloperMasterBoardViewModel(serializeDeveloperMasterBoard(board), 'delivery-lanes')

    expect(selectRecommendedDeveloperLane(view.parsedBoard, view.autonomyAnalysis)?.id).toBe('control-plane')
    expect(selectReadyDeveloperLanes(view.parsedBoard, view.autonomyAnalysis).map((lane) => lane.id)).toEqual([
      'control-plane',
      'delivery-lanes',
    ])
    expect(selectBlockedDeveloperLanes(view.parsedBoard, view.autonomyAnalysis).map((lane) => lane.id)).toEqual([
      'platform-runtime',
    ])
    expect(selectDeveloperAdvisoryGapAnalyses(view.autonomyAnalysis).map((lane) => lane.laneId)).toEqual([
      'control-plane',
    ])
    expect(view.blockedLaneCount).toBe(1)
  })

  it('preserves explicit validation basis on the selected lane and suppresses its advisory gap', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in board fixture')
    }

    controlPlaneLane.validation_basis = {
      owner: 'OmShriMaatreNamaha',
      summary: 'Explicit operator-reviewed validation basis is now present.',
      evidence: ['confidential-docs/architecture/validation-proof.md'],
      last_reviewed_at: '2026-03-18T21:00:00.000Z',
    }

    const view = deriveDeveloperMasterBoardViewModel(serializeDeveloperMasterBoard(board), 'control-plane')

    expect(view.selectedLane?.validation_basis).toMatchObject({
      owner: 'OmShriMaatreNamaha',
      last_reviewed_at: '2026-03-18T21:00:00.000Z',
    })
    expect(
      view.autonomyAnalysis?.laneAnalyses.find((lane) => lane.laneId === 'control-plane')?.structuralWarnings
    ).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'active-without-validation-evidence' }),
      ])
    )
  })

  it('treats completed lanes without persisted closure as blocked drift until closure exists', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in board fixture')
    }

    controlPlaneLane.status = 'completed'
    delete controlPlaneLane.closure

    const view = deriveDeveloperMasterBoardViewModel(serializeDeveloperMasterBoard(board), 'control-plane')

    expect(view.blockedLanes.map((lane) => lane.id)).toContain('control-plane')
    expect(view.autonomyAnalysis?.laneAnalyses.find((lane) => lane.laneId === 'control-plane')).toMatchObject({
      readiness: 'blocked',
      structuralWarnings: expect.arrayContaining([
        expect.objectContaining({
          code: 'completed-without-closure',
          severity: 'blocking',
        }),
      ]),
    })
  })

  it('returns an invalid-json view model without throwing', () => {
    const view = deriveDeveloperMasterBoardViewModel('{', null)

    expect(view.parsedBoard).toBeNull()
    expect(view.jsonError).toBeTruthy()
    expect(view.lanes).toEqual([])
    expect(view.readyLanes).toEqual([])
    expect(view.blockedLanes).toEqual([])
    expect(view.advisoryGapAnalyses).toEqual([])
    expect(view.dispatchPacket).toBeNull()
  })

  it('derives local fallback persistence status from hydration and storage availability', () => {
    expect(
      deriveDeveloperControlPlanePersistenceStatus(false, true, 'idle', 'idle', null, 'generic', null)
    ).toEqual({
      tone: 'loading',
      label: 'Loading local fallback state',
      description:
        'BijMantra is still hydrating the browser-local fallback board state for this hidden control-plane surface.',
    })

    expect(
      deriveDeveloperControlPlanePersistenceStatus(true, true, 'no-record', 'idle', null, 'generic', null)
    ).toEqual({
      tone: 'fallback',
      label: 'No shared board yet',
      description:
        'No active canonical board exists yet in backend persistence for this organization, so BijMantra is truthfully continuing from the browser-local fallback until the next successful save.',
    })

    expect(
      deriveDeveloperControlPlanePersistenceStatus(true, false, 'no-record', 'idle', null, 'generic', null)
    ).toEqual({
      tone: 'warning',
      label: 'No shared board; memory only',
      description:
        'No active canonical board exists yet in backend persistence and persistent browser storage is unavailable, so the control plane is currently operating in memory only until a save succeeds.',
    })

    expect(
      deriveDeveloperControlPlanePersistenceStatus(true, true, 'ready', 'saved', null, 'generic', null)
    ).toEqual({
      tone: 'synced',
      label: 'Shared backend persistence active',
      description:
        'This hidden control-plane surface is now backed by the shared active-board API, with browser-local state retained only as fallback continuity.',
    })

    expect(
      deriveDeveloperControlPlanePersistenceStatus(
        true,
        true,
        'ready',
        'conflict',
        'Active board save conflict; refetch the current board before retrying',
        'generic',
        '2026-03-18T12:00:00.000Z'
      )
    ).toEqual({
      tone: 'warning',
      label: 'Shared board conflict',
      description:
        `Backend persistence rejected the save because a newer canonical board already exists from ${new Date('2026-03-18T12:00:00.000Z').toLocaleString()}. Refetch the shared board before retrying so agent evidence is not overwritten silently.`,
    })

    expect(
      deriveDeveloperControlPlanePersistenceStatus(
        true,
        true,
        'unavailable',
        'error',
        'Developer control-plane persistence schema is not ready; missing table(s): developer_control_plane_board_revisions. Run backend alembic upgrade through revision 20260318_1500.',
        'schema-not-ready',
        null
      )
    ).toEqual({
      tone: 'warning',
      label: 'Shared persistence schema incomplete',
      description:
        'Developer control-plane persistence schema is not ready; missing table(s): developer_control_plane_board_revisions. Run backend alembic upgrade through revision 20260318_1500.',
    })
  })
})