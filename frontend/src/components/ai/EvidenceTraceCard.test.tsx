import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import EvidenceTraceCard, { type EvidenceEnvelope } from './EvidenceTraceCard'

describe('EvidenceTraceCard', () => {
  const envelope: EvidenceEnvelope = {
    claims: ['Trial-backed recommendation was generated.'],
    claim_traces: [
      {
        statement: 'Database evidence supports this recommendation.',
        support_type: 'retrieval_backed',
        evidence_refs: ['db:trial:TRIAL-1'],
      },
      {
        statement: 'Rank ordering was computed from deterministic trial and weather inputs.',
        support_type: 'calculation_backed',
        calculation_ids: ['calc:cross_domain:join'],
      },
      {
        statement: 'Further field monitoring is still advised.',
        support_type: 'model_synthesis',
      },
    ],
    evidence_refs: [
      {
        source_type: 'database',
        entity_id: 'db:trial:TRIAL-1',
        query_or_method: 'trial_summary.query',
        retrieved_at: '2026-03-28T10:00:00Z',
        freshness_seconds: 120,
      },
      {
        source_type: 'function',
        entity_id: 'fn:weather.forecast',
        query_or_method: 'weather_service.get_forecast',
        retrieved_at: '2026-03-28T10:05:00Z',
      },
    ],
    calculation_steps: [
      {
        step_id: 'calc:cross_domain:join',
        formula: 'rank(trial_yield, weather_risk)',
      },
    ],
    uncertainty: {
      confidence: 0.62,
      missing_data: ['soil_records'],
    },
    missing_evidence_signals: ['missing_calculation_provenance'],
    policy_flags: ['stale_evidence:db:trial:TRIAL-1'],
  }

  it('shows source, calculation, and uncertainty trust cues in the collapsed header', () => {
    render(<EvidenceTraceCard envelope={envelope} />)

    expect(screen.getByText('Source: Database + Function')).toBeInTheDocument()
    expect(screen.getByText('Calculation: 1 step')).toBeInTheDocument()
    expect(screen.getByText('Uncertainty: Medium · 2 issues')).toBeInTheDocument()
  })

  it('renders detailed trust metadata when expanded', () => {
    render(<EvidenceTraceCard envelope={envelope} />)

    fireEvent.click(screen.getByRole('button', { name: 'Toggle evidence trace details' }))

    expect(screen.getByText('Trust Cues')).toBeInTheDocument()
    expect(screen.getByText('Source coverage')).toBeInTheDocument()
    expect(screen.getByText('Calculation provenance')).toBeInTheDocument()
    expect(screen.getByText('Method: trial_summary.query')).toBeInTheDocument()
    expect(screen.getByText('Retrieved: 2026-03-28T10:00:00Z')).toBeInTheDocument()
    expect(screen.getByText('Missing Evidence Signals')).toBeInTheDocument()
    expect(screen.getByText('missing_calculation_provenance')).toBeInTheDocument()
    expect(screen.getByText('Claim Support')).toBeInTheDocument()
    expect(screen.getByText('Retrieval-Backed Claims (1)')).toBeInTheDocument()
    expect(screen.getByText('Calculation-Backed Claims (1)')).toBeInTheDocument()
    expect(screen.getByText('Model Synthesis Text (1)')).toBeInTheDocument()
    expect(screen.getByText('Database evidence supports this recommendation.')).toBeInTheDocument()
    expect(screen.getByText('Further field monitoring is still advised.')).toBeInTheDocument()
  })
})
