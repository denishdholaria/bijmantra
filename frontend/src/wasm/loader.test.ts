import { describe, expect, it } from 'vitest'

import { resolveGenomicsWasmPath } from './loader'

describe('resolveGenomicsWasmPath', () => {
  it('resolves the shipped public wasm asset at the root base URL', () => {
    expect(resolveGenomicsWasmPath('/')).toBe('/wasm/bijmantra_genomics.js')
  })

  it('preserves non-root deploy bases for the public wasm asset', () => {
    expect(resolveGenomicsWasmPath('/bijmantra')).toBe('/bijmantra/wasm/bijmantra_genomics.js')
    expect(resolveGenomicsWasmPath('/bijmantra/')).toBe('/bijmantra/wasm/bijmantra_genomics.js')
  })
})
