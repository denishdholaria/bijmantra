import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('initWasm', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
  })

  it('returns the JavaScript fallback when the optional WASM bundle is unavailable', async () => {
    vi.doMock('./loader', () => ({
      loadWasmModule: vi.fn().mockRejectedValue(new Error('missing wasm bundle')),
    }))

    const wasmModule = await import('./index')
    const wasm = await wasmModule.initWasm()

    expect(wasm.get_version()).toBe('fallback-0.0.0')
    expect(wasmModule.isWasmReady()).toBe(false)
  })

  it('initializes the WASM module when the optional bundle is present', async () => {
    const initialize = vi.fn().mockResolvedValue(undefined)
    const getVersion = vi.fn().mockReturnValue('1.2.3')
    const isReady = vi.fn().mockReturnValue(true)

    vi.doMock('./loader', () => ({
      loadWasmModule: vi.fn().mockResolvedValue({
        default: initialize,
        get_version: getVersion,
        is_wasm_ready: isReady,
      }),
    }))

    const wasmModule = await import('./index')
    const wasm = await wasmModule.initWasm()

    expect(initialize).toHaveBeenCalledOnce()
    expect(wasm.get_version()).toBe('1.2.3')
    expect(wasmModule.getWasm()).toBe(wasm)
    expect(wasmModule.isWasmReady()).toBe(true)
  })
})
