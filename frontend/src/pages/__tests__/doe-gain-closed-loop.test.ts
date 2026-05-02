import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('DOE to genetic gain closed loop constraints', () => {
  it('uses service-backed generation/calculation and has no random scoring logic', () => {
    const experimentDesigner = readFileSync(resolve(process.cwd(), 'src/pages/ExperimentDesigner.tsx'), 'utf8')
    const geneticGain = readFileSync(resolve(process.cwd(), 'src/pages/GeneticGain.tsx'), 'utf8')
    const gainCalculator = readFileSync(resolve(process.cwd(), 'src/pages/GeneticGainCalculator.tsx'), 'utf8')

    expect(experimentDesigner.includes('Math.random')).toBe(false)
    expect(experimentDesigner.includes('trialDesignService.generateRCBD')).toBe(true)
    expect(experimentDesigner.includes('trialDesignService.generateAlphaLattice')).toBe(true)
    expect(experimentDesigner.includes('trialDesignService.generateAugmented')).toBe(true)
    expect(experimentDesigner.includes('trialDesignService.generateSplitPlot')).toBe(true)

    expect(geneticGain.includes('geneticGainService.calculateGain')).toBe(true)
    expect(geneticGain.includes('geneticGainService.getProjection')).toBe(true)

    expect(gainCalculator.includes('selectionIndexService.predictSelectionResponse')).toBe(true)
    expect(gainCalculator.includes('geneticGainService.calculateGain')).toBe(true)
  })
})
