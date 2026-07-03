/**
 * @vitest-environment jsdom
 */

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ReevuRunTimelineCard from './ReevuRunTimelineCard'

describe('ReevuRunTimelineCard', () => {
  it('renders the latest REEVU run event and expands timeline details', () => {
    render(
      <ReevuRunTimelineCard
        events={[
          {
            type: 'reevu_run',
            run_id: 'run-1',
            event: 'run.started',
            status: 'started',
            title: 'REEVU run started',
            detail: 'Scoping the request.',
          },
          {
            type: 'reevu_run',
            run_id: 'run-1',
            event: 'tool.completed',
            status: 'completed',
            title: 'Domain tool completed',
            detail: 'Tool output is available.',
            tool_name: 'get_trial_results',
            domains_involved: ['trials'],
            evidence_count: 3,
            calculation_count: 1,
          },
        ]}
      />,
    )

    expect(screen.getByText('ReevuRun')).toBeInTheDocument()
    expect(screen.getAllByText('Domain tool completed')).toHaveLength(2)
    expect(screen.getByText('2 events')).toBeInTheDocument()
    expect(screen.getByText('get_trial_results')).toBeInTheDocument()
    expect(screen.getByText('3 evidence refs')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Toggle REEVU run timeline' }))

    expect(screen.getByText('REEVU run started')).toBeInTheDocument()
    expect(screen.getByText('Scoping the request.')).toBeInTheDocument()
  })

  it('does not render without events', () => {
    const { container } = render(<ReevuRunTimelineCard events={[]} />)

    expect(container).toBeEmptyDOMElement()
  })
})
