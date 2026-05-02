import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ReevuSafeFailureCard from './ReevuSafeFailureCard'

describe('ReevuSafeFailureCard', () => {
  it('renders structured safe-failure sections with actionable details', () => {
    render(
      <ReevuSafeFailureCard
        safeFailure={{
          error_category: 'insufficient_evidence',
          searched: ['retrieved_context', 'response_validation'],
          missing: ['grounded evidence for one or more claims'],
          next_steps: ['Narrow the query by crop, trial, location, or season.'],
          missing_context: [
            {
              domain: 'weather',
              reason: 'resolved location has no stored coordinates',
              location_query: 'Ludhiana',
            },
          ],
        }}
      />,
    )

    expect(screen.getByText('Structured safe failure')).toBeInTheDocument()
    expect(screen.getByText('insufficient evidence')).toBeInTheDocument()
    expect(screen.getByText('What REEVU checked')).toBeInTheDocument()
    expect(screen.getByText('retrieved_context')).toBeInTheDocument()
    expect(screen.getByText('What is still missing')).toBeInTheDocument()
    expect(screen.getByText('grounded evidence for one or more claims')).toBeInTheDocument()
    expect(screen.getByText('Suggested next steps')).toBeInTheDocument()
    expect(screen.getByText('Narrow the query by crop, trial, location, or season.')).toBeInTheDocument()
    expect(screen.getByText('Missing context details')).toBeInTheDocument()
    expect(screen.getByText('weather: resolved location has no stored coordinates · location query=Ludhiana')).toBeInTheDocument()
  })
})
