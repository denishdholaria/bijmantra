import { describe, expect, it } from 'vitest'

import { defaultDeveloperMasterBoard } from './contracts/board'
import {
  analyzeDeveloperMasterBoard,
  buildDeveloperBoardSystemRecommendations,
  createDeveloperLaneDispatchPacket,
  selectAdvisoryGapDeveloperLaneAnalyses,
  selectBlockedDeveloperLaneAnalyses,
  selectNextRecommendedDeveloperLaneId,
  selectReadyDeveloperLaneAnalyses,
} from './autonomy'
import {
  createDeveloperLaneQueueCandidate,
  createDeveloperLaneQueueJobId,
  materializeDeveloperLaneQueueEntry,
} from './contracts/dispatch'

describe('developer control-plane autonomy helpers', () => {
  it('derives ready, blocked, and recommended lane outputs independently', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')
    const deliveryLane = board.lanes.find((lane) => lane.id === 'delivery-lanes')

    if (!platformRuntimeLane || !deliveryLane) {
      throw new Error('Expected default control-plane lanes in board fixture')
    }

    platformRuntimeLane.dependencies = ['missing-runtime']
    deliveryLane.status = 'planned'
    deliveryLane.dependencies = []

    const autonomy = analyzeDeveloperMasterBoard(board)

    expect(selectReadyDeveloperLaneAnalyses(autonomy.laneAnalyses).map((lane) => lane.laneId)).toEqual([
      'control-plane',
      'delivery-lanes',
    ])
    expect(selectBlockedDeveloperLaneAnalyses(autonomy.laneAnalyses).map((lane) => lane.laneId)).toEqual([
      'platform-runtime',
    ])
    expect(selectNextRecommendedDeveloperLaneId(autonomy.laneAnalyses)).toBe('control-plane')
  })

  it('builds advisory-gap and blocker recommendations without dispatch coupling', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')

    if (!controlPlaneLane || !platformRuntimeLane) {
      throw new Error('Expected default control-plane lanes in board fixture')
    }

    controlPlaneLane.inputs = []
    controlPlaneLane.subplans = []
    controlPlaneLane.outputs = []
    platformRuntimeLane.dependencies = ['missing-runtime']

    const autonomy = analyzeDeveloperMasterBoard(board)
    const controlPlaneAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'control-plane')

    expect(controlPlaneAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'missing-outputs',
          severity: 'advisory',
        }),
      ])
    )

    expect(selectAdvisoryGapDeveloperLaneAnalyses(autonomy.laneAnalyses).map((lane) => lane.laneId)).toEqual([
      'control-plane',
    ])
    expect(
      buildDeveloperBoardSystemRecommendations(
        autonomy.laneAnalyses,
        selectNextRecommendedDeveloperLaneId(autonomy.laneAnalyses)
      )
    ).toEqual(
      expect.arrayContaining([
        'Next recommended lane: Control Plane and Agent Orchestration',
        '1 lane(s) have structural or dependency blockers that will cause drift if ignored',
        '1 lane(s) have advisory gaps; bounded slices will improve continuity',
        '3 lane(s) carry explicit structural drift warnings (1 blocking, 3 advisory)',
      ])
    )
  })

  it('keeps missing outputs advisory while orphaned dependencies stay blocking', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    const deliveryLane = board.lanes.find((lane) => lane.id === 'delivery-lanes')

    if (!controlPlaneLane || !deliveryLane) {
      throw new Error('Expected default control-plane lanes in board fixture')
    }

    controlPlaneLane.outputs = []
    deliveryLane.status = 'planned'
    deliveryLane.dependencies = ['unknown-lane']

    const autonomy = analyzeDeveloperMasterBoard(board)
    const controlPlaneAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'control-plane')
    const deliveryAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'delivery-lanes')

    expect(controlPlaneAnalysis?.readiness).toBe('ready')
    expect(controlPlaneAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'missing-outputs', severity: 'advisory' }),
      ])
    )
    expect(deliveryAnalysis?.readiness).toBe('blocked')
    expect(deliveryAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'orphaned-dependencies', severity: 'blocking' }),
      ])
    )
  })

  it('prefers explicit validation_basis fields over heuristic keyword scans', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board fixture')
    }

    controlPlaneLane.inputs = []
    controlPlaneLane.outputs = []
    controlPlaneLane.completion_criteria = ['Proceed with the next bounded slice.']
    controlPlaneLane.validation_basis = {
      owner: 'OmVishnaveNamah',
      summary: 'Focused contract review remains current.',
      evidence: ['frontend/src/features/dev-control-plane/autonomy.test.ts'],
      last_reviewed_at: '2026-03-18T20:00:00.000Z',
    }

    const autonomy = analyzeDeveloperMasterBoard(board)
    const controlPlaneAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'control-plane')

    expect(controlPlaneAnalysis?.structuralWarnings).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'active-without-validation-evidence' }),
      ])
    )
  })

  it('treats an incomplete explicit validation_basis field as insufficient for active-lane confidence', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const platformRuntimeLane = board.lanes.find((lane) => lane.id === 'platform-runtime')

    if (!platformRuntimeLane) {
      throw new Error('Expected platform-runtime lane in default board fixture')
    }

    platformRuntimeLane.validation_basis = {
      owner: 'OmVishnaveNamah',
      summary: 'Missing evidence should keep the advisory warning visible.',
      evidence: [],
      last_reviewed_at: '2026-03-18T20:00:00.000Z',
    }

    const autonomy = analyzeDeveloperMasterBoard(board)
    const platformRuntimeAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'platform-runtime')

    expect(platformRuntimeAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'active-without-validation-evidence',
          severity: 'advisory',
        }),
      ])
    )
  })

  it('requires explicit closure evidence before a completed lane is treated as completed', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const deliveryLane = board.lanes.find((lane) => lane.id === 'delivery-lanes')

    if (!deliveryLane) {
      throw new Error('Expected delivery-lanes lane in default board fixture')
    }

    deliveryLane.status = 'completed'

    let autonomy = analyzeDeveloperMasterBoard(board)
    let deliveryAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'delivery-lanes')

    expect(deliveryAnalysis?.readiness).toBe('blocked')
    expect(deliveryAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'completed-without-closure',
          severity: 'blocking',
        }),
      ])
    )

    deliveryLane.closure = {
      queue_job_id: 'overnight-lane-delivery-lanes-token1234',
      queue_sha256: 'queue-sha-1234',
      source_board_concurrency_token: 'token-1234',
      closure_summary: 'Delivery evidence was reviewed and accepted.',
      evidence: ['Focused delivery tests passed', 'Queue job status is completed'],
      completed_at: '2026-03-18T18:00:00.000Z',
    }

    autonomy = analyzeDeveloperMasterBoard(board)
    deliveryAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'delivery-lanes')

    expect(deliveryAnalysis?.readiness).toBe('completed')
    expect(deliveryAnalysis?.structuralWarnings).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'completed-without-closure' }),
      ])
    )
  })

  it('surfaces advisory drift when owner labels do not match declared agent roles', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')

    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board fixture')
    }

    controlPlaneLane.owners = ['OmShriMaatreNamaha', 'Agent Alpha']

    const autonomy = analyzeDeveloperMasterBoard(board)
    const controlPlaneAnalysis = autonomy.laneAnalyses.find((lane) => lane.laneId === 'control-plane')

    expect(controlPlaneAnalysis?.readiness).toBe('ready')
    expect(controlPlaneAnalysis?.structuralWarnings).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'unregistered-owners',
          severity: 'advisory',
        }),
      ])
    )
  })

  it('maps a dispatch packet into a deterministic queue candidate with provenance', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const dispatchPacket = createDeveloperLaneDispatchPacket(
      board,
      'control-plane',
      '2026-03-18T18:00:00.000Z'
    )

    const candidate = createDeveloperLaneQueueCandidate(dispatchPacket, 'active-token-1')

    expect(candidate).toEqual({
      candidateVersion: '1.0.0',
      exportedAt: '2026-03-18T18:00:00.000Z',
      boardId: 'bijmantra-app-development-master-board',
      boardTitle: 'BijMantra Developer Control Plane',
      sourceBoardConcurrencyToken: 'active-token-1',
      sourceLaneId: 'control-plane',
      title: 'Control Plane and Agent Orchestration',
      primaryAgent: 'OmShriMaatreNamaha',
      supportAgents: ['OmVishnaveNamah'],
      goal: expect.any(String),
      successCriteria: expect.any(Array),
      lane: {
        objective: expect.any(String),
        inputs: expect.any(Array),
        outputs: expect.any(Array),
        dependencies: expect.any(Array),
        completion_criteria: expect.any(Array),
      },
      precedence: {
        canonicalPlanningSource: 'active-board',
        derivedExecutionSurface: 'overnight-queue',
        exportDisposition: 'manual-candidate-only',
        conflictResolution: 'board-wins-no-silent-overwrite',
        staleIfSourceBoardChanges: true,
      },
    })
  })

  it('does not create a queue candidate when shared board provenance is missing', () => {
    const dispatchPacket = createDeveloperLaneDispatchPacket(
      structuredClone(defaultDeveloperMasterBoard),
      'control-plane',
      '2026-03-18T18:00:00.000Z'
    )

    expect(createDeveloperLaneQueueCandidate(dispatchPacket, null)).toBeNull()
  })

  it('materializes a queue-native entry with deterministic defaults', () => {
    const dispatchPacket = createDeveloperLaneDispatchPacket(
      structuredClone(defaultDeveloperMasterBoard),
      'control-plane',
      '2026-03-18T18:00:00.000Z'
    )
    const candidate = createDeveloperLaneQueueCandidate(dispatchPacket, 'shared-token-1')

    const materialized = materializeDeveloperLaneQueueEntry(candidate, {
      'platform-runtime': createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
      'control-plane': createDeveloperLaneQueueJobId('control-plane', 'shared-token-1'),
      'delivery-lanes': createDeveloperLaneQueueJobId('delivery-lanes', 'shared-token-1'),
      'cross-domain-hub': createDeveloperLaneQueueJobId('cross-domain-hub', 'shared-token-1'),
    })

    expect(materialized.unresolvedDependencyLaneIds).toEqual([])
    expect(materialized.entry).toMatchObject({
      jobId: 'overnight-lane-control-plane-sharedto',
      title: 'Control Plane and Agent Orchestration',
      status: 'queued',
      priority: 'p2',
      primaryAgent: 'OmShriMaatreNamaha',
      provenance: {
        candidateVersion: '1.0.0',
        exportedAt: '2026-03-18T18:00:00.000Z',
        boardId: 'bijmantra-app-development-master-board',
        boardTitle: 'BijMantra Developer Control Plane',
        sourceBoardConcurrencyToken: 'shared-token-1',
        sourceLaneId: 'control-plane',
        precedence: {
          canonicalPlanningSource: 'active-board',
          derivedExecutionSurface: 'overnight-queue',
          exportDisposition: 'manual-candidate-only',
          conflictResolution: 'board-wins-no-silent-overwrite',
          staleIfSourceBoardChanges: true,
        },
      },
      executionMode: 'same-control-plane',
      autonomousTrigger: {
        type: 'overnight-window',
        window: 'nightly',
        enabled: true,
      },
      verification: {
        commands: [],
        stateRefreshRequired: true,
      },
    })
  })

  it('blocks queue materialization when dependency lane ids are unresolved', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    const controlPlaneLane = board.lanes.find((lane) => lane.id === 'control-plane')
    if (!controlPlaneLane) {
      throw new Error('Expected control-plane lane in default board')
    }

    controlPlaneLane.dependencies = ['platform-runtime']

    const dispatchPacket = createDeveloperLaneDispatchPacket(
      board,
      'control-plane',
      '2026-03-18T18:00:00.000Z'
    )
    const candidate = createDeveloperLaneQueueCandidate(dispatchPacket, 'shared-token-1')
    const materialized = materializeDeveloperLaneQueueEntry(candidate, {})

    expect(materialized.entry).toBeNull()
    expect(materialized.unresolvedDependencyLaneIds).toEqual(['platform-runtime'])
  })

  it('does not mutate queue candidate planning fields during materialization', () => {
    const dispatchPacket = createDeveloperLaneDispatchPacket(
      structuredClone(defaultDeveloperMasterBoard),
      'control-plane',
      '2026-03-18T18:00:00.000Z'
    )
    const candidate = createDeveloperLaneQueueCandidate(dispatchPacket, 'shared-token-1')
    const candidateSnapshot = JSON.stringify(candidate)

    materializeDeveloperLaneQueueEntry(candidate, {
      'platform-runtime': createDeveloperLaneQueueJobId('platform-runtime', 'shared-token-1'),
      'control-plane': createDeveloperLaneQueueJobId('control-plane', 'shared-token-1'),
      'delivery-lanes': createDeveloperLaneQueueJobId('delivery-lanes', 'shared-token-1'),
      'cross-domain-hub': createDeveloperLaneQueueJobId('cross-domain-hub', 'shared-token-1'),
    })

    expect(JSON.stringify(candidate)).toBe(candidateSnapshot)
  })
})