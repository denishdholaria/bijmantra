import type { ReactNode } from 'react'

import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { WasmGBLUP } from './WasmGBLUP'

vi.mock('@/wasm/hooks', () => ({
  useWasm: () => ({ isReady: true, version: 'test' }),
  useGRM: () => ({ calculate: vi.fn(), result: null }),
  useGBLUP: () => ({ calculate: vi.fn(), result: null }),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

vi.mock('recharts', () => {
  const Mock = ({ children }: { children?: ReactNode }) => <div>{children}</div>
  return {
    ResponsiveContainer: Mock,
    ScatterChart: Mock,
    Scatter: Mock,
    XAxis: Mock,
    YAxis: Mock,
    CartesianGrid: Mock,
    Tooltip: Mock,
  }
})

describe('WasmGBLUP server mode', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    class MockResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }

    global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

    global.fetch = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const url = String(input)

      if (url === '/api/v2/compute/grm') {
        return new Response(JSON.stringify({
          output: {
            matrix: [
              [1, 0.2],
              [0.2, 1],
            ],
            method: 'vanraden1',
            n_individuals: 2,
            n_markers: 500,
          },
        })
        )
      }

      if (url === '/api/v2/compute/gblup') {
        return new Response(JSON.stringify({
          output: {
            breeding_values: [1.25, -0.5],
            reliability: [0.8, 0.6],
            accuracy: [0.8944, 0.7746],
            genetic_variance: 0.765,
            error_variance: 0.245,
            mean: 101.5,
            converged: true,
          },
        })
        )
      }

      return new Response(JSON.stringify({ detail: `Unexpected endpoint: ${url}` }), {
        status: 500,
      })
    }) as unknown as typeof fetch
  })

  it('uses canonical compute endpoints for server G-matrix and GBLUP', async () => {
    render(<WasmGBLUP />)

    fireEvent.click(screen.getByRole('button', { name: /server/i }))
    fireEvent.click(screen.getByRole('button', { name: /step 1: calculate g-matrix/i }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v2/compute/grm',
        expect.objectContaining({ method: 'POST' }),
      )
    })

    const runGblupButton = screen.getByRole('button', { name: /step 2: run gblup/i })
    await waitFor(() => expect(runGblupButton).toBeEnabled())

    fireEvent.click(runGblupButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v2/compute/gblup',
        expect.objectContaining({ method: 'POST' }),
      )
    })

    const requestedUrls = vi.mocked(global.fetch).mock.calls.map(([url]) => String(url))
    expect(requestedUrls).toContain('/api/v2/compute/grm')
    expect(requestedUrls).toContain('/api/v2/compute/gblup')
    expect(requestedUrls).not.toContain('/api/v2/genomic-selection/g-matrix')
    expect(requestedUrls).not.toContain('/api/v2/genomic-selection/gblup')

    await waitFor(() => {
      expect(screen.getByText('0.77')).toBeInTheDocument()
      expect(screen.getByText('101.50')).toBeInTheDocument()
    })
  })
})