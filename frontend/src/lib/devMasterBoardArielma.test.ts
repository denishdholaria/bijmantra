import { describe, expect, it } from 'vitest'

import { defaultDeveloperMasterBoard } from '@/features/dev-control-plane/contracts/board'
import { createDeveloperMasterBoardArielma } from './devMasterBoardArielma'

describe('createDeveloperMasterBoardArielma', () => {
  it('builds a system topology view from the canonical board', () => {
    const source = createDeveloperMasterBoardArielma(defaultDeveloperMasterBoard, 'system-topology')

    expect(source).toContain('flowchart LR')
    expect(source).toContain('BijMantra Developer Control Plane')
    expect(source).toContain('Primary orchestrator')
    expect(source).toContain('Hidden board surface')
  })

  it('builds a dependency flow view with unblock edges', () => {
    const source = createDeveloperMasterBoardArielma(defaultDeveloperMasterBoard, 'dependency-flow')

    expect(source).toContain('Execution dependencies')
    expect(source).toContain('|unblocks|')
    expect(source).toContain('Control Plane and Agent Orchestration')
  })

  it('builds an agent ownership view tied to lane owners', () => {
    const source = createDeveloperMasterBoardArielma(defaultDeveloperMasterBoard, 'agent-ownership')

    expect(source).toContain('Primary orchestrator')
    expect(source).toContain('|owns|')
    expect(source).toContain('OmShriMaatreNamaha')
  })
})