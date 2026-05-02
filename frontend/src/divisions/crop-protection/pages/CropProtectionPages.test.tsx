import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CropProtectionDashboard } from './Dashboard'
import { DiseaseRiskForecastPage } from './DiseaseRiskForecast'
import { IPMStrategies } from './IPMStrategies'
import { PestObservations } from './PestObservations'
import { SprayApplication } from './SprayApplication'

const { mockApiClient, mockToast } = vi.hoisted(() => ({
  mockApiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  mockToast: vi.fn(),
}))

vi.mock('@/lib/api-client', () => ({
  apiClient: mockApiClient,
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('@/hooks/useToast', () => ({
  useToast: () => ({ toast: mockToast }),
}))

function renderWithProviders(ui: ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    </MemoryRouter>
  )
}

describe('crop protection pages', () => {
  beforeEach(() => {
    mockApiClient.get.mockImplementation(async (url: string) => {
      if (url.includes('/compliance-report')) {
        return { total_applications: 1, compliant_applications: 1, compliance_rate: 100 }
      }
      return []
    })
    mockApiClient.post.mockResolvedValue({})
    mockApiClient.put.mockResolvedValue({})
    mockApiClient.delete.mockResolvedValue({})
  })

  it('renders the crop protection dashboard', async () => {
    renderWithProviders(<CropProtectionDashboard />)
    expect(await screen.findByText('Crop Protection')).toBeInTheDocument()
    expect(await screen.findByText('Operational readiness')).toBeInTheDocument()
  })

  it('renders the pest observations page', async () => {
    renderWithProviders(<PestObservations />)
    expect(await screen.findByText('Pest Observations')).toBeInTheDocument()
    expect(await screen.findByText('Scouting queue')).toBeInTheDocument()
  })

  it('renders the disease risk forecast page', async () => {
    renderWithProviders(<DiseaseRiskForecastPage />)
    expect(await screen.findByText('Disease Risk Forecasts')).toBeInTheDocument()
    expect(await screen.findByText('All forecasts')).toBeInTheDocument()
  })

  it('renders the spray applications page', async () => {
    renderWithProviders(<SprayApplication />)
    expect(await screen.findByText('Spray Applications')).toBeInTheDocument()
    expect(await screen.findByText('Application history')).toBeInTheDocument()
  })

  it('renders the IPM strategies page', async () => {
    renderWithProviders(<IPMStrategies />)
    expect(await screen.findByText('IPM Strategies')).toBeInTheDocument()
    expect(await screen.findByText('Strategy library')).toBeInTheDocument()
  })
})
