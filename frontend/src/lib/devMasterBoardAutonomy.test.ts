import { describe, expect, it } from 'vitest'

import {
  analyzeDeveloperMasterBoard,
  createDeveloperLaneDispatchPacket,
  defaultDeveloperMasterBoard,
} from '@/features/dev-control-plane'

describe('Developer master board autonomy', () => {
  it('recommends the strongest ready lane for dispatch', () => {
    const analysis = analyzeDeveloperMasterBoard(defaultDeveloperMasterBoard)

    expect(analysis.nextRecommendedLaneId).toBe('control-plane')
    expect(analysis.readyLaneIds).toContain('control-plane')
    expect(analysis.systemRecommendations[0]).toContain('Control Plane and Agent Orchestration')
  })

  it('marks missing execution contract fields as blockers', () => {
    const board = structuredClone(defaultDeveloperMasterBoard)
    board.lanes[0].owners = []
    board.lanes[0].completion_criteria = []

    const analysis = analyzeDeveloperMasterBoard(board)
    const laneAnalysis = analysis.laneAnalyses.find((lane) => lane.laneId === 'control-plane')

    expect(laneAnalysis?.readiness).toBe('blocked')
    expect(laneAnalysis?.missingFields).toEqual(expect.arrayContaining(['owners', 'completion criteria']))
  })

  it('builds a dispatch packet for the recommended or requested lane', () => {
    const packet = createDeveloperLaneDispatchPacket(defaultDeveloperMasterBoard, 'control-plane', '2026-03-17T19:15:00.000Z')

    expect(packet).not.toBeNull()
    expect(packet?.generatedAt).toBe('2026-03-17T19:15:00.000Z')
    expect(packet?.lane.id).toBe('control-plane')
    expect(packet?.agentRoles.map((role) => role.agent)).toEqual(
      expect.arrayContaining(['OmShriMaatreNamaha', 'OmVishnaveNamah'])
    )
  })
})