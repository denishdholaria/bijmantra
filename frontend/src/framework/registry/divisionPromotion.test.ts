import { describe, expect, it } from 'vitest'

import { divisions } from './divisions'
import { futureDivisions } from './futureDivisions'
import { futureWorkspaces } from './futureWorkspaces'

const promotedDivisionIds = [
  'crop-intelligence',
  'soil-nutrients',
  'crop-protection',
  'water-irrigation',
] as const

describe('Promoted division registry integrity', () => {
  it('keeps promoted domains in the active division registry', () => {
    for (const id of promotedDivisionIds) {
      const division = divisions.find((entry) => entry.id === id)

      expect(division, `missing promoted division: ${id}`).toBeDefined()
      expect(division?.status).toMatch(/active|preview/)
      expect(division?.component, `missing component for promoted division: ${id}`).toBeDefined()
    }
  })

  it('removes promoted domains from future-only registries', () => {
    for (const id of promotedDivisionIds) {
      expect(futureDivisions.some((entry) => entry.id === id), `future division still exported: ${id}`).toBe(false)
      expect(futureWorkspaces.some((entry) => entry.id === id), `future workspace still exported: ${id}`).toBe(false)
    }
  })
})
