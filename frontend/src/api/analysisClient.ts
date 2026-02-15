
/**
 * Analysis API Client
 * 
 * specialized client for Analysis Engine endpoints (v2) which return raw JSON 
 * (Dict) instead of strict BrAPI envelopes.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function analysisFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  // Ensure endpoint starts with /
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${path}`

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const errorBody = await response.text()
      try {
        const errorJson = JSON.parse(errorBody)
        throw new Error(errorJson.detail || `API Error: ${response.statusText}`)
      } catch (e) {
        throw new Error(`API Error: ${response.statusText} - ${errorBody}`)
      }
    }

    return await response.json()
  } catch (error) {
    console.error('Analysis API Error:', error)
    throw error
  }
}

export async function analysisPost<T>(endpoint: string, data: any): Promise<T> {
  return analysisFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function analysisGet<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
  let url = endpoint
  if (params) {
    const queryString = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryString.append(key, String(value))
      }
    })
    url = `${endpoint}?${queryString.toString()}`
  }
  return analysisFetch<T>(url, { method: 'GET' })
}
