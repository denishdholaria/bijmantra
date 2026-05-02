import { render, screen } from '@testing-library/react'
import { PdfReportTemplateRenderer, PdfReportData, PdfReportTemplate } from './PdfReportTemplateRenderer'
import { describe, it, expect, vi } from 'vitest'
import React from 'react'

// Mock Lucide icons to avoid issues in test environment if any
vi.mock('lucide-react', async () => {
  const actual = await vi.importActual('lucide-react') as Record<string, unknown>
  return {
    ...actual,
    // Add any specific mocks if needed
  }
})

describe('PdfReportTemplateRenderer', () => {
  const mockData: PdfReportData = {
    title: 'Trial Performance Report',
    subtitle: '2024 Summer Maize Trial',
    generatedAt: '2025-01-24',
    generatedBy: 'System Agent',
    metrics: [
      { label: 'Avg Yield', value: '8.4', unit: 't/ha' },
      { label: 'Lines Tested', value: '45' }
    ],
    summary: 'The trial showed significant progress in drought tolerance.',
    tables: [
      {
        title: 'Top Performers',
        headers: ['Line', 'Yield', 'Rank'],
        rows: [
          ['MZ-101', 9.2, 1],
          ['MZ-204', 8.9, 2]
        ]
      }
    ],
    reevuInsights: [
      {
        claims: ['MZ-101 exhibits superior water use efficiency.'],
        uncertainty: { score: 0.95, missing_data_indicators: [] },
        evidence_refs: [
          { source_type: 'Trial', entity_id: 'T-2024-01', retrieved_at: '2025-01-24', query_or_method: 'Aggregation', freshness_seconds: 60 }
        ]
      }
    ]
  }

  const mockTemplate: PdfReportTemplate = {
    id: 't1',
    name: 'Standard Scientific',
    pageSize: 'A4',
    orientation: 'portrait',
    showPageNumbers: true,
    showTableOfContents: false,
    themeColor: '#000000'
  }

  it('renders report title and subtitle', () => {
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} />)
    // Title appears in control bar and report header
    const titles = screen.getAllByText('Trial Performance Report')
    expect(titles.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('2024 Summer Maize Trial')).toBeInTheDocument()
  })

  it('renders metrics correctly', () => {
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} />)
    expect(screen.getByText('Avg Yield')).toBeInTheDocument()
    expect(screen.getByText('8.4')).toBeInTheDocument()
    expect(screen.getByText('t/ha')).toBeInTheDocument()
  })

  it('renders data tables correctly', () => {
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} />)
    expect(screen.getByText('Top Performers')).toBeInTheDocument()
    expect(screen.getByText('MZ-101')).toBeInTheDocument()
    expect(screen.getByText('9.2')).toBeInTheDocument()
  })

  it('renders REEVU insights and evidence', () => {
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} />)
    expect(screen.getByText('REEVU Scientific Insight')).toBeInTheDocument()
    expect(screen.getByText('MZ-101 exhibits superior water use efficiency.')).toBeInTheDocument()
    expect(screen.getByText('CONFIDENCE: 95%')).toBeInTheDocument()
    expect(screen.getByText('Evidence Assembly (Traceable Provenance)')).toBeInTheDocument()
    // Check for specific evidence details
    expect(screen.getByText('ID: T-2024-01')).toBeInTheDocument()
    expect(screen.getByText(/Aggregation/i)).toBeInTheDocument()
  })

  it('shows draft watermark when isDraft is true', () => {
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} isDraft={true} />)
    expect(screen.getByText('DRAFT')).toBeInTheDocument()
  })

  it('triggers window.print when print button is clicked', () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})
    render(<PdfReportTemplateRenderer data={mockData} template={mockTemplate} />)

    const printButton = screen.getByRole('button', { name: /print/i })
    printButton.click()

    expect(printSpy).toHaveBeenCalled()
    printSpy.mockRestore()
  })
})
