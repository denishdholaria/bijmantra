import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const pageFiles = [
  'src/pages/BreedingSimulator.tsx',
  'src/pages/ParentSelection.tsx',
  'src/pages/SelectionIndex.tsx',
  'src/pages/PlannedCrosses.tsx',
  'src/pages/CrossPrediction.tsx',
]

describe('breeding decision workflow hard constraints', () => {
  it('does not use Math.random in core page flows', () => {
    for (const file of pageFiles) {
      const source = readFileSync(resolve(process.cwd(), file), 'utf8')
      expect(source.includes('Math.random')).toBe(false)
    }
  })

  it('does not include local compute fallback for core decisions', () => {
    const forbiddenMarkers = [
      'Selection index calculated (local)',
      'Prediction failed, using fallback',
      'Weather API failed, using fallback empty weather data for simulation',
      'Fallback to local calculation',
    ]

    for (const file of pageFiles) {
      const source = readFileSync(resolve(process.cwd(), file), 'utf8')
      for (const marker of forbiddenMarkers) {
        expect(source.includes(marker)).toBe(false)
      }
    }
  })
})
