import { render, screen } from '@testing-library/react'
import { GermplasmSummaryPanel } from '../GermplasmSummaryPanel'
import { describe, it, expect } from 'vitest'

describe('GermplasmSummaryPanel', () => {
  const mockGermplasm = {
    germplasmName: 'Test Germplasm',
    germplasmDbId: '123'
  }

  const mockStats = {
    trialsCount: 5,
    observationsCount: 120,
    pedigreeDepth: 3,
    imagesCount: 2
  }

  it('renders stats correctly when provided', () => {
    render(<GermplasmSummaryPanel germplasm={mockGermplasm} stats={mockStats} />)

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('Trials')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('Observations')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Pedigree Depth')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('Images')).toBeInTheDocument()
  })

  it('renders dashes when stats are missing', () => {
    render(<GermplasmSummaryPanel germplasm={mockGermplasm} />)

    const dashes = screen.getAllByText('-')
    expect(dashes.length).toBeGreaterThanOrEqual(4)
  })
})
