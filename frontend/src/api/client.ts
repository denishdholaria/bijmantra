import { API_URL } from '@/config';
import { withTraceHeaders } from '@/lib/tracing/http'
/**
 * BrAPI Client - Base API client configuration
 */


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
 * Base fetch function with error handling.
 * Makes a generic API request to a specified endpoint.
 * @template T The expected type of the result data.
 * @param {string} endpoint The API endpoint relative to the base URL.
 * @param {RequestInit} [options] Optional request options (e.g., method, headers).
 * @returns {Promise<BrAPIResponse<T>>} A promise that resolves to the API response structure.
 */
export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<BrAPIResponse<T>> {
  const url = `${API_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers: withTraceHeaders({
        'Content-Type': 'application/json',
        ...options?.headers,
      }),
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
