import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Devices } from './Devices'
import { LiveData } from './LiveData'
import { Alerts } from './Alerts'

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

vi.mock('@/components/charts/LiveSensorChart', () => ({
  LiveSensorChart: () => <div data-testid="live-sensor-chart" />,
}))

describe('Sensor Networks route access', () => {
  it('renders Devices page without requiring active workspace', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ devices: [], types: [] }),
    }))

    render(<Devices />)
    expect(await screen.findByText('Sensor Devices')).toBeInTheDocument()
  })

  it('renders Live Data page without requiring active workspace', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ readings: [], devices: [] }),
    }))

    render(<LiveData />)
    expect(await screen.findByText('Live Sensor Data')).toBeInTheDocument()
  })

  it('renders Alerts page without requiring active workspace', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ rules: [], events: [] }),
    }))

    render(<Alerts />)
    expect(await screen.findByText('Sensor Alerts')).toBeInTheDocument()
  })
})
