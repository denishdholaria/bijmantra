import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ReevuExecutionTraceCard from './ReevuExecutionTraceCard'

describe('ReevuExecutionTraceCard', () => {
  it('renders retrieval audit and execution plan details when expanded', () => {
    render(
      <ReevuExecutionTraceCard
        retrievalAudit={{
          services: ['trial_search_service.search', 'weather_service.get_forecast'],
          tables: ['Trial'],
          entities: {
            crop: 'rice',
            resolved_weather_location_id: 'LOC-1',
            weather_coordinates_used: true,
          },
        }}
        planExecutionSummary={{
          plan_id: 'plan-1',
          is_compound: true,
          domains_involved: ['trials', 'weather'],
          total_steps: 2,
          metadata: {
            fallback_reasons: ['low_confidence_threshold'],
          },
          missing_domains: ['weather'],
          steps: [
            {
              step_id: 'step-1',
              domain: 'trials',
              description: 'Search trials',
              prerequisites: [],
              expected_outputs: ['trials', 'study_ids'],
              deterministic: true,
              completed: true,
              status: 'completed',
              actual_outputs: ['trials', 'study_ids'],
              services: ['trial_search_service.search'],
              output_counts: {
                trials: 1,
                study_ids: 1,
              },
              output_entity_ids: {
                trials: ['TRIAL-1'],
                study_ids: ['31'],
              },
              output_metadata: {
                resolved_location: 'Ludhiana',
              },
              compute_methods: ['fn:trial_ranker'],
            },
            {
              step_id: 'step-2',
              domain: 'weather',
              description: 'Join weather context',
              prerequisites: ['step-1'],
              completed: false,
              status: 'missing',
              actual_outputs: ['locations'],
              services: ['location_search_service.search', 'weather_service.get_forecast'],
              output_counts: {
                locations: 1,
              },
              output_entity_ids: {
                locations: ['LOC-1'],
              },
              missing_reason: 'weather service is unavailable',
            },
          ],
        }}
      />,
    )

    expect(screen.getByText('Execution Trace')).toBeInTheDocument()
    expect(screen.getByText('Services: 2')).toBeInTheDocument()
    expect(screen.getByText('Steps: 2')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Toggle execution trace details' }))

    expect(screen.getByText('Retrieval Services')).toBeInTheDocument()
    expect(screen.getAllByText('trial_search_service.search').length).toBeGreaterThan(0)
    expect(screen.getByText('Resolved scope')).toBeInTheDocument()
    expect(screen.getAllByText('LOC-1').length).toBeGreaterThan(0)
    expect(screen.getByText('Execution plan')).toBeInTheDocument()
    expect(screen.getByText('Search trials')).toBeInTheDocument()
    expect(screen.getByText('Join weather context')).toBeInTheDocument()
    expect(screen.getByText('Deterministic')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Missing')).toBeInTheDocument()
    expect(screen.getByText('Planner metadata')).toBeInTheDocument()
    expect(screen.getByText('low_confidence_threshold')).toBeInTheDocument()
    expect(screen.getByText('Missing: weather')).toBeInTheDocument()
    expect(screen.getByText('Expected outputs')).toBeInTheDocument()
    expect(screen.getAllByText('Actual outputs').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Services used').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Output counts').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Sample entities').length).toBeGreaterThan(0)
    expect(screen.getByText('Additional context')).toBeInTheDocument()
    expect(screen.getByText('Deterministic methods')).toBeInTheDocument()
    expect(screen.getByText('fn:trial_ranker')).toBeInTheDocument()
    expect(screen.getByText('weather service is unavailable')).toBeInTheDocument()
    expect(screen.getByText('Resolved Location')).toBeInTheDocument()
    expect(screen.getByText('Ludhiana')).toBeInTheDocument()
  })
})
