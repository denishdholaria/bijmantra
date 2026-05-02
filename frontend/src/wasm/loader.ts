import { APP_BASE_URL } from '@/config'

export function resolveGenomicsWasmPath(baseUrl = APP_BASE_URL) {
  const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
  return `${normalizedBaseUrl}wasm/bijmantra_genomics.js`
}

const genomicsWasmPath = resolveGenomicsWasmPath()

export async function loadWasmModule() {
  return import(/* @vite-ignore */ genomicsWasmPath)
}
