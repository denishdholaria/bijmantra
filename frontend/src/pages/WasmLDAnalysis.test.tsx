import type { ReactNode } from 'react'

import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiClient } from '@/lib/api-client'

import { WasmLDAnalysis } from './WasmLDAnalysis'

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

vi.mock('@/wasm/hooks', () => ({
  useWasm: () => ({ isReady: true, version: 'test', wasm: null }),
}))

vi.mock('recharts', () => {
  const Mock = ({ children }: { children?: ReactNode }) => <div>{children}</div>
  return {
    ResponsiveContainer: Mock,
    LineChart: Mock,
    Line: Mock,
    XAxis: Mock,
    YAxis: Mock,
    CartesianGrid: Mock,
    Tooltip: Mock,
  }
})

describe('WasmLDAnalysis server mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

    Element.prototype.setPointerCapture = vi.fn()
    Element.prototype.releasePointerCapture = vi.fn()
    Element.prototype.hasPointerCapture = vi.fn()

    if (!global.PointerEvent) {
      class MockPointerEvent extends MouseEvent {
        constructor(type: string, props: PointerEventInit = {}) {
          super(type, props)
        }
      }

      global.PointerEvent = MockPointerEvent as unknown as typeof PointerEvent
    }
  })

  it('requires a real variant set id before running server analysis', async () => {
    render(<WasmLDAnalysis />)

    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }))

    expect(await screen.findByText(/enter a variant set id/i)).toBeInTheDocument()
    expect(apiClient.post).not.toHaveBeenCalled()
  })

  it('uses the direct LD API contract for server analysis', async () => {
    vi.mocked(apiClient.post).mockImplementation(async (endpoint: string) => {
      if (endpoint === '/api/v2/ld/calculate') {
        return {
          pairs: [
            {
              marker1: 'M1',
              marker2: 'M2',
              distance: 100,
              r2: 0.81,
              d_prime: 0.9,
            },
          ],
          marker_count: 2,
          sample_count: 12,
          mean_r2: 0.81,
        }
      }

      if (endpoint === '/api/v2/ld/decay') {
        return {
          decay_curve: [{ distance: 100, mean_r2: 0.81, pair_count: 1 }],
        }
      }

      throw new Error(`Unexpected endpoint: ${endpoint}`)
    })

    vi.mocked(apiClient.get).mockResolvedValue({
      markers: ['M1', 'M2'],
      matrix: [
        [1, 0.81],
        [0.81, 1],
      ],
      region: 'region1',
    })

    render(<WasmLDAnalysis />)

    fireEvent.change(screen.getByLabelText(/variant set id/i), {
      target: { value: 'vs-1' },
    })
    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }))

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v2/ld/calculate',
        expect.objectContaining({ variant_set_id: 'vs-1' }),
      )
    })

    await waitFor(() => {
      expect(screen.getByText('1 pairs')).toBeInTheDocument()
      expect(screen.getByText('M1')).toBeInTheDocument()
      expect(screen.getByText('M2')).toBeInTheDocument()
      expect(screen.getAllByText('0.810').length).toBeGreaterThan(0)
    })
  })
})