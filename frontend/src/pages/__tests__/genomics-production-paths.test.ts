import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const files = [
  'src/pages/QTLMapping.tsx',
  'src/pages/WasmGenomics.tsx',
  'src/pages/GxEInteraction.tsx',
]

describe('genomics production paths', () => {
  it('do not contain synthetic genotype/phenotype generation or demo mode markers', () => {
    const forbidden = [
      'Math.random',
      'generateTestData',
      'Demo Mode',
      'simulated',
      'useRealData &&',
    ]

    for (const file of files) {
      const source = readFileSync(resolve(process.cwd(), file), 'utf8')
      for (const marker of forbidden) {
        expect(source.includes(marker)).toBe(false)
      }
    }
  })
})
