import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { UsageFuelGauge } from './UsageFuelGauge'

const { getTokenMock, getUsageMock } = vi.hoisted(() => ({
  getTokenMock: vi.fn(),
  getUsageMock: vi.fn(),
}))

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    getToken: getTokenMock,
    chatService: {
      getUsage: getUsageMock,
    },
  },
}))

vi.mock('@/components/ui/tooltip', () => ({
  Tooltip: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TooltipTrigger: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TooltipContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  TooltipProvider: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

describe('UsageFuelGauge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getTokenMock.mockReturnValue('token-1')
    getUsageMock.mockResolvedValue({
      used: 42,
      limit: 50,
      remaining: 8,
      request_percentage_used: 84,
      quota_authority: 'request_count',
      provider: {
        active_provider: 'openai',
        active_model: 'gpt-4.1-mini',
        active_provider_source: 'organization_config',
        active_provider_source_label: 'Organization AI settings',
      },
      token_telemetry: {
        input_tokens: 2100,
        output_tokens: 540,
        total_tokens: 2640,
        coverage_state: 'supplemental',
        coverage_message:
          'Token telemetry is supplemental only. Request-count quota remains the enforcement authority for this slice.',
      },
      attribution: {
        lane: {
          supported: false,
          value: null,
          reason: 'Lane attribution is not linked from the canonical REEVU chat request path yet.',
        },
        mission: {
          supported: false,
          value: null,
          reason: 'Mission attribution is not linked from the canonical REEVU chat request path yet.',
        },
      },
      soft_alert: {
        state: 'watch',
        threshold_basis: 'request_count',
        percent_used: 84,
        message: 'Quota pressure is rising. Plan managed usage carefully.',
      },
    })
  })

  it('renders richer usage telemetry in the tooltip', async () => {
    render(<UsageFuelGauge />)

    expect(await screen.findByText('42/50')).toBeInTheDocument()

    expect(await screen.findByText('Daily AI Quota')).toBeInTheDocument()
    expect(screen.getByText(/Quota pressure is rising/)).toBeInTheDocument()
    expect(screen.getByText(/Provider:/)).toBeInTheDocument()
    expect(screen.getByText('openai')).toBeInTheDocument()
    expect(screen.getByText('gpt-4.1-mini')).toBeInTheDocument()
    expect(screen.getByText(/2,640/)).toBeInTheDocument()
    expect(
      screen.getByText(/Token telemetry is supplemental only\. Request-count quota remains the enforcement authority/i)
    ).toBeInTheDocument()
    expect(screen.getByText(/Lane attribution is not linked/)).toBeInTheDocument()
    expect(screen.getByText(/Mission attribution is not linked/)).toBeInTheDocument()
  })
})