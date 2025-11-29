/**
 * BrAPI Client - Base API client configuration
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface BrAPIResponse<T> {
  metadata: {
    datafiles: any[]
    pagination: {
      currentPage: number
      pageSize: number
      totalCount: number
      totalPages: number
    }
    status: Array<{
      message: string
      messageType: string
    }>
  }
  result: T
}

/**
 * Base fetch function with error handling
 */
export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<BrAPIResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('API Fetch Error:', error)
    throw error
  }
}

/**
 * GET request
 */
export async function apiGet<T>(endpoint: string): Promise<BrAPIResponse<T>> {
  return apiFetch<T>(endpoint, { method: 'GET' })
}

/**
 * POST request
 */
export async function apiPost<T>(
  endpoint: string,
  data: any,
): Promise<BrAPIResponse<T>> {
  return apiFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * PUT request
 */
export async function apiPut<T>(
  endpoint: string,
  data: any,
): Promise<BrAPIResponse<T>> {
  return apiFetch<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

/**
 * DELETE request
 */
export async function apiDelete<T>(endpoint: string): Promise<BrAPIResponse<T>> {
  return apiFetch<T>(endpoint, { method: 'DELETE' })
}
