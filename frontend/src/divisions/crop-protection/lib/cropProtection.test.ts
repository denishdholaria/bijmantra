import { describe, expect, it } from 'vitest'

import {
  average,
  joinMultilineList,
  parseMultilineList,
  riskRank,
  toDayBoundary,
  toNumberOrNull,
} from './cropProtection'

describe('crop protection helpers', () => {
  it('normalizes numeric form values', () => {
    expect(toNumberOrNull('42')).toBe(42)
    expect(toNumberOrNull('')).toBeNull()
    expect(toNumberOrNull(undefined)).toBeNull()
    expect(toNumberOrNull('abc')).toBeNull()
  })

  it('parses and joins multiline lists safely', () => {
    expect(parseMultilineList('Inspect canopy\nApply traps, Release predators')).toEqual([
      'Inspect canopy',
      'Apply traps',
      'Release predators',
    ])
    expect(joinMultilineList(['One', 'Two'])).toBe('One\nTwo')
  })

  it('creates day boundary timestamps for validity windows', () => {
    expect(toDayBoundary('2026-03-24', 'start')).toBe('2026-03-24T00:00:00')
    expect(toDayBoundary('2026-03-24', 'end')).toBe('2026-03-24T23:59:59')
  })

  it('orders risk levels and averages numeric data', () => {
    expect(riskRank('critical')).toBeGreaterThan(riskRank('medium'))
    expect(average([null, 20, undefined, 40])).toBe(30)
    expect(average([null, undefined])).toBeNull()
  })
})
