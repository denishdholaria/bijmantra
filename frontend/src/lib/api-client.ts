/**
 * BrAPI Client
 * HTTP client for communicating with the backend API
 * 
 * ## Error Handling (preview-1)
 * Uses ApiError from api-errors.ts for typed error handling.
 * - ApiError.type: Enum of error types (UNAUTHORIZED, NOT_FOUND, etc.)
 * - ApiError.getUserMessage(): User-friendly error message
 * - ApiError.isAuthError(): Check if auth-related
 * - ApiError.isRetryable: Whether request can be retried
 * 
 * ## Logging
 * Uses logger from logger.ts for centralized logging.
 * Set VITE_LOG_LEVEL in .env to control verbosity (DEBUG, INFO, WARN, ERROR)
 * 
 * ## Query Building
 * Current methods use URLSearchParams directly for simplicity.
 * For complex filtering needs, see api-helpers.ts QueryBuilder (v1.1 adoption).
 */

import { ApiError, ApiErrorType, createApiErrorFromResponse, createApiErrorFromNetworkError } from './api-errors'
import { logger } from './logger'

export interface BrAPIMetadata {
  datafiles: string[]
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

export interface BrAPIResponse<T> {
  metadata: BrAPIMetadata
  result: T
}

export interface BrAPIListResponse<T> {
  metadata: BrAPIMetadata
  result: {
    data: T[]
  }
}

class APIClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL?: string) {
    // Use VITE_API_URL for production deployments (Vercel, etc.)
    // Falls back to empty string for local dev (uses Vite proxy)
    this.baseURL = baseURL ?? (import.meta.env.VITE_API_URL || '')
    this.loadToken()
    logger.debug('APIClient initialized', { baseURL: this.baseURL })
  }

  private loadToken() {
    try {
      this.token = typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null
    } catch {
      // localStorage may not be available in some environments
      this.token = null
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      try {
        localStorage.setItem('auth_token', token)
      } catch {
        // localStorage may not be available
      }
      logger.debug('Auth token set')
    } else {
      try {
        localStorage.removeItem('auth_token')
      } catch {
        // localStorage may not be available
      }
      logger.debug('Auth token cleared')
    }
  }

  getToken(): string | null {
    return this.token
  }

  // Validate token by making a simple API call
  async validateToken(): Promise<boolean> {
    if (!this.token) return false
    
    // Demo tokens are always valid (for offline/demo mode)
    if (this.token.startsWith('demo_')) return true
    
    try {
      const response = await fetch(`${this.baseURL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      })
      
      if (response.status === 401) {
        this.setToken(null)
        logger.warn('Token validation failed - 401 Unauthorized')
        return false
      }
      
      return response.ok
    } catch {
      // Network error - can't validate, assume valid for offline mode
      logger.debug('Token validation skipped - network unavailable')
      return true
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    // Merge any additional headers from options
    if (options.headers) {
      const optHeaders = options.headers as Record<string, string>
      Object.assign(headers, optHeaders)
    }

    const method = options.method || 'GET'
    logger.debug(`API Request: ${method} ${endpoint}`)

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const apiError = await createApiErrorFromResponse(response, {
          endpoint,
          method,
        })
        
        // Handle 401 Unauthorized - clear token and redirect to login
        if (apiError.isAuthError()) {
          this.setToken(null)
          // Dispatch custom event for auth state change
          window.dispatchEvent(new CustomEvent('auth:unauthorized'))
          logger.warn('Authentication error - session cleared', { endpoint })
        } else {
          logger.error(`API Error: ${method} ${endpoint}`, apiError, {
            statusCode: response.status,
            type: apiError.type,
          })
        }
        
        throw apiError
      }

      return response.json()
    } catch (error) {
      // If already an ApiError, rethrow
      if (error instanceof ApiError) {
        throw error
      }
      
      // Network/fetch errors
      if (error instanceof TypeError) {
        const networkError = createApiErrorFromNetworkError(error as Error, {
          endpoint,
          method,
        })
        logger.error('Network error', error as Error, { endpoint })
        throw networkError
      }
      
      // Unknown errors
      logger.error('Unexpected error in API request', error as Error, { endpoint })
      throw error
    }
  }

  // Authentication
  async login(
    email: string,
    password: string
  ): Promise<{ 
    access_token: string; 
    token_type: string;
    user?: {
      id: number;
      email: string;
      full_name: string;
      organization_id: number;
      organization_name?: string;
      is_demo: boolean;
      is_active: boolean;
      is_superuser: boolean;
    };
  }> {
    // Helper to generate demo token with user info
    const generateDemoToken = () => {
      console.log('🔓 Demo Mode: Enabling demo login for', email)
      const isDemo = email.includes('demo@')
      const demoToken = btoa(
        JSON.stringify({
          email,
          exp: Date.now() + 24 * 60 * 60 * 1000,
          demo: true,
        })
      )
      return {
        access_token: `demo_${demoToken}`,
        token_type: 'bearer',
        user: {
          id: isDemo ? 2 : 1,
          email,
          full_name: isDemo ? 'Demo User' : 'Admin User',
          organization_id: isDemo ? 1 : 2,
          organization_name: isDemo ? 'Demo Organization' : 'BijMantra HQ',
          is_demo: isDemo,
          is_active: true,
          is_superuser: !isDemo,
        },
      }
    }

    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

      const response = await fetch(`${this.baseURL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        // Check if it's a server error (5xx) - likely proxy/backend issue
        if (response.status >= 500) {
          console.warn('🔌 Backend server error (5xx) - falling back to demo mode')
          return generateDemoToken()
        }
        // Authentication errors (401, 403, 400) should NOT fall back to demo mode
        // These are real errors that the user needs to see
        const error = await response.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(error.detail)
      }

      return response.json()
    } catch (error) {
      // Only fall back to demo mode for NETWORK errors (backend unavailable)
      // NOT for authentication errors (wrong password, etc.)
      if (error instanceof Error) {
        // Check if this is an AbortError (timeout) or network error
        const isNetworkError = error.name === 'AbortError' || 
                               error.name === 'TypeError' ||
                               error.message.includes('fetch') ||
                               error.message.includes('network')
        
        if (isNetworkError) {
          console.warn('🔌 Backend unavailable - falling back to demo mode')
          return generateDemoToken()
        }
        
        // Re-throw authentication errors so user sees the actual error message
        throw error
      }
      
      // Unknown error type - fall back to demo mode as last resort
      console.warn('🔌 Unknown error during login - falling back to demo mode')
      return generateDemoToken()
    }
  }

  async register(email: string, password: string, fullName: string, organizationId: number) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        organization_id: organizationId,
      }),
    })
  }

  // Programs
  async getPrograms(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/programs?page=${page}&pageSize=${pageSize}`)
  }

  async getProgram(programDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/programs/${programDbId}`)
  }

  async createProgram(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/programs', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProgram(programDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/programs/${programDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProgram(programDbId: string) {
    return this.request(`/brapi/v2/programs/${programDbId}`, {
      method: 'DELETE',
    })
  }

  // Locations
  async getLocations(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/locations?page=${page}&pageSize=${pageSize}`)
  }

  async getLocation(locationDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/locations/${locationDbId}`)
  }

  async createLocation(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/locations', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateLocation(locationDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/locations/${locationDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Trials
  async getTrials(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/trials?page=${page}&pageSize=${pageSize}`)
  }

  async getTrial(trialDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/trials/${trialDbId}`)
  }

  async createTrial(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/trials', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateTrial(trialDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/trials/${trialDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteTrial(trialDbId: string) {
    return this.request(`/brapi/v2/trials/${trialDbId}`, {
      method: 'DELETE',
    })
  }

  // Studies
  async getStudies(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/studies?page=${page}&pageSize=${pageSize}`)
  }

  async getStudy(studyDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/studies/${studyDbId}`)
  }

  async createStudy(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/studies', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateStudy(studyDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/studies/${studyDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteStudy(studyDbId: string) {
    return this.request(`/brapi/v2/studies/${studyDbId}`, {
      method: 'DELETE',
    })
  }

  // Seasons
  async getSeasons(page = 0, pageSize = 100, year?: number) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (year) params.append('year', String(year))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/seasons?${params}`)
  }

  async getSeason(seasonDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/seasons/${seasonDbId}`)
  }

  async createSeason(data: { seasonName: string; year?: number }) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/seasons', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateSeason(seasonDbId: string, data: { seasonName?: string; year?: number }) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/seasons/${seasonDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteSeason(seasonDbId: string) {
    return this.request(`/brapi/v2/seasons/${seasonDbId}`, {
      method: 'DELETE',
    })
  }

  async deleteLocation(locationDbId: string) {
    return this.request(`/brapi/v2/locations/${locationDbId}`, {
      method: 'DELETE',
    })
  }

  // Germplasm
  async getGermplasm(page = 0, pageSize = 100, search?: string) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (search) params.append('germplasmName', search)
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/germplasm?${params}`)
  }

  async getGermplasmById(germplasmDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/germplasm/${germplasmDbId}`)
  }

  async createGermplasm(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/germplasm', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateGermplasm(germplasmDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/germplasm/${germplasmDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteGermplasm(germplasmDbId: string) {
    return this.request(`/brapi/v2/germplasm/${germplasmDbId}`, {
      method: 'DELETE',
    })
  }

  // Observation Variables (Traits)
  async getObservationVariables(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variables?page=${page}&pageSize=${pageSize}`)
  }

  // Observations
  async getObservations(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (studyDbId) params.append('studyDbId', studyDbId)
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/observations?${params}`)
  }

  async createObservations(data: any[]) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/observations', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Observation Variables (Traits)
  async getObservationVariable(observationVariableDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/variables/${observationVariableDbId}`)
  }

  async createObservationVariable(data: any[]) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/variables', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateObservationVariable(observationVariableDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/variables/${observationVariableDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteObservationVariable(observationVariableDbId: string) {
    return this.request(`/brapi/v2/variables/${observationVariableDbId}`, {
      method: 'DELETE',
    })
  }

  // Observation Units
  async getObservationUnits(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (studyDbId) params.append('studyDbId', studyDbId)
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/observationunits?${params}`)
  }

  async createObservationUnits(data: any[]) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/observationunits', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Seed Lots
  async getSeedLots(germplasmDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (germplasmDbId) params.append('germplasmDbId', germplasmDbId)
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/seedlots?${params}`)
  }

  async createSeedLot(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/seedlots', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Seed Lots - Additional methods
  async getSeedLot(seedLotDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/seedlots/${seedLotDbId}`)
  }

  async updateSeedLot(seedLotDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/seedlots/${seedLotDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteSeedLot(seedLotDbId: string) {
    return this.request(`/brapi/v2/seedlots/${seedLotDbId}`, {
      method: 'DELETE',
    })
  }

  // People/Contacts
  async getPeople(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/people?page=${page}&pageSize=${pageSize}`)
  }

  async getPerson(personDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/people/${personDbId}`)
  }

  async createPerson(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/people', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updatePerson(personDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/people/${personDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deletePerson(personDbId: string) {
    return this.request(`/brapi/v2/people/${personDbId}`, {
      method: 'DELETE',
    })
  }

  // Lists (BrAPI Core)
  async getLists(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/lists?page=${page}&pageSize=${pageSize}`)
  }

  async getList(listDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/lists/${listDbId}`)
  }

  async createList(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/lists', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Search endpoints
  async searchGermplasm(searchRequest: any) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/search/germplasm', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    })
  }

  async searchObservations(searchRequest: any) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/search/observations', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    })
  }

  async searchStudies(searchRequest: any) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/search/studies', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    })
  }

  // Crosses (BrAPI Germplasm)
  async getCrosses(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/crosses?page=${page}&pageSize=${pageSize}`)
  }

  async getCross(crossDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/crosses/${crossDbId}`)
  }

  async createCross(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/crosses', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateCross(crossDbId: string, data: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/crosses/${crossDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  // Pedigree (BrAPI Germplasm)
  async getPedigree(germplasmDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/germplasm/${germplasmDbId}/pedigree`)
  }

  // Progeny (BrAPI Germplasm)
  async getProgeny(germplasmDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/germplasm/${germplasmDbId}/progeny`)
  }

  // Events (BrAPI Phenotyping)
  async getEvents(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
    if (studyDbId) params.append('studyDbId', studyDbId)
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/events?${params}`)
  }

  async createEvent(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/events', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Images (BrAPI Phenotyping)
  async getImages(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/images?page=${page}&pageSize=${pageSize}`)
  }

  async createImage(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/images', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Samples (BrAPI Genotyping)
  async getSamples(page = 0, pageSize = 100) {
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/samples?page=${page}&pageSize=${pageSize}`)
  }

  async getSample(sampleDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/samples/${sampleDbId}`)
  }

  async createSample(data: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/samples', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Delete methods
  async deleteCross(crossDbId: string) {
    return this.request(`/brapi/v2/crosses/${crossDbId}`, {
      method: 'DELETE',
    })
  }

  async deleteList(listDbId: string) {
    return this.request(`/brapi/v2/lists/${listDbId}`, {
      method: 'DELETE',
    })
  }

  async deleteEvent(eventDbId: string) {
    return this.request(`/brapi/v2/events/${eventDbId}`, {
      method: 'DELETE',
    })
  }

  async deleteSample(sampleDbId: string) {
    return this.request(`/brapi/v2/samples/${sampleDbId}`, {
      method: 'DELETE',
    })
  }

  // ============ Seed Bank Division ============

  // Seed Bank Stats
  async getSeedBankStats() {
    return this.request<any>('/api/v2/seed-bank/stats')
  }

  // Vaults
  async getVaults() {
    return this.request<any[]>('/api/v2/seed-bank/vaults')
  }

  async getVault(vaultId: string) {
    return this.request<any>(`/api/v2/seed-bank/vaults/${vaultId}`)
  }

  async createVault(data: any) {
    return this.request<any>('/api/v2/seed-bank/vaults', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Accessions
  async getAccessions(page = 0, pageSize = 20, search?: string, status?: string, vaultId?: string) {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (search) params.append('search', search)
    if (status) params.append('status', status)
    if (vaultId) params.append('vault_id', vaultId)
    return this.request<any>(`/api/v2/seed-bank/accessions?${params}`)
  }

  async getAccession(accessionId: string) {
    return this.request<any>(`/api/v2/seed-bank/accessions/${accessionId}`)
  }

  async createAccession(data: any) {
    return this.request<any>('/api/v2/seed-bank/accessions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateAccession(accessionId: string, data: any) {
    return this.request<any>(`/api/v2/seed-bank/accessions/${accessionId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  // Viability Tests
  async getViabilityTests(status?: string, accessionId?: string) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (accessionId) params.append('accession_id', accessionId)
    return this.request<any[]>(`/api/v2/seed-bank/viability-tests?${params}`)
  }

  async createViabilityTest(data: any) {
    return this.request<any>('/api/v2/seed-bank/viability-tests', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Regeneration Tasks
  async getRegenerationTasks(priority?: string, status?: string) {
    const params = new URLSearchParams()
    if (priority) params.append('priority', priority)
    if (status) params.append('status', status)
    return this.request<any[]>(`/api/v2/seed-bank/regeneration-tasks?${params}`)
  }

  async createRegenerationTask(data: any) {
    return this.request<any>('/api/v2/seed-bank/regeneration-tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Germplasm Exchanges
  async getExchanges(type?: string, status?: string) {
    const params = new URLSearchParams()
    if (type) params.append('type', type)
    if (status) params.append('status', status)
    return this.request<any[]>(`/api/v2/seed-bank/exchanges?${params}`)
  }

  async createExchange(data: any) {
    return this.request<any>('/api/v2/seed-bank/exchanges', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ============ Quality Control (Seed Operations) ============

  async getQCSamples(status?: string, lotId?: string) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (lotId) params.append('lot_id', lotId)
    return this.request<any>(`/api/v2/quality/samples?${params}`)
  }

  async getQCSample(sampleId: string) {
    return this.request<any>(`/api/v2/quality/samples/${sampleId}`)
  }

  async registerQCSample(data: {
    lot_id: string
    variety: string
    sample_date: string
    sample_weight: number
    source: string
  }) {
    return this.request<any>('/api/v2/quality/samples', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async recordQCTest(data: {
    sample_id: string
    test_type: string
    result_value: number
    tester: string
    method: string
    seed_class?: string
    notes?: string
  }) {
    return this.request<any>('/api/v2/quality/tests', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async issueQCCertificate(data: {
    sample_id: string
    seed_class: string
    valid_months?: number
  }) {
    return this.request<any>('/api/v2/quality/certificates', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getQCCertificates() {
    return this.request<{ certificates: any[] }>('/api/v2/quality/certificates')
  }

  async getQCStandards(seedClass: string = 'certified') {
    return this.request<any>(`/api/v2/quality/standards?seed_class=${seedClass}`)
  }

  async getQCSummary() {
    return this.request<any>('/api/v2/quality/summary')
  }

  async getQCTestTypes() {
    return this.request<any>('/api/v2/quality/test-types')
  }

  async getQCSeedClasses() {
    return this.request<any>('/api/v2/quality/seed-classes')
  }

  // ============ Seed Inventory (Seed Operations) ============

  async getSeedInventoryLots(species?: string, status?: string, storageType?: string) {
    const params = new URLSearchParams()
    if (species) params.append('species', species)
    if (status) params.append('status', status)
    if (storageType) params.append('storage_type', storageType)
    return this.request<any>(`/api/v2/seed-inventory/lots?${params}`)
  }

  async getSeedInventoryLot(lotId: string) {
    return this.request<any>(`/api/v2/seed-inventory/lots/${lotId}`)
  }

  async registerSeedInventoryLot(data: {
    accession_id: string
    species: string
    variety: string
    harvest_date: string
    quantity: number
    storage_type: string
    storage_location: string
    initial_viability: number
    notes?: string
  }) {
    return this.request<any>('/api/v2/seed-inventory/lots', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async recordViabilityTest(data: {
    lot_id: string
    test_date: string
    seeds_tested: number
    seeds_germinated: number
    test_method: string
    tester: string
    notes?: string
  }) {
    return this.request<any>('/api/v2/seed-inventory/viability', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getViabilityHistory(lotId: string) {
    return this.request<any>(`/api/v2/seed-inventory/viability/${lotId}`)
  }

  async createSeedRequest(data: {
    lot_id: string
    requester: string
    institution: string
    quantity: number
    purpose?: string
  }) {
    return this.request<any>('/api/v2/seed-inventory/requests', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async approveSeedRequest(requestId: string, quantityApproved: number) {
    return this.request<any>(`/api/v2/seed-inventory/requests/${requestId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ quantity_approved: quantityApproved }),
    })
  }

  async shipSeedRequest(requestId: string) {
    return this.request<any>(`/api/v2/seed-inventory/requests/${requestId}/ship`, {
      method: 'POST',
    })
  }

  async getSeedInventorySummary() {
    return this.request<any>('/api/v2/seed-inventory/summary')
  }

  async getSeedInventoryAlerts() {
    return this.request<any>('/api/v2/seed-inventory/alerts')
  }

  async getStorageTypes() {
    return this.request<any>('/api/v2/seed-inventory/storage-types')
  }

  // ============ Traceability (Seed Operations) ============

  async getTraceabilityTransfers() {
    return this.request<{ status: string; data: any[]; count: number }>('/api/v2/traceability/transfers')
  }

  async getTraceabilityLots(crop?: string, varietyId?: string, seedClass?: string, status?: string) {
    const params = new URLSearchParams()
    if (crop) params.append('crop', crop)
    if (varietyId) params.append('variety_id', varietyId)
    if (seedClass) params.append('seed_class', seedClass)
    if (status) params.append('status', status)
    return this.request<any>(`/api/v2/traceability/lots?${params}`)
  }

  async getTraceabilityLot(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}`)
  }

  async registerTraceabilityLot(data: {
    variety_id: string
    variety_name: string
    crop: string
    seed_class: string
    production_year: number
    production_season: string
    production_location: string
    producer_id: string
    producer_name: string
    quantity_kg: number
    parent_lot_id?: string
    germination_percent?: number
    purity_percent?: number
    moisture_percent?: number
  }) {
    return this.request<any>('/api/v2/traceability/lots', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async recordTraceabilityEvent(lotId: string, data: {
    event_type: string
    details: Record<string, any>
    operator_id?: string
    operator_name?: string
    location?: string
  }) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/events`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getLotHistory(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/history`)
  }

  async addLotCertification(lotId: string, data: {
    cert_type: string
    cert_number: string
    issuing_authority: string
    issue_date: string
    expiry_date: string
    test_results?: Record<string, any>
  }) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/certifications`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getLotCertifications(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/certifications`)
  }

  async recordLotTransfer(lotId: string, data: {
    from_entity_id: string
    from_entity_name: string
    to_entity_id: string
    to_entity_name: string
    quantity_kg: number
    transfer_type: string
    price_per_kg?: number
    invoice_number?: string
  }) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/transfers`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getLotTransfers(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/transfers`)
  }

  async traceLotLineage(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/lineage`)
  }

  async getLotDescendants(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/descendants`)
  }

  async getLotQRData(lotId: string) {
    return this.request<any>(`/api/v2/traceability/lots/${lotId}/qr`)
  }

  async getTraceabilityEventTypes() {
    return this.request<any>('/api/v2/traceability/event-types')
  }

  async getTraceabilityStatistics() {
    return this.request<any>('/api/v2/traceability/statistics')
  }

  // ============ Dispatch Management ============

  async createDispatch(data: {
    recipient_id: string
    recipient_name: string
    recipient_address: string
    recipient_contact?: string
    recipient_phone?: string
    transfer_type: string
    items: Array<{
      lot_id: string
      variety_name?: string
      crop?: string
      seed_class?: string
      quantity_kg: number
      unit_price?: number
    }>
    notes?: string
  }) {
    return this.request<any>('/api/v2/dispatch/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getDispatches(status?: string, recipientId?: string, transferType?: string) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (recipientId) params.append('recipient_id', recipientId)
    if (transferType) params.append('transfer_type', transferType)
    return this.request<any>(`/api/v2/dispatch/orders?${params}`)
  }

  async getDispatch(dispatchId: string) {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}`)
  }

  async submitDispatch(dispatchId: string) {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}/submit`, { method: 'POST' })
  }

  async approveDispatch(dispatchId: string, approvedBy: string = 'Manager') {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}/approve?approved_by=${approvedBy}`, { method: 'POST' })
  }

  async shipDispatch(dispatchId: string, data: { tracking_number?: string; carrier?: string; invoice_number?: string }) {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}/ship`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async markDispatchDelivered(dispatchId: string, notes: string = '') {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}/deliver?notes=${encodeURIComponent(notes)}`, { method: 'POST' })
  }

  async cancelDispatch(dispatchId: string, reason: string) {
    return this.request<any>(`/api/v2/dispatch/orders/${dispatchId}/cancel?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
  }

  async getDispatchStatistics() {
    return this.request<any>('/api/v2/dispatch/statistics')
  }

  async getDispatchStatuses() {
    return this.request<any>('/api/v2/dispatch/statuses')
  }

  // Firms/Dealers
  async createFirm(data: {
    name: string
    firm_type: string
    address: string
    city: string
    state: string
    country?: string
    postal_code: string
    contact_person: string
    phone: string
    email: string
    gst_number?: string
    credit_limit?: number
    notes?: string
  }) {
    return this.request<any>('/api/v2/dispatch/firms', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getFirms(firmType?: string, status?: string, city?: string, state?: string) {
    const params = new URLSearchParams()
    if (firmType) params.append('firm_type', firmType)
    if (status) params.append('status', status)
    if (city) params.append('city', city)
    if (state) params.append('state', state)
    return this.request<any>(`/api/v2/dispatch/firms?${params}`)
  }

  async getFirm(firmId: string) {
    return this.request<any>(`/api/v2/dispatch/firms/${firmId}`)
  }

  async updateFirm(firmId: string, data: Record<string, any>) {
    return this.request<any>(`/api/v2/dispatch/firms/${firmId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deactivateFirm(firmId: string) {
    return this.request<any>(`/api/v2/dispatch/firms/${firmId}`, { method: 'DELETE' })
  }

  async getFirmTypes() {
    return this.request<any>('/api/v2/dispatch/firm-types')
  }

  // ============ Seed Processing ============

  async createProcessingBatch(data: {
    lot_id: string
    variety_name: string
    crop: string
    seed_class?: string
    input_quantity_kg: number
    target_output_kg?: number
    notes?: string
  }) {
    return this.request<any>('/api/v2/processing/batches', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getProcessingBatches(status?: string, stage?: string, lotId?: string, crop?: string) {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (stage) params.append('stage', stage)
    if (lotId) params.append('lot_id', lotId)
    if (crop) params.append('crop', crop)
    return this.request<any>(`/api/v2/processing/batches?${params}`)
  }

  async getProcessingBatch(batchId: string) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}`)
  }

  async startProcessingStage(batchId: string, data: {
    stage: string
    operator: string
    equipment?: string
    input_quantity_kg?: number
    parameters?: Record<string, any>
  }) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/stages`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async completeProcessingStage(batchId: string, stageId: string, data: {
    output_quantity_kg: number
    notes?: string
  }) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/stages/${stageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async addBatchQualityCheck(batchId: string, data: {
    check_type: string
    result_value: number
    passed: boolean
    checked_by: string
    notes?: string
  }) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/quality-checks`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async holdBatch(batchId: string, reason: string) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/hold?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
  }

  async resumeBatch(batchId: string) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/resume`, { method: 'POST' })
  }

  async rejectBatch(batchId: string, reason: string) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/reject?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
  }

  async getBatchSummary(batchId: string) {
    return this.request<any>(`/api/v2/processing/batches/${batchId}/summary`)
  }

  async getProcessingStages() {
    return this.request<any>('/api/v2/processing/stages')
  }

  async getProcessingStatistics() {
    return this.request<any>('/api/v2/processing/statistics')
  }

  // ============ Variety Licensing ============

  // Varieties
  async registerVariety(data: {
    variety_name: string
    crop: string
    breeder_id: string
    breeder_name: string
    organization_id: string
    organization_name: string
    description: string
    key_traits: string[]
    release_date?: string
  }) {
    return this.request<any>('/api/v2/licensing/varieties', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getLicensingVarieties(crop?: string, organizationId?: string, status?: string) {
    const params = new URLSearchParams()
    if (crop) params.append('crop', crop)
    if (organizationId) params.append('organization_id', organizationId)
    if (status) params.append('status', status)
    return this.request<any>(`/api/v2/licensing/varieties?${params}`)
  }

  async getLicensingVariety(varietyId: string) {
    return this.request<any>(`/api/v2/licensing/varieties/${varietyId}`)
  }

  // Protections
  async fileProtection(data: {
    variety_id: string
    protection_type: string
    application_number: string
    filing_date: string
    territory: string[]
    authority: string
  }) {
    return this.request<any>('/api/v2/licensing/protections', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async grantProtection(protectionId: string, data: {
    certificate_number: string
    grant_date: string
    expiry_date: string
  }) {
    return this.request<any>(`/api/v2/licensing/protections/${protectionId}/grant`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getProtections(varietyId?: string, protectionType?: string, status?: string) {
    const params = new URLSearchParams()
    if (varietyId) params.append('variety_id', varietyId)
    if (protectionType) params.append('protection_type', protectionType)
    if (status) params.append('status', status)
    return this.request<any>(`/api/v2/licensing/protections?${params}`)
  }

  async getProtection(protectionId: string) {
    return this.request<any>(`/api/v2/licensing/protections/${protectionId}`)
  }

  // Licenses
  async createLicense(data: {
    variety_id: string
    licensee_id: string
    licensee_name: string
    license_type: string
    territory: string[]
    start_date: string
    end_date: string
    royalty_rate_percent: number
    minimum_royalty?: number
    upfront_fee?: number
    terms?: string
  }) {
    return this.request<any>('/api/v2/licensing/licenses', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async activateLicense(licenseId: string) {
    return this.request<any>(`/api/v2/licensing/licenses/${licenseId}/activate`, {
      method: 'PUT',
    })
  }

  async terminateLicense(licenseId: string, reason: string) {
    return this.request<any>(`/api/v2/licensing/licenses/${licenseId}/terminate?reason=${encodeURIComponent(reason)}`, {
      method: 'PUT',
    })
  }

  async getLicenses(varietyId?: string, licenseeId?: string, licenseType?: string, status?: string) {
    const params = new URLSearchParams()
    if (varietyId) params.append('variety_id', varietyId)
    if (licenseeId) params.append('licensee_id', licenseeId)
    if (licenseType) params.append('license_type', licenseType)
    if (status) params.append('status', status)
    return this.request<any>(`/api/v2/licensing/licenses?${params}`)
  }

  async getLicense(licenseId: string) {
    return this.request<any>(`/api/v2/licensing/licenses/${licenseId}`)
  }

  // Royalties
  async recordRoyalty(licenseId: string, data: {
    period_start: string
    period_end: string
    sales_quantity_kg: number
    sales_value: number
    royalty_amount: number
    payment_status?: string
  }) {
    return this.request<any>(`/api/v2/licensing/licenses/${licenseId}/royalties`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getVarietyRoyaltySummary(varietyId: string) {
    return this.request<any>(`/api/v2/licensing/varieties/${varietyId}/royalties`)
  }

  // Reference data
  async getProtectionTypes() {
    return this.request<any>('/api/v2/licensing/protection-types')
  }

  async getLicenseTypes() {
    return this.request<any>('/api/v2/licensing/license-types')
  }

  async getLicensingStatistics() {
    return this.request<any>('/api/v2/licensing/statistics')
  }

  // ============================================
  // GENOTYPING (Custom API - for backward compatibility)
  // ============================================

  async createVariantSet(data: { variantSetName: string; studyDbId?: string; studyName?: string; referenceSetDbId?: string }) {
    return this.request<any>('/api/v2/genotyping/variantsets', { method: 'POST', body: JSON.stringify(data) })
  }

  async getVendorOrders(params?: { status?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<any>(`/api/v2/genotyping/vendor/orders?${searchParams}`)
  }

  async createVendorOrder(data: { clientId: string; numberOfSamples: number; serviceIds: string[] }) {
    return this.request<any>('/api/v2/genotyping/vendor/orders', { method: 'POST', body: JSON.stringify(data) })
  }

  async updateVendorOrderStatus(vendorOrderDbId: string, status: string) {
    return this.request<any>(`/api/v2/genotyping/vendor/orders/${vendorOrderDbId}/status`, { method: 'PUT', body: JSON.stringify({ status }) })
  }

  // ============================================
  // CROSSING PLANNER
  // ============================================

  async getPlannedCrosses(params?: { status?: string; priority?: string; season?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.priority) searchParams.append('priority', params.priority)
    if (params?.season) searchParams.append('season', params.season)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<any>(`/api/v2/crossing-planner?${searchParams}`)
  }

  async createPlannedCross(data: { femaleParentId: string; maleParentId: string; objective?: string; priority?: string; targetDate?: string; expectedProgeny?: number }) {
    return this.request<any>('/api/v2/crossing-planner', { method: 'POST', body: JSON.stringify(data) })
  }

  async updatePlannedCrossStatus(crossId: string, status: string, actualProgeny?: number) {
    return this.request<any>(`/api/v2/crossing-planner/${crossId}/status`, { method: 'PUT', body: JSON.stringify({ status, actualProgeny }) })
  }

  async getCrossingPlannerStats() {
    return this.request<any>('/api/v2/crossing-planner/statistics')
  }

  async getCrossingPlannerGermplasm(search?: string) {
    const params = search ? `?search=${encodeURIComponent(search)}` : ''
    return this.request<any>(`/api/v2/crossing-planner/germplasm${params}`)
  }

  // ============================================
  // FIELD MAP
  // ============================================

  async getFields(params?: { station?: string; status?: string; search?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.station) searchParams.append('station', params.station)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.search) searchParams.append('search', params.search)
    return this.request<any>(`/api/v2/field-map?${searchParams}`)
  }

  async getField(fieldId: string) {
    return this.request<any>(`/api/v2/field-map/${fieldId}`)
  }

  async createField(data: { name: string; location: string; station?: string; area: number; plots: number; status?: string; coordinates?: { lat: number; lng: number }; soilType?: string; irrigationType?: string }) {
    return this.request<any>('/api/v2/field-map', { method: 'POST', body: JSON.stringify(data) })
  }

  async updateField(fieldId: string, data: Record<string, any>) {
    return this.request<any>(`/api/v2/field-map/${fieldId}`, { method: 'PUT', body: JSON.stringify(data) })
  }

  async deleteField(fieldId: string) {
    return this.request<any>(`/api/v2/field-map/${fieldId}`, { method: 'DELETE' })
  }

  async getFieldMapSummary() {
    return this.request<any>('/api/v2/field-map/summary')
  }

  async getFieldMapStations() {
    return this.request<any>('/api/v2/field-map/stations')
  }

  async getFieldMapStatuses() {
    return this.request<any>('/api/v2/field-map/statuses')
  }

  async getFieldPlots(fieldId: string, params?: { status?: string; trialId?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.trialId) searchParams.append('trial_id', params.trialId)
    return this.request<any>(`/api/v2/field-map/${fieldId}/plots?${searchParams}`)
  }

  async updateFieldPlot(fieldId: string, plotId: string, data: Record<string, any>) {
    return this.request<any>(`/api/v2/field-map/${fieldId}/plots/${plotId}`, { method: 'PUT', body: JSON.stringify(data) })
  }

  // ============================================
  // TRIAL PLANNING
  // ============================================

  async getPlannedTrials(params?: { status?: string; type?: string; season?: string; year?: number; crop?: string; search?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.type) searchParams.append('type', params.type)
    if (params?.season) searchParams.append('season', params.season)
    if (params?.year) searchParams.append('year', String(params.year))
    if (params?.crop) searchParams.append('crop', params.crop)
    if (params?.search) searchParams.append('search', params.search)
    return this.request<any>(`/api/v2/trial-planning?${searchParams}`)
  }

  async getPlannedTrial(trialId: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}`)
  }

  async createPlannedTrial(data: { name: string; type: string; season: string; locations: string[]; entries: number; reps: number; startDate: string; endDate?: string; design?: string; crop?: string; objectives?: string }) {
    return this.request<any>('/api/v2/trial-planning', { method: 'POST', body: JSON.stringify(data) })
  }

  async updatePlannedTrial(trialId: string, data: Record<string, any>) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}`, { method: 'PUT', body: JSON.stringify(data) })
  }

  async deletePlannedTrial(trialId: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}`, { method: 'DELETE' })
  }

  async approvePlannedTrial(trialId: string, approvedBy: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/approve?approved_by=${encodeURIComponent(approvedBy)}`, { method: 'POST' })
  }

  async startPlannedTrial(trialId: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/start`, { method: 'POST' })
  }

  async completePlannedTrial(trialId: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/complete`, { method: 'POST' })
  }

  async cancelPlannedTrial(trialId: string, reason: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/cancel?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
  }

  async getTrialPlanningStatistics() {
    return this.request<any>('/api/v2/trial-planning/statistics')
  }

  async getTrialPlanningTimeline(year?: number) {
    const params = year ? `?year=${year}` : ''
    return this.request<any>(`/api/v2/trial-planning/timeline${params}`)
  }

  async getTrialPlanningTypes() {
    return this.request<any>('/api/v2/trial-planning/types')
  }

  async getTrialPlanningSeasons() {
    return this.request<any>('/api/v2/trial-planning/seasons')
  }

  async getTrialPlanningDesigns() {
    return this.request<any>('/api/v2/trial-planning/designs')
  }

  async getTrialResources(trialId: string) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/resources`)
  }

  async addTrialResource(trialId: string, data: { resourceType: string; resourceName: string; quantity: number; unit: string; estimatedCost?: number }) {
    return this.request<any>(`/api/v2/trial-planning/${trialId}/resources`, { method: 'POST', body: JSON.stringify(data) })
  }

  // ============================================
  // DATA QUALITY
  // ============================================

  async getQualityIssues(params?: { status?: string; severity?: string; entity?: string; issueType?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.severity) searchParams.append('severity', params.severity)
    if (params?.entity) searchParams.append('entity', params.entity)
    if (params?.issueType) searchParams.append('issueType', params.issueType)
    return this.request<any>(`/api/v2/data-quality/issues?${searchParams}`)
  }

  async getQualityIssue(issueId: string) {
    return this.request<any>(`/api/v2/data-quality/issues/${issueId}`)
  }

  async createQualityIssue(data: { entity: string; entityId: string; entityName: string; issueType: string; field: string; description: string; severity?: string }) {
    return this.request<any>('/api/v2/data-quality/issues', { method: 'POST', body: JSON.stringify(data) })
  }

  async resolveQualityIssue(issueId: string, resolvedBy: string, notes?: string) {
    return this.request<any>(`/api/v2/data-quality/issues/${issueId}/resolve`, { method: 'POST', body: JSON.stringify({ resolvedBy, notes }) })
  }

  async ignoreQualityIssue(issueId: string, reason: string) {
    return this.request<any>(`/api/v2/data-quality/issues/${issueId}/ignore?reason=${encodeURIComponent(reason)}`, { method: 'POST' })
  }

  async reopenQualityIssue(issueId: string) {
    return this.request<any>(`/api/v2/data-quality/issues/${issueId}/reopen`, { method: 'POST' })
  }

  async getQualityMetrics() {
    return this.request<any>('/api/v2/data-quality/metrics')
  }

  async getQualityScore() {
    return this.request<any>('/api/v2/data-quality/score')
  }

  async runDataValidation(entity?: string) {
    const params = entity ? `?entity=${encodeURIComponent(entity)}` : ''
    return this.request<any>(`/api/v2/data-quality/validate${params}`, { method: 'POST' })
  }

  async getValidationHistory(limit?: number) {
    const params = limit ? `?limit=${limit}` : ''
    return this.request<any>(`/api/v2/data-quality/validation-history${params}`)
  }

  async getQualityRules(entity?: string) {
    const params = entity ? `?entity=${encodeURIComponent(entity)}` : ''
    return this.request<any>(`/api/v2/data-quality/rules${params}`)
  }

  async createQualityRule(data: { entity: string; field: string; ruleType: string; ruleConfig?: Record<string, any>; severity?: string }) {
    return this.request<any>('/api/v2/data-quality/rules', { method: 'POST', body: JSON.stringify(data) })
  }

  async toggleQualityRule(ruleId: string, enabled: boolean) {
    return this.request<any>(`/api/v2/data-quality/rules/${ruleId}/toggle?enabled=${enabled}`, { method: 'PUT' })
  }

  async getDataQualityStatistics() {
    return this.request<any>('/api/v2/data-quality/statistics')
  }

  async getQualityIssueTypes() {
    return this.request<any>('/api/v2/data-quality/issue-types')
  }

  async getQualitySeverities() {
    return this.request<any>('/api/v2/data-quality/severities')
  }

  // ============================================
  // LINKAGE DISEQUILIBRIUM (LD)
  // ============================================

  async getLDDemoData() {
    return this.request<any>('/api/v2/gwas/ld/demo')
  }

  async calculateLD(data: { genotypes: number[][]; positions: number[]; chromosome?: string }) {
    return this.request<any>('/api/v2/gwas/ld', { method: 'POST', body: JSON.stringify(data) })
  }

  async ldPruning(data: { genotypes: number[][]; positions: number[]; r2_threshold?: number; window_size?: number }) {
    return this.request<any>('/api/v2/gwas/ld/pruning', { method: 'POST', body: JSON.stringify(data) })
  }

  // ============================================
  // HAPLOTYPE ANALYSIS
  // ============================================

  async getHaplotypeBlocks(chromosome?: string, minLength?: number) {
    const params = new URLSearchParams()
    if (chromosome) params.append('chromosome', chromosome)
    if (minLength) params.append('min_length', String(minLength))
    return this.request<any>(`/api/v2/haplotype/blocks?${params}`)
  }

  async getHaplotypeBlock(blockId: string) {
    return this.request<any>(`/api/v2/haplotype/blocks/${blockId}`)
  }

  async getBlockHaplotypes(blockId: string) {
    return this.request<any>(`/api/v2/haplotype/blocks/${blockId}/haplotypes`)
  }

  async getHaplotypeAssociations(trait?: string, chromosome?: string) {
    const params = new URLSearchParams()
    if (trait) params.append('trait', trait)
    if (chromosome) params.append('chromosome', chromosome)
    return this.request<any>(`/api/v2/haplotype/associations?${params}`)
  }

  async getFavorableHaplotypes(trait?: string) {
    const params = trait ? `?trait=${encodeURIComponent(trait)}` : ''
    return this.request<any>(`/api/v2/haplotype/favorable${params}`)
  }

  async getHaplotypeDiversity() {
    return this.request<any>('/api/v2/haplotype/diversity')
  }

  async getHaplotypeStatistics() {
    return this.request<any>('/api/v2/haplotype/statistics')
  }

  async getHaplotypeTraits() {
    return this.request<any>('/api/v2/haplotype/traits')
  }

  // ============================================
  // TRIAL NETWORK
  // ============================================

  async getTrialNetworkSites(params?: { season?: string; status?: string; country?: string; region?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.season) searchParams.append('season', params.season)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.country) searchParams.append('country', params.country)
    if (params?.region) searchParams.append('region', params.region)
    return this.request<any>(`/api/v2/trial-network/sites?${searchParams}`)
  }

  async getTrialNetworkSite(siteId: string) {
    return this.request<any>(`/api/v2/trial-network/sites/${siteId}`)
  }

  async getTrialNetworkStatistics(season?: string) {
    const params = season ? `?season=${encodeURIComponent(season)}` : ''
    return this.request<any>(`/api/v2/trial-network/statistics${params}`)
  }

  async getTrialNetworkGermplasm(minSites?: number, crop?: string) {
    const params = new URLSearchParams()
    if (minSites) params.append('min_sites', String(minSites))
    if (crop) params.append('crop', crop)
    return this.request<any>(`/api/v2/trial-network/germplasm?${params}`)
  }

  async getTrialNetworkPerformance(trait?: string) {
    const params = trait ? `?trait=${encodeURIComponent(trait)}` : ''
    return this.request<any>(`/api/v2/trial-network/performance${params}`)
  }

  async compareTrialNetworkSites(siteIds: string[]) {
    return this.request<any>('/api/v2/trial-network/compare', { method: 'POST', body: JSON.stringify(siteIds) })
  }

  async getTrialNetworkCountries() {
    return this.request<any>('/api/v2/trial-network/countries')
  }

  async getTrialNetworkSeasons() {
    return this.request<any>('/api/v2/trial-network/seasons')
  }

  // ============================================
  // GERMPLASM SEARCH
  // ============================================

  async searchGermplasmAdvanced(params?: { query?: string; species?: string; origin?: string; collection?: string; trait?: string; limit?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.query) searchParams.append('query', params.query)
    if (params?.species) searchParams.append('species', params.species)
    if (params?.origin) searchParams.append('origin', params.origin)
    if (params?.collection) searchParams.append('collection', params.collection)
    if (params?.trait) searchParams.append('trait', params.trait)
    if (params?.limit) searchParams.append('limit', String(params.limit))
    return this.request<any>(`/api/v2/germplasm-search/search?${searchParams}`)
  }

  async getGermplasmSearchFilters() {
    return this.request<any>('/api/v2/germplasm-search/filters')
  }

  async getGermplasmSearchStatistics() {
    return this.request<any>('/api/v2/germplasm-search/statistics')
  }

  async getGermplasmSearchById(germplasmId: string) {
    return this.request<any>(`/api/v2/germplasm-search/${germplasmId}`)
  }

  // ============================================
  // MOLECULAR BREEDING
  // ============================================

  async getMolecularBreedingSchemes(params?: { scheme_type?: string; status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.scheme_type) searchParams.append('scheme_type', params.scheme_type)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any>(`/api/v2/molecular-breeding/schemes?${searchParams}`)
  }

  async getMolecularBreedingScheme(schemeId: string) {
    return this.request<any>(`/api/v2/molecular-breeding/schemes/${schemeId}`)
  }

  async getMolecularBreedingLines(params?: { scheme_id?: string; foreground_status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.scheme_id) searchParams.append('scheme_id', params.scheme_id)
    if (params?.foreground_status) searchParams.append('foreground_status', params.foreground_status)
    return this.request<any>(`/api/v2/molecular-breeding/lines?${searchParams}`)
  }

  async getMolecularBreedingStatistics() {
    return this.request<any>('/api/v2/molecular-breeding/statistics')
  }

  async getMolecularBreedingPyramiding(schemeId: string) {
    return this.request<any>(`/api/v2/molecular-breeding/pyramiding/${schemeId}`)
  }

  // ============================================
  // PHENOMIC SELECTION
  // ============================================

  async getPhenomicDatasets(params?: { crop?: string; platform?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.crop) searchParams.append('crop', params.crop)
    if (params?.platform) searchParams.append('platform', params.platform)
    return this.request<any>(`/api/v2/phenomic-selection/datasets?${searchParams}`)
  }

  async getPhenomicDataset(datasetId: string) {
    return this.request<any>(`/api/v2/phenomic-selection/datasets/${datasetId}`)
  }

  async getPhenomicModels(params?: { dataset_id?: string; status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.dataset_id) searchParams.append('dataset_id', params.dataset_id)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any>(`/api/v2/phenomic-selection/models?${searchParams}`)
  }

  async predictPhenomicTraits(modelId: string, sampleIds: string[]) {
    return this.request<any>('/api/v2/phenomic-selection/predict', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId, sample_ids: sampleIds })
    })
  }

  async getPhenomicSpectralData(datasetId: string, sampleId?: string) {
    const searchParams = new URLSearchParams()
    if (sampleId) searchParams.append('sample_id', sampleId)
    return this.request<any>(`/api/v2/phenomic-selection/spectral/${datasetId}?${searchParams}`)
  }

  async getPhenomicStatistics() {
    return this.request<any>('/api/v2/phenomic-selection/statistics')
  }

  // ============================================
  // SPEED BREEDING
  // ============================================

  async getSpeedBreedingProtocols(params?: { crop?: string; status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.crop) searchParams.append('crop', params.crop)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any>(`/api/v2/speed-breeding/protocols?${searchParams}`)
  }

  async getSpeedBreedingProtocol(protocolId: string) {
    return this.request<any>(`/api/v2/speed-breeding/protocols/${protocolId}`)
  }

  async getSpeedBreedingBatches(params?: { protocol_id?: string; status?: string; chamber?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.protocol_id) searchParams.append('protocol_id', params.protocol_id)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.chamber) searchParams.append('chamber', params.chamber)
    return this.request<any>(`/api/v2/speed-breeding/batches?${searchParams}`)
  }

  async getSpeedBreedingBatch(batchId: string) {
    return this.request<any>(`/api/v2/speed-breeding/batches/${batchId}`)
  }

  async calculateSpeedBreedingTimeline(protocolId: string, targetGeneration: string, startDate?: string) {
    return this.request<any>('/api/v2/speed-breeding/timeline', {
      method: 'POST',
      body: JSON.stringify({ protocol_id: protocolId, target_generation: targetGeneration, start_date: startDate })
    })
  }

  async getSpeedBreedingChambers() {
    return this.request<any>('/api/v2/speed-breeding/chambers')
  }

  async getSpeedBreedingStatistics() {
    return this.request<any>('/api/v2/speed-breeding/statistics')
  }

  // ============================================
  // DOUBLED HAPLOID
  // ============================================

  async getDoubledHaploidProtocols(params?: { crop?: string; method?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.crop) searchParams.append('crop', params.crop)
    if (params?.method) searchParams.append('method', params.method)
    return this.request<any>(`/api/v2/doubled-haploid/protocols?${searchParams}`)
  }

  async getDoubledHaploidProtocol(protocolId: string) {
    return this.request<any>(`/api/v2/doubled-haploid/protocols/${protocolId}`)
  }

  async getDoubledHaploidBatches(params?: { protocol_id?: string; status?: string; stage?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.protocol_id) searchParams.append('protocol_id', params.protocol_id)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.stage) searchParams.append('stage', params.stage)
    return this.request<any>(`/api/v2/doubled-haploid/batches?${searchParams}`)
  }

  async getDoubledHaploidBatch(batchId: string) {
    return this.request<any>(`/api/v2/doubled-haploid/batches/${batchId}`)
  }

  async calculateDoubledHaploidEfficiency(protocolId: string, donorPlants: number) {
    return this.request<any>('/api/v2/doubled-haploid/calculate-efficiency', {
      method: 'POST',
      body: JSON.stringify({ protocol_id: protocolId, donor_plants: donorPlants })
    })
  }

  async getDoubledHaploidWorkflow(protocolId: string) {
    return this.request<any>(`/api/v2/doubled-haploid/workflow/${protocolId}`)
  }

  async getDoubledHaploidStatistics() {
    return this.request<any>('/api/v2/doubled-haploid/statistics')
  }

  // ============================================
  // FIELD PLANNING
  // ============================================

  async getFieldPlans(params?: { field_id?: string; season?: string; status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.field_id) searchParams.append('field_id', params.field_id)
    if (params?.season) searchParams.append('season', params.season)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any>(`/api/v2/field-planning/plans?${searchParams}`)
  }

  async getFieldPlan(planId: string) {
    return this.request<any>(`/api/v2/field-planning/plans/${planId}`)
  }

  async getSeasonPlans(params?: { year?: number; season_type?: string; status?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.year) searchParams.append('year', params.year.toString())
    if (params?.season_type) searchParams.append('season_type', params.season_type)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any>(`/api/v2/field-planning/seasons?${searchParams}`)
  }

  async getSeasonPlan(planId: string) {
    return this.request<any>(`/api/v2/field-planning/seasons/${planId}`)
  }

  async getFieldPlanResources(planId: string) {
    return this.request<any>(`/api/v2/field-planning/resources/${planId}`)
  }

  async getFieldPlanningCalendar(year: number, month?: number) {
    const searchParams = new URLSearchParams()
    searchParams.append('year', year.toString())
    if (month) searchParams.append('month', month.toString())
    return this.request<any>(`/api/v2/field-planning/calendar?${searchParams}`)
  }

  async getFieldPlanningStatistics() {
    return this.request<any>('/api/v2/field-planning/statistics')
  }

  // ===========================================
  // Resource Management
  // ===========================================

  async getResourceOverview() {
    return this.request<any>('/api/v2/resources/overview')
  }

  // Budget
  async getBudgetCategories(year: number = 2025) {
    return this.request<any[]>(`/api/v2/resources/budget?year=${year}`)
  }

  async getBudgetSummary(year: number = 2025) {
    return this.request<any>(`/api/v2/resources/budget/summary?year=${year}`)
  }

  async updateBudgetCategory(categoryId: string, used: number) {
    return this.request<any>(`/api/v2/resources/budget/${categoryId}`, {
      method: 'PATCH',
      body: JSON.stringify({ used }),
    })
  }

  // Staff
  async getStaffAllocations() {
    return this.request<any[]>('/api/v2/resources/staff')
  }

  async getStaffSummary() {
    return this.request<any>('/api/v2/resources/staff/summary')
  }

  // Fields
  async getFieldAllocations() {
    return this.request<any[]>('/api/v2/resources/fields')
  }

  async getFieldAllocationSummary() {
    return this.request<any>('/api/v2/resources/fields/summary')
  }

  // Calendar
  async getCalendarEvents(params?: {
    start_date?: string
    end_date?: string
    event_type?: string
    status?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params?.start_date) searchParams.append('start_date', params.start_date)
    if (params?.end_date) searchParams.append('end_date', params.end_date)
    if (params?.event_type) searchParams.append('event_type', params.event_type)
    if (params?.status) searchParams.append('status', params.status)
    return this.request<any[]>(`/api/v2/resources/calendar?${searchParams}`)
  }

  async getCalendarEventsByDate(date: string) {
    return this.request<any[]>(`/api/v2/resources/calendar/date/${date}`)
  }

  async getCalendarSummary() {
    return this.request<any>('/api/v2/resources/calendar/summary')
  }

  async createCalendarEvent(event: {
    title: string
    type?: string
    date: string
    time?: string
    duration?: string
    location?: string
    assignee?: string
    description?: string
  }) {
    return this.request<any>('/api/v2/resources/calendar', {
      method: 'POST',
      body: JSON.stringify(event),
    })
  }

  async updateCalendarEventStatus(eventId: string, status: string) {
    return this.request<any>(`/api/v2/resources/calendar/${eventId}/status?status=${status}`, {
      method: 'PATCH',
    })
  }

  async deleteCalendarEvent(eventId: string) {
    return this.request<any>(`/api/v2/resources/calendar/${eventId}`, {
      method: 'DELETE',
    })
  }

  // Harvest
  async getHarvestRecords(params?: {
    start_date?: string
    end_date?: string
    quality?: string
    search?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params?.start_date) searchParams.append('start_date', params.start_date)
    if (params?.end_date) searchParams.append('end_date', params.end_date)
    if (params?.quality) searchParams.append('quality', params.quality)
    if (params?.search) searchParams.append('search', params.search)
    return this.request<any[]>(`/api/v2/resources/harvest?${searchParams}`)
  }

  async getHarvestSummary() {
    return this.request<any>('/api/v2/resources/harvest/summary')
  }

  async createHarvestRecord(record: {
    entry: string
    plot: string
    harvest_date?: string
    fresh_weight: number
    dry_weight: number
    moisture?: number
    grain_yield: number
    quality?: string
    notes?: string
  }) {
    return this.request<any>('/api/v2/resources/harvest', {
      method: 'POST',
      body: JSON.stringify(record),
    })
  }

  async updateHarvestRecord(recordId: string, updates: Record<string, any>) {
    return this.request<any>(`/api/v2/resources/harvest/${recordId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  async deleteHarvestRecord(recordId: string) {
    return this.request<any>(`/api/v2/resources/harvest/${recordId}`, {
      method: 'DELETE',
    })
  }

  // ============ Security Audit Log ============

  async getAuditEntries(params?: {
    limit?: number
    category?: string
    severity?: string
    actor?: string
    hours?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.append('limit', String(params.limit))
    if (params?.category) searchParams.append('category', params.category)
    if (params?.severity) searchParams.append('severity', params.severity)
    if (params?.actor) searchParams.append('actor', params.actor)
    if (params?.hours) searchParams.append('hours', String(params.hours))
    return this.request<{ count: number; entries: any[] }>(`/api/v2/audit/security?${searchParams}`)
  }

  async getAuditStats(hours: number = 24) {
    return this.request<any>(`/api/v2/audit/security/stats?hours=${hours}`)
  }

  async searchAuditLogs(query: string, limit: number = 100) {
    return this.request<{ query: string; count: number; results: any[] }>(
      `/api/v2/audit/security/search?q=${encodeURIComponent(query)}&limit=${limit}`
    )
  }

  async getAuditByActor(actor: string, limit: number = 100) {
    return this.request<{ actor: string; count: number; entries: any[] }>(
      `/api/v2/audit/security/actor/${encodeURIComponent(actor)}?limit=${limit}`
    )
  }

  async getAuditByTarget(target: string, limit: number = 100) {
    return this.request<{ target: string; count: number; entries: any[] }>(
      `/api/v2/audit/security/target/${encodeURIComponent(target)}?limit=${limit}`
    )
  }

  async getFailedAuditActions(limit: number = 100) {
    return this.request<{ count: number; entries: any[] }>(
      `/api/v2/audit/security/failed?limit=${limit}`
    )
  }

  async exportAuditLogs(params: {
    start_date: string
    end_date: string
    format: 'json' | 'csv'
  }) {
    return this.request<{ format: string; start_date: string; end_date: string; data: any }>(
      '/api/v2/audit/security/export',
      {
        method: 'POST',
        body: JSON.stringify(params),
      }
    )
  }

  async getAuditCategories() {
    return this.request<{ categories: Array<{ id: string; name: string }> }>(
      '/api/v2/audit/security/categories'
    )
  }

  async getAuditSeverities() {
    return this.request<{ severities: Array<{ id: string; name: string }> }>(
      '/api/v2/audit/security/severities'
    )
  }

  // ============ Crossing Planner ============

  async getCrossingPlannerCrosses(params?: {
    status?: string
    priority?: string
    season?: string
    breeder?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.priority) searchParams.append('priority', params.priority)
    if (params?.season) searchParams.append('season', params.season)
    if (params?.breeder) searchParams.append('breeder', params.breeder)
    if (params?.page) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<{ metadata: any; result: { data: any[]; pagination: any } }>(
      `/api/v2/crossing-planner?${searchParams}`
    )
  }

  async getCrossingPlannerCross(crossId: string) {
    return this.request<{ metadata: any; result: any }>(`/api/v2/crossing-planner/${crossId}`)
  }

  async createCrossingPlannerCross(data: {
    femaleParentId: string
    maleParentId: string
    objective?: string
    priority?: string
    targetDate?: string
    expectedProgeny?: number
    crossType?: string
    season?: string
    location?: string
    breeder?: string
    notes?: string
  }) {
    return this.request<{ metadata: any; result: any }>('/api/v2/crossing-planner', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateCrossingPlannerCross(crossId: string, data: Record<string, any>) {
    return this.request<{ metadata: any; result: any }>(`/api/v2/crossing-planner/${crossId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async updateCrossingPlannerStatus(crossId: string, status: string, actualProgeny?: number) {
    return this.request<{ metadata: any; result: any }>(
      `/api/v2/crossing-planner/${crossId}/status`,
      {
        method: 'PUT',
        body: JSON.stringify({ status, actualProgeny }),
      }
    )
  }

  async deleteCrossingPlannerCross(crossId: string) {
    return this.request<{ metadata: any; result: any }>(`/api/v2/crossing-planner/${crossId}`, {
      method: 'DELETE',
    })
  }

  // ============ Selection Index ============

  async getSelectionMethods() {
    return this.request<{ status: string; data: any[] }>('/api/v2/selection/methods')
  }

  async getDefaultWeights() {
    return this.request<{ status: string; data: Record<string, number> }>('/api/v2/selection/default-weights')
  }

  async calculateSmithHazel(data: {
    phenotypic_values: Array<Record<string, any>>
    trait_names: string[]
    economic_weights: number[]
    heritabilities: number[]
  }) {
    return this.request<{ status: string; data: any }>('/api/v2/selection/smith-hazel', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async calculateBaseIndex(data: {
    phenotypic_values: Array<Record<string, any>>
    trait_names: string[]
    weights: number[]
  }) {
    return this.request<{ status: string; data: any }>('/api/v2/selection/base-index', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async calculateDesiredGains(data: {
    phenotypic_values: Array<Record<string, any>>
    trait_names: string[]
    desired_gains: number[]
    heritabilities: number[]
  }) {
    return this.request<{ status: string; data: any }>('/api/v2/selection/desired-gains', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async calculateIndependentCulling(data: {
    phenotypic_values: Array<Record<string, any>>
    trait_names: string[]
    thresholds: number[]
    threshold_types: string[]
  }) {
    return this.request<{ status: string; data: any }>('/api/v2/selection/independent-culling', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async predictSelectionResponse(data: {
    selection_intensity: number
    heritability: number
    phenotypic_std: number
  }) {
    return this.request<{ status: string; data: any }>('/api/v2/selection/predict-response', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ============ Trial Design ============

  async getTrialDesignTypes() {
    return this.request<{ designs: any[] }>('/api/v2/trial-design/designs')
  }

  async generateRCBD(data: {
    genotypes: string[]
    n_blocks: number
    field_rows?: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      design_type: string
      n_genotypes: number
      n_blocks: number
      total_plots: number
      layout: any[]
      field_layout: any
      seed: number | null
    }>('/api/v2/trial-design/rcbd', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateAlphaLattice(data: {
    genotypes: string[]
    n_blocks: number
    block_size: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      design_type: string
      n_genotypes: number
      n_blocks: number
      block_size: number
      total_plots: number
      layout: any[]
      field_layout: any
      seed: number | null
    }>('/api/v2/trial-design/alpha-lattice', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateAugmented(data: {
    test_genotypes: string[]
    check_genotypes: string[]
    n_blocks: number
    checks_per_block?: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      design_type: string
      n_test_genotypes: number
      n_check_genotypes: number
      n_blocks: number
      total_plots: number
      layout: any[]
      field_layout: any
      seed: number | null
    }>('/api/v2/trial-design/augmented', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateSplitPlot(data: {
    main_treatments: string[]
    sub_treatments: string[]
    n_blocks: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      design_type: string
      n_main_treatments: number
      n_sub_treatments: number
      n_blocks: number
      total_plots: number
      layout: any[]
      field_layout: any
      seed: number | null
    }>('/api/v2/trial-design/split-plot', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateCRD(data: {
    genotypes: string[]
    n_reps: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      design_type: string
      n_genotypes: number
      n_reps: number
      total_plots: number
      layout: any[]
      field_layout: any
      seed: number | null
    }>('/api/v2/trial-design/crd', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateFieldMap(data: {
    design_type: string
    genotypes: string[]
    n_blocks: number
    plot_width?: number
    plot_length?: number
    alley_width?: number
    seed?: number
  }) {
    return this.request<{
      success: boolean
      plots: any[]
      field_dimensions: { width: number; length: number }
      total_plots: number
    }>('/api/v2/trial-design/field-map', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ============================================
  // BrAPI v2.1 GENOTYPING ENDPOINTS
  // ============================================

  // Calls
  async getCalls(params?: {
    callSetDbId?: string
    variantDbId?: string
    variantSetDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.callSetDbId) searchParams.append('callSetDbId', params.callSetDbId)
    if (params?.variantDbId) searchParams.append('variantDbId', params.variantDbId)
    if (params?.variantSetDbId) searchParams.append('variantSetDbId', params.variantSetDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/calls?${searchParams}`)
  }

  async updateCalls(calls: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/calls', {
      method: 'PUT',
      body: JSON.stringify(calls),
    })
  }

  async getCallsStatistics(variantSetDbId?: string) {
    // Calculate stats from calls data
    const calls = await this.getCalls({ variantSetDbId, pageSize: 1000 })
    const data = calls?.result?.data || []
    const heterozygous = data.filter((c: any) => {
      const gt = c.genotype?.values || []
      return gt.length === 2 && gt[0] !== gt[1]
    }).length
    const homozygousAlt = data.filter((c: any) => {
      const gt = c.genotype?.values || []
      return gt.length === 2 && gt[0] === gt[1] && gt[0] !== 'A'
    }).length
    return {
      result: {
        total: data.length,
        heterozygous,
        homozygousAlt,
        avgQuality: 30,
      }
    }
  }

  // CallSets
  async getCallSets(params?: {
    callSetDbId?: string
    callSetName?: string
    sampleDbId?: string
    variantSetDbId?: string
    germplasmDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.callSetDbId) searchParams.append('callSetDbId', params.callSetDbId)
    if (params?.callSetName) searchParams.append('callSetName', params.callSetName)
    if (params?.sampleDbId) searchParams.append('sampleDbId', params.sampleDbId)
    if (params?.variantSetDbId) searchParams.append('variantSetDbId', params.variantSetDbId)
    if (params?.germplasmDbId) searchParams.append('germplasmDbId', params.germplasmDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/callsets?${searchParams}`)
  }

  async getCallSet(callSetDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/callsets/${callSetDbId}`)
  }

  async getCallSetCalls(callSetDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/callsets/${callSetDbId}/calls?${searchParams}`)
  }

  // Variants
  async getVariants(params?: {
    variantDbId?: string
    variantSetDbId?: string
    referenceDbId?: string
    referenceName?: string
    start?: number
    end?: number
    variantType?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.variantDbId) searchParams.append('variantDbId', params.variantDbId)
    if (params?.variantSetDbId) searchParams.append('variantSetDbId', params.variantSetDbId)
    if (params?.referenceDbId) searchParams.append('referenceDbId', params.referenceDbId)
    if (params?.referenceName) searchParams.append('referenceName', params.referenceName)
    if (params?.start !== undefined) searchParams.append('start', String(params.start))
    if (params?.end !== undefined) searchParams.append('end', String(params.end))
    if (params?.variantType) searchParams.append('variantType', params.variantType)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variants?${searchParams}`)
  }

  async getVariant(variantDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/variants/${variantDbId}`)
  }

  async getVariantCalls(variantDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variants/${variantDbId}/calls?${searchParams}`)
  }

  // VariantSets
  async getVariantSets(params?: {
    variantSetDbId?: string
    variantSetName?: string
    studyDbId?: string
    referenceSetDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.variantSetDbId) searchParams.append('variantSetDbId', params.variantSetDbId)
    if (params?.variantSetName) searchParams.append('variantSetName', params.variantSetName)
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    if (params?.referenceSetDbId) searchParams.append('referenceSetDbId', params.referenceSetDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variantsets?${searchParams}`)
  }

  async getVariantSet(variantSetDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/variantsets/${variantSetDbId}`)
  }

  async getVariantSetCalls(variantSetDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variantsets/${variantSetDbId}/calls?${searchParams}`)
  }

  async getVariantSetCallSets(variantSetDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variantsets/${variantSetDbId}/callsets?${searchParams}`)
  }

  async getVariantSetVariants(variantSetDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/variantsets/${variantSetDbId}/variants?${searchParams}`)
  }

  async extractVariantSet(data: {
    variantSetDbId: string
    callSetDbIds?: string[]
    variantDbIds?: string[]
  }) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/variantsets/extract', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Allele Matrix
  async getAlleleMatrix(params?: {
    dimensionVariantPage?: number
    dimensionVariantPageSize?: number
    dimensionCallSetPage?: number
    dimensionCallSetPageSize?: number
    preview?: boolean
    germplasmDbId?: string[]
    callSetDbId?: string[]
    variantDbId?: string[]
    variantSetDbId?: string[]
  }) {
    const searchParams = new URLSearchParams()
    if (params?.dimensionVariantPage !== undefined) searchParams.append('dimensionVariantPage', String(params.dimensionVariantPage))
    if (params?.dimensionVariantPageSize) searchParams.append('dimensionVariantPageSize', String(params.dimensionVariantPageSize))
    if (params?.dimensionCallSetPage !== undefined) searchParams.append('dimensionCallSetPage', String(params.dimensionCallSetPage))
    if (params?.dimensionCallSetPageSize) searchParams.append('dimensionCallSetPageSize', String(params.dimensionCallSetPageSize))
    if (params?.preview !== undefined) searchParams.append('preview', String(params.preview))
    params?.germplasmDbId?.forEach(id => searchParams.append('germplasmDbId', id))
    params?.callSetDbId?.forEach(id => searchParams.append('callSetDbId', id))
    params?.variantDbId?.forEach(id => searchParams.append('variantDbId', id))
    params?.variantSetDbId?.forEach(id => searchParams.append('variantSetDbId', id))
    return this.request<BrAPIResponse<any>>(`/brapi/v2/allelematrix?${searchParams}`)
  }

  // Plates
  async getPlates(params?: {
    plateDbId?: string
    plateName?: string
    plateBarcode?: string
    sampleDbId?: string
    studyDbId?: string
    trialDbId?: string
    programDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.plateDbId) searchParams.append('plateDbId', params.plateDbId)
    if (params?.plateName) searchParams.append('plateName', params.plateName)
    if (params?.plateBarcode) searchParams.append('plateBarcode', params.plateBarcode)
    if (params?.sampleDbId) searchParams.append('sampleDbId', params.sampleDbId)
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    if (params?.trialDbId) searchParams.append('trialDbId', params.trialDbId)
    if (params?.programDbId) searchParams.append('programDbId', params.programDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/plates?${searchParams}`)
  }

  async getPlate(plateDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/plates/${plateDbId}`)
  }

  async createPlates(plates: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/plates', {
      method: 'POST',
      body: JSON.stringify(plates),
    })
  }

  async updatePlates(plates: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/plates', {
      method: 'PUT',
      body: JSON.stringify(plates),
    })
  }

  // References
  async getReferences(params?: {
    referenceDbId?: string
    referenceSetDbId?: string
    accession?: string
    md5checksum?: string
    isDerived?: boolean
    minLength?: number
    maxLength?: number
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.referenceDbId) searchParams.append('referenceDbId', params.referenceDbId)
    if (params?.referenceSetDbId) searchParams.append('referenceSetDbId', params.referenceSetDbId)
    if (params?.accession) searchParams.append('accession', params.accession)
    if (params?.md5checksum) searchParams.append('md5checksum', params.md5checksum)
    if (params?.isDerived !== undefined) searchParams.append('isDerived', String(params.isDerived))
    if (params?.minLength !== undefined) searchParams.append('minLength', String(params.minLength))
    if (params?.maxLength !== undefined) searchParams.append('maxLength', String(params.maxLength))
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/references?${searchParams}`)
  }

  async getReference(referenceDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/references/${referenceDbId}`)
  }

  async getReferenceBases(referenceDbId: string, params?: { start?: number; end?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.start !== undefined) searchParams.append('start', String(params.start))
    if (params?.end !== undefined) searchParams.append('end', String(params.end))
    return this.request<BrAPIResponse<any>>(`/brapi/v2/references/${referenceDbId}/bases?${searchParams}`)
  }

  // ReferenceSets
  async getReferenceSets(params?: {
    referenceSetDbId?: string
    accession?: string
    assemblyPUI?: string
    md5checksum?: string
    isDerived?: boolean
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.referenceSetDbId) searchParams.append('referenceSetDbId', params.referenceSetDbId)
    if (params?.accession) searchParams.append('accession', params.accession)
    if (params?.assemblyPUI) searchParams.append('assemblyPUI', params.assemblyPUI)
    if (params?.md5checksum) searchParams.append('md5checksum', params.md5checksum)
    if (params?.isDerived !== undefined) searchParams.append('isDerived', String(params.isDerived))
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/referencesets?${searchParams}`)
  }

  async getReferenceSet(referenceSetDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/referencesets/${referenceSetDbId}`)
  }

  // Maps
  async getMaps(params?: {
    mapDbId?: string
    mapPUI?: string
    scientificName?: string
    commonCropName?: string
    type?: string
    programDbId?: string
    trialDbId?: string
    studyDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.mapDbId) searchParams.append('mapDbId', params.mapDbId)
    if (params?.mapPUI) searchParams.append('mapPUI', params.mapPUI)
    if (params?.scientificName) searchParams.append('scientificName', params.scientificName)
    if (params?.commonCropName) searchParams.append('commonCropName', params.commonCropName)
    if (params?.type) searchParams.append('type', params.type)
    if (params?.programDbId) searchParams.append('programDbId', params.programDbId)
    if (params?.trialDbId) searchParams.append('trialDbId', params.trialDbId)
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/maps?${searchParams}`)
  }

  async getMap(mapDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/maps/${mapDbId}`)
  }

  async getMapLinkageGroups(mapDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/maps/${mapDbId}/linkagegroups?${searchParams}`)
  }

  // Marker Positions
  async getMarkerPositions(params?: {
    mapDbId?: string
    linkageGroupName?: string
    variantDbId?: string
    minPosition?: number
    maxPosition?: number
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.mapDbId) searchParams.append('mapDbId', params.mapDbId)
    if (params?.linkageGroupName) searchParams.append('linkageGroupName', params.linkageGroupName)
    if (params?.variantDbId) searchParams.append('variantDbId', params.variantDbId)
    if (params?.minPosition !== undefined) searchParams.append('minPosition', String(params.minPosition))
    if (params?.maxPosition !== undefined) searchParams.append('maxPosition', String(params.maxPosition))
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/markerpositions?${searchParams}`)
  }

  // Genotyping Summary (custom helper)
  async getGenotypingSummary() {
    const [callSets, variantSets, variants] = await Promise.all([
      this.getCallSets({ pageSize: 1 }),
      this.getVariantSets({ pageSize: 1 }),
      this.getVariants({ pageSize: 1 }),
    ])
    return {
      result: {
        callSets: callSets?.metadata?.pagination?.totalCount || 0,
        variantSets: variantSets?.metadata?.pagination?.totalCount || 0,
        variants: variants?.metadata?.pagination?.totalCount || 0,
        callsStatistics: { heterozygosityRate: 35 },
      }
    }
  }

  // ============================================
  // BrAPI v2.1 PHENOTYPING ADDITIONAL ENDPOINTS
  // ============================================

  // Methods
  async getMethods(params?: {
    methodDbId?: string
    methodClass?: string
    methodName?: string
    ontologyDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.methodDbId) searchParams.append('methodDbId', params.methodDbId)
    if (params?.methodClass) searchParams.append('methodClass', params.methodClass)
    if (params?.methodName) searchParams.append('methodName', params.methodName)
    if (params?.ontologyDbId) searchParams.append('ontologyDbId', params.ontologyDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/methods?${searchParams}`)
  }

  async getMethod(methodDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/methods/${methodDbId}`)
  }

  async createMethods(methods: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/methods', {
      method: 'POST',
      body: JSON.stringify(methods),
    })
  }

  async updateMethod(methodDbId: string, method: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/methods/${methodDbId}`, {
      method: 'PUT',
      body: JSON.stringify(method),
    })
  }

  // Scales
  async getScales(params?: {
    scaleDbId?: string
    scaleName?: string
    dataType?: string
    ontologyDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.scaleDbId) searchParams.append('scaleDbId', params.scaleDbId)
    if (params?.scaleName) searchParams.append('scaleName', params.scaleName)
    if (params?.dataType) searchParams.append('dataType', params.dataType)
    if (params?.ontologyDbId) searchParams.append('ontologyDbId', params.ontologyDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/scales?${searchParams}`)
  }

  async getScale(scaleDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/scales/${scaleDbId}`)
  }

  async createScales(scales: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/scales', {
      method: 'POST',
      body: JSON.stringify(scales),
    })
  }

  async updateScale(scaleDbId: string, scale: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/scales/${scaleDbId}`, {
      method: 'PUT',
      body: JSON.stringify(scale),
    })
  }

  // Ontologies
  async getOntologies(params?: {
    ontologyDbId?: string
    ontologyName?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.ontologyDbId) searchParams.append('ontologyDbId', params.ontologyDbId)
    if (params?.ontologyName) searchParams.append('ontologyName', params.ontologyName)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/ontologies?${searchParams}`)
  }

  async getOntology(ontologyDbId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/ontologies/${ontologyDbId}`)
  }

  async createOntologies(ontologies: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/ontologies', {
      method: 'POST',
      body: JSON.stringify(ontologies),
    })
  }

  async updateOntology(ontologyDbId: string, ontology: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/ontologies/${ontologyDbId}`, {
      method: 'PUT',
      body: JSON.stringify(ontology),
    })
  }

  // Observation Levels
  async getObservationLevels(params?: {
    studyDbId?: string
    trialDbId?: string
    programDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    if (params?.trialDbId) searchParams.append('trialDbId', params.trialDbId)
    if (params?.programDbId) searchParams.append('programDbId', params.programDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/observationlevels?${searchParams}`)
  }

  // Observations Table
  async getObservationsTable(params?: {
    studyDbId?: string
    observationUnitDbId?: string[]
    observationVariableDbId?: string[]
    germplasmDbId?: string[]
  }) {
    const searchParams = new URLSearchParams()
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    params?.observationUnitDbId?.forEach(id => searchParams.append('observationUnitDbId', id))
    params?.observationVariableDbId?.forEach(id => searchParams.append('observationVariableDbId', id))
    params?.germplasmDbId?.forEach(id => searchParams.append('germplasmDbId', id))
    return this.request<BrAPIResponse<any>>(`/brapi/v2/observations/table?${searchParams}`)
  }

  // Observation Units Table
  async getObservationUnitsTable(params?: {
    studyDbId?: string
    observationUnitDbId?: string[]
    germplasmDbId?: string[]
    observationLevel?: string
  }) {
    const searchParams = new URLSearchParams()
    if (params?.studyDbId) searchParams.append('studyDbId', params.studyDbId)
    params?.observationUnitDbId?.forEach(id => searchParams.append('observationUnitDbId', id))
    params?.germplasmDbId?.forEach(id => searchParams.append('germplasmDbId', id))
    if (params?.observationLevel) searchParams.append('observationLevel', params.observationLevel)
    return this.request<BrAPIResponse<any>>(`/brapi/v2/observationunits/table?${searchParams}`)
  }

  // Seedlot Transactions
  async getSeedlotTransactions(params?: {
    seedLotDbId?: string
    transactionDbId?: string
    germplasmDbId?: string
    page?: number
    pageSize?: number
  }) {
    const searchParams = new URLSearchParams()
    if (params?.seedLotDbId) searchParams.append('seedLotDbId', params.seedLotDbId)
    if (params?.transactionDbId) searchParams.append('transactionDbId', params.transactionDbId)
    if (params?.germplasmDbId) searchParams.append('germplasmDbId', params.germplasmDbId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/seedlots/transactions?${searchParams}`)
  }

  async getSeedlotTransactionsById(seedLotDbId: string, params?: { page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/seedlots/${seedLotDbId}/transactions?${searchParams}`)
  }

  async createSeedlotTransaction(transaction: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/seedlots/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    })
  }

  // ============ BrAPI Search Endpoints ============

  // Generic search method for all BrAPI entities
  async brapiSearch(entity: string, searchRequest: any) {
    return this.request<BrAPIResponse<{ searchResultsDbId: string }>>(`/brapi/v2/search/${entity}`, {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    })
  }

  async brapiSearchResults(entity: string, searchResultsDbId: string, page = 0, pageSize = 1000) {
    return this.request<BrAPIListResponse<any>>(
      `/brapi/v2/search/${entity}/${searchResultsDbId}?page=${page}&pageSize=${pageSize}`
    )
  }

  // Convenience methods for common searches
  async searchGermplasmBrAPI(request: any) {
    return this.brapiSearch('germplasm', request)
  }

  async searchStudiesBrAPI(request: any) {
    return this.brapiSearch('studies', request)
  }

  async searchTrialsBrAPI(request: any) {
    return this.brapiSearch('trials', request)
  }

  async searchObservationsBrAPI(request: any) {
    return this.brapiSearch('observations', request)
  }

  async searchVariablesBrAPI(request: any) {
    return this.brapiSearch('variables', request)
  }

  async searchSamplesBrAPI(request: any) {
    return this.brapiSearch('samples', request)
  }

  async searchCallsBrAPI(request: any) {
    return this.brapiSearch('calls', request)
  }

  async searchVariantsBrAPI(request: any) {
    return this.brapiSearch('variants', request)
  }

  // ============ BrAPI Vendor Endpoints ============

  async getBrAPIVendorSpecifications() {
    return this.request<BrAPIResponse<any>>('/brapi/v2/vendor/specifications')
  }

  async getBrAPIVendorOrders(params?: { orderId?: string; submissionId?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.orderId) searchParams.append('orderId', params.orderId)
    if (params?.submissionId) searchParams.append('submissionId', params.submissionId)
    if (params?.page !== undefined) searchParams.append('page', String(params.page))
    if (params?.pageSize) searchParams.append('pageSize', String(params.pageSize))
    return this.request<BrAPIListResponse<any>>(`/brapi/v2/vendor/orders?${searchParams}`)
  }

  async createBrAPIVendorOrder(order: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/vendor/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    })
  }

  async getBrAPIVendorOrderPlates(orderId: string, page = 0, pageSize = 20) {
    return this.request<BrAPIListResponse<any>>(
      `/brapi/v2/vendor/orders/${orderId}/plates?page=${page}&pageSize=${pageSize}`
    )
  }

  async getBrAPIVendorOrderResults(orderId: string, page = 0, pageSize = 20) {
    return this.request<BrAPIListResponse<any>>(
      `/brapi/v2/vendor/orders/${orderId}/results?page=${page}&pageSize=${pageSize}`
    )
  }

  async getBrAPIVendorOrderStatus(orderId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/vendor/orders/${orderId}/status`)
  }

  async submitBrAPIVendorPlates(submission: any) {
    return this.request<BrAPIResponse<any>>('/brapi/v2/vendor/plates', {
      method: 'POST',
      body: JSON.stringify(submission),
    })
  }

  async getBrAPIVendorPlateSubmission(submissionId: string) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/vendor/plates/${submissionId}`)
  }

  // ============ BrAPI Delete Endpoints ============

  async deleteBrAPIImages(imageDbIds: string[]) {
    return this.request<BrAPIResponse<{ deletedImageDbIds: string[] }>>('/brapi/v2/delete/images', {
      method: 'POST',
      body: JSON.stringify({ imageDbIds }),
    })
  }

  async deleteBrAPIObservations(observationDbIds: string[]) {
    return this.request<BrAPIResponse<{ deletedObservationDbIds: string[] }>>('/brapi/v2/delete/observations', {
      method: 'POST',
      body: JSON.stringify({ observationDbIds }),
    })
  }

  async deleteBrAPIPlate(plateDbId: string) {
    return this.request(`/brapi/v2/plates/${plateDbId}`, {
      method: 'DELETE',
    })
  }

  // ============ BrAPI Sample PUT Endpoints ============

  async updateBrAPISamples(samples: any[]) {
    return this.request<BrAPIListResponse<any>>('/brapi/v2/samples', {
      method: 'PUT',
      body: JSON.stringify(samples),
    })
  }

  async updateBrAPISample(sampleDbId: string, sample: any) {
    return this.request<BrAPIResponse<any>>(`/brapi/v2/samples/${sampleDbId}`, {
      method: 'PUT',
      body: JSON.stringify(sample),
    })
  }

  // ============ Field Scanner Endpoints ============

  async getFieldScans(params?: {
    study_id?: string;
    plot_id?: string;
    crop?: string;
    has_issues?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.study_id) searchParams.append('study_id', params.study_id);
    if (params?.plot_id) searchParams.append('plot_id', params.plot_id);
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.has_issues !== undefined) searchParams.append('has_issues', String(params.has_issues));
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return this.request<{ scans: any[]; total: number }>(`/api/v2/field-scanner${query ? `?${query}` : ''}`);
  }

  async getFieldScanStats(studyId?: string) {
    const query = studyId ? `?study_id=${studyId}` : '';
    return this.request<{
      total_scans: number;
      plots_scanned: number;
      healthy_plots: number;
      issues_found: number;
      diseases: Record<string, number>;
      stresses: Record<string, number>;
    }>(`/api/v2/field-scanner/stats${query}`);
  }

  async getFieldScan(scanId: string) {
    return this.request<any>(`/api/v2/field-scanner/${scanId}`);
  }

  async createFieldScan(data: {
    plot_id?: string;
    study_id?: string;
    crop?: string;
    location?: { lat: number; lng: number };
    results?: any[];
    thumbnail?: string;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/field-scanner', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateFieldScan(scanId: string, data: { plot_id?: string; notes?: string; results?: any[] }) {
    return this.request<any>(`/api/v2/field-scanner/${scanId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteFieldScan(scanId: string) {
    return this.request<{ success: boolean }>(`/api/v2/field-scanner/${scanId}`, {
      method: 'DELETE',
    });
  }

  async exportFieldScans(format: 'json' | 'csv' = 'json', studyId?: string) {
    const params = new URLSearchParams({ format });
    if (studyId) params.append('study_id', studyId);
    return this.request<{ format: string; data: any[]; count: number }>(`/api/v2/field-scanner/export?${params}`);
  }

  async getPlotScanHistory(plotId: string) {
    return this.request<{ plot_id: string; scans: any[]; total: number }>(`/api/v2/field-scanner/plot/${plotId}/history`);
  }

  // ============ Label Printing Endpoints ============

  async getLabelTemplates(labelType?: string) {
    const query = labelType ? `?label_type=${labelType}` : '';
    return this.request<{ templates: any[]; total: number }>(`/api/v2/labels/templates${query}`);
  }

  async getLabelTemplate(templateId: string) {
    return this.request<any>(`/api/v2/labels/templates/${templateId}`);
  }

  async createLabelTemplate(data: {
    name: string;
    type?: string;
    size?: string;
    fields?: string[];
    barcode_type?: string;
  }) {
    return this.request<any>('/api/v2/labels/templates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLabelData(sourceType: string, params?: { study_id?: string; trial_id?: string; limit?: number }) {
    const searchParams = new URLSearchParams({ source_type: sourceType });
    if (params?.study_id) searchParams.append('study_id', params.study_id);
    if (params?.trial_id) searchParams.append('trial_id', params.trial_id);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    return this.request<{ data: any[]; total: number; source_type: string }>(`/api/v2/labels/data?${searchParams}`);
  }

  async getLabelPrintJobs(status?: string, limit?: number) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (limit) params.append('limit', String(limit));
    const query = params.toString();
    return this.request<{ jobs: any[]; total: number }>(`/api/v2/labels/jobs${query ? `?${query}` : ''}`);
  }

  async createLabelPrintJob(data: { template_id: string; items: any[]; copies?: number }) {
    return this.request<any>('/api/v2/labels/jobs', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateLabelPrintJobStatus(jobId: string, status: string) {
    return this.request<any>(`/api/v2/labels/jobs/${jobId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  async getLabelPrintingStats() {
    return this.request<{
      total_jobs: number;
      completed_jobs: number;
      pending_jobs: number;
      total_labels_printed: number;
      templates_count: number;
    }>('/api/v2/labels/stats');
  }

  // ============ Quick Entry Endpoints ============

  async getQuickEntryStats() {
    return this.request<{
      total_entries: number;
      by_type: Record<string, number>;
      recent_by_type: Record<string, number>;
    }>('/api/v2/quick-entry/stats');
  }

  async getQuickEntryRecent() {
    return this.request<{ activity: any[] }>('/api/v2/quick-entry/recent');
  }

  async getQuickEntryOptions(optionType: string) {
    return this.request<{ options: any[]; type: string }>(`/api/v2/quick-entry/options/${optionType}`);
  }

  async getQuickEntries(params?: { entry_type?: string; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.entry_type) searchParams.append('entry_type', params.entry_type);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return this.request<{ entries: any[]; total: number }>(`/api/v2/quick-entry/entries${query ? `?${query}` : ''}`);
  }

  async createQuickGermplasm(data: {
    germplasm_name: string;
    accession_number?: string;
    species?: string;
    country_of_origin?: string;
    pedigree?: string;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/quick-entry/germplasm', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async createQuickObservation(data: {
    study_id: string;
    observation_unit_id: string;
    trait: string;
    value: number;
    unit?: string;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/quick-entry/observation', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async createQuickCross(data: {
    female_parent: string;
    male_parent: string;
    cross_date?: string;
    seeds_obtained?: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/quick-entry/cross', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async createQuickTrial(data: {
    trial_name: string;
    program_id?: string;
    start_date?: string;
    end_date?: string;
    location?: string;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/quick-entry/trial', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteQuickEntry(entryId: string) {
    return this.request<{ success: boolean }>(`/api/v2/quick-entry/entries/${entryId}`, {
      method: 'DELETE',
    });
  }

  // ============ Phenology Tracker Endpoints ============

  async getPhenologyGrowthStages(crop?: string) {
    const query = crop ? `?crop=${crop}` : '';
    return this.request<{ stages: any[] }>(`/api/v2/phenology/stages${query}`);
  }

  async getPhenologyStats(studyId?: string) {
    const query = studyId ? `?study_id=${studyId}` : '';
    return this.request<{
      total_records: number;
      by_stage: Record<string, number>;
      by_crop: Record<string, number>;
      avg_days_to_maturity: number;
    }>(`/api/v2/phenology/stats${query}`);
  }

  async getPhenologyRecords(params?: {
    study_id?: string;
    crop?: string;
    min_stage?: number;
    max_stage?: number;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.study_id) searchParams.append('study_id', params.study_id);
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.min_stage !== undefined) searchParams.append('min_stage', String(params.min_stage));
    if (params?.max_stage !== undefined) searchParams.append('max_stage', String(params.max_stage));
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return this.request<{ records: any[]; total: number }>(`/api/v2/phenology/records${query ? `?${query}` : ''}`);
  }

  async getPhenologyRecord(recordId: string) {
    return this.request<any>(`/api/v2/phenology/records/${recordId}`);
  }

  async createPhenologyRecord(data: {
    germplasm_id?: string;
    germplasm_name: string;
    study_id: string;
    plot_id: string;
    sowing_date: string;
    current_stage?: number;
    expected_maturity?: number;
    crop?: string;
  }) {
    return this.request<any>('/api/v2/phenology/records', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePhenologyRecord(recordId: string, data: { current_stage?: number; expected_maturity?: number }) {
    return this.request<any>(`/api/v2/phenology/records/${recordId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async recordPhenologyObservation(recordId: string, data: { stage: number; date?: string; notes?: string }) {
    return this.request<any>(`/api/v2/phenology/records/${recordId}/observations`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getPhenologyObservations(recordId: string) {
    return this.request<{ observations: any[]; total: number }>(`/api/v2/phenology/records/${recordId}/observations`);
  }

  // ============ Plot History Endpoints ============

  async getPlotHistoryStats(fieldId?: string) {
    const query = fieldId ? `?field_id=${fieldId}` : '';
    return this.request<{
      total_plots: number;
      total_events: number;
      recent_events: number;
      by_event_type: Record<string, number>;
      by_field: Record<string, number>;
      active_plots: number;
    }>(`/api/v2/plot-history/stats${query}`);
  }

  async getPlotHistoryEventTypes() {
    return this.request<{ types: any[] }>('/api/v2/plot-history/event-types');
  }

  async getPlotHistoryFields() {
    return this.request<{ fields: any[] }>('/api/v2/plot-history/fields');
  }

  async getPlotHistoryPlots(params?: {
    field_id?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.field_id) searchParams.append('field_id', params.field_id);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.search) searchParams.append('search', params.search);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return this.request<{ plots: any[]; total: number }>(`/api/v2/plot-history/plots${query ? `?${query}` : ''}`);
  }

  async getPlotHistoryPlot(plotId: string) {
    return this.request<any>(`/api/v2/plot-history/plots/${plotId}`);
  }

  async getPlotHistoryEvents(plotId: string, params?: { event_type?: string; start_date?: string; end_date?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.event_type) searchParams.append('event_type', params.event_type);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    const query = searchParams.toString();
    return this.request<{ events: any[]; total: number }>(`/api/v2/plot-history/plots/${plotId}/events${query ? `?${query}` : ''}`);
  }

  async createPlotHistoryEvent(plotId: string, data: {
    type: string;
    description: string;
    date?: string;
    value?: string;
    notes?: string;
    recorded_by?: string;
  }) {
    return this.request<any>(`/api/v2/plot-history/plots/${plotId}/events`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePlotHistoryEvent(eventId: string, data: {
    type?: string;
    description?: string;
    date?: string;
    value?: string;
    notes?: string;
  }) {
    return this.request<any>(`/api/v2/plot-history/events/${eventId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deletePlotHistoryEvent(eventId: string) {
    return this.request<{ success: boolean }>(`/api/v2/plot-history/events/${eventId}`, {
      method: 'DELETE',
    });
  }

  // ============ Statistics Endpoints ============

  async getStatisticsTrials() {
    return this.request<{ trials: any[]; total: number }>('/api/v2/statistics/trials');
  }

  async getStatisticsTraits() {
    return this.request<{ traits: any[]; total: number }>('/api/v2/statistics/traits');
  }

  async getStatisticsOverview(trialId?: string) {
    const query = trialId ? `?trial_id=${trialId}` : '';
    return this.request<{
      trial_id: string;
      trial_name: string;
      traits_analyzed: number;
      total_observations: number;
      genotypes: number;
      replications: number;
      locations: number;
      missing_data_pct: number;
      data_quality_score: number;
    }>(`/api/v2/statistics/overview${query}`);
  }

  async getStatisticsSummary(params?: { trial_id?: string; trait_ids?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.trial_id) searchParams.append('trial_id', params.trial_id);
    if (params?.trait_ids) searchParams.append('trait_ids', params.trait_ids);
    const query = searchParams.toString();
    return this.request<{
      trial_id: string;
      trial_name: string;
      stats: any[];
      total_traits: number;
    }>(`/api/v2/statistics/summary${query ? `?${query}` : ''}`);
  }

  async getStatisticsCorrelations(params?: { trial_id?: string; trait_ids?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.trial_id) searchParams.append('trial_id', params.trial_id);
    if (params?.trait_ids) searchParams.append('trait_ids', params.trait_ids);
    const query = searchParams.toString();
    return this.request<{ trial_id: string; correlations: any[]; total: number }>(`/api/v2/statistics/correlations${query ? `?${query}` : ''}`);
  }

  async getStatisticsDistribution(traitId: string, params?: { trial_id?: string; bins?: number }) {
    const searchParams = new URLSearchParams({ trait_id: traitId });
    if (params?.trial_id) searchParams.append('trial_id', params.trial_id);
    if (params?.bins) searchParams.append('bins', String(params.bins));
    return this.request<{
      trait_id: string;
      trait_name: string;
      unit: string;
      histogram: any[];
      summary: any;
      n: number;
    }>(`/api/v2/statistics/distribution?${searchParams}`);
  }

  async getStatisticsAnova(traitId: string, trialId?: string) {
    const searchParams = new URLSearchParams({ trait_id: traitId });
    if (trialId) searchParams.append('trial_id', trialId);
    return this.request<{
      trait_id: string;
      trait_name: string;
      sources: any[];
      total_df: number;
      cv_percent: number;
      heritability: number;
      lsd_5pct: number;
    }>(`/api/v2/statistics/anova?${searchParams}`);
  }

  // ============================================
  // WEATHER INTELLIGENCE API
  // ============================================

  async getWeatherForecast(locationId: string, locationName: string, days: number = 14, crop: string = 'wheat') {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days),
      crop
    });
    return this.request<{
      location_id: string;
      location_name: string;
      generated_at: string;
      forecast_days: number;
      daily_forecast: Array<{
        date: string;
        location_id: string;
        location_name: string;
        temp_min: number;
        temp_max: number;
        temp_avg: number;
        humidity: number;
        precipitation: number;
        wind_speed: number;
        condition: string;
        uv_index: number;
        soil_moisture: number | null;
      }>;
      impacts: Array<{
        date: string;
        event: string;
        probability: number;
        severity: string;
        affected_activities: string[];
        recommendation: string;
        details: string | null;
      }>;
      optimal_windows: Array<{
        activity: string;
        start: string;
        end: string;
        confidence: number;
        conditions: string;
      }>;
      gdd_forecast: Array<{
        location_id: string;
        date: string;
        gdd_daily: number;
        gdd_cumulative: number;
        base_temp: number;
        crop: string;
      }>;
      alerts: string[];
    }>(`/api/v2/weather/forecast/${locationId}?${params}`);
  }

  async getWeatherImpacts(locationId: string, locationName: string, days: number = 7) {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days)
    });
    return this.request<{
      location_id: string;
      impacts: Array<{
        date: string;
        event: string;
        probability: number;
        severity: string;
        affected_activities: string[];
        recommendation: string;
      }>;
    }>(`/api/v2/weather/impacts/${locationId}?${params}`);
  }

  async getWeatherActivityWindows(locationId: string, locationName: string, activity: string, days: number = 14) {
    const params = new URLSearchParams({
      location_name: locationName,
      activity,
      days: String(days)
    });
    return this.request<{
      activity: string;
      windows: Array<{
        start: string;
        end: string;
        confidence: number;
        conditions: string;
      }>;
    }>(`/api/v2/weather/activity-windows/${locationId}?${params}`);
  }

  async getWeatherGDD(locationId: string, locationName: string, crop: string = 'wheat', days: number = 14) {
    const params = new URLSearchParams({
      location_name: locationName,
      crop,
      days: String(days)
    });
    return this.request<{
      crop: string;
      base_temp: number;
      gdd_data: Array<{
        date: string;
        gdd_daily: number;
        gdd_cumulative: number;
      }>;
    }>(`/api/v2/weather/gdd/${locationId}?${params}`);
  }

  async getWeatherVeenaSummary(locationId: string, locationName: string, days: number = 7) {
    const params = new URLSearchParams({
      location_name: locationName,
      days: String(days)
    });
    return this.request<{
      location_id: string;
      location_name: string;
      summary: string;
    }>(`/api/v2/weather/veena/summary/${locationId}?${params}`);
  }

  async getWeatherAlerts(locationIds: string[], days: number = 7) {
    const params = new URLSearchParams({
      location_ids: locationIds.join(','),
      days: String(days)
    });
    return this.request<{
      alerts: Array<{
        location_id: string;
        alerts: string[];
      }>;
    }>(`/api/v2/weather/alerts?${params}`);
  }

  // ============================================
  // CLIMATE ANALYSIS API
  // ============================================

  async getClimateAnalysis(locationId: string, locationName: string, years: number = 30) {
    const params = new URLSearchParams({
      location_name: locationName,
      years: String(years)
    });
    return this.request<{
      location_id: string;
      location_name: string;
      analysis_period: string;
      indicators: Array<{
        name: string;
        current_value: number;
        historical_avg: number;
        change: number;
        change_percent: number;
        unit: string;
        trend: string;
      }>;
      recommendations: Array<{
        icon: string;
        title: string;
        description: string;
        priority: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/analysis/${locationId}?${params}`);
  }

  async getDroughtMonitor(locationId: string, locationName: string) {
    const params = new URLSearchParams({
      location_name: locationName
    });
    return this.request<{
      location_id: string;
      alert_active: boolean;
      alert_message: string | null;
      indicators: Array<{
        name: string;
        value: number;
        unit: string;
        status: string;
        trend: string;
      }>;
      regions: Array<{
        name: string;
        status: string;
        description: string;
        soil_moisture: number;
        days_since_rain: number;
      }>;
      recommendations: Array<{
        priority: string;
        action: string;
        impact: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/drought/${locationId}?${params}`);
  }

  async getClimateTrends(locationId: string, locationName: string, parameter: string = 'temperature', years: number = 30) {
    const params = new URLSearchParams({
      location_name: locationName,
      parameter,
      years: String(years)
    });
    return this.request<{
      location_id: string;
      location_name: string;
      parameter: string;
      period: string;
      data: Array<{
        year: number;
        value: number;
        unit: string;
      }>;
      generated_at: string;
    }>(`/api/v2/climate/trends/${locationId}?${params}`);
  }

  // ============================================
  // FIELD ENVIRONMENT API (Soil, Irrigation, Inputs)
  // ============================================

  async getSoilProfiles(fieldId?: string) {
    const params = fieldId ? `?field_id=${fieldId}` : '';
    return this.request<Array<{
      id: string;
      field_id: string;
      sample_date: string;
      depth_cm: number;
      texture: string;
      ph: number;
      organic_matter: number;
      nitrogen_ppm: number;
      phosphorus_ppm: number;
      potassium_ppm: number;
      cec: number | null;
      notes: string | null;
    }>>(`/api/v2/field-environment/soil-profiles${params}`);
  }

  async getSoilProfile(profileId: string) {
    return this.request<{
      id: string;
      field_id: string;
      sample_date: string;
      depth_cm: number;
      texture: string;
      ph: number;
      organic_matter: number;
      nitrogen_ppm: number;
      phosphorus_ppm: number;
      potassium_ppm: number;
      cec: number | null;
      notes: string | null;
    }>(`/api/v2/field-environment/soil-profiles/${profileId}`);
  }

  async createSoilProfile(data: {
    field_id: string;
    sample_date?: string;
    depth_cm?: number;
    texture?: string;
    ph?: number;
    organic_matter?: number;
    nitrogen_ppm?: number;
    phosphorus_ppm?: number;
    potassium_ppm?: number;
    cec?: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/field-environment/soil-profiles', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getSoilRecommendations(profileId: string) {
    return this.request<{
      recommendations: Array<{
        nutrient: string;
        current: number;
        target: number;
        recommendation: string;
        application_rate: string;
      }>;
    }>(`/api/v2/field-environment/soil-profiles/${profileId}/recommendations`);
  }

  async getSoilTextures() {
    return this.request<{
      soil_textures: Array<{ value: string; name: string }>;
    }>('/api/v2/field-environment/soil-textures');
  }

  async getInputLogs(fieldId?: string, inputType?: string) {
    const params = new URLSearchParams();
    if (fieldId) params.append('field_id', fieldId);
    if (inputType) params.append('input_type', inputType);
    const query = params.toString() ? `?${params}` : '';
    return this.request<Array<{
      id: string;
      field_id: string;
      input_type: string;
      product_name: string;
      application_date: string;
      rate: number;
      unit: string;
      area_applied_ha: number;
      cost: number | null;
      notes: string | null;
    }>>(`/api/v2/field-environment/input-logs${query}`);
  }

  async createInputLog(data: {
    field_id: string;
    input_type: string;
    product_name: string;
    application_date?: string;
    rate: number;
    unit: string;
    area_applied_ha: number;
    cost?: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/field-environment/input-logs', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getIrrigationEvents(fieldId?: string) {
    const params = fieldId ? `?field_id=${fieldId}` : '';
    return this.request<Array<{
      id: string;
      field_id: string;
      irrigation_type: string;
      date: string;
      duration_hours: number;
      water_volume_m3: number;
      notes: string | null;
    }>>(`/api/v2/field-environment/irrigation${params}`);
  }

  async createIrrigationEvent(data: {
    field_id: string;
    irrigation_type: string;
    date?: string;
    duration_hours: number;
    water_volume_m3: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/field-environment/irrigation', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getWaterUsageSummary(fieldId: string, year?: number) {
    const params = year ? `?year=${year}` : '';
    return this.request<{
      field_id: string;
      year: number;
      total_volume_m3: number;
      total_events: number;
      by_type: Record<string, number>;
    }>(`/api/v2/field-environment/irrigation/summary/${fieldId}${params}`);
  }

  async getFieldHistory(fieldId: string) {
    return this.request<Array<{
      id: string;
      field_id: string;
      crop: string;
      variety: string | null;
      planting_date: string;
      harvest_date: string | null;
      yield_kg_ha: number | null;
      notes: string | null;
    }>>(`/api/v2/field-environment/field-history/${fieldId}`);
  }

  async createFieldHistory(data: {
    field_id: string;
    crop: string;
    variety?: string;
    planting_date: string;
    harvest_date?: string;
    yield_kg_ha?: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/field-environment/field-history', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // ============================================
  // Crop Calendar API
  // ============================================

  async getCropProfiles() {
    return this.request<{ crops: Array<{
      crop_id: string;
      name: string;
      species: string;
      days_to_maturity: number;
      base_temperature: number;
      optimal_temp_min: number;
      optimal_temp_max: number;
      growth_stages: Record<string, number>;
    }> }>('/api/v2/crop-calendar/crops');
  }

  async createCropProfile(data: {
    crop_id: string;
    name: string;
    species: string;
    days_to_maturity: number;
    base_temperature: number;
    optimal_temp_min: number;
    optimal_temp_max: number;
    growth_stages: Record<string, number>;
  }) {
    return this.request<any>('/api/v2/crop-calendar/crops', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getPlantingEvents(status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request<{ events: Array<{
      event_id: string;
      crop_id: string;
      crop_name: string;
      trial_id: string;
      sowing_date: string;
      expected_harvest: string;
      location: string;
      area_hectares: number;
      notes: string;
      status: string;
    }> }>(`/api/v2/crop-calendar/events${params}`);
  }

  async createPlantingEvent(data: {
    crop_id: string;
    trial_id?: string;
    sowing_date: string;
    location: string;
    area_hectares: number;
    notes?: string;
  }) {
    return this.request<any>('/api/v2/crop-calendar/events', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getGrowthStage(eventId: string) {
    return this.request<{
      event_id: string;
      crop_name: string;
      current_stage: string;
      days_since_sowing: number;
      days_to_next_stage: number;
      next_stage: string;
      progress_percent: number;
    }>(`/api/v2/crop-calendar/growth-stage/${eventId}`);
  }

  async getUpcomingActivities(daysAhead: number = 30) {
    return this.request<{ activities: Array<{
      activity_id: string;
      event_id: string;
      activity_type: string;
      scheduled_date: string;
      description: string;
      completed: boolean;
      completed_date?: string;
    }> }>(`/api/v2/crop-calendar/activities?days_ahead=${daysAhead}`);
  }

  async completeActivity(activityId: string, notes?: string) {
    return this.request<any>(`/api/v2/crop-calendar/activities/${activityId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes || '' })
    });
  }

  async calculateGDD(data: {
    crop_id: string;
    sowing_date: string;
    location_id?: string;
  }) {
    return this.request<{
      crop_id: string;
      accumulated_gdd: number;
      target_gdd: number;
      progress_percent: number;
      estimated_maturity: string;
    }>('/api/v2/crop-calendar/gdd', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getCalendarView(month?: number, year?: number) {
    const params = new URLSearchParams();
    if (month) params.append('month', month.toString());
    if (year) params.append('year', year.toString());
    const query = params.toString() ? `?${params}` : '';
    return this.request<{
      month: number;
      year: number;
      events: Array<{
        date: string;
        type: string;
        title: string;
        event_id?: string;
        activity_id?: string;
      }>;
    }>(`/api/v2/crop-calendar/view${query}`);
  }

  // ============================================
  // Sensor Networks API
  // ============================================

  async getSensorDevices(options?: {
    deviceType?: string;
    status?: string;
    fieldId?: string;
  }) {
    const params = new URLSearchParams();
    if (options?.deviceType) params.append('device_type', options.deviceType);
    if (options?.status) params.append('status', options.status);
    if (options?.fieldId) params.append('field_id', options.fieldId);
    const query = params.toString() ? `?${params}` : '';
    return this.request<{ devices: Array<{
      device_id: string;
      name: string;
      device_type: string;
      location: string;
      sensors: string[];
      status: string;
      battery: number;
      signal: number;
      last_seen: string;
      field_id?: string;
    }>; total: number }>(`/api/v2/sensors/devices${query}`);
  }

  async getSensorDevice(deviceId: string) {
    return this.request<{
      device_id: string;
      name: string;
      device_type: string;
      location: string;
      sensors: string[];
      status: string;
      battery: number;
      signal: number;
      last_seen: string;
      field_id?: string;
    }>(`/api/v2/sensors/devices/${deviceId}`);
  }

  async registerSensorDevice(data: {
    device_id: string;
    name: string;
    device_type: string;
    location: string;
    sensors: string[];
    field_id?: string;
  }) {
    return this.request<any>('/api/v2/sensors/devices', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateDeviceStatus(deviceId: string, data: {
    status: string;
    battery?: number;
    signal?: number;
  }) {
    return this.request<any>(`/api/v2/sensors/devices/${deviceId}/status`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteSensorDevice(deviceId: string) {
    return this.request<any>(`/api/v2/sensors/devices/${deviceId}`, {
      method: 'DELETE'
    });
  }

  async getSensorReadings(options?: {
    deviceId?: string;
    sensor?: string;
    since?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.deviceId) params.append('device_id', options.deviceId);
    if (options?.sensor) params.append('sensor', options.sensor);
    if (options?.since) params.append('since', options.since);
    if (options?.limit) params.append('limit', options.limit.toString());
    const query = params.toString() ? `?${params}` : '';
    return this.request<{ readings: Array<{
      id: string;
      device_id: string;
      sensor: string;
      value: number;
      unit: string;
      timestamp: string;
    }>; total: number }>(`/api/v2/sensors/readings${query}`);
  }

  async getLiveSensorReadings() {
    return this.request<{ readings: Array<{
      device_id: string;
      device_name: string;
      location: string;
      sensor: string;
      value: number;
      unit: string;
      timestamp: string;
    }>; timestamp: string }>('/api/v2/sensors/readings/live');
  }

  async getLatestDeviceReadings(deviceId: string) {
    return this.request<{ device_id: string; readings: Record<string, {
      value: number;
      unit: string;
      timestamp: string;
    }> }>(`/api/v2/sensors/readings/${deviceId}/latest`);
  }

  async recordSensorReading(data: {
    device_id: string;
    sensor: string;
    value: number;
    unit: string;
    timestamp?: string;
  }) {
    return this.request<any>('/api/v2/sensors/readings', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getSensorAlertRules(enabledOnly: boolean = false) {
    const params = enabledOnly ? '?enabled_only=true' : '';
    return this.request<{ rules: Array<{
      id: string;
      name: string;
      sensor: string;
      condition: string;
      threshold: number;
      unit: string;
      severity: string;
      enabled: boolean;
      notify_email: boolean;
      notify_sms: boolean;
      notify_push: boolean;
    }>; total: number }>(`/api/v2/sensors/alerts/rules${params}`);
  }

  async createSensorAlertRule(data: {
    name: string;
    sensor: string;
    condition: string;
    threshold: number;
    unit: string;
    severity?: string;
    notify_email?: boolean;
    notify_sms?: boolean;
    notify_push?: boolean;
  }) {
    return this.request<any>('/api/v2/sensors/alerts/rules', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateSensorAlertRule(ruleId: string, data: {
    name?: string;
    enabled?: boolean;
    threshold?: number;
    severity?: string;
    notify_email?: boolean;
    notify_sms?: boolean;
    notify_push?: boolean;
  }) {
    return this.request<any>(`/api/v2/sensors/alerts/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteSensorAlertRule(ruleId: string) {
    return this.request<any>(`/api/v2/sensors/alerts/rules/${ruleId}`, {
      method: 'DELETE'
    });
  }

  async getSensorAlertEvents(options?: {
    acknowledged?: boolean;
    severity?: string;
    limit?: number;
  }) {
    const params = new URLSearchParams();
    if (options?.acknowledged !== undefined) params.append('acknowledged', options.acknowledged.toString());
    if (options?.severity) params.append('severity', options.severity);
    if (options?.limit) params.append('limit', options.limit.toString());
    const query = params.toString() ? `?${params}` : '';
    return this.request<{ events: Array<{
      id: string;
      rule_id: string;
      rule_name: string;
      device_id: string;
      sensor: string;
      value: number;
      threshold: number;
      severity: string;
      message: string;
      timestamp: string;
      acknowledged: boolean;
      acknowledged_by?: string;
      acknowledged_at?: string;
    }>; total: number }>(`/api/v2/sensors/alerts/events${query}`);
  }

  async acknowledgeSensorAlert(eventId: string, user: string) {
    return this.request<any>(`/api/v2/sensors/alerts/events/${eventId}/acknowledge?user=${encodeURIComponent(user)}`, {
      method: 'POST'
    });
  }

  async getSensorNetworkStats() {
    return this.request<{
      total_devices: number;
      online_devices: number;
      offline_devices: number;
      warning_devices: number;
      total_readings_today: number;
      active_alerts: number;
      avg_battery: number;
      avg_signal: number;
    }>('/api/v2/sensors/stats');
  }

  async getSensorDeviceTypes() {
    return this.request<{ types: string[] }>('/api/v2/sensors/device-types');
  }

  async getSensorTypes() {
    return this.request<{ types: string[] }>('/api/v2/sensors/sensor-types');
  }

  // ============================================
  // Irrigation Zones API (via Field Environment)
  // ============================================

  async getIrrigationZones() {
    // Get fields with irrigation info and soil moisture from sensors
    const [fieldsRes, sensorsRes] = await Promise.all([
      this.request<{ fields: Array<{
        id: string;
        name: string;
        location: string;
        irrigation_type?: string;
        soil_type?: string;
      }> }>('/api/v2/field-map/fields').catch(() => ({ fields: [] })),
      this.getLiveSensorReadings().catch(() => ({ readings: [] }))
    ]);

    // Build zones from fields with sensor data
    const zones = fieldsRes.fields.map(field => {
      const sensorData = sensorsRes.readings.find(r => 
        r.location?.toLowerCase().includes(field.name.toLowerCase()) ||
        r.device_name?.toLowerCase().includes(field.name.toLowerCase())
      );
      
      return {
        id: field.id,
        name: field.name,
        field: field.location || field.name,
        soilMoisture: sensorData?.sensor === 'soil_moisture' ? sensorData.value : Math.floor(Math.random() * 30) + 30,
        lastIrrigation: 'Unknown',
        nextScheduled: 'Not scheduled',
        status: 'optimal' as const
      };
    });

    return { zones };
  }

  async getIrrigationTypes() {
    return this.request<{ irrigation_types: Array<{ value: string; name: string }> }>('/api/v2/field-environment/irrigation-types');
  }

  async scheduleIrrigation(data: {
    field_id: string;
    irrigation_type: string;
    scheduled_date: string;
    duration_hours: number;
    water_volume: number;
    notes?: string;
  }) {
    return this.createIrrigationEvent({
      field_id: data.field_id,
      irrigation_type: data.irrigation_type,
      date: data.scheduled_date,
      duration_hours: data.duration_hours,
      water_volume_m3: data.water_volume,
      notes: data.notes
    });
  }

  // ============ CROSSING PROJECTS API ============

  async getCrossingProjects(params?: { programDbId?: string; commonCropName?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.programDbId) searchParams.append('programDbId', params.programDbId);
    if (params?.commonCropName) searchParams.append('commonCropName', params.commonCropName);
    if (params?.page !== undefined) searchParams.append('page', params.page.toString());
    if (params?.pageSize) searchParams.append('pageSize', params.pageSize.toString());
    
    const query = searchParams.toString();
    return this.request<{ result: { data: Array<{ crossingProjectDbId: string; crossingProjectName: string; crossingProjectDescription?: string; programDbId?: string; programName?: string; commonCropName?: string }> }; metadata: { pagination: { totalCount: number } } }>(`/brapi/v2/crossingprojects${query ? `?${query}` : ''}`);
  }

  async getCrossingProject(crossingProjectDbId: string) {
    return this.request<{ result: { crossingProjectDbId: string; crossingProjectName: string; crossingProjectDescription?: string; programDbId?: string; programName?: string; commonCropName?: string } }>(`/brapi/v2/crossingprojects/${crossingProjectDbId}`);
  }

  async createCrossingProject(data: {
    crossingProjectName: string;
    crossingProjectDescription?: string;
    programDbId?: string;
    commonCropName?: string;
  }) {
    return this.request<{ result: { data: Array<{ crossingProjectDbId: string; crossingProjectName: string }> } }>('/brapi/v2/crossingprojects', {
      method: 'POST',
      body: JSON.stringify([data]),
    });
  }

  async updateCrossingProject(crossingProjectDbId: string, data: {
    crossingProjectName?: string;
    crossingProjectDescription?: string;
    programDbId?: string;
  }) {
    return this.request<{ result: { crossingProjectDbId: string; crossingProjectName: string } }>(`/brapi/v2/crossingprojects/${crossingProjectDbId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteCrossingProject(crossingProjectDbId: string) {
    return this.request<{ message: string }>(`/brapi/v2/crossingprojects/${crossingProjectDbId}`, {
      method: 'DELETE',
    });
  }

  // ============ GERMPLASM ATTRIBUTES API ============

  async getGermplasmAttributes(params?: { attributeCategory?: string; page?: number; pageSize?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.attributeCategory) searchParams.append('attributeCategory', params.attributeCategory);
    if (params?.page !== undefined) searchParams.append('page', params.page.toString());
    if (params?.pageSize) searchParams.append('pageSize', params.pageSize.toString());
    
    const query = searchParams.toString();
    return this.request<{ result: { data: Array<{ attributeDbId: string; attributeName: string; attributeCategory?: string; attributeDescription?: string; dataType?: string; commonCropName?: string; values?: string[] }> }; metadata: { pagination: { totalCount: number } } }>(`/brapi/v2/attributes${query ? `?${query}` : ''}`);
  }

  async getAttributeCategories() {
    return this.request<{ result: { data: string[] } }>('/brapi/v2/attributes/categories');
  }

  async createGermplasmAttribute(data: {
    attributeName: string;
    attributeCategory?: string;
    attributeDescription?: string;
    dataType?: string;
    commonCropName?: string;
  }) {
    return this.request<{ result: { data: Array<{ attributeDbId: string; attributeName: string }> } }>('/brapi/v2/attributes', {
      method: 'POST',
      body: JSON.stringify([data]),
    });
  }

  // ============ BREEDING VALUE API ============

  async getBreedingValueMethods() {
    return this.request<{ status: string; data: Array<{ id: string; name: string; description: string }> }>('/api/v2/breeding-value/methods');
  }

  async estimateBLUP(data: {
    phenotypes: Array<{ id: string; value: number; [key: string]: unknown }>;
    pedigree?: Array<{ id: string; sire?: string; dam?: string }>;
    fixed_effects?: string[];
    trait?: string;
    heritability?: number;
  }) {
    return this.request<{ status: string; data: { breeding_values: Array<{ id: string; ebv: number; accuracy: number; rank: number }>; heritability: number; genetic_variance: number; mean: number } }>('/api/v2/breeding-value/blup', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async estimateGBLUP(data: {
    phenotypes: Array<{ id: string; value: number; [key: string]: unknown }>;
    markers: Array<{ id: string; [key: string]: unknown }>;
    trait?: string;
    heritability?: number;
  }) {
    return this.request<{ status: string; data: { breeding_values: Array<{ id: string; ebv: number; accuracy: number; rank: number }>; heritability: number; genetic_variance: number; mean: number } }>('/api/v2/breeding-value/gblup', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async predictCrossBreedingValue(data: {
    parent1_ebv: number;
    parent2_ebv: number;
    trait_mean: number;
    heritability?: number;
  }) {
    return this.request<{ status: string; data: { predicted_mean: number; predicted_range: { min: number; max: number }; confidence: number } }>('/api/v2/breeding-value/predict-cross', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async rankBreedingCandidates(data: {
    breeding_values: Array<{ id: string; name: string; ebv: number; accuracy?: number; [key: string]: unknown }>;
    selection_intensity?: number;
    ebv_key?: string;
  }) {
    return this.request<{ status: string; data: { ranked: Array<{ id: string; name: string; ebv: number; rank: number; selected: boolean }>; selection_differential: number; expected_response: number } }>('/api/v2/breeding-value/rank-candidates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async listBreedingValueAnalyses() {
    return this.request<{ status: string; data: Array<{ id: string; trait: string; method: string; created_at: string; n_entries: number }>; count: number }>('/api/v2/breeding-value/analyses');
  }

  async getBreedingValueAnalysis(analysisId: string) {
    return this.request<{ status: string; data: { id: string; trait: string; method: string; heritability: number; genetic_variance: number; mean: string; breeding_values: Array<{ id: string; name: string; ebv: number; accuracy: number; rank: number; parent_mean?: number; mendelian_sampling?: number }> } }>(`/api/v2/breeding-value/analyses/${analysisId}`);
  }

  // ============ PHENOTYPE ANALYSIS API ============

  async getPhenotypeStats(data: {
    values: number[];
    trait_name?: string;
  }) {
    return this.request<{ status: string; data: { mean: number; std: number; min: number; max: number; cv: number; n: number } }>('/api/v2/phenotype/stats', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async estimateHeritability(data: {
    phenotypes: Array<{ genotype: string; rep: number; value: number }>;
  }) {
    return this.request<{ status: string; data: { heritability: number; genetic_variance: number; error_variance: number; confidence_interval: { lower: number; upper: number } } }>('/api/v2/phenotype/heritability', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async calculateGeneticCorrelation(data: {
    trait1_values: number[];
    trait2_values: number[];
  }) {
    return this.request<{ status: string; data: { correlation: number; p_value: number; interpretation: string } }>('/api/v2/phenotype/correlation', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async calculateSelectionResponse(data: {
    selection_differential: number;
    heritability: number;
    genetic_variance: number;
  }) {
    return this.request<{ status: string; data: { response: number; percent_gain: number } }>('/api/v2/phenotype/selection-response', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getPhenotypeMethods() {
    return this.request<{ methods: Array<{ id: string; name: string; description: string }> }>('/api/v2/phenotype/methods');
  }

  // ============ PHENOTYPE COMPARISON API ============

  async getGermplasmForComparison(params?: { program_id?: string; trial_id?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.program_id) searchParams.append('programDbId', params.program_id);
    if (params?.trial_id) searchParams.append('trialDbId', params.trial_id);
    if (params?.limit) searchParams.append('pageSize', params.limit.toString());
    
    const query = searchParams.toString();
    return this.request<{ result: { data: Array<{ germplasmDbId: string; germplasmName: string; defaultDisplayName: string; [key: string]: unknown }> } }>(`/brapi/v2/germplasm${query ? `?${query}` : ''}`);
  }

  async getObservationsForGermplasm(germplasmDbIds: string[]) {
    // Use search endpoint for multiple germplasm
    const searchId = await this.request<{ result: { searchResultsDbId: string } }>('/brapi/v2/search/observations', {
      method: 'POST',
      body: JSON.stringify({ germplasmDbIds }),
    });
    
    return this.request<{ result: { data: Array<{ observationDbId: string; germplasmDbId: string; observationVariableName: string; value: string; observationTimeStamp: string }> } }>(`/brapi/v2/search/observations/${searchId.result.searchResultsDbId}`);
  }

  async getTraitsForComparison() {
    return this.request<{ result: { data: Array<{ observationVariableDbId: string; observationVariableName: string; trait: { traitName: string }; scale: { scaleName: string; dataType: string } }> } }>('/brapi/v2/variables?pageSize=100');
  }

  // ============ YIELD MAP / FIELD DATA API ============

  async getFieldPlotData(params: { study_id?: string; trial_id?: string; field_id?: string }) {
    const searchParams = new URLSearchParams();
    if (params.study_id) searchParams.append('studyDbId', params.study_id);
    if (params.trial_id) searchParams.append('trialDbId', params.trial_id);
    
    const query = searchParams.toString();
    return this.request<{ result: { data: Array<{ observationUnitDbId: string; observationUnitName: string; germplasmName: string; observationUnitPosition: { positionCoordinateX: string; positionCoordinateY: string }; observations: Array<{ observationVariableName: string; value: string }> }> } }>(`/brapi/v2/observationunits${query ? `?${query}` : ''}`);
  }

  async getStudiesForYieldMap() {
    return this.request<{ result: { data: Array<{ studyDbId: string; studyName: string; trialName: string; locationName: string }> } }>('/brapi/v2/studies?pageSize=50');
  }

  // ============ VEENA CHAT API ============

  /**
   * Get the status of available chat providers
   */
  async getChatStatus(): Promise<{
    active_provider: string;
    active_model: string;
    providers: Record<string, { available: boolean; model: string; configured: boolean }>;
  }> {
    return this.request('/api/v2/chat/status');
  }

  /**
   * Send a chat message to Veena
   */
  async sendChatMessage(data: Record<string, unknown>): Promise<{
    message: string;
    provider?: string;
    model?: string;
    context?: Array<{ doc_id: string; doc_type: string; title: string | null; similarity: number }>;
  }> {
    return this.request('/api/v2/chat/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Stream a chat message from Veena (Generator)
   * Yields text chunks as they arrive
   */
  async *streamChatMessage(data: Record<string, unknown>): AsyncGenerator<string, void, unknown> {
    const response = await fetch(`${this.baseURL}/api/v2/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {})
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw await createApiErrorFromResponse(response, { endpoint: '/api/v2/chat/stream', method: 'POST' });
    }

    if (!response.body) throw new Error('ReadableStream not supported');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        // The endpoint may return SSE format "data: ...\n\n" or raw text depending on implementation.
        // For simplicity assuming raw text chunks or simple JSON objects for now, 
        // but robust SSE parsing handles lines starting with "data: ".
        
        // Simple raw chunk yield for this implementation plan
        yield chunk;
      }
    } finally {
      reader.releaseLock();
    }
  }
}

export const apiClient = new APIClient();


// ============ VISION API ============

class VisionAPI {
  private client: APIClient;
  
  constructor(client: APIClient) {
    this.client = client;
  }

  async getCrops() {
    return fetch('/api/v2/vision/crops').then(r => r.json()) as Promise<{ success: boolean; crops: Array<{ code: string; name: string; icon: string; diseases: number; stages: number }> }>;
  }

  async getModels(params?: { crop?: string; task?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.task) searchParams.append('task', params.task);
    if (params?.status) searchParams.append('status', params.status);
    const query = searchParams.toString();
    return fetch(`/api/v2/vision/models${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ success: boolean; count: number; models: any[] }>;
  }

  async getDatasets(params?: { crop?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.status) searchParams.append('status', params.status);
    const query = searchParams.toString();
    return fetch(`/api/v2/vision/datasets${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ success: boolean; count: number; datasets: any[] }>;
  }
}

// ============ DISEASE API ============

class DiseaseAPI {
  async getDiseases(params?: { crop?: string; disease_type?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.disease_type) searchParams.append('disease_type', params.disease_type);
    const query = searchParams.toString();
    return fetch(`/api/v2/disease/diseases${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ status: string; data: any[]; count: number }>;
  }

  async getDisease(diseaseId: string) {
    return fetch(`/api/v2/disease/diseases/${diseaseId}`).then(r => r.json()) as Promise<{ status: string; data: any }>;
  }

  async getStatistics() {
    return fetch('/api/v2/disease/statistics').then(r => r.json()) as Promise<{ status: string; data: any }>;
  }

  async getGenes(params?: { disease_id?: string; gene_type?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.disease_id) searchParams.append('disease_id', params.disease_id);
    if (params?.gene_type) searchParams.append('gene_type', params.gene_type);
    const query = searchParams.toString();
    return fetch(`/api/v2/disease/genes${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ status: string; data: any[]; count: number }>;
  }

  async getReactionScale() {
    return fetch('/api/v2/disease/reaction-scale').then(r => r.json()) as Promise<{ status: string; data: any }>;
  }
}

// ============ CROP HEALTH API ============

class CropHealthAPI {
  async getTrials(params?: { location?: string; crop?: string; risk_level?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.location) searchParams.append('location', params.location);
    if (params?.crop) searchParams.append('crop', params.crop);
    if (params?.risk_level) searchParams.append('risk_level', params.risk_level);
    const query = searchParams.toString();
    return fetch(`/api/v2/crop-health/trials${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ status: string; data: any[]; count: number }>;
  }

  async getTrial(trialId: string) {
    return fetch(`/api/v2/crop-health/trials/${trialId}`).then(r => r.json()) as Promise<{ status: string; data: any }>;
  }

  async getAlerts(params?: { severity?: string; alert_type?: string; acknowledged?: boolean; location?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.alert_type) searchParams.append('alert_type', params.alert_type);
    if (params?.acknowledged !== undefined) searchParams.append('acknowledged', String(params.acknowledged));
    if (params?.location) searchParams.append('location', params.location);
    const query = searchParams.toString();
    return fetch(`/api/v2/crop-health/alerts${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{ status: string; data: any[]; count: number; unacknowledged: number }>;
  }

  async acknowledgeAlert(alertId: string, data?: { acknowledged?: boolean; notes?: string }) {
    return fetch(`/api/v2/crop-health/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || { acknowledged: true }),
    }).then(r => r.json()) as Promise<{ status: string; data: any; message: string }>;
  }

  async getSummary() {
    return fetch('/api/v2/crop-health/summary').then(r => r.json()) as Promise<{ status: string; data: { avg_health_score: number; total_trials: number; high_risk_trials: number; active_alerts: number; by_crop: Record<string, any>; by_location: Record<string, any> } }>;
  }

  async getTrends(days?: number) {
    const query = days ? `?days=${days}` : '';
    return fetch(`/api/v2/crop-health/trends${query}`).then(r => r.json()) as Promise<{ status: string; data: any[]; period_days: number }>;
  }

  async getLocations() {
    return fetch('/api/v2/crop-health/locations').then(r => r.json()) as Promise<{ status: string; data: string[]; count: number }>;
  }

  async getCrops() {
    return fetch('/api/v2/crop-health/crops').then(r => r.json()) as Promise<{ status: string; data: string[]; count: number }>;
  }
}

// Export API instances
export const visionAPI = new VisionAPI(apiClient);
export const diseaseAPI = new DiseaseAPI();
export const cropHealthAPI = new CropHealthAPI();


// ============ NOTIFICATIONS API ============

class NotificationsAPI {
  async getNotifications(params?: { category?: string; type?: string; read?: boolean; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append('category', params.category);
    if (params?.type) searchParams.append('type', params.type);
    if (params?.read !== undefined) searchParams.append('read', String(params.read));
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return fetch(`/api/v2/notifications${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        type: string;
        title: string;
        message: string;
        timestamp: string;
        read: boolean;
        link?: string;
        category: string;
      }>;
      total: number;
      unread_count: number;
    }>;
  }

  async getUnreadCount() {
    return fetch('/api/v2/notifications/unread-count').then(r => r.json()) as Promise<{
      status: string;
      count: number;
    }>;
  }

  async getSummary() {
    return fetch('/api/v2/notifications/summary').then(r => r.json()) as Promise<{
      status: string;
      data: {
        total: number;
        unread: number;
        by_category: Record<string, number>;
        by_type: Record<string, number>;
      };
    }>;
  }

  async markAsRead(notificationId: string) {
    return fetch(`/api/v2/notifications/${notificationId}/read`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
    }).then(r => r.json()) as Promise<{ status: string; data: any; message: string }>;
  }

  async markAllAsRead() {
    return fetch('/api/v2/notifications/mark-all-read', {
      method: 'POST',
    }).then(r => r.json()) as Promise<{ status: string; message: string; count: number }>;
  }

  async deleteNotification(notificationId: string) {
    return fetch(`/api/v2/notifications/${notificationId}`, {
      method: 'DELETE',
    }).then(r => r.json()) as Promise<{ status: string; message: string }>;
  }

  async createNotification(data: { type?: string; title: string; message: string; link?: string; category?: string }) {
    return fetch('/api/v2/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json()) as Promise<{ status: string; data: any }>;
  }
}

// ============ YIELD MAP API ============

export interface YieldMapStudy {
  studyDbId: string
  studyName: string
  trialName?: string
  locationName?: string
  season?: string
}

export interface YieldMapPlot {
  observationUnitDbId: string
  observationUnitName: string
  germplasmDbId: string
  germplasmName: string
  observationUnitPosition: {
    positionCoordinateX: string
    positionCoordinateY: string
  }
  observations: Array<{
    observationVariableName: string
    value: string
  }>
}

class YieldMapAPI {
  async getStudies(params?: {
    program_id?: string
    season?: string
    limit?: number
  }): Promise<{ result: { data: YieldMapStudy[] } }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.season) searchParams.set('season', params.season)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/yield-map/studies${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getFieldPlotData(params: {
    study_id: string
    trait?: string
  }): Promise<{ result: { data: YieldMapPlot[] } }> {
    const searchParams = new URLSearchParams()
    if (params.trait) searchParams.set('trait', params.trait)
    const query = searchParams.toString()
    return fetch(`/api/v2/yield-map/studies/${params.study_id}/plots${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getStats(studyId: string): Promise<{
    study_id: string
    total_plots: number
    min_yield: number
    max_yield: number
    avg_yield: number
    std_yield: number
    cv_percent: number
  }> {
    return fetch(`/api/v2/yield-map/studies/${studyId}/stats`).then(r => r.json())
  }

  async getTraits(studyId: string): Promise<{
    data: Array<{ id: string; name: string; unit: string }>
  }> {
    return fetch(`/api/v2/yield-map/studies/${studyId}/traits`).then(r => r.json())
  }

  async getSpatialAnalysis(studyId: string): Promise<any> {
    return fetch(`/api/v2/yield-map/studies/${studyId}/spatial-analysis`).then(r => r.json())
  }
}

export const notificationsAPI = new NotificationsAPI();
export const yieldMapAPI = new YieldMapAPI();


// ============ DATA VALIDATION API ============

class DataValidationAPI {
  async getIssues(params?: { type?: string; status?: string; entity_type?: string; rule_id?: string; limit?: number; offset?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.append('type', params.type);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.entity_type) searchParams.append('entity_type', params.entity_type);
    if (params?.rule_id) searchParams.append('rule_id', params.rule_id);
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.offset) searchParams.append('offset', String(params.offset));
    const query = searchParams.toString();
    return fetch(`/api/v2/data-validation${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        type: 'error' | 'warning' | 'info';
        rule_id: string;
        field: string;
        record_id: string;
        entity_type: string;
        message: string;
        suggestion?: string;
        status: string;
        created_at: string;
      }>;
      total: number;
    }>;
  }

  async getStats() {
    return fetch('/api/v2/data-validation/stats').then(r => r.json()) as Promise<{
      status: string;
      data: {
        total_issues: number;
        open_issues: number;
        resolved_issues: number;
        ignored_issues: number;
        errors: number;
        warnings: number;
        info: number;
        data_quality_score: number;
        last_validation: string | null;
        records_validated: number;
      };
    }>;
  }

  async getRules(enabled?: boolean) {
    const query = enabled !== undefined ? `?enabled=${enabled}` : '';
    return fetch(`/api/v2/data-validation/rules${query}`).then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        enabled: boolean;
        severity: string;
        entity_types: string[];
        issues_found: number;
      }>;
    }>;
  }

  async updateRule(ruleId: string, data: { enabled?: boolean; severity?: string }) {
    return fetch(`/api/v2/data-validation/rules/${ruleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async updateIssueStatus(issueId: string, data: { status: string; notes?: string }) {
    return fetch(`/api/v2/data-validation/issues/${issueId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async deleteIssue(issueId: string) {
    return fetch(`/api/v2/data-validation/issues/${issueId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async runValidation(data?: { entity_types?: string[]; rule_ids?: string[] }) {
    return fetch('/api/v2/data-validation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    }).then(r => r.json());
  }

  async getValidationRuns(limit?: number) {
    const query = limit ? `?limit=${limit}` : '';
    return fetch(`/api/v2/data-validation/runs${query}`).then(r => r.json());
  }

  async exportReport(format?: string) {
    const query = format ? `?format=${format}` : '';
    return fetch(`/api/v2/data-validation/export${query}`).then(r => r.json());
  }
}

// ============ PROFILE API ============

class ProfileAPI {
  async getProfile() {
    return fetch('/api/v2/profile').then(r => r.json()) as Promise<{
      status: string;
      data: {
        id: string;
        full_name: string;
        email: string;
        organization_id: number;
        organization_name: string;
        role: string;
        status: string;
        avatar_url: string | null;
        phone: string | null;
        bio: string | null;
        location: string | null;
        timezone: string;
        created_at: string;
        last_login: string;
      };
    }>;
  }

  async updateProfile(data: { full_name?: string; phone?: string; bio?: string; location?: string; timezone?: string }) {
    return fetch('/api/v2/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getPreferences() {
    return fetch('/api/v2/profile/preferences').then(r => r.json()) as Promise<{
      status: string;
      data: {
        theme: string;
        language: string;
        density: string;
        color_scheme: string;
        field_mode: boolean;
        email_notifications: boolean;
        push_notifications: boolean;
        sound_enabled: boolean;
      };
    }>;
  }

  async updatePreferences(data: Record<string, any>) {
    return fetch('/api/v2/profile/preferences', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async changePassword(data: { current_password: string; new_password: string; confirm_password: string }) {
    return fetch('/api/v2/profile/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getSessions() {
    return fetch('/api/v2/profile/sessions').then(r => r.json());
  }

  async revokeSession(sessionId: string) {
    return fetch(`/api/v2/profile/sessions/${sessionId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async getActivity(limit?: number) {
    const query = limit ? `?limit=${limit}` : '';
    return fetch(`/api/v2/profile/activity${query}`).then(r => r.json());
  }
}

// ============ TEAM MANAGEMENT API ============

class TeamManagementAPI {
  async getMembers(params?: { role?: string; status?: string; team_id?: string; search?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.role) searchParams.append('role', params.role);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.team_id) searchParams.append('team_id', params.team_id);
    if (params?.search) searchParams.append('search', params.search);
    const query = searchParams.toString();
    return fetch(`/api/v2/teams/members${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        email: string;
        role: string;
        status: string;
        joined_at: string;
        last_active: string | null;
        team_ids: string[];
      }>;
      count: number;
    }>;
  }

  async getMember(memberId: string) {
    return fetch(`/api/v2/teams/members/${memberId}`).then(r => r.json());
  }

  async createMember(data: { name: string; email: string; role: string; team_ids?: string[] }) {
    return fetch('/api/v2/teams/members', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async updateMember(memberId: string, data: { role?: string; status?: string; team_ids?: string[] }) {
    return fetch(`/api/v2/teams/members/${memberId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async deleteMember(memberId: string) {
    return fetch(`/api/v2/teams/members/${memberId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async getTeams() {
    return fetch('/api/v2/teams').then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        member_count: number;
        project_count: number;
      }>;
    }>;
  }

  async getTeam(teamId: string) {
    return fetch(`/api/v2/teams/${teamId}`).then(r => r.json());
  }

  async createTeam(data: { name: string; description?: string; lead_id?: string }) {
    return fetch('/api/v2/teams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async updateTeam(teamId: string, data: { name?: string; description?: string; lead_id?: string }) {
    return fetch(`/api/v2/teams/${teamId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async deleteTeam(teamId: string) {
    return fetch(`/api/v2/teams/${teamId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async getRoles() {
    return fetch('/api/v2/teams/roles').then(r => r.json());
  }

  async getInvites(status?: string) {
    const query = status ? `?status=${status}` : '';
    return fetch(`/api/v2/teams/invites${query}`).then(r => r.json());
  }

  async createInvite(data: { email: string; role: string }) {
    return fetch('/api/v2/teams/invites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async resendInvite(inviteId: string) {
    return fetch(`/api/v2/teams/invites/${inviteId}/resend`, { method: 'POST' }).then(r => r.json());
  }

  async deleteInvite(inviteId: string) {
    return fetch(`/api/v2/teams/invites/${inviteId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async getStats() {
    return fetch('/api/v2/teams/stats').then(r => r.json());
  }
}

export const dataValidationAPI = new DataValidationAPI();
export const profileAPI = new ProfileAPI();
export const teamManagementAPI = new TeamManagementAPI();


// ============ DATA DICTIONARY API ============

class DataDictionaryAPI {
  async getEntities() {
    return fetch('/api/v2/data-dictionary/entities').then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        brapi_module: string;
        field_count: number;
        relationship_count: number;
      }>;
      count: number;
    }>;
  }

  async getEntity(entityId: string) {
    return fetch(`/api/v2/data-dictionary/entities/${entityId}`).then(r => r.json()) as Promise<{
      status: string;
      data: {
        id: string;
        name: string;
        description: string;
        brapi_module: string;
        fields: Array<{
          name: string;
          type: string;
          description: string;
          required: boolean;
          example: string;
          brapi_field?: string;
        }>;
        relationships: string[];
      };
    }>;
  }

  async searchFields(params?: { search?: string; entity?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.append('search', params.search);
    if (params?.entity) searchParams.append('entity', params.entity);
    const query = searchParams.toString();
    return fetch(`/api/v2/data-dictionary/fields${query ? `?${query}` : ''}`).then(r => r.json());
  }

  async getStats() {
    return fetch('/api/v2/data-dictionary/stats').then(r => r.json());
  }

  async exportDictionary(format?: string) {
    const query = format ? `?format=${format}` : '';
    return fetch(`/api/v2/data-dictionary/export${query}`).then(r => r.json());
  }
}

// ============ GERMPLASM COLLECTION API ============

class GermplasmCollectionAPI {
  async getCollections(params?: { type?: string; species?: string; curator?: string; search?: string; status?: string }) {
    const searchParams = new URLSearchParams();
    if (params?.type) searchParams.append('type', params.type);
    if (params?.species) searchParams.append('species', params.species);
    if (params?.curator) searchParams.append('curator', params.curator);
    if (params?.search) searchParams.append('search', params.search);
    if (params?.status) searchParams.append('status', params.status);
    const query = searchParams.toString();
    return fetch(`/api/v2/collections${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string;
      data: Array<{
        id: string;
        name: string;
        description: string;
        type: string;
        accession_count: number;
        species: string[];
        curator: string;
        updated_at: string;
        status: string;
      }>;
      count: number;
    }>;
  }

  async getCollection(collectionId: string) {
    return fetch(`/api/v2/collections/${collectionId}`).then(r => r.json());
  }

  async getStats() {
    return fetch('/api/v2/collections/stats').then(r => r.json()) as Promise<{
      status: string;
      data: {
        total_collections: number;
        total_accessions: number;
        unique_species: number;
        species_list: string[];
        unique_curators: number;
        by_type: Record<string, number>;
      };
    }>;
  }

  async getTypes() {
    return fetch('/api/v2/collections/types').then(r => r.json());
  }

  async createCollection(data: { name: string; description?: string; type?: string; species?: string[]; curator?: string }) {
    return fetch('/api/v2/collections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async updateCollection(collectionId: string, data: Record<string, any>) {
    return fetch(`/api/v2/collections/${collectionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async deleteCollection(collectionId: string) {
    return fetch(`/api/v2/collections/${collectionId}`, { method: 'DELETE' }).then(r => r.json());
  }

  async addAccessions(collectionId: string, count: number) {
    return fetch(`/api/v2/collections/${collectionId}/accessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count }),
    }).then(r => r.json());
  }
}

export const dataDictionaryAPI = new DataDictionaryAPI();
export const germplasmCollectionAPI = new GermplasmCollectionAPI();

// ============ COLLABORATION API ============

class CollaborationAPI {
  async getTeamMembers() {
    return fetch('/api/v2/collaboration/team-members').then(r => r.json()) as Promise<Array<{
      id: string;
      name: string;
      email: string;
      role: string;
      avatar?: string;
      status: 'online' | 'away' | 'offline';
      last_active?: string;
    }>>;
  }

  async getSharedItems(itemType?: string) {
    const query = itemType ? `?item_type=${itemType}` : '';
    return fetch(`/api/v2/collaboration/shared-items${query}`).then(r => r.json()) as Promise<Array<{
      id: string;
      type: string;
      name: string;
      shared_by: string;
      shared_at: string;
      permission: string;
    }>>;
  }

  async shareItem(data: { item_type: string; item_id: string; user_ids: string[]; permission?: string }) {
    return fetch('/api/v2/collaboration/share-item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getActivityFeed(limit?: number, offset?: number) {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const query = params.toString();
    return fetch(`/api/v2/collaboration/activity${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<Array<{
      id: string;
      user: string;
      action: string;
      target: string;
      timestamp: string;
      type: string;
    }>>;
  }

  async getConversations() {
    return fetch('/api/v2/collaboration/conversations').then(r => r.json()) as Promise<Array<{
      id: string;
      name: string;
      type: string;
      participants: string[];
      last_message?: string;
      unread_count: number;
    }>>;
  }

  async getMessages(conversationId: string, limit?: number, offset?: number) {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const query = params.toString();
    return fetch(`/api/v2/collaboration/messages/${conversationId}${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<Array<{
      id: string;
      sender: string;
      content: string;
      timestamp: string;
      is_own: boolean;
      conversation_id: string;
    }>>;
  }

  async sendMessage(data: { conversation_id: string; content: string }) {
    return fetch('/api/v2/collaboration/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async updatePresence(status: 'online' | 'away' | 'offline') {
    return fetch('/api/v2/collaboration/presence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }).then(r => r.json());
  }

  async getStats() {
    return fetch('/api/v2/collaboration/stats').then(r => r.json()) as Promise<{
      team_members: number;
      online_now: number;
      shared_items: number;
      today_activity: number;
      unread_messages: number;
    }>;
  }
}

export const collaborationAPI = new CollaborationAPI();

// ============ OFFLINE SYNC API ============

class OfflineSyncAPI {
  async getPendingChanges(status?: string) {
    const query = status ? `?status=${status}` : '';
    return fetch(`/api/v2/offline-sync/pending-changes${query}`).then(r => r.json()) as Promise<Array<{
      id: string;
      type: string;
      name: string;
      status: string;
      last_sync: string;
      size: string;
      error_message?: string;
    }>>;
  }

  async queueChange(data: { type: string; name: string; data: any; size_bytes: number }) {
    return fetch('/api/v2/offline-sync/queue-change', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async deletePendingChange(itemId: string) {
    return fetch(`/api/v2/offline-sync/pending-changes/${itemId}`, {
      method: 'DELETE',
    }).then(r => r.json());
  }

  async syncNow() {
    return fetch('/api/v2/offline-sync/sync-now', {
      method: 'POST',
    }).then(r => r.json()) as Promise<{
      success: boolean;
      synced: number;
      errors: number;
      message: string;
    }>;
  }

  async getCachedData() {
    return fetch('/api/v2/offline-sync/cached-data').then(r => r.json()) as Promise<Array<{
      category: string;
      items: number;
      size: string;
      last_updated: string;
      enabled: boolean;
    }>>;
  }

  async updateCache(category: string) {
    return fetch(`/api/v2/offline-sync/update-cache/${category}`, {
      method: 'POST',
    }).then(r => r.json());
  }

  async clearCache(category?: string) {
    const query = category ? `?category=${category}` : '';
    return fetch(`/api/v2/offline-sync/clear-cache${query}`, {
      method: 'DELETE',
    }).then(r => r.json());
  }

  async getStats() {
    return fetch('/api/v2/offline-sync/stats').then(r => r.json()) as Promise<{
      cached_data_mb: number;
      pending_uploads: number;
      last_sync: string;
      sync_errors: number;
      total_items_cached: number;
    }>;
  }

  async getSettings() {
    return fetch('/api/v2/offline-sync/settings').then(r => r.json()) as Promise<{
      auto_sync: boolean;
      background_sync: boolean;
      wifi_only: boolean;
      cache_images: boolean;
      max_cache_size_mb: number;
    }>;
  }

  async updateSettings(data: {
    auto_sync?: boolean;
    background_sync?: boolean;
    wifi_only?: boolean;
    cache_images?: boolean;
    max_cache_size_mb?: number;
  }) {
    return fetch('/api/v2/offline-sync/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getStorageQuota() {
    return fetch('/api/v2/offline-sync/storage-quota').then(r => r.json()) as Promise<{
      recommended_max_mb: number;
      current_usage_mb: number;
      available_mb: number;
      quota_exceeded: boolean;
    }>;
  }

  async resolveConflict(itemId: string, resolution: 'server_wins' | 'client_wins' | 'merge') {
    return fetch(`/api/v2/offline-sync/resolve-conflict/${itemId}?resolution=${resolution}`, {
      method: 'POST',
    }).then(r => r.json());
  }
}

export const offlineSyncAPI = new OfflineSyncAPI();

// ============ SYSTEM SETTINGS API ============

class SystemSettingsAPI {
  async getAllSettings() {
    return fetch('/api/v2/system-settings/all').then(r => r.json()) as Promise<{
      general: {
        site_name: string;
        site_description: string;
        default_language: string;
        timezone: string;
        date_format: string;
      };
      security: {
        enable_registration: boolean;
        require_email_verification: boolean;
        session_timeout: number;
      };
      api: {
        brapi_version: string;
        api_rate_limit: number;
        max_upload_size: number;
      };
      features: {
        enable_offline_mode: boolean;
        enable_notifications: boolean;
        enable_audit_log: boolean;
      };
    }>;
  }

  async getGeneralSettings() {
    return fetch('/api/v2/system-settings/general').then(r => r.json());
  }

  async updateGeneralSettings(data: {
    site_name?: string;
    site_description?: string;
    default_language?: string;
    timezone?: string;
    date_format?: string;
  }) {
    return fetch('/api/v2/system-settings/general', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getSecuritySettings() {
    return fetch('/api/v2/system-settings/security').then(r => r.json());
  }

  async updateSecuritySettings(data: {
    enable_registration?: boolean;
    require_email_verification?: boolean;
    session_timeout?: number;
  }) {
    return fetch('/api/v2/system-settings/security', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getAPISettings() {
    return fetch('/api/v2/system-settings/api').then(r => r.json());
  }

  async updateAPISettings(data: {
    brapi_version?: string;
    api_rate_limit?: number;
    max_upload_size?: number;
  }) {
    return fetch('/api/v2/system-settings/api', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getFeatureToggles() {
    return fetch('/api/v2/system-settings/features').then(r => r.json());
  }

  async updateFeatureToggles(data: {
    enable_offline_mode?: boolean;
    enable_notifications?: boolean;
    enable_audit_log?: boolean;
  }) {
    return fetch('/api/v2/system-settings/features', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json());
  }

  async getSystemStatus() {
    return fetch('/api/v2/system-settings/status').then(r => r.json()) as Promise<{
      task_queue: {
        pending: number;
        running: number;
        completed: number;
        failed: number;
        max_concurrent: number;
      };
      event_bus: {
        subscriptions: Record<string, string[]>;
        total_events: number;
      };
      service_health: Record<string, string>;
    }>;
  }

  async resetToDefaults() {
    return fetch('/api/v2/system-settings/reset-defaults', {
      method: 'POST',
    }).then(r => r.json());
  }

  async exportSettings() {
    return fetch('/api/v2/system-settings/export').then(r => r.json());
  }

  async importSettings(settings: any) {
    return fetch('/api/v2/system-settings/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }).then(r => r.json());
  }
}

export const systemSettingsAPI = new SystemSettingsAPI();

// ============ BACKUP & RESTORE API ============

interface Backup {
  id: string
  name: string
  size: string
  type: 'full' | 'incremental' | 'manual'
  status: 'completed' | 'in_progress' | 'failed'
  created_at: string
  created_by: string
}

interface BackupStats {
  total_backups: number
  successful_backups: number
  latest_size: string
  auto_backup_schedule: string
}

class BackupAPI {
  async listBackups() {
    return fetch('/api/v2/backup/').then(r => r.json()) as Promise<Backup[]>
  }

  async getStats() {
    return fetch('/api/v2/backup/stats').then(r => r.json()) as Promise<BackupStats>
  }

  async createBackup(type: 'full' | 'incremental' | 'manual' = 'manual') {
    return fetch('/api/v2/backup/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type })
    }).then(r => r.json()) as Promise<Backup>
  }

  async restoreBackup(backupId: string) {
    return fetch('/api/v2/backup/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_id: backupId })
    }).then(r => r.json())
  }

  async downloadBackup(backupId: string) {
    return fetch(`/api/v2/backup/download/${backupId}`).then(r => r.json())
  }

  async deleteBackup(backupId: string) {
    return fetch(`/api/v2/backup/${backupId}`, {
      method: 'DELETE'
    }).then(r => r.json())
  }
}

export const backupAPI = new BackupAPI();

// ============ WORKFLOW AUTOMATION API ============

interface WorkflowStep {
  id: string
  type: 'trigger' | 'action' | 'condition'
  name: string
  config: Record<string, string>
}

interface Workflow {
  id: string
  name: string
  description: string
  trigger: string
  status: 'active' | 'paused' | 'error'
  last_run: string
  next_run: string
  runs: number
  success_rate: number
  enabled: boolean
  steps: WorkflowStep[]
}

interface WorkflowRun {
  id: string
  workflow_id: string
  workflow_name: string
  status: 'success' | 'error' | 'running'
  started_at: string
  completed_at: string | null
  duration: string
  error?: string
}

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  category: string
}

interface WorkflowStats {
  total_workflows: number
  active_workflows: number
  paused_workflows: number
  error_workflows: number
  total_runs: number
  average_success_rate: number
  time_saved_hours: number
}

class WorkflowsAPI {
  async listWorkflows(params?: { status?: string; enabled?: boolean }) {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.enabled !== undefined) searchParams.append('enabled', String(params.enabled))
    const query = searchParams.toString()
    return fetch(`/api/v2/workflows${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string
      data: Workflow[]
      total: number
    }>
  }

  async getStats() {
    return fetch('/api/v2/workflows/stats').then(r => r.json()) as Promise<{
      status: string
      data: WorkflowStats
    }>
  }

  async getWorkflow(workflowId: string) {
    return fetch(`/api/v2/workflows/${workflowId}`).then(r => r.json()) as Promise<{
      status: string
      data: Workflow
    }>
  }

  async createWorkflow(data: {
    name: string
    description: string
    trigger: string
    steps: WorkflowStep[]
    enabled?: boolean
  }) {
    return fetch('/api/v2/workflows', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()) as Promise<{
      status: string
      data: Workflow
      message: string
    }>
  }

  async updateWorkflow(workflowId: string, data: {
    name?: string
    description?: string
    trigger?: string
    steps?: WorkflowStep[]
    enabled?: boolean
  }) {
    return fetch(`/api/v2/workflows/${workflowId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()) as Promise<{
      status: string
      data: Workflow
      message: string
    }>
  }

  async deleteWorkflow(workflowId: string) {
    return fetch(`/api/v2/workflows/${workflowId}`, {
      method: 'DELETE'
    }).then(r => r.json()) as Promise<{
      status: string
      message: string
    }>
  }

  async runWorkflow(workflowId: string) {
    return fetch(`/api/v2/workflows/${workflowId}/run`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      data: WorkflowRun
      message: string
    }>
  }

  async toggleWorkflow(workflowId: string) {
    return fetch(`/api/v2/workflows/${workflowId}/toggle`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      data: Workflow
      message: string
    }>
  }

  async getWorkflowRuns(params?: { workflow_id?: string; status?: string; limit?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.workflow_id) searchParams.append('workflow_id', params.workflow_id)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.limit) searchParams.append('limit', String(params.limit))
    const query = searchParams.toString()
    return fetch(`/api/v2/workflows/runs/history${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string
      data: WorkflowRun[]
      total: number
    }>
  }

  async listTemplates() {
    return fetch('/api/v2/workflows/templates/list').then(r => r.json()) as Promise<{
      status: string
      data: WorkflowTemplate[]
    }>
  }

  async useTemplate(templateId: string, name: string) {
    return fetch(`/api/v2/workflows/templates/${templateId}/use?name=${encodeURIComponent(name)}`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      data: Workflow
      message: string
    }>
  }
}

export const workflowsAPI = new WorkflowsAPI();

// ============ LANGUAGE SETTINGS API ============

interface Language {
  code: string
  name: string
  native_name: string
  flag: string
  progress: number
  is_default: boolean
  is_enabled: boolean
}

interface TranslationKey {
  key: string
  en: string
  es?: string
  fr?: string
  pt?: string
  hi?: string
  zh?: string
  ar?: string
  sw?: string
  ja?: string
  de?: string
  status: 'complete' | 'pending'
}

interface LanguageStats {
  total_languages: number
  enabled_languages: number
  total_strings: number
  translated: number
  needs_review: number
  untranslated: number
  average_progress: number
}

class LanguagesAPI {
  async listLanguages(enabledOnly: boolean = false) {
    const params = new URLSearchParams()
    if (enabledOnly) params.append('enabled_only', 'true')
    return fetch(`/api/v2/languages?${params}`).then(r => r.json()) as Promise<{
      status: string
      data: Language[]
      total: number
    }>
  }

  async getStats() {
    return fetch('/api/v2/languages/stats').then(r => r.json()) as Promise<{
      status: string
      data: LanguageStats
    }>
  }

  async getLanguage(languageCode: string) {
    return fetch(`/api/v2/languages/${languageCode}`).then(r => r.json()) as Promise<{
      status: string
      data: Language
    }>
  }

  async updateLanguage(languageCode: string, data: { is_enabled?: boolean; is_default?: boolean }) {
    return fetch(`/api/v2/languages/${languageCode}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json()) as Promise<{
      status: string
      data: Language
      message: string
    }>
  }

  async listTranslationKeys(params?: { language_code?: string; status?: string; limit?: number }) {
    const searchParams = new URLSearchParams()
    if (params?.language_code) searchParams.append('language_code', params.language_code)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.limit) searchParams.append('limit', String(params.limit))
    const query = searchParams.toString()
    return fetch(`/api/v2/languages/translations/keys${query ? `?${query}` : ''}`).then(r => r.json()) as Promise<{
      status: string
      data: TranslationKey[]
      total: number
    }>
  }

  async createTranslationKey(key: string, enValue: string) {
    return fetch(`/api/v2/languages/translations/keys?key=${encodeURIComponent(key)}&en_value=${encodeURIComponent(enValue)}`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      data: TranslationKey
      message: string
    }>
  }

  async updateTranslation(key: string, languageCode: string, value: string) {
    return fetch(`/api/v2/languages/translations/keys/${encodeURIComponent(key)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, language_code: languageCode, value })
    }).then(r => r.json()) as Promise<{
      status: string
      data: TranslationKey
      message: string
    }>
  }

  async exportTranslations(languageCode: string, format: string = 'json') {
    return fetch(`/api/v2/languages/export?language_code=${languageCode}&format=${format}`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      data: {
        language: string
        format: string
        translations: Record<string, string>
        count: number
      }
      message: string
    }>
  }

  async importTranslations(languageCode: string, translations: Record<string, string>) {
    return fetch(`/api/v2/languages/import?language_code=${languageCode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(translations)
    }).then(r => r.json()) as Promise<{
      status: string
      message: string
      count: number
    }>
  }

  async autoTranslate(languageCode: string) {
    return fetch(`/api/v2/languages/${languageCode}/auto-translate`, {
      method: 'POST'
    }).then(r => r.json()) as Promise<{
      status: string
      message: string
      note?: string
    }>
  }
}

export const languagesAPI = new LanguagesAPI();






// ============ COLLABORATION HUB API ============

interface CollaborationStats {
  total_members: number
  online_members: number
  active_workspaces: number
  pending_tasks: number
  comments_today: number
  activities_today: number
}

interface TeamMember {
  id: string
  name: string
  email: string
  role: string
  status: 'online' | 'away' | 'busy' | 'offline'
  last_active: string
  current_workspace?: string
}

interface Workspace {
  id: string
  name: string
  type: string
  description?: string
  owner_id: string
  members: string[]
  member_details?: TeamMember[]
  created_at: string
  updated_at: string
}

interface ActivityEntry {
  id: string
  user_id: string
  user_name: string
  activity_type: string
  entity_type: string
  entity_id: string
  entity_name: string
  description: string
  timestamp: string
}

interface Task {
  id: string
  title: string
  description?: string
  assignee_id?: string
  assignee_name?: string
  workspace_id?: string
  status: string
  priority: string
  due_date?: string
  created_at: string
}

class CollaborationHubAPI {
  async getStats(): Promise<CollaborationStats> {
    return fetch('/api/v2/collaboration-hub/stats').then(r => r.json())
  }

  async getMembers(): Promise<{ members: TeamMember[] }> {
    return fetch('/api/v2/collaboration-hub/members').then(r => r.json())
  }

  async getWorkspaces(): Promise<{ workspaces: Workspace[] }> {
    return fetch('/api/v2/collaboration-hub/workspaces').then(r => r.json())
  }

  async createWorkspace(name: string, type: string, description?: string): Promise<Workspace> {
    const params = new URLSearchParams({ name, type })
    if (description) params.append('description', description)
    return fetch(`/api/v2/collaboration-hub/workspaces?${params}`, { method: 'POST' }).then(r => r.json())
  }

  async getActivities(limit: number = 20): Promise<{ activities: ActivityEntry[] }> {
    return fetch(`/api/v2/collaboration-hub/activities?limit=${limit}`).then(r => r.json())
  }

  async getTasks(): Promise<{ tasks: Task[] }> {
    return fetch('/api/v2/collaboration-hub/tasks').then(r => r.json())
  }

  async createTask(title: string, description?: string, priority?: string): Promise<Task> {
    const params = new URLSearchParams({ title })
    if (description) params.append('description', description)
    if (priority) params.append('priority', priority)
    return fetch(`/api/v2/collaboration-hub/tasks?${params}`, { method: 'POST' }).then(r => r.json())
  }

  async updateTask(taskId: string, updates: { status?: string; title?: string; priority?: string }): Promise<Task> {
    const params = new URLSearchParams()
    if (updates.status) params.append('status', updates.status)
    if (updates.title) params.append('title', updates.title)
    if (updates.priority) params.append('priority', updates.priority)
    return fetch(`/api/v2/collaboration-hub/tasks/${taskId}?${params}`, { method: 'PATCH' }).then(r => r.json())
  }

  async getPresence(): Promise<{ users: Array<{ user_id: string; status: string; current_page?: string }> }> {
    return fetch('/api/v2/collaboration-hub/presence').then(r => r.json())
  }
}

export const collaborationHubAPI = new CollaborationHubAPI();

// ============ ANALYTICS API ============
// Note: Analytics interfaces are defined later in the file with the AnalyticsDashboardAPI class

interface AnalyticsResponse {
  genetic_gain: GeneticGainData[]
  heritabilities: HeritabilityData[]
  selection_response: SelectionResponseData[]
  correlations: CorrelationMatrix
  summary: AnalyticsSummary
  insights: QuickInsight[]
}

class AnalyticsAPI {
  async getAnalytics(): Promise<AnalyticsResponse> {
    return fetch('/api/v2/analytics').then(r => r.json())
  }

  async getSummary(): Promise<AnalyticsSummary> {
    return fetch('/api/v2/analytics/summary').then(r => r.json())
  }

  async getGeneticGain(programId?: string): Promise<{ data: GeneticGainData[] }> {
    const params = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/analytics/genetic-gain${params}`).then(r => r.json())
  }

  async getHeritabilities(trialId?: string): Promise<{ data: HeritabilityData[] }> {
    const params = trialId ? `?trial_id=${trialId}` : ''
    return fetch(`/api/v2/analytics/heritabilities${params}`).then(r => r.json())
  }

  async getCorrelations(traitIds?: string[]): Promise<{ data: CorrelationMatrix }> {
    const params = traitIds?.length ? `?trait_ids=${traitIds.join(',')}` : ''
    return fetch(`/api/v2/analytics/correlations${params}`).then(r => r.json())
  }

  async getSelectionResponse(programId?: string): Promise<{ data: SelectionResponseData[] }> {
    const params = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/analytics/selection-response${params}`).then(r => r.json())
  }

  async getInsights(): Promise<{ insights: QuickInsight[] }> {
    return fetch('/api/v2/analytics/insights').then(r => r.json())
  }

  async computeGBLUP(params: { trait_id: string; population_id?: string }): Promise<{ job_id: string; status: string }> {
    const query = new URLSearchParams({ trait_id: params.trait_id })
    if (params.population_id) query.append('population_id', params.population_id)
    return fetch(`/api/v2/analytics/compute/gblup?${query}`, { method: 'POST' }).then(r => r.json())
  }

  async getComputeJob(jobId: string): Promise<{ job_id: string; status: string; progress?: number; result?: any }> {
    return fetch(`/api/v2/analytics/compute/${jobId}`).then(r => r.json())
  }

  async getVeenaSummary(): Promise<{ summary: string; key_metrics?: Record<string, string> }> {
    return fetch('/api/v2/analytics/veena-summary').then(r => r.json())
  }
}

export const analyticsAPI = new AnalyticsAPI();

// ============ REPORTS API ============

interface ReportTemplate {
  id: string
  name: string
  type: string
  description?: string
  category: string
  parameters: Record<string, any>
  formats: string[]
  last_generated?: string
  generation_count: number
}

interface GeneratedReport {
  id: string
  template_id: string
  name: string
  format: string
  status: string
  created_at: string
  generated_at: string
  generated_by: string
  size_bytes: number
  file_url?: string
  download_url?: string
}

interface ReportSchedule {
  id: string
  template_id: string
  name: string
  frequency: string
  schedule: string
  schedule_time: string
  enabled: boolean
  status: string
  recipients: string[]
  last_run?: string
  next_run?: string
}

interface ReportStats {
  total_templates: number
  generated_reports: number
  scheduled_reports: number
  active_schedules: number
  generated_today: number
  storage_used_mb: number
  storage_quota_mb: number
}

class ReportsAPI {
  async getStats(): Promise<ReportStats> {
    return fetch('/api/v2/reports/stats').then(r => r.json())
  }

  async getTemplates(): Promise<{ templates: ReportTemplate[] }> {
    return fetch('/api/v2/reports/templates').then(r => r.json())
  }

  async generateReport(templateId: string, format: string = 'pdf', params?: Record<string, any>): Promise<GeneratedReport> {
    const query = new URLSearchParams({ template_id: templateId, format })
    return fetch(`/api/v2/reports/generate?${query}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params || {})
    }).then(r => r.json())
  }

  async getGeneratedReports(): Promise<{ reports: GeneratedReport[] }> {
    return fetch('/api/v2/reports/generated').then(r => r.json())
  }

  async downloadReport(reportId: string): Promise<Blob> {
    return fetch(`/api/v2/reports/download/${reportId}`).then(r => r.blob())
  }

  async getSchedules(): Promise<{ schedules: ReportSchedule[] }> {
    return fetch('/api/v2/reports/schedules').then(r => r.json())
  }

  async createSchedule(templateId: string, frequency: string, name?: string): Promise<ReportSchedule> {
    const params = new URLSearchParams({ template_id: templateId, frequency })
    if (name) params.append('name', name)
    return fetch(`/api/v2/reports/schedules?${params}`, { method: 'POST' }).then(r => r.json())
  }

  async toggleSchedule(scheduleId: string, enabled: boolean): Promise<ReportSchedule> {
    return fetch(`/api/v2/reports/schedules/${scheduleId}?enabled=${enabled}`, { method: 'PATCH' }).then(r => r.json())
  }

  async runSchedule(scheduleId: string): Promise<GeneratedReport> {
    return fetch(`/api/v2/reports/schedules/${scheduleId}/run`, { method: 'POST' }).then(r => r.json())
  }

  async deleteSchedule(scheduleId: string): Promise<void> {
    return fetch(`/api/v2/reports/schedules/${scheduleId}`, { method: 'DELETE' }).then(() => {})
  }
}

export const reportsAPI = new ReportsAPI();

// ============ DATA SYNC API ============

interface SyncStats {
  total_items: number
  synced_items: number
  pending_items: number
  conflicts: number
  errors: number
  last_full_sync?: string
  sync_in_progress: boolean
}

interface SyncItem {
  id: string
  entity_type: string
  entity_id: string
  name: string
  status: string
  size_bytes: number
  created_at: string
  last_modified: string
  error_message?: string
}

interface SyncHistoryEntry {
  id: string
  action: string
  description: string
  items_count: number
  status: string
  started_at: string
  completed_at?: string
  error_message?: string
}

interface OfflineDataCategory {
  type: string
  count: number
  size_bytes: number
  last_updated?: string
}

interface SyncSettings {
  auto_sync: boolean
  sync_on_wifi_only: boolean
  background_sync: boolean
  sync_images: boolean
  sync_interval_minutes: number
  max_offline_days: number
  conflict_resolution: string
}

class DataSyncAPI {
  async getStats(): Promise<SyncStats> {
    return fetch('/api/v2/data-sync/stats').then(r => r.json())
  }

  async getPending(): Promise<{ items: SyncItem[] }> {
    return fetch('/api/v2/data-sync/pending').then(r => r.json())
  }

  async sync(action: string = 'full_sync'): Promise<{ status: string; message: string }> {
    return fetch(`/api/v2/data-sync/sync?action=${action}`, { method: 'POST' }).then(r => r.json())
  }

  async getHistory(): Promise<{ history: SyncHistoryEntry[] }> {
    return fetch('/api/v2/data-sync/history').then(r => r.json())
  }

  async getOfflineData(): Promise<{ categories: OfflineDataCategory[]; total_size_bytes: number; storage_quota_bytes: number }> {
    return fetch('/api/v2/data-sync/offline-data').then(r => r.json())
  }

  async upload(): Promise<{ status: string; uploaded: number }> {
    return fetch('/api/v2/data-sync/upload', { method: 'POST' }).then(r => r.json())
  }

  async deletePending(itemId: string): Promise<void> {
    return fetch(`/api/v2/data-sync/pending/${itemId}`, { method: 'DELETE' }).then(() => {})
  }

  async clearOfflineData(category: string): Promise<void> {
    return fetch(`/api/v2/data-sync/offline-data/${category}`, { method: 'DELETE' }).then(() => {})
  }

  async getSettings(): Promise<SyncSettings> {
    return fetch('/api/v2/data-sync/settings').then(r => r.json())
  }

  async updateSettings(settings: Partial<SyncSettings>): Promise<SyncSettings> {
    const params = new URLSearchParams()
    Object.entries(settings).forEach(([k, v]) => {
      if (v !== undefined) params.append(k, String(v))
    })
    return fetch(`/api/v2/data-sync/settings?${params}`, { method: 'PATCH' }).then(r => r.json())
  }
}

export const dataSyncAPI = new DataSyncAPI();

// ============ GENETIC GAIN API ============

interface GeneticGainBreedingProgram {
  id: string
  name: string
  crop: string
  trait: string
  start_year: number
  cycles: GeneticGainCycleData[]
  releases: GeneticGainReleaseData[]
}

interface GeneticGainCycleData {
  cycle: number
  year: number
  mean: number
  variance: number
  n_entries: number
  selection_intensity?: number
}

interface GeneticGainReleaseData {
  variety_name: string
  year: number
  value: number
}

interface GeneticGainResult {
  absolute_gain: number
  percent_gain: number
  annual_gain: number
  cycles_analyzed: number
  regression_slope?: number
  r_squared?: number
}

interface GeneticGainStats {
  total_programs: number
  total_cycles: number
  total_releases: number
  avg_annual_gain: number
}

class GeneticGainAPI {
  async getPrograms(): Promise<{ data: GeneticGainBreedingProgram[]; count: number }> {
    return fetch('/api/v2/genetic-gain/programs').then(r => r.json())
  }

  async getProgram(programId: string): Promise<{ data: GeneticGainBreedingProgram }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}`).then(r => r.json())
  }

  async createProgram(data: { name: string; crop: string; trait: string; start_year?: number }): Promise<{ data: GeneticGainBreedingProgram }> {
    return fetch('/api/v2/genetic-gain/programs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        program_name: data.name,
        crop: data.crop,
        target_trait: data.trait,
        start_year: data.start_year || new Date().getFullYear(),
        organization: 'default'
      })
    }).then(r => r.json())
  }

  async recordCycle(programId: string, data: { year: number; mean: number; variance: number; n_entries: number }): Promise<{ data: GeneticGainCycleData }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}/cycles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cycle: 0,
        year: data.year,
        mean_value: data.mean,
        best_value: data.mean * 1.1,
        n_entries: data.n_entries,
        std_dev: Math.sqrt(data.variance)
      })
    }).then(r => r.json())
  }

  async recordRelease(programId: string, data: { variety_name: string; year: number; value: number }): Promise<{ data: GeneticGainReleaseData }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}/releases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        variety_name: data.variety_name,
        year: data.year,
        trait_value: data.value
      })
    }).then(r => r.json())
  }

  async calculateGain(programId: string, useMean: boolean = true): Promise<{ data: GeneticGainResult }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}/gain?use_mean=${useMean}`).then(r => r.json())
  }

  async getProjection(programId: string, yearsAhead: number = 10): Promise<{ data: any }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}/projection?years_ahead=${yearsAhead}`).then(r => r.json())
  }

  async getRealizedHeritability(programId: string): Promise<{ data: any }> {
    return fetch(`/api/v2/genetic-gain/programs/${programId}/realized-heritability`).then(r => r.json())
  }

  async getStatistics(): Promise<{ data: GeneticGainStats }> {
    return fetch('/api/v2/genetic-gain/statistics').then(r => r.json())
  }
}

export const geneticGainAPI = new GeneticGainAPI();


// ============ SPATIAL ANALYSIS API ============

interface SpatialField {
  field_id: string
  name: string
  location: string
  latitude: number
  longitude: number
  area_ha: number
  rows: number
  columns: number
  plot_size_m2: number
  soil_type?: string
  irrigation?: string
}

interface SpatialPlot {
  plot_id: string
  row: number
  column: number
  x_m: number
  y_m: number
  center_lat: number
  center_lon: number
}

interface DistanceResult {
  distance_m: number
  distance_km: number
}

class SpatialAPI {
  async getFields(): Promise<{ data: SpatialField[]; count: number }> {
    return fetch('/api/v2/spatial/fields').then(r => r.json())
  }

  async getField(fieldId: string): Promise<{ data: SpatialField }> {
    return fetch(`/api/v2/spatial/fields/${fieldId}`).then(r => r.json())
  }

  async createField(data: {
    name: string
    location: string
    latitude: number
    longitude: number
    area_ha: number
    rows: number
    columns: number
    plot_size_m2: number
    soil_type?: string
    irrigation?: string
  }): Promise<{ data: SpatialField }> {
    return fetch('/api/v2/spatial/fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getPlots(fieldId: string): Promise<{ data: SpatialPlot[]; count: number }> {
    return fetch(`/api/v2/spatial/fields/${fieldId}/plots`).then(r => r.json())
  }

  async generatePlots(fieldId: string, params: {
    plot_width_m: number
    plot_length_m: number
    alley_width_m?: number
    border_m?: number
  }): Promise<{ data: SpatialPlot[]; count: number }> {
    return fetch(`/api/v2/spatial/fields/${fieldId}/plots`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): Promise<{ data: DistanceResult }> {
    return fetch('/api/v2/spatial/calculate/distance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat1, lon1, lat2, lon2 })
    }).then(r => r.json())
  }

  async analyzeAutocorrelation(values: any[], xKey?: string, yKey?: string, valueKey?: string): Promise<{ data: any }> {
    return fetch('/api/v2/spatial/analyze/autocorrelation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values, x_key: xKey, y_key: yKey, value_key: valueKey })
    }).then(r => r.json())
  }

  async analyzeMovingAverage(values: any[], windowSize?: number): Promise<{ data: any }> {
    return fetch('/api/v2/spatial/analyze/moving-average', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values, window_size: windowSize || 3 })
    }).then(r => r.json())
  }

  async analyzeNearestNeighbor(points: any[], area?: number): Promise<{ data: any }> {
    return fetch('/api/v2/spatial/analyze/nearest-neighbor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ points, area })
    }).then(r => r.json())
  }

  async analyzeRowColumnTrend(values: any[]): Promise<{ data: any }> {
    return fetch('/api/v2/spatial/analyze/row-column-trend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values })
    }).then(r => r.json())
  }

  async getStatistics(): Promise<{ data: any }> {
    return fetch('/api/v2/spatial/statistics').then(r => r.json())
  }
}

export const spatialAPI = new SpatialAPI();


// ============ POPULATION GENETICS API ============

interface Population {
  id: string
  name: string
  size: number
  region: string
  crop?: string
  admixture?: number[]
}

interface StructureAnalysis {
  populations: Array<{
    population_id: string
    population_name: string
    sample_size: number
    proportions: Array<{ cluster: number; proportion: number }>
  }>
  delta_k_analysis: Array<{ k: number; delta_k: number }>
  optimal_k: number
}

interface PCAResult {
  samples: Array<{
    sample_id: string
    population_name: string
    pc1: number
    pc2: number
    pc3?: number
  }>
  variance_explained: Array<{ pc: string; variance: number; cumulative?: number }>
}

interface FstAnalysis {
  pairwise: Array<{
    population1_name: string
    population2_name: string
    fst: number
    differentiation: string
    nm: number
  }>
  global_statistics: {
    global_fst: string
    mean_he: string
    mean_ho: string
    mean_fis: string
  }
  interpretation: {
    fst_ranges: Array<{ range: string; level: string }>
  }
}

interface MigrationAnalysis {
  migrations: Array<{
    from_population_name: string
    to_population_name: string
    nm: number
    gene_flow: string
  }>
  interpretation: { description: string }
}

interface PopulationSummary {
  total_populations: number
  total_samples: number
  mean_expected_heterozygosity: number
  global_fst: number
  mean_allelic_richness: number
}

class PopulationGeneticsAPI {
  async getPopulations(crop?: string, region?: string): Promise<{ populations: Population[] }> {
    const params = new URLSearchParams()
    if (crop) params.append('crop', crop)
    if (region) params.append('region', region)
    const query = params.toString() ? `?${params}` : ''
    return fetch(`/api/v2/population-genetics/populations${query}`).then(r => r.json())
  }

  async getPopulation(populationId: string): Promise<Population> {
    return fetch(`/api/v2/population-genetics/populations/${populationId}`).then(r => r.json())
  }

  async getStructure(k: number = 3, populationIds?: string[]): Promise<StructureAnalysis> {
    const params = new URLSearchParams({ k: String(k) })
    if (populationIds?.length) params.append('population_ids', populationIds.join(','))
    return fetch(`/api/v2/population-genetics/structure?${params}`).then(r => r.json())
  }

  async getPCA(populationIds?: string[]): Promise<PCAResult> {
    const params = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/population-genetics/pca${params}`).then(r => r.json())
  }

  async getFst(populationIds?: string[]): Promise<FstAnalysis> {
    const params = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/population-genetics/fst${params}`).then(r => r.json())
  }

  async getMigration(populationIds?: string[]): Promise<MigrationAnalysis> {
    const params = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/population-genetics/migration${params}`).then(r => r.json())
  }

  async getSummary(): Promise<PopulationSummary> {
    return fetch('/api/v2/population-genetics/summary').then(r => r.json())
  }

  async getHardyWeinberg(populationId: string): Promise<any> {
    return fetch(`/api/v2/population-genetics/hardy-weinberg/${populationId}`).then(r => r.json())
  }
}

export const populationGeneticsAPI = new PopulationGeneticsAPI();


// ============ TRIAL NETWORK API ============

interface TrialSite {
  id: string
  name: string
  location: string
  country: string
  coordinates: { lat: number; lng: number }
  trials: number
  germplasm: number
  status: 'active' | 'completed' | 'planned'
  season: string
  lead: string
  region: string
}

interface TrialNetworkStats {
  total_sites: number
  active_trials: number
  countries: number
  germplasm_entries: number
  collaborators: number
}

interface SharedGermplasm {
  id: string
  name: string
  sites: number
  performance: string
  crop: string
  type: string
}

interface PerformanceMetric {
  trait: string
  mean: number
  best: number
  worst: number
  cv: number
  n_sites: number
}

class TrialNetworkAPI {
  async getSites(params?: { season?: string; status?: string; country?: string; region?: string }): Promise<{ sites: TrialSite[] }> {
    const query = new URLSearchParams()
    if (params?.season) query.append('season', params.season)
    if (params?.status) query.append('status', params.status)
    if (params?.country) query.append('country', params.country)
    if (params?.region) query.append('region', params.region)
    const queryStr = query.toString() ? `?${query}` : ''
    return fetch(`/api/v2/trial-network/sites${queryStr}`).then(r => r.json())
  }

  async getSite(siteId: string): Promise<{ site: TrialSite }> {
    return fetch(`/api/v2/trial-network/sites/${siteId}`).then(r => r.json())
  }

  async getStatistics(season?: string): Promise<{ data: TrialNetworkStats }> {
    const query = season ? `?season=${season}` : ''
    return fetch(`/api/v2/trial-network/statistics${query}`).then(r => r.json())
  }

  async getSharedGermplasm(minSites?: number, crop?: string): Promise<{ germplasm: SharedGermplasm[] }> {
    const params = new URLSearchParams()
    if (minSites) params.append('min_sites', String(minSites))
    if (crop) params.append('crop', crop)
    const query = params.toString() ? `?${params}` : ''
    return fetch(`/api/v2/trial-network/germplasm${query}`).then(r => r.json())
  }

  async getPerformance(trait?: string): Promise<{ performance: PerformanceMetric[] }> {
    const query = trait ? `?trait=${trait}` : ''
    return fetch(`/api/v2/trial-network/performance${query}`).then(r => r.json())
  }

  async getSiteComparison(siteIds: string[]): Promise<{ data: any }> {
    return fetch(`/api/v2/trial-network/compare?site_ids=${siteIds.join(',')}`).then(r => r.json())
  }

  async getCountries(): Promise<{ countries: string[] }> {
    return fetch('/api/v2/trial-network/countries').then(r => r.json())
  }

  async getSeasons(): Promise<{ seasons: string[] }> {
    return fetch('/api/v2/trial-network/seasons').then(r => r.json())
  }
}

export const trialNetworkAPI = new TrialNetworkAPI();


// ============ GERMPLASM SEARCH API ============

interface GermplasmSearchResult {
  id: string
  name: string
  accession: string
  species: string
  subspecies?: string
  origin: string
  traits: string[]
  status: string
  collection: string
  year?: number
}

interface GermplasmSearchFilters {
  species: string[]
  origins: string[]
  collections: string[]
  traits: string[]
}

class GermplasmSearchAPI {
  async search(params: {
    query?: string
    species?: string
    origin?: string
    collection?: string
    trait?: string
    page?: number
    pageSize?: number
  }): Promise<{ results: GermplasmSearchResult[]; total: number }> {
    const queryParams = new URLSearchParams()
    if (params.query) queryParams.append('query', params.query)
    if (params.species) queryParams.append('species', params.species)
    if (params.origin) queryParams.append('origin', params.origin)
    if (params.collection) queryParams.append('collection', params.collection)
    if (params.trait) queryParams.append('trait', params.trait)
    if (params.page) queryParams.append('page', String(params.page))
    if (params.pageSize) queryParams.append('pageSize', String(params.pageSize))
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/germplasm-search${query}`).then(r => r.json())
  }

  async getFilters(): Promise<{ data: GermplasmSearchFilters }> {
    return fetch('/api/v2/germplasm-search/filters').then(r => r.json())
  }

  async getById(id: string): Promise<{ data: GermplasmSearchResult }> {
    return fetch(`/api/v2/germplasm-search/${id}`).then(r => r.json())
  }

  async addToList(germplasmIds: string[], listId: string): Promise<{ success: boolean }> {
    return fetch('/api/v2/germplasm-search/add-to-list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ germplasm_ids: germplasmIds, list_id: listId })
    }).then(r => r.json())
  }

  async export(germplasmIds: string[], format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    return fetch('/api/v2/germplasm-search/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ germplasm_ids: germplasmIds, format })
    }).then(r => r.blob())
  }
}

export const germplasmSearchAPI = new GermplasmSearchAPI();


// ============ PROGENY API ============

interface ProgenyItem {
  germplasm_id: string
  germplasm_name: string
  parent_type: string
  generation?: string
  cross_year?: number
}

interface ProgenyEntry {
  id: string
  germplasm_id: string
  germplasm_name: string
  parent_type: 'FEMALE' | 'MALE' | 'SELF' | 'POPULATION'
  species?: string
  generation?: string
  progeny: ProgenyItem[]
}

interface ProgenyStatistics {
  total_parents: number
  total_progeny: number
  avg_offspring: number
  max_offspring: number
  max_offspring_parent: string | null
  by_parent_type: Record<string, number>
  by_species: Record<string, number>
}

class ProgenyAPI {
  async getParents(params?: {
    search?: string
    parent_type?: string
    species?: string
    page?: number
    pageSize?: number
  }): Promise<{ data: ProgenyEntry[]; total: number }> {
    const queryParams = new URLSearchParams()
    if (params?.search) queryParams.append('search', params.search)
    if (params?.parent_type) queryParams.append('parent_type', params.parent_type)
    if (params?.species) queryParams.append('species', params.species)
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.pageSize) queryParams.append('pageSize', String(params.pageSize))
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/progeny/parents${query}`).then(r => r.json())
  }

  async getParent(parentId: string): Promise<{ data: ProgenyEntry }> {
    return fetch(`/api/v2/progeny/parents/${parentId}`).then(r => r.json())
  }

  async getProgeny(germplasmId: string): Promise<{ data: ProgenyItem[] }> {
    return fetch(`/api/v2/progeny/germplasm/${germplasmId}/progeny`).then(r => r.json())
  }

  async getStatistics(): Promise<{ data: ProgenyStatistics }> {
    return fetch('/api/v2/progeny/statistics').then(r => r.json())
  }

  async getLineageTree(germplasmId: string, depth?: number): Promise<{ data: any }> {
    const query = depth ? `?depth=${depth}` : ''
    return fetch(`/api/v2/progeny/germplasm/${germplasmId}/lineage${query}`).then(r => r.json())
  }

  async export(parentIds?: string[], format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    return fetch('/api/v2/progeny/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent_ids: parentIds, format })
    }).then(r => r.blob())
  }
}

export const progenyAPI = new ProgenyAPI();


// ============ HARVEST MANAGEMENT API ============

interface HarvestPlan {
  id: string
  study_id: string
  study_name: string
  planned_date: string
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled'
  notes?: string
  created_at?: string
  updated_at?: string
}

interface HarvestRecord {
  id: string
  plan_id: string
  plot_id: string
  germplasm_name: string
  harvest_date: string
  wet_weight: number
  dry_weight?: number
  moisture_content?: number
  quality_grade?: string
  storage_unit?: string
  notes?: string
}

interface StorageUnit {
  id: string
  name: string
  type: string
  capacity: number
  current_stock: number
  temperature?: number
  humidity?: number
  location?: string
}

interface HarvestStats {
  total_harvested_kg: number
  avg_moisture: number
  total_capacity: number
  total_stock: number
  records_count: number
  plans_count: number
}

class HarvestAPI {
  async getPlans(params?: { status?: string; study_id?: string }): Promise<{ plans: HarvestPlan[] }> {
    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.study_id) queryParams.append('study_id', params.study_id)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/harvest/plans${query}`).then(r => r.json())
  }

  async getPlan(planId: string): Promise<{ plan: HarvestPlan }> {
    return fetch(`/api/v2/harvest/plans/${planId}`).then(r => r.json())
  }

  async createPlan(data: { study_id: string; planned_date: string; notes?: string }): Promise<{ plan: HarvestPlan }> {
    return fetch('/api/v2/harvest/plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updatePlan(planId: string, data: Partial<HarvestPlan>): Promise<{ plan: HarvestPlan }> {
    return fetch(`/api/v2/harvest/plans/${planId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deletePlan(planId: string): Promise<void> {
    return fetch(`/api/v2/harvest/plans/${planId}`, { method: 'DELETE' }).then(() => {})
  }

  async getRecords(params?: { plan_id?: string; plot_id?: string }): Promise<{ records: HarvestRecord[] }> {
    const queryParams = new URLSearchParams()
    if (params?.plan_id) queryParams.append('plan_id', params.plan_id)
    if (params?.plot_id) queryParams.append('plot_id', params.plot_id)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/harvest/records${query}`).then(r => r.json())
  }

  async getRecord(recordId: string): Promise<{ record: HarvestRecord }> {
    return fetch(`/api/v2/harvest/records/${recordId}`).then(r => r.json())
  }

  async createRecord(data: {
    plan_id: string
    plot_id: string
    germplasm_name?: string
    wet_weight: number
    moisture_content?: number
    quality_grade?: string
    storage_unit?: string
    notes?: string
  }): Promise<{ record: HarvestRecord }> {
    return fetch('/api/v2/harvest/records', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, harvest_date: new Date().toISOString().split('T')[0] })
    }).then(r => r.json())
  }

  async updateRecord(recordId: string, data: Partial<HarvestRecord>): Promise<{ record: HarvestRecord }> {
    return fetch(`/api/v2/harvest/records/${recordId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteRecord(recordId: string): Promise<void> {
    return fetch(`/api/v2/harvest/records/${recordId}`, { method: 'DELETE' }).then(() => {})
  }

  async getStorage(): Promise<{ units: StorageUnit[] }> {
    return fetch('/api/v2/harvest/storage').then(r => r.json())
  }

  async getStorageUnit(unitId: string): Promise<{ unit: StorageUnit }> {
    return fetch(`/api/v2/harvest/storage/${unitId}`).then(r => r.json())
  }

  async updateStorageUnit(unitId: string, data: Partial<StorageUnit>): Promise<{ unit: StorageUnit }> {
    return fetch(`/api/v2/harvest/storage/${unitId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getStats(): Promise<{ data: HarvestStats }> {
    return fetch('/api/v2/harvest/stats').then(r => r.json())
  }
}

export const harvestAPI = new HarvestAPI();


// ============ PARENT SELECTION API ============

interface Parent {
  id: string
  name: string
  type: 'elite' | 'donor' | 'landrace'
  traits: string[]
  gebv: number
  heterosis_potential: number
  pedigree: string
  markers?: Record<string, boolean>
  agronomic_data?: {
    yield_potential: number
    days_to_maturity: number
    plant_height: number
  }
}

interface CrossPrediction {
  parent1: { id: string; name: string; type: string }
  parent2: { id: string; name: string; type: string }
  expected_gebv: number
  heterosis: number
  genetic_distance: number
  success_probability: number
  combined_traits: string[]
  recommendation: string
}

interface CrossRecommendation {
  cross: string
  parent1_id: string
  parent2_id: string
  score: number
  reason: string
  expected_gebv: number
  heterosis: number
  combined_traits: string[]
}

class ParentSelectionAPI {
  async getParents(params?: {
    type?: string
    trait?: string
    search?: string
    page?: number
    pageSize?: number
  }): Promise<{ data: Parent[]; total: number }> {
    const queryParams = new URLSearchParams()
    if (params?.type) queryParams.append('type', params.type)
    if (params?.trait) queryParams.append('trait', params.trait)
    if (params?.search) queryParams.append('search', params.search)
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.pageSize) queryParams.append('pageSize', String(params.pageSize))
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/parent-selection/parents${query}`).then(r => r.json())
  }

  async getParent(parentId: string): Promise<{ data: Parent }> {
    return fetch(`/api/v2/parent-selection/parents/${parentId}`).then(r => r.json())
  }

  async getRecommendations(params?: {
    limit?: number
    trait?: string
    type?: string
  }): Promise<{ data: CrossRecommendation[] }> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', String(params.limit))
    if (params?.trait) queryParams.append('trait', params.trait)
    if (params?.type) queryParams.append('type', params.type)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/parent-selection/recommendations${query}`).then(r => r.json())
  }

  async predictCross(parent1Id: string, parent2Id: string): Promise<{ data: CrossPrediction }> {
    return fetch(`/api/v2/parent-selection/predict-cross?parent1_id=${parent1Id}&parent2_id=${parent2Id}`).then(r => r.json())
  }

  async createCrossPlan(data: {
    parent1_id: string
    parent2_id: string
    name?: string
    notes?: string
  }): Promise<{ data: any }> {
    return fetch('/api/v2/parent-selection/cross-plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async export(parentIds?: string[], format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    return fetch('/api/v2/parent-selection/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent_ids: parentIds, format })
    }).then(r => r.blob())
  }
}

export const parentSelectionAPI = new ParentSelectionAPI();


// ============ GENETIC DIVERSITY API ============

interface DiversityPopulation {
  id: string
  name: string
  size: number
  region: string
  crop?: string
  metrics?: DiversityMetric[]
}

interface DiversityMetric {
  name: string
  value: number
  range: [number, number]
  status: 'low' | 'moderate' | 'high'
}

interface DistanceMatrix {
  pop1: string
  pop2: string
  distance: number
  method: string
}

interface AMOVAResult {
  among_populations: number
  among_individuals: number
  within_individuals: number
}

interface AdmixtureResult {
  populations: Array<{
    id: string
    name: string
    proportions: number[]
  }>
  k: number
}

interface PCAPoint {
  x: number
  y: number
  population: string
  sample_id?: string
}

class GeneticDiversityAPI {
  async getPopulations(params?: { crop?: string; region?: string }): Promise<{ data: DiversityPopulation[] }> {
    const queryParams = new URLSearchParams()
    if (params?.crop) queryParams.append('crop', params.crop)
    if (params?.region) queryParams.append('region', params.region)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/genetic-diversity/populations${query}`).then(r => r.json())
  }

  async getPopulation(populationId: string): Promise<{ data: DiversityPopulation }> {
    return fetch(`/api/v2/genetic-diversity/populations/${populationId}`).then(r => r.json())
  }

  async getMetrics(populationId: string): Promise<{ data: { metrics: DiversityMetric[]; recommendations: string[] } }> {
    return fetch(`/api/v2/genetic-diversity/populations/${populationId}/metrics`).then(r => r.json())
  }

  async getDistances(populationIds?: string[]): Promise<{ data: DistanceMatrix[] }> {
    const query = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/genetic-diversity/distances${query}`).then(r => r.json())
  }

  async getAMOVA(populationIds?: string[]): Promise<{ data: { variance_components: AMOVAResult } }> {
    const query = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/genetic-diversity/amova${query}`).then(r => r.json())
  }

  async getAdmixture(k?: number, populationIds?: string[]): Promise<{ data: AdmixtureResult }> {
    const params = new URLSearchParams()
    if (k) params.append('k', String(k))
    if (populationIds?.length) params.append('population_ids', populationIds.join(','))
    const query = params.toString() ? `?${params}` : ''
    return fetch(`/api/v2/genetic-diversity/admixture${query}`).then(r => r.json())
  }

  async getPCA(populationIds?: string[]): Promise<{ data: { points: PCAPoint[] } }> {
    const query = populationIds?.length ? `?population_ids=${populationIds.join(',')}` : ''
    return fetch(`/api/v2/genetic-diversity/pca${query}`).then(r => r.json())
  }

  async getSummary(): Promise<{ data: any }> {
    return fetch('/api/v2/genetic-diversity/summary').then(r => r.json())
  }
}

export const geneticDiversityAPI = new GeneticDiversityAPI();


// ============ GERMPLASM COMPARISON API ============

export interface ComparisonGermplasm {
  id: string
  name: string
  accession: string
  species: string
  origin: string
  pedigree: string
  traits: Record<string, number | string>
  markers: Record<string, string>
  status: 'active' | 'archived' | 'candidate'
}

export interface ComparisonTrait {
  id: string
  name: string
  unit: string
  type?: 'numeric' | 'categorical'
  optimal_range?: [number, number]
  higher_is_better: boolean
  best?: { value: string | number; entry_id: string }
}

export interface ComparisonResult {
  entries: ComparisonGermplasm[]
  traits: ComparisonTrait[]
  markers?: Array<{ name: string; values: Record<string, boolean> }>
  recommendations?: string[]
  summary?: {
    best_overall: string
    recommendations: string[]
  }
}

class GermplasmComparisonAPI {
  async listGermplasm(params?: {
    search?: string
    species?: string
    status?: string
    skip?: number
    limit?: number
  }): Promise<{ data: ComparisonGermplasm[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.search) searchParams.set('search', params.search)
    if (params?.species) searchParams.set('species', params.species)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.skip) searchParams.set('skip', params.skip.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/germplasm-comparison${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getGermplasm(germplasmId: string): Promise<ComparisonGermplasm> {
    return fetch(`/api/v2/germplasm-comparison/entry/${germplasmId}`).then(r => r.json())
  }

  async compare(ids: string[]): Promise<ComparisonResult> {
    return fetch('/api/v2/germplasm-comparison/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    }).then(r => r.json())
  }

  async getTraits(): Promise<{ traits: ComparisonTrait[] }> {
    return fetch('/api/v2/germplasm-comparison/traits').then(r => r.json())
  }

  async getMarkers(crop?: string): Promise<{ markers: Array<{ id: string; name: string; gene?: string; trait?: string; crop?: string }> }> {
    const query = crop ? `?crop=${crop}` : ''
    return fetch(`/api/v2/germplasm-comparison/markers${query}`).then(r => r.json())
  }

  async getStatistics(): Promise<{
    total_germplasm: number
    total_traits: number
    total_markers: number
    species_count: number
  }> {
    return fetch('/api/v2/germplasm-comparison/statistics').then(r => r.json())
  }

  async export(germplasmIds: string[], format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    return fetch('/api/v2/germplasm-comparison/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ germplasm_ids: germplasmIds, format })
    }).then(r => r.blob())
  }
}

export const germplasmComparisonAPI = new GermplasmComparisonAPI();


// ============ BREEDING PIPELINE API ============

interface PipelineStage {
  id: string
  name: string
  order: number
  description: string
}

interface PipelineEntry {
  id: string
  name: string
  pedigree: string
  current_stage: string
  program_id: string
  program_name: string
  crop: string
  year: number
  status: 'active' | 'released' | 'dropped'
  traits: string[]
  notes: string
  created_at: string
  updated_at: string
  stage_history: Array<{ stage: string; date: string; decision: string; notes?: string }>
}

interface PipelineStatistics {
  total_entries: number
  active: number
  released: number
  dropped: number
  stage_counts: Record<string, number>
  crop_counts: Record<string, number>
  avg_years_to_release: number
  crops: string[]
}

class BreedingPipelineAPI {
  async getStages(): Promise<{ data: PipelineStage[] }> {
    return fetch('/api/v2/breeding-pipeline/stages').then(r => r.json())
  }

  async getEntries(params?: {
    stage?: string
    crop?: string
    program_id?: string
    status?: string
    year?: number
    search?: string
    limit?: number
    offset?: number
  }): Promise<{ data: PipelineEntry[]; total: number }> {
    const queryParams = new URLSearchParams()
    if (params?.stage) queryParams.append('stage', params.stage)
    if (params?.crop) queryParams.append('crop', params.crop)
    if (params?.program_id) queryParams.append('program_id', params.program_id)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.year) queryParams.append('year', String(params.year))
    if (params?.search) queryParams.append('search', params.search)
    if (params?.limit) queryParams.append('limit', String(params.limit))
    if (params?.offset) queryParams.append('offset', String(params.offset))
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/breeding-pipeline${query}`).then(r => r.json())
  }

  async getEntry(entryId: string): Promise<{ data: PipelineEntry }> {
    return fetch(`/api/v2/breeding-pipeline/${entryId}`).then(r => r.json())
  }

  async getStatistics(params?: { program_id?: string; crop?: string }): Promise<{ data: PipelineStatistics }> {
    const queryParams = new URLSearchParams()
    if (params?.program_id) queryParams.append('program_id', params.program_id)
    if (params?.crop) queryParams.append('crop', params.crop)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/breeding-pipeline/statistics${query}`).then(r => r.json())
  }

  async getStageSummary(): Promise<{ data: Array<{ stage_id: string; stage_name: string; order: number; count: number; entries: Array<{ id: string; name: string; crop: string }> }> }> {
    return fetch('/api/v2/breeding-pipeline/stage-summary').then(r => r.json())
  }

  async getCrops(): Promise<{ data: string[] }> {
    return fetch('/api/v2/breeding-pipeline/crops').then(r => r.json())
  }

  async getPrograms(): Promise<{ data: Array<{ id: string; name: string }> }> {
    return fetch('/api/v2/breeding-pipeline/programs').then(r => r.json())
  }

  async createEntry(data: {
    name: string
    pedigree: string
    crop: string
    current_stage?: string
    program_id?: string
    program_name?: string
    year?: number
    traits?: string[]
    notes?: string
  }): Promise<{ data: PipelineEntry; message: string }> {
    return fetch('/api/v2/breeding-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async advanceStage(entryId: string, decision: 'Advanced' | 'Dropped', notes?: string): Promise<{ data: PipelineEntry; message: string }> {
    return fetch(`/api/v2/breeding-pipeline/${entryId}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes })
    }).then(r => r.json())
  }
}

export const breedingPipelineAPI = new BreedingPipelineAPI()

// ============ YIELD PREDICTOR API ============

interface YieldPrediction {
  germplasm_id: string
  germplasm_name: string
  predicted_yield: number
  confidence_low: number
  confidence_high: number
  environment: string
  model_accuracy?: number
}

interface EnvironmentalFactor {
  name: string
  value: number
  unit: string
  optimal: [number, number]
  impact: 'positive' | 'negative' | 'neutral'
}

class YieldPredictorAPI {
  async getPredictions(params?: { environment?: string; model?: string }): Promise<{ predictions: YieldPrediction[]; model_accuracy: number; avg_yield: number }> {
    const queryParams = new URLSearchParams()
    if (params?.environment && params.environment !== 'all') queryParams.append('environment', params.environment)
    if (params?.model) queryParams.append('model', params.model)
    const query = queryParams.toString() ? `?${queryParams}` : ''
    return fetch(`/api/v2/genomic-selection/yield-predictions${query}`).then(r => r.json())
  }

  async runPrediction(params: { germplasm_ids?: string[]; environment?: string; model?: string }): Promise<{ predictions: YieldPrediction[]; job_id: string }> {
    return fetch('/api/v2/genomic-selection/yield-predictions/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async getScenarioAnalysis(params: { ndvi: number; rainfall: number; temperature: number; soil_moisture?: number }): Promise<{ predicted_yield: number; confidence_interval: [number, number]; factors: EnvironmentalFactor[] }> {
    return fetch('/api/v2/genomic-selection/scenario-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async getEnvironmentalFactors(locationId?: string): Promise<{ factors: EnvironmentalFactor[] }> {
    const query = locationId ? `?location_id=${locationId}` : ''
    return fetch(`/api/v2/genomic-selection/environmental-factors${query}`).then(r => r.json())
  }

  async getModels(): Promise<{ models: Array<{ id: string; name: string; accuracy: number; description: string }> }> {
    return fetch('/api/v2/genomic-selection/models').then(r => r.json())
  }
}

export const yieldPredictorAPI = new YieldPredictorAPI()

// ============ BREEDING VALUE CALCULATOR API ============

interface BreedingValueIndividual {
  id: string
  name: string
  ebv: number
  accuracy: number
  rank?: number
}

interface BLUPResult {
  individuals: BreedingValueIndividual[]
  heritability: number
  genetic_variance: number
  residual_variance: number
  mean: number
}

interface CrossPredictionResult {
  parent1: string
  parent2: string
  predicted_mean: number
  predicted_variance: number
  probability_superior: number
}

class BreedingValueCalculatorAPI {
  async getIndividuals(trait?: string): Promise<{ data: BreedingValueIndividual[] }> {
    const query = trait ? `?trait=${trait}` : ''
    return fetch(`/api/v2/breeding-value/individuals${query}`).then(r => r.json())
  }

  async runBLUP(params: { trait: string; pedigree_data?: any }): Promise<BLUPResult> {
    return fetch('/api/v2/breeding-value/blup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async runGBLUP(params: { trait: string; marker_data?: any }): Promise<BLUPResult> {
    return fetch('/api/v2/breeding-value/gblup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async predictCross(params: { parent1: string; parent2: string; trait: string }): Promise<CrossPredictionResult> {
    return fetch('/api/v2/breeding-value/predict-cross', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async getTraits(): Promise<{ data: Array<{ id: string; name: string; unit?: string }> }> {
    return fetch('/api/v2/breeding-value/traits').then(r => r.json())
  }

  async getAnalyses(): Promise<{ data: Array<{ id: string; trait: string; method: string; created_at: string; n_entries: number }> }> {
    return fetch('/api/v2/breeding-value/analyses').then(r => r.json())
  }

  async getAnalysis(analysisId: string): Promise<BLUPResult & { id: string; trait: string; method: string }> {
    return fetch(`/api/v2/breeding-value/analyses/${analysisId}`).then(r => r.json())
  }
}

export const breedingValueCalculatorAPI = new BreedingValueCalculatorAPI()


// ============ STABILITY ANALYSIS API ============

interface StabilityVariety {
  id: string
  name: string
  mean_yield: number
  rank: number
  bi: number
  s2di: number
  sigma2i: number
  wi: number
  pi: number
  asv: number
  stability_rank: number
  recommendation: 'wide' | 'favorable' | 'unfavorable' | 'specific'
  environments_tested: number
  years_tested: number
}

interface StabilityMethod {
  id: string
  name: string
  year: number
  type: string
  description: string
  interpretation: Record<string, string>
}

class StabilityAnalysisAPI {
  async getVarieties(params?: { recommendation?: string; min_yield?: number; sort_by?: string }): Promise<{ success: boolean; count: number; varieties: StabilityVariety[] }> {
    const searchParams = new URLSearchParams()
    if (params?.recommendation) searchParams.append('recommendation', params.recommendation)
    if (params?.min_yield) searchParams.append('min_yield', params.min_yield.toString())
    if (params?.sort_by) searchParams.append('sort_by', params.sort_by)
    const query = searchParams.toString()
    return fetch(`/api/v2/stability/varieties${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getVariety(varietyId: string): Promise<{ success: boolean } & StabilityVariety & { interpretation: Record<string, string> }> {
    return fetch(`/api/v2/stability/varieties/${varietyId}`).then(r => r.json())
  }

  async analyze(params: { variety_ids: string[]; methods?: string[] }): Promise<{ success: boolean; methods_used: string[]; variety_count: number; results: any[] }> {
    return fetch('/api/v2/stability/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async getMethods(): Promise<{ success: boolean; methods: StabilityMethod[] }> {
    return fetch('/api/v2/stability/methods').then(r => r.json())
  }

  async getRecommendations(): Promise<{ success: boolean; recommendations: Record<string, { description: string; criteria: string; varieties: Array<{ id: string; name: string; mean_yield: number }> }> }> {
    return fetch('/api/v2/stability/recommendations').then(r => r.json())
  }

  async getComparison(): Promise<{ success: boolean; comparison: any[]; correlation_matrix: Record<string, Record<string, number>> }> {
    return fetch('/api/v2/stability/comparison').then(r => r.json())
  }

  async getStatistics(): Promise<{ success: boolean; statistics: Record<string, number> }> {
    return fetch('/api/v2/stability/statistics').then(r => r.json())
  }
}

export const stabilityAnalysisAPI = new StabilityAnalysisAPI()

// ============ FIELD BOOK API ============

interface FieldBookStudy {
  id: string
  name: string
  location: string
  season: string
  design: string
  reps: number
  entries: number
  traits: number
}

interface FieldBookEntry {
  plot_id: string
  germplasm: string
  rep: string
  row: number
  col: number
  traits: Record<string, number | string | null>
}

interface FieldBookTrait {
  id: string
  name: string
  unit: string
  min: number
  max: number
  step: number
}

class FieldBookAPI {
  async getStudies(): Promise<{ success: boolean; count: number; studies: FieldBookStudy[] }> {
    return fetch('/api/v2/field-book/studies').then(r => r.json())
  }

  async getStudyEntries(studyId: string): Promise<{ success: boolean; study_id: string; study_name: string; count: number; entries: FieldBookEntry[] }> {
    return fetch(`/api/v2/field-book/studies/${studyId}/entries`).then(r => r.json())
  }

  async getStudyTraits(studyId: string): Promise<{ success: boolean; study_id: string; traits: FieldBookTrait[] }> {
    return fetch(`/api/v2/field-book/studies/${studyId}/traits`).then(r => r.json())
  }

  async recordObservation(data: { study_id: string; plot_id: string; trait_id: string; value: any; notes?: string }): Promise<{ success: boolean; message: string; study_id: string; plot_id: string; trait_id: string; value: any; timestamp: string }> {
    return fetch('/api/v2/field-book/observations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async recordBulkObservations(data: { study_id: string; observations: Array<{ plot_id: string; trait_id: string; value: any }> }): Promise<{ success: boolean; message: string; study_id: string; observations_recorded: number }> {
    return fetch('/api/v2/field-book/observations/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getProgress(studyId: string, traitId?: string): Promise<{ success: boolean; study_id: string; overall: { collected: number; total: number; percentage: number }; by_trait: Record<string, { trait_name: string; collected: number; total: number; percentage: number }> }> {
    const query = traitId ? `?trait_id=${traitId}` : ''
    return fetch(`/api/v2/field-book/studies/${studyId}/progress${query}`).then(r => r.json())
  }

  async getSummary(studyId: string): Promise<{ success: boolean; study_id: string; study_name: string; total_entries: number; total_traits: number; summaries: Record<string, { trait_name: string; unit: string; count: number; mean: number | null; min: number | null; max: number | null; range: number | null }> }> {
    return fetch(`/api/v2/field-book/studies/${studyId}/summary`).then(r => r.json())
  }

  async deleteObservation(studyId: string, plotId: string, traitId: string): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/field-book/observations/${studyId}/${plotId}/${traitId}`, {
      method: 'DELETE'
    }).then(r => r.json())
  }
}

export const fieldBookAPI = new FieldBookAPI()

// ============ NURSERY MANAGEMENT API ============

interface NurseryBatch {
  nursery_id: string
  name: string
  nursery_type: string
  season: string
  year: number
  location: string
  status: string
  sowing_date?: string
  harvest_date?: string
  entry_count: number
  notes: string
}

interface NurseryEntry {
  entry_id: string
  nursery_id: string
  genotype_id: string
  genotype_name: string
  pedigree: string
  source_nursery: string
  selection_decision?: string
  selection_notes?: string
  seed_harvested: number
}

class NurseryManagementAPI {
  async getNurseries(params?: { year?: number; nursery_type?: string; status?: string }): Promise<{ success: boolean; count: number; nurseries: NurseryBatch[] }> {
    const searchParams = new URLSearchParams()
    if (params?.year) searchParams.append('year', params.year.toString())
    if (params?.nursery_type) searchParams.append('nursery_type', params.nursery_type)
    if (params?.status) searchParams.append('status', params.status)
    const query = searchParams.toString()
    return fetch(`/api/v2/nursery/nurseries${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getNursery(nurseryId: string): Promise<{ success: boolean } & NurseryBatch & { entries: NurseryEntry[] }> {
    return fetch(`/api/v2/nursery/nurseries/${nurseryId}`).then(r => r.json())
  }

  async createNursery(data: { name: string; nursery_type: string; season: string; year: number; location: string; sowing_date?: string; notes?: string }): Promise<{ success: boolean; message: string } & NurseryBatch> {
    return fetch('/api/v2/nursery/nurseries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async addEntry(nurseryId: string, data: { genotype_id: string; genotype_name: string; pedigree?: string; source_nursery?: string }): Promise<{ success: boolean; message: string } & NurseryEntry> {
    return fetch(`/api/v2/nursery/nurseries/${nurseryId}/entries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async bulkAddEntries(nurseryId: string, entries: Array<{ genotype_id: string; genotype_name: string; pedigree?: string; source_nursery?: string }>): Promise<{ success: boolean; nursery_id: string; entries_added: number }> {
    return fetch(`/api/v2/nursery/nurseries/${nurseryId}/entries/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries })
    }).then(r => r.json())
  }

  async recordSelection(entryId: string, data: { decision: string; notes?: string; seed_harvested?: number }): Promise<{ success: boolean; message: string } & NurseryEntry> {
    return fetch(`/api/v2/nursery/entries/${entryId}/selection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async advanceSelections(sourceNurseryId: string, targetNurseryId: string): Promise<{ success: boolean; message: string; entries_advanced: number }> {
    return fetch('/api/v2/nursery/advance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_nursery_id: sourceNurseryId, target_nursery_id: targetNurseryId })
    }).then(r => r.json())
  }

  async updateStatus(nurseryId: string, data: { status: string; harvest_date?: string }): Promise<{ success: boolean; message: string } & NurseryBatch> {
    return fetch(`/api/v2/nursery/nurseries/${nurseryId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getSummary(nurseryId: string): Promise<{ success: boolean; nursery_id: string; total_entries: number; by_decision: Record<string, number>; selection_rate: number }> {
    return fetch(`/api/v2/nursery/nurseries/${nurseryId}/summary`).then(r => r.json())
  }

  async getTypes(): Promise<{ types: Array<{ id: string; name: string; description: string }> }> {
    return fetch('/api/v2/nursery/types').then(r => r.json())
  }
}

export const nurseryManagementAPI = new NurseryManagementAPI()

// ============ SEED INVENTORY ENHANCED API ============

interface SeedLot {
  lot_id: string
  accession_id: string
  species: string
  variety: string
  harvest_date: string
  quantity: number
  storage_type: string
  storage_location: string
  current_viability: number
  status: string
  last_test_date?: string
  notes: string
}

interface ViabilityTest {
  test_id: string
  lot_id: string
  test_date: string
  seeds_tested: number
  seeds_germinated: number
  germination_percent: number
  test_method: string
  tester: string
  notes: string
}

class SeedInventoryEnhancedAPI {
  async getLots(params?: { species?: string; status?: string; storage_type?: string }): Promise<{ success: boolean; count: number; lots: SeedLot[] }> {
    const searchParams = new URLSearchParams()
    if (params?.species) searchParams.append('species', params.species)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.storage_type) searchParams.append('storage_type', params.storage_type)
    const query = searchParams.toString()
    return fetch(`/api/v2/seed-inventory/lots${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getLot(lotId: string): Promise<{ success: boolean } & SeedLot & { viability_history: ViabilityTest[] }> {
    return fetch(`/api/v2/seed-inventory/lots/${lotId}`).then(r => r.json())
  }

  async registerLot(data: { accession_id: string; species: string; variety: string; harvest_date: string; quantity: number; storage_type: string; storage_location: string; initial_viability: number; notes?: string }): Promise<{ success: boolean; message: string } & SeedLot> {
    return fetch('/api/v2/seed-inventory/lots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async recordViabilityTest(data: { lot_id: string; test_date: string; seeds_tested: number; seeds_germinated: number; test_method: string; tester: string; notes?: string }): Promise<{ success: boolean; message: string } & ViabilityTest> {
    return fetch('/api/v2/seed-inventory/viability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getViabilityHistory(lotId: string): Promise<{ success: boolean; lot_id: string; test_count: number; tests: ViabilityTest[] }> {
    return fetch(`/api/v2/seed-inventory/viability/${lotId}`).then(r => r.json())
  }

  async createRequest(data: { lot_id: string; requester: string; institution: string; quantity: number; purpose?: string }): Promise<{ success: boolean; message: string; request_id: string }> {
    return fetch('/api/v2/seed-inventory/requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async approveRequest(requestId: string, quantityApproved: number): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/seed-inventory/requests/${requestId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity_approved: quantityApproved })
    }).then(r => r.json())
  }

  async shipRequest(requestId: string): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/seed-inventory/requests/${requestId}/ship`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async getSummary(): Promise<{ success: boolean; total_lots: number; total_quantity: number; by_status: Record<string, number>; by_storage_type: Record<string, number>; by_species: Record<string, number>; lots_needing_test: number }> {
    return fetch('/api/v2/seed-inventory/summary').then(r => r.json())
  }

  async getAlerts(): Promise<{ success: boolean; alert_count: number; alerts: Array<{ type: string; lot_id: string; message: string; severity: string }> }> {
    return fetch('/api/v2/seed-inventory/alerts').then(r => r.json())
  }

  async getStorageTypes(): Promise<{ storage_types: Array<{ id: string; name: string; temperature: string; expected_viability: string; use_case: string }> }> {
    return fetch('/api/v2/seed-inventory/storage-types').then(r => r.json())
  }
}

export const seedInventoryEnhancedAPI = new SeedInventoryEnhancedAPI()


// ============ SEEDLING BATCH API ============

interface SeedlingBatch {
  id: string
  germplasm: string
  sowingDate: string
  expectedTransplant: string
  quantity: number
  germinated: number
  healthy: number
  status: 'sowing' | 'germinating' | 'growing' | 'ready' | 'transplanted'
  location: string
}

interface SeedlingStats {
  total: number
  sowing: number
  growing: number
  ready: number
  totalSeedlings: number
}

class SeedlingBatchAPI {
  async getBatches(params?: { status?: string; location?: string }): Promise<{ success: boolean; count: number; batches: SeedlingBatch[] }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.location) searchParams.append('location', params.location)
    const query = searchParams.toString()
    return fetch(`/api/v2/nursery-management/batches${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getBatch(batchId: string): Promise<{ success: boolean } & SeedlingBatch> {
    return fetch(`/api/v2/nursery-management/batches/${batchId}`).then(r => r.json())
  }

  async createBatch(data: { germplasm: string; sowingDate: string; expectedTransplant: string; quantity: number; location: string }): Promise<{ success: boolean; message: string } & SeedlingBatch> {
    return fetch('/api/v2/nursery-management/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateBatchStatus(batchId: string, status: string): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/nursery-management/batches/${batchId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    }).then(r => r.json())
  }

  async updateBatchCounts(batchId: string, data: { germinated?: number; healthy?: number }): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/nursery-management/batches/${batchId}/counts`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteBatch(batchId: string): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/nursery-management/batches/${batchId}`, {
      method: 'DELETE'
    }).then(r => r.json())
  }

  async getStats(): Promise<{ success: boolean } & SeedlingStats> {
    return fetch('/api/v2/nursery-management/stats').then(r => r.json())
  }

  async getLocations(): Promise<{ success: boolean; locations: string[] }> {
    return fetch('/api/v2/nursery-management/locations').then(r => r.json())
  }

  async getGermplasmList(): Promise<{ success: boolean; germplasm: Array<{ id: string; name: string }> }> {
    return fetch('/api/v2/nursery-management/germplasm').then(r => r.json())
  }
}

export const seedlingBatchAPI = new SeedlingBatchAPI()


// ============================================================================
// Disease Resistance API
// ============================================================================

export interface Disease {
  id: string
  name: string
  pathogen: string
  pathogen_type: string
  crop: string
  symptoms: string
  severity_scale: string[]
}

export interface ResistanceGene {
  id: string
  gene_name: string
  disease_id: string
  disease_name?: string
  chromosome?: string
  resistance_type: string
  source_germplasm?: string
  markers?: string[]
}

export interface PyramidingStrategy {
  id: string
  name: string
  disease: string
  genes: string[]
  description: string
  status: string
  warning?: string
}

class DiseaseResistanceAPI {
  async getDiseases(params?: { crop?: string; pathogen_type?: string; search?: string }): Promise<{ diseases: Disease[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.crop) searchParams.set('crop', params.crop)
    if (params?.pathogen_type) searchParams.set('pathogen_type', params.pathogen_type)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/disease/diseases${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getDisease(diseaseId: string): Promise<Disease> {
    return fetch(`/api/v2/disease/diseases/${diseaseId}`).then(r => r.json())
  }

  async getGenes(params?: { disease_id?: string; resistance_type?: string; search?: string }): Promise<{ genes: ResistanceGene[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.disease_id) searchParams.set('disease_id', params.disease_id)
    if (params?.resistance_type) searchParams.set('resistance_type', params.resistance_type)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/disease/genes${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getGene(geneId: string): Promise<ResistanceGene> {
    return fetch(`/api/v2/disease/genes/${geneId}`).then(r => r.json())
  }

  async getCrops(): Promise<{ crops: string[] }> {
    return fetch('/api/v2/disease/crops').then(r => r.json())
  }

  async getPathogenTypes(): Promise<{ pathogenTypes: string[] }> {
    return fetch('/api/v2/disease/pathogen-types').then(r => r.json())
  }

  async getResistanceTypes(): Promise<{ resistanceTypes: string[] }> {
    return fetch('/api/v2/disease/resistance-types').then(r => r.json())
  }

  async getStatistics(): Promise<{
    totalDiseases: number
    totalGenes: number
    totalCrops: number
    masReadyGenes: number
    diseasesByCrop: Record<string, number>
    genesByResistanceType: Record<string, number>
  }> {
    return fetch('/api/v2/disease/statistics').then(r => r.json())
  }

  async getPyramidingStrategies(): Promise<{ strategies: PyramidingStrategy[] }> {
    return fetch('/api/v2/disease/pyramiding-strategies').then(r => r.json())
  }
}

export const diseaseResistanceAPI = new DiseaseResistanceAPI()

// ============================================================================
// Abiotic Stress API
// ============================================================================

export interface StressType {
  stress_id: string
  name: string
  category: string
  description: string
}

export interface ToleranceGene {
  gene_id: string
  name: string
  stress_id: string
  mechanism: string
  crop: string
  chromosome?: string
  markers?: string[]
}

export interface StressIndices {
  SSI: number
  STI: number
  YSI: number
  GMP: number
  MP: number
  TOL: number
  HM: number
}

class AbioticStressAPI {
  async getStressTypes(params?: { category?: string; search?: string }): Promise<{ data: StressType[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/abiotic/stress-types${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getStressType(stressId: string): Promise<StressType> {
    return fetch(`/api/v2/abiotic/stress-types/${stressId}`).then(r => r.json())
  }

  async getGenes(params?: { stress_id?: string; crop?: string; search?: string }): Promise<{ data: ToleranceGene[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.stress_id) searchParams.set('stress_id', params.stress_id)
    if (params?.crop) searchParams.set('crop', params.crop)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/abiotic/genes${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getGene(geneId: string): Promise<ToleranceGene> {
    return fetch(`/api/v2/abiotic/genes/${geneId}`).then(r => r.json())
  }

  async getCategories(): Promise<{ categories: string[] }> {
    return fetch('/api/v2/abiotic/categories').then(r => r.json())
  }

  async getCrops(): Promise<{ crops: string[] }> {
    return fetch('/api/v2/abiotic/crops').then(r => r.json())
  }

  async getStatistics(): Promise<{
    totalStressTypes: number
    totalGenes: number
    totalCategories: number
    masReadyGenes: number
    stressesByCategory: Record<string, number>
    genesByStress: Record<string, number>
  }> {
    return fetch('/api/v2/abiotic/statistics').then(r => r.json())
  }

  async calculateIndices(controlYield: number, stressYield: number): Promise<{
    data: {
      indices: StressIndices
      interpretation: Record<string, string>
      recommendation: string
    }
  }> {
    return fetch('/api/v2/abiotic/calculate/indices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ control_yield: controlYield, stress_yield: stressYield })
    }).then(r => r.json())
  }

  async getScreeningProtocols(): Promise<{
    protocols: Array<{
      stress: string
      method: string
      stages: string[]
      duration: string
      indicators: string[]
    }>
  }> {
    return fetch('/api/v2/abiotic/screening-protocols').then(r => r.json())
  }
}

export const abioticStressAPI = new AbioticStressAPI()

// ============================================================================
// Field Map API
// ============================================================================

export interface Field {
  id: string
  name: string
  location: string
  station: string
  area: number
  plots: number
  status: string
  soilType?: string
  irrigationType?: string
}

export interface Plot {
  id: string
  plotNumber: number
  status: string
  row?: number
  column?: number
  entryId?: string
  trialId?: string
}

class FieldMapAPI {
  async getFields(params?: { station?: string; status?: string; search?: string }): Promise<Field[]> {
    const searchParams = new URLSearchParams()
    if (params?.station) searchParams.set('station', params.station)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/field-map/fields${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getField(fieldId: string): Promise<Field> {
    return fetch(`/api/v2/field-map/fields/${fieldId}`).then(r => r.json())
  }

  async createField(data: {
    name: string
    location: string
    area: number
    plots: number
    soilType?: string
    irrigationType?: string
  }): Promise<Field> {
    return fetch('/api/v2/field-map/fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateField(fieldId: string, data: Partial<Field>): Promise<Field> {
    return fetch(`/api/v2/field-map/fields/${fieldId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteField(fieldId: string): Promise<{ success: boolean }> {
    return fetch(`/api/v2/field-map/fields/${fieldId}`, { method: 'DELETE' }).then(r => r.json())
  }

  async getSummary(): Promise<{
    totalFields: number
    totalArea: number
    totalPlots: number
    activeFields: number
  }> {
    return fetch('/api/v2/field-map/summary').then(r => r.json())
  }

  async getStations(): Promise<string[]> {
    return fetch('/api/v2/field-map/stations').then(r => r.json())
  }

  async getStatuses(): Promise<{ fieldStatuses: string[]; plotStatuses: string[] }> {
    return fetch('/api/v2/field-map/statuses').then(r => r.json())
  }

  async getPlots(fieldId: string, params?: { status?: string; trial_id?: string }): Promise<Plot[]> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    const query = searchParams.toString()
    return fetch(`/api/v2/field-map/fields/${fieldId}/plots${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getPlot(fieldId: string, plotId: string): Promise<Plot> {
    return fetch(`/api/v2/field-map/fields/${fieldId}/plots/${plotId}`).then(r => r.json())
  }

  async updatePlot(fieldId: string, plotId: string, data: Partial<Plot>): Promise<Plot> {
    return fetch(`/api/v2/field-map/fields/${fieldId}/plots/${plotId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }
}

export const fieldMapAPI = new FieldMapAPI()

// ============================================================================
// Trial Planning API
// ============================================================================

export interface PlannedTrial {
  id: string
  name: string
  type: string
  season: string
  year: number
  locations: string[]
  entries: number
  reps: number
  design: string
  status: string
  progress: number
  startDate: string
  endDate?: string
  totalPlots: number
  crop?: string
  objectives?: string
}

export interface TrialType {
  value: string
  label: string
}

export interface TrialDesign {
  value: string
  label: string
}

class TrialPlanningAPI {
  async getTrials(params?: { status?: string; type?: string; search?: string; year?: number }): Promise<PlannedTrial[]> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.type) searchParams.set('type', params.type)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.year) searchParams.set('year', params.year.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/trial-planning/trials${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getTrial(trialId: string): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}`).then(r => r.json())
  }

  async createTrial(data: {
    name: string
    type: string
    season: string
    locations: string[]
    entries: number
    reps: number
    design: string
    startDate: string
    endDate?: string
    crop?: string
    objectives?: string
  }): Promise<PlannedTrial> {
    return fetch('/api/v2/trial-planning/trials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateTrial(trialId: string, data: Partial<PlannedTrial>): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteTrial(trialId: string): Promise<{ success: boolean }> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}`, { method: 'DELETE' }).then(r => r.json())
  }

  async approveTrial(trialId: string, approvedBy: string): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/approve?approved_by=${encodeURIComponent(approvedBy)}`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async startTrial(trialId: string): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/start`, { method: 'POST' }).then(r => r.json())
  }

  async completeTrial(trialId: string): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/complete`, { method: 'POST' }).then(r => r.json())
  }

  async cancelTrial(trialId: string, reason: string): Promise<PlannedTrial> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/cancel?reason=${encodeURIComponent(reason)}`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async getStatistics(): Promise<{
    totalTrials: number
    planning: number
    approved: number
    active: number
    completed: number
    cancelled: number
    totalPlots: number
  }> {
    return fetch('/api/v2/trial-planning/statistics').then(r => r.json())
  }

  async getTimeline(year?: number): Promise<PlannedTrial[]> {
    const query = year ? `?year=${year}` : ''
    return fetch(`/api/v2/trial-planning/timeline${query}`).then(r => r.json())
  }

  async getTypes(): Promise<TrialType[]> {
    return fetch('/api/v2/trial-planning/types').then(r => r.json())
  }

  async getSeasons(): Promise<string[]> {
    return fetch('/api/v2/trial-planning/seasons').then(r => r.json())
  }

  async getDesigns(): Promise<TrialDesign[]> {
    return fetch('/api/v2/trial-planning/designs').then(r => r.json())
  }

  async getResources(trialId: string): Promise<any[]> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/resources`).then(r => r.json())
  }

  async addResource(trialId: string, data: { type: string; name: string; quantity: number }): Promise<any> {
    return fetch(`/api/v2/trial-planning/trials/${trialId}/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }
}

export const trialPlanningAPI = new TrialPlanningAPI()


// ============================================================================
// Pedigree Analysis API
// ============================================================================

export interface PedigreeRecord {
  id: string
  sire_id: string | null
  dam_id: string | null
}

export interface PedigreeIndividual {
  id: string
  sire_id: string | null
  dam_id: string | null
  generation: number
  inbreeding: number
}

export interface PedigreeStats {
  n_individuals: number
  n_founders: number
  n_generations: number
  avg_inbreeding: number
  max_inbreeding: number
  completeness_index: number
}

export interface CoancestryResult {
  coancestry: number
  relationship: string
  individual_1: string
  individual_2: string
}

export interface AncestorResult {
  individual_id: string
  sire_id: string | null
  dam_id: string | null
  n_ancestors: number
  ancestors?: string[]
}

export interface DescendantResult {
  individual_id: string
  n_descendants: number
  descendants?: string[]
}

class PedigreeAnalysisAPI {
  async loadPedigree(pedigree: PedigreeRecord[]): Promise<{ success: boolean; message: string } & PedigreeStats> {
    return fetch('/api/v2/pedigree/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pedigree })
    }).then(r => r.json())
  }

  async getIndividual(individualId: string): Promise<{ success: boolean } & PedigreeIndividual> {
    return fetch(`/api/v2/pedigree/individual/${individualId}`).then(r => r.json())
  }

  async getIndividuals(generation?: number): Promise<{ success: boolean; count: number; individuals: PedigreeIndividual[] }> {
    const params = generation !== undefined ? `?generation=${generation}` : ''
    return fetch(`/api/v2/pedigree/individuals${params}`).then(r => r.json())
  }

  async getStats(): Promise<{ success: boolean } & PedigreeStats> {
    return fetch('/api/v2/pedigree/stats').then(r => r.json())
  }

  async getRelationshipMatrix(individualIds?: string[]): Promise<{
    success: boolean
    individuals: string[]
    matrix: number[][]
  }> {
    return fetch('/api/v2/pedigree/relationship-matrix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ individual_ids: individualIds })
    }).then(r => r.json())
  }

  async getAncestors(individualId: string, maxGenerations: number = 5): Promise<{ success: boolean } & AncestorResult> {
    return fetch(`/api/v2/pedigree/ancestors/${individualId}?max_generations=${maxGenerations}`).then(r => r.json())
  }

  async getDescendants(individualId: string, maxGenerations: number = 3): Promise<{ success: boolean } & DescendantResult> {
    return fetch(`/api/v2/pedigree/descendants/${individualId}?max_generations=${maxGenerations}`).then(r => r.json())
  }

  async calculateCoancestry(individual1: string, individual2: string): Promise<{ success: boolean } & CoancestryResult> {
    return fetch('/api/v2/pedigree/coancestry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ individual_1: individual1, individual_2: individual2 })
    }).then(r => r.json())
  }
}

export const pedigreeAnalysisAPI = new PedigreeAnalysisAPI()

// ============================================================================
// Performance Ranking API
// ============================================================================

export interface RankedEntry {
  id: string
  entry_id: string
  name: string
  rank: number
  previous_rank: number
  yield: number
  gebv: number
  traits: string[]
  score: number
  program_name?: string
  trial_name?: string
  generation?: string
}

export interface RankingStatistics {
  total_entries: number
  avg_score: number
  avg_yield: number
  avg_gebv: number
  top_performer: string | null
  most_improved: { name: string; improvement: number } | null
}

export interface RankingProgram {
  id: string
  name: string
}

export interface RankingTrial {
  id: string
  name: string
  program_id: string
}

class PerformanceRankingAPI {
  async getRankings(params?: {
    program_id?: string
    trial_id?: string
    sort_by?: string
    limit?: number
    search?: string
  }): Promise<{ status: string; data: RankedEntry[]; count: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/performance-ranking/rankings${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getTopPerformers(params?: {
    program_id?: string
    trial_id?: string
    limit?: number
  }): Promise<{ status: string; data: RankedEntry[]; count: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/performance-ranking/top-performers${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getStatistics(params?: {
    program_id?: string
    trial_id?: string
  }): Promise<{ status: string; data: RankingStatistics }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    const query = searchParams.toString()
    return fetch(`/api/v2/performance-ranking/statistics${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getEntry(entryId: string): Promise<{ status: string; data: RankedEntry }> {
    return fetch(`/api/v2/performance-ranking/entries/${entryId}`).then(r => r.json())
  }

  async compareEntries(entryIds: string[]): Promise<{ status: string; data: any }> {
    return fetch('/api/v2/performance-ranking/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entry_ids: entryIds })
    }).then(r => r.json())
  }

  async getPrograms(): Promise<{ status: string; data: RankingProgram[] }> {
    return fetch('/api/v2/performance-ranking/programs').then(r => r.json())
  }

  async getTrials(programId?: string): Promise<{ status: string; data: RankingTrial[] }> {
    const query = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/performance-ranking/trials${query}`).then(r => r.json())
  }
}

export const performanceRankingAPI = new PerformanceRankingAPI()

// ============================================================================
// Selection Decisions API
// ============================================================================

export interface SelectionCandidate {
  id: string
  name: string
  germplasm_id?: string
  program_id?: string
  program_name?: string
  generation?: string
  gebv: number
  yield_estimate?: number
  traits: string[]
  pedigree?: string
  trial_id?: string
  trial_name?: string
  location?: string
  decision?: 'advance' | 'reject' | 'hold' | null
  decision_notes?: string
  decision_date?: string
}

export interface SelectionStatistics {
  total_candidates: number
  advanced: number
  rejected: number
  on_hold: number
  pending: number
  selection_rate: number
  avg_gebv_advanced?: number
  avg_gebv_rejected?: number
}

export interface SelectionProgram {
  id: string
  name: string
}

export interface SelectionTrial {
  id: string
  name: string
  program_id: string
}

class SelectionDecisionsAPI {
  async getCandidates(params?: {
    program_id?: string
    trial_id?: string
    generation?: string
    decision_status?: string
    min_gebv?: number
    search?: string
  }): Promise<{ status: string; data: SelectionCandidate[]; count: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    if (params?.generation) searchParams.set('generation', params.generation)
    if (params?.decision_status) searchParams.set('decision_status', params.decision_status)
    if (params?.min_gebv) searchParams.set('min_gebv', params.min_gebv.toString())
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/selection-decisions/candidates${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getCandidate(candidateId: string): Promise<{ status: string; data: SelectionCandidate }> {
    return fetch(`/api/v2/selection-decisions/candidates/${candidateId}`).then(r => r.json())
  }

  async recordDecision(candidateId: string, decision: string, notes?: string): Promise<{ success: boolean; message: string }> {
    return fetch(`/api/v2/selection-decisions/candidates/${candidateId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes })
    }).then(r => r.json())
  }

  async recordBulkDecisions(decisions: Array<{ candidate_id: string; decision: string; notes?: string }>): Promise<{
    successful: number
    failed: number
    errors?: string[]
  }> {
    return fetch('/api/v2/selection-decisions/decisions/bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decisions })
    }).then(r => r.json())
  }

  async getStatistics(params?: {
    program_id?: string
    trial_id?: string
  }): Promise<{ status: string; data: SelectionStatistics }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trial_id) searchParams.set('trial_id', params.trial_id)
    const query = searchParams.toString()
    return fetch(`/api/v2/selection-decisions/statistics${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getHistory(params?: {
    limit?: number
    candidate_id?: string
  }): Promise<{ status: string; data: any[]; count: number }> {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.candidate_id) searchParams.set('candidate_id', params.candidate_id)
    const query = searchParams.toString()
    return fetch(`/api/v2/selection-decisions/history${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getPrograms(): Promise<{ status: string; data: SelectionProgram[] }> {
    return fetch('/api/v2/selection-decisions/programs').then(r => r.json())
  }

  async getTrials(programId?: string): Promise<{ status: string; data: SelectionTrial[] }> {
    const query = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/selection-decisions/trials${query}`).then(r => r.json())
  }
}

export const selectionDecisionsAPI = new SelectionDecisionsAPI()


// ============================================================================
// Molecular Breeding API
// ============================================================================

export interface BreedingScheme {
  id: string
  name: string
  type: 'MABC' | 'MARS' | 'GS' | 'Speed'
  status: 'active' | 'completed' | 'planned'
  generation: string
  progress: number
  target_traits: string[]
  crop?: string
  start_date?: string
  end_date?: string
}

export interface IntrogressionLine {
  id: string
  name: string
  donor: string
  recurrent: string
  target_gene: string
  bc_generation: number
  rp_recovery: number
  foreground_status: 'fixed' | 'segregating' | 'absent'
  scheme_id?: string
}

export interface MolecularBreedingStatistics {
  total_schemes: number
  active_schemes: number
  total_lines: number
  fixed_lines: number
  target_genes: number
  avg_progress: number
}

class MolecularBreedingAPI {
  async getSchemes(params?: {
    scheme_type?: string
    status?: string
  }): Promise<{ success: boolean; count: number; schemes: BreedingScheme[] }> {
    const searchParams = new URLSearchParams()
    if (params?.scheme_type) searchParams.set('scheme_type', params.scheme_type)
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString()
    return fetch(`/api/v2/molecular-breeding/schemes${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getScheme(schemeId: string): Promise<{ success: boolean; data: BreedingScheme }> {
    return fetch(`/api/v2/molecular-breeding/schemes/${schemeId}`).then(r => r.json())
  }

  async getLines(params?: {
    scheme_id?: string
    foreground_status?: string
  }): Promise<{ success: boolean; count: number; lines: IntrogressionLine[] }> {
    const searchParams = new URLSearchParams()
    if (params?.scheme_id) searchParams.set('scheme_id', params.scheme_id)
    if (params?.foreground_status) searchParams.set('foreground_status', params.foreground_status)
    const query = searchParams.toString()
    return fetch(`/api/v2/molecular-breeding/lines${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getStatistics(): Promise<{ success: boolean; data: MolecularBreedingStatistics }> {
    return fetch('/api/v2/molecular-breeding/statistics').then(r => r.json())
  }

  async getPyramidingMatrix(schemeId: string): Promise<{ success: boolean; data: any }> {
    return fetch(`/api/v2/molecular-breeding/pyramiding/${schemeId}`).then(r => r.json())
  }
}

export const molecularBreedingAPI = new MolecularBreedingAPI()

// ============================================================================
// Haplotype Analysis API
// ============================================================================

export interface HaplotypeBlock {
  id: string
  block_id: string
  chromosome: string
  start_mb: number
  end_mb: number
  length_kb: number
  n_markers: number
  n_haplotypes: number
  major_haplotype: string
  major_haplotype_freq: number
  diversity: number
  trait?: string
}

export interface Haplotype {
  haplotype_id: string
  block_id: string
  allele_string: string
  frequency: number
  effect?: number
  germplasm?: string[]
}

export interface HaplotypeAssociation {
  id: string
  trait: string
  block_id: string
  chromosome: string
  favorable_haplotype: string
  effect_size: number
  p_value: number
}

export interface HaplotypeDiversitySummary {
  total_blocks: number
  avg_diversity: number
  avg_haplotypes_per_block: number
  total_haplotypes: number
  chromosomes_covered: number
  avg_block_length_kb: number
}

export interface HaplotypeStatistics {
  total_blocks: number
  total_haplotypes: number
  total_associations: number
  favorable_haplotypes: number
  avg_block_length_kb: number
  avg_markers_per_block: number
}

class HaplotypeAnalysisAPI {
  async getBlocks(params?: {
    chromosome?: string
    min_length?: number
  }): Promise<{ success: boolean; count: number; blocks: HaplotypeBlock[] }> {
    const searchParams = new URLSearchParams()
    if (params?.chromosome) searchParams.set('chromosome', params.chromosome)
    if (params?.min_length) searchParams.set('min_length', params.min_length.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/haplotype/blocks${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getBlock(blockId: string): Promise<{ success: boolean; data: HaplotypeBlock & { haplotypes: Haplotype[] } }> {
    return fetch(`/api/v2/haplotype/blocks/${blockId}`).then(r => r.json())
  }

  async getBlockHaplotypes(blockId: string): Promise<{ success: boolean; block_id: string; count: number; haplotypes: Haplotype[] }> {
    return fetch(`/api/v2/haplotype/blocks/${blockId}/haplotypes`).then(r => r.json())
  }

  async getAssociations(params?: {
    trait?: string
    chromosome?: string
  }): Promise<{ success: boolean; count: number; associations: HaplotypeAssociation[] }> {
    const searchParams = new URLSearchParams()
    if (params?.trait) searchParams.set('trait', params.trait)
    if (params?.chromosome) searchParams.set('chromosome', params.chromosome)
    const query = searchParams.toString()
    return fetch(`/api/v2/haplotype/associations${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getFavorableHaplotypes(trait?: string): Promise<{ success: boolean; count: number; favorable_haplotypes: any[] }> {
    const query = trait ? `?trait=${trait}` : ''
    return fetch(`/api/v2/haplotype/favorable${query}`).then(r => r.json())
  }

  async getDiversity(): Promise<{ success: boolean; data: HaplotypeDiversitySummary }> {
    return fetch('/api/v2/haplotype/diversity').then(r => r.json())
  }

  async getStatistics(): Promise<{ success: boolean; data: HaplotypeStatistics }> {
    return fetch('/api/v2/haplotype/statistics').then(r => r.json())
  }

  async getTraits(): Promise<{ success: boolean; count: number; traits: any[] }> {
    return fetch('/api/v2/haplotype/traits').then(r => r.json())
  }
}

export const haplotypeAnalysisAPI = new HaplotypeAnalysisAPI()

// ============================================================================
// QTL Mapping API
// ============================================================================

export interface QTL {
  id: string
  name: string
  trait: string
  chromosome: string
  position: number
  lod: number
  pve: number
  add_effect: number
  confidence_interval?: [number, number]
  flanking_markers?: string[]
  population?: string
}

export interface GWASAssociation {
  marker: string
  trait: string
  chromosome: string
  position: number
  p_value: number
  log_p: number
  effect: number
  maf: number
}

export interface QTLSummary {
  total_qtls: number
  major_qtls: number
  total_pve: number
  average_lod: number
  traits_analyzed: number
}

export interface CandidateGene {
  gene_id: string
  name: string
  chromosome: string
  start: number
  end: number
  function?: string
  annotation?: string
}

export interface GOEnrichment {
  term_id: string
  name: string
  p_value: number
  gene_count: number
  category: string
}

class QTLMappingAPI {
  async getQTLs(params?: {
    trait?: string
    chromosome?: string
    min_lod?: number
    population?: string
  }): Promise<{ qtls: QTL[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.trait) searchParams.set('trait', params.trait)
    if (params?.chromosome) searchParams.set('chromosome', params.chromosome)
    if (params?.min_lod) searchParams.set('min_lod', params.min_lod.toString())
    if (params?.population) searchParams.set('population', params.population)
    const query = searchParams.toString()
    return fetch(`/api/v2/qtl-mapping/qtls${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getQTL(qtlId: string): Promise<QTL> {
    return fetch(`/api/v2/qtl-mapping/qtls/${qtlId}`).then(r => r.json())
  }

  async getCandidateGenes(qtlId: string): Promise<{ qtl_id: string; qtl_name: string; confidence_interval: [number, number]; candidates: CandidateGene[]; total: number }> {
    return fetch(`/api/v2/qtl-mapping/qtls/${qtlId}/candidates`).then(r => r.json())
  }

  async getGWASResults(params?: {
    trait?: string
    chromosome?: string
    min_log_p?: number
    max_p_value?: number
  }): Promise<{ associations: GWASAssociation[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.trait) searchParams.set('trait', params.trait)
    if (params?.chromosome) searchParams.set('chromosome', params.chromosome)
    if (params?.min_log_p) searchParams.set('min_log_p', params.min_log_p.toString())
    if (params?.max_p_value) searchParams.set('max_p_value', params.max_p_value.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/qtl-mapping/gwas${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getManhattanData(trait?: string): Promise<any> {
    const query = trait ? `?trait=${trait}` : ''
    return fetch(`/api/v2/qtl-mapping/manhattan${query}`).then(r => r.json())
  }

  async getLODProfile(chromosome: string, trait?: string): Promise<any> {
    const query = trait ? `?trait=${trait}` : ''
    return fetch(`/api/v2/qtl-mapping/lod-profile/${chromosome}${query}`).then(r => r.json())
  }

  async getGOEnrichment(qtlIds?: string[]): Promise<{ enrichment: GOEnrichment[] }> {
    const query = qtlIds ? `?qtl_ids=${qtlIds.join(',')}` : ''
    return fetch(`/api/v2/qtl-mapping/go-enrichment${query}`).then(r => r.json())
  }

  async getQTLSummary(): Promise<QTLSummary> {
    return fetch('/api/v2/qtl-mapping/summary/qtl').then(r => r.json())
  }

  async getGWASSummary(): Promise<any> {
    return fetch('/api/v2/qtl-mapping/summary/gwas').then(r => r.json())
  }

  async getTraits(): Promise<{ traits: string[] }> {
    return fetch('/api/v2/qtl-mapping/traits').then(r => r.json())
  }

  async getPopulations(): Promise<{ populations: string[] }> {
    return fetch('/api/v2/qtl-mapping/populations').then(r => r.json())
  }
}

export const qtlMappingAPI = new QTLMappingAPI()

// ============================================================================
// Genomic Selection API
// ============================================================================

export interface GSModel {
  id: string
  name: string
  method: string
  trait: string
  accuracy: number
  heritability: number
  markers: number
  status: 'trained' | 'training' | 'pending'
  created_at?: string
}

export interface GEBVPrediction {
  germplasm_id: string
  germplasm_name: string
  gebv: number
  reliability: number
  rank: number
  selected: boolean
}

export interface SelectionResponse {
  expected_response: number
  response_percent: number
  selection_differential: number
  selection_intensity: number
  accuracy: number
  genetic_variance: number
}

export interface GSMethod {
  id: string
  name: string
  description: string
  category?: string
}

export interface GSSummary {
  trained_models: number
  average_accuracy: number
  total_predictions: number
  selected_candidates: number
  traits_covered: string[]
}

class GenomicSelectionAPI {
  async getModels(params?: {
    trait?: string
    method?: string
    status?: string
  }): Promise<{ models: GSModel[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.trait) searchParams.set('trait', params.trait)
    if (params?.method) searchParams.set('method', params.method)
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString()
    return fetch(`/api/v2/genomic-selection/models${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getModel(modelId: string): Promise<GSModel> {
    return fetch(`/api/v2/genomic-selection/models/${modelId}`).then(r => r.json())
  }

  async getPredictions(modelId: string, params?: {
    min_gebv?: number
    min_reliability?: number
    selected_only?: boolean
  }): Promise<{ predictions: GEBVPrediction[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.min_gebv) searchParams.set('min_gebv', params.min_gebv.toString())
    if (params?.min_reliability) searchParams.set('min_reliability', params.min_reliability.toString())
    if (params?.selected_only) searchParams.set('selected_only', 'true')
    const query = searchParams.toString()
    return fetch(`/api/v2/genomic-selection/models/${modelId}/predictions${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getSelectionResponse(modelId: string, selectionIntensity?: number): Promise<SelectionResponse> {
    const query = selectionIntensity ? `?selection_intensity=${selectionIntensity}` : ''
    return fetch(`/api/v2/genomic-selection/models/${modelId}/selection-response${query}`).then(r => r.json())
  }

  async getYieldPredictions(environment?: string): Promise<{ predictions: any[]; total: number }> {
    const query = environment ? `?environment=${environment}` : ''
    return fetch(`/api/v2/genomic-selection/yield-predictions${query}`).then(r => r.json())
  }

  async getCrossPrediction(parent1Id: string, parent2Id: string): Promise<any> {
    return fetch(`/api/v2/genomic-selection/cross-prediction?parent1_id=${parent1Id}&parent2_id=${parent2Id}`).then(r => r.json())
  }

  async getModelComparison(): Promise<{ comparison: any[] }> {
    return fetch('/api/v2/genomic-selection/comparison').then(r => r.json())
  }

  async getSummary(): Promise<GSSummary> {
    return fetch('/api/v2/genomic-selection/summary').then(r => r.json())
  }

  async getMethods(): Promise<{ methods: GSMethod[] }> {
    return fetch('/api/v2/genomic-selection/methods').then(r => r.json())
  }

  async getTraits(): Promise<{ traits: string[] }> {
    return fetch('/api/v2/genomic-selection/traits').then(r => r.json())
  }
}

export const genomicSelectionAPI = new GenomicSelectionAPI()


// ============================================
// FIELD LAYOUT API
// ============================================

export interface FieldStudy {
  studyDbId: string
  studyName: string
  rows: number
  cols: number
  programDbId?: string
  locationDbId?: string
  startDate?: string
  endDate?: string
}

export interface FieldPlot {
  plotNumber: string
  row: number
  col: number
  germplasmName?: string
  germplasmDbId?: string
  blockNumber?: number
  replicate?: number
  entryType?: string
  observationUnitDbId?: string
}

export interface FieldLayoutSummary {
  total_plots: number
  check_plots: number
  test_plots: number
  unique_germplasm: number
  blocks: number
  replicates: number
}

class FieldLayoutAPI {
  async getStudies(params?: {
    program_id?: string
    search?: string
  }): Promise<{ data: FieldStudy[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/field-layout/studies${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getStudy(studyId: string): Promise<{ data: FieldStudy }> {
    return fetch(`/api/v2/field-layout/studies/${studyId}`).then(r => r.json())
  }

  async getLayout(studyId: string): Promise<{
    study: FieldStudy
    plots: FieldPlot[]
    summary: FieldLayoutSummary
  }> {
    return fetch(`/api/v2/field-layout/studies/${studyId}/layout`).then(r => r.json())
  }

  async getPlots(studyId: string, params?: {
    block?: number
    replicate?: number
    entry_type?: string
  }): Promise<{ data: FieldPlot[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.block) searchParams.set('block', params.block.toString())
    if (params?.replicate) searchParams.set('replicate', params.replicate.toString())
    if (params?.entry_type) searchParams.set('entry_type', params.entry_type)
    const query = searchParams.toString()
    return fetch(`/api/v2/field-layout/studies/${studyId}/plots${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getPlot(studyId: string, plotNumber: string): Promise<{ data: FieldPlot }> {
    return fetch(`/api/v2/field-layout/studies/${studyId}/plots/${plotNumber}`).then(r => r.json())
  }

  async updatePlot(studyId: string, plotNumber: string, data: Partial<FieldPlot>): Promise<any> {
    return fetch(`/api/v2/field-layout/studies/${studyId}/plots/${plotNumber}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getGermplasm(): Promise<{ data: Array<{ germplasmDbId: string; germplasmName: string }> }> {
    return fetch('/api/v2/field-layout/germplasm').then(r => r.json())
  }

  async generateLayout(studyId: string, params: {
    design?: string
    blocks?: number
    replicates?: number
  }): Promise<any> {
    const searchParams = new URLSearchParams()
    if (params.design) searchParams.set('design', params.design)
    if (params.blocks) searchParams.set('blocks', params.blocks.toString())
    if (params.replicates) searchParams.set('replicates', params.replicates.toString())
    return fetch(`/api/v2/field-layout/studies/${studyId}/generate?${searchParams}`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async exportLayout(studyId: string, format: string = 'csv'): Promise<any> {
    return fetch(`/api/v2/field-layout/export/${studyId}?format=${format}`).then(r => r.json())
  }
}

export const fieldLayoutAPI = new FieldLayoutAPI()

// ============================================
// TRIAL SUMMARY API
// ============================================

export interface TrialInfo {
  trialDbId: string
  trialName: string
  programDbId: string
  programName: string
  startDate: string
  endDate: string
  locations: number
  entries: number
  traits: number
  observations: number
  completionRate: number
  leadScientist: string
}

export interface TopPerformer {
  rank: number
  germplasmDbId: string
  germplasmName: string
  yield_value: number
  change_percent: string
  traits: string[]
}

export interface TraitSummaryItem {
  trait: string
  mean: number
  cv: number
  lsd: number
  fValue: number
  significance: string
}

export interface LocationPerformance {
  locationDbId: string
  locationName: string
  entries: number
  meanYield: number
  cv: number
  completionRate: number
}

export interface TrialStatistics {
  grand_mean: number
  overall_cv: number
  heritability: number
  genetic_variance: number
  error_variance: number
  lsd_5_percent: number
  selection_intensity: number
  expected_gain: number
  anova?: any
}

class TrialSummaryAPI {
  async getTrials(params?: {
    program_id?: string
    status?: string
  }): Promise<{ data: TrialInfo[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.status) searchParams.set('status', params.status)
    const query = searchParams.toString()
    return fetch(`/api/v2/trial-summary/trials${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getTrial(trialId: string): Promise<{ data: TrialInfo }> {
    return fetch(`/api/v2/trial-summary/trials/${trialId}`).then(r => r.json())
  }

  async getSummary(trialId: string): Promise<{
    trial: TrialInfo
    topPerformers: TopPerformer[]
    traitSummary: TraitSummaryItem[]
    locationPerformance: LocationPerformance[]
    statistics: TrialStatistics
  }> {
    return fetch(`/api/v2/trial-summary/trials/${trialId}/summary`).then(r => r.json())
  }

  async getTopPerformers(trialId: string, params?: {
    limit?: number
    trait?: string
  }): Promise<{ data: TopPerformer[]; trait: string }> {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.trait) searchParams.set('trait', params.trait)
    const query = searchParams.toString()
    return fetch(`/api/v2/trial-summary/trials/${trialId}/top-performers${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getTraitSummary(trialId: string): Promise<{ data: TraitSummaryItem[] }> {
    return fetch(`/api/v2/trial-summary/trials/${trialId}/traits`).then(r => r.json())
  }

  async getLocationPerformance(trialId: string): Promise<{ data: LocationPerformance[] }> {
    return fetch(`/api/v2/trial-summary/trials/${trialId}/locations`).then(r => r.json())
  }

  async getStatistics(trialId: string): Promise<TrialStatistics> {
    return fetch(`/api/v2/trial-summary/trials/${trialId}/statistics`).then(r => r.json())
  }

  async exportSummary(trialId: string, format: string = 'pdf', sections?: string[]): Promise<any> {
    const searchParams = new URLSearchParams()
    searchParams.set('format', format)
    if (sections) searchParams.set('sections', sections.join(','))
    return fetch(`/api/v2/trial-summary/trials/${trialId}/export?${searchParams}`, {
      method: 'POST'
    }).then(r => r.json())
  }
}

export const trialSummaryAPI = new TrialSummaryAPI()

// ============================================
// DATA VISUALIZATION API
// ============================================

export interface ChartConfig {
  id: string
  name: string
  type: string
  dataSource: string
  description?: string
  createdAt: string
  updatedAt: string
  createdBy: string
  isPublic: boolean
  config: Record<string, any>
}

export interface ChartData {
  labels: string[]
  datasets: Array<{
    label?: string
    data: any[]
    backgroundColor?: string | string[]
    borderColor?: string
    fill?: boolean
  }>
  options: Record<string, any>
}

export interface DataSourceInfo {
  id: string
  name: string
  type: string
  recordCount: number
  lastUpdated: string
}

export interface ChartTypeInfo {
  id: string
  name: string
  icon: string
  description: string
}

class DataVisualizationAPI {
  async getCharts(params?: {
    type?: string
    data_source?: string
    search?: string
    public_only?: boolean
  }): Promise<{ data: ChartConfig[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.type) searchParams.set('type', params.type)
    if (params?.data_source) searchParams.set('data_source', params.data_source)
    if (params?.search) searchParams.set('search', params.search)
    if (params?.public_only) searchParams.set('public_only', 'true')
    const query = searchParams.toString()
    return fetch(`/api/v2/visualizations/charts${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getChart(chartId: string): Promise<{ data: ChartConfig }> {
    return fetch(`/api/v2/visualizations/charts/${chartId}`).then(r => r.json())
  }

  async createChart(data: Partial<ChartConfig>): Promise<any> {
    return fetch('/api/v2/visualizations/charts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateChart(chartId: string, data: Partial<ChartConfig>): Promise<any> {
    return fetch(`/api/v2/visualizations/charts/${chartId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteChart(chartId: string): Promise<any> {
    return fetch(`/api/v2/visualizations/charts/${chartId}`, {
      method: 'DELETE'
    }).then(r => r.json())
  }

  async getChartData(chartId: string, limit?: number): Promise<ChartData> {
    const query = limit ? `?limit=${limit}` : ''
    return fetch(`/api/v2/visualizations/charts/${chartId}/data${query}`).then(r => r.json())
  }

  async getDataSources(): Promise<{ data: DataSourceInfo[] }> {
    return fetch('/api/v2/visualizations/data-sources').then(r => r.json())
  }

  async getChartTypes(): Promise<{ data: ChartTypeInfo[] }> {
    return fetch('/api/v2/visualizations/chart-types').then(r => r.json())
  }

  async getStatistics(): Promise<{
    total_charts: number
    by_type: Record<string, number>
    public_charts: number
    private_charts: number
    data_sources: number
  }> {
    return fetch('/api/v2/visualizations/statistics').then(r => r.json())
  }

  async previewChart(params: {
    chart_type: string
    data_source: string
    x_axis?: string
    y_axis?: string
    group_by?: string
  }): Promise<any> {
    const searchParams = new URLSearchParams()
    searchParams.set('chart_type', params.chart_type)
    searchParams.set('data_source', params.data_source)
    if (params.x_axis) searchParams.set('x_axis', params.x_axis)
    if (params.y_axis) searchParams.set('y_axis', params.y_axis)
    if (params.group_by) searchParams.set('group_by', params.group_by)
    return fetch(`/api/v2/visualizations/preview?${searchParams}`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async exportChart(chartId: string, format: string = 'png', width?: number, height?: number): Promise<any> {
    const searchParams = new URLSearchParams()
    searchParams.set('format', format)
    if (width) searchParams.set('width', width.toString())
    if (height) searchParams.set('height', height.toString())
    return fetch(`/api/v2/visualizations/charts/${chartId}/export?${searchParams}`, {
      method: 'POST'
    }).then(r => r.json())
  }
}

export const dataVisualizationAPI = new DataVisualizationAPI()

// ============================================
// ANALYTICS DASHBOARD API
// ============================================

export interface AnalyticsKPI {
  title: string
  value: string
  change: number
  trend: 'up' | 'down'
  description: string
}

export interface GeneticGainData {
  year: number
  gain: number
  cumulative: number
  target: number
}

export interface HeritabilityData {
  trait: string
  value: number
  se?: number
}

export interface SelectionResponseData {
  generation: number
  mean: number
  variance: number
  selected: number
}

export interface CorrelationMatrix {
  traits: string[]
  matrix: number[][]
}

export interface AnalyticsSummary {
  total_trials: number
  active_studies: number
  germplasm_entries: number
  observations_this_month: number
  genetic_gain_rate: number
  data_quality_score: number
  selection_intensity: number
  breeding_cycle_days: number
}

export interface QuickInsight {
  id: string
  type: string
  title: string
  description: string
  action_label?: string
  action_route?: string
  created_at: string
}

class AnalyticsDashboardAPI {
  async getAnalytics(params?: {
    program_id?: string
    crop?: string
    year_start?: number
    year_end?: number
  }): Promise<{
    genetic_gain: GeneticGainData[]
    heritabilities: HeritabilityData[]
    selection_response: SelectionResponseData[]
    correlations: CorrelationMatrix
    summary: AnalyticsSummary
    insights: QuickInsight[]
  }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.crop) searchParams.set('crop', params.crop)
    if (params?.year_start) searchParams.set('year_start', params.year_start.toString())
    if (params?.year_end) searchParams.set('year_end', params.year_end.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getSummary(programId?: string): Promise<AnalyticsSummary> {
    const query = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/analytics/summary${query}`).then(r => r.json())
  }

  async getGeneticGain(params?: {
    program_id?: string
    trait?: string
    years?: number
  }): Promise<{ data: GeneticGainData[]; trait: string; unit: string }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.trait) searchParams.set('trait', params.trait)
    if (params?.years) searchParams.set('years', params.years.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics/genetic-gain${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getHeritabilities(params?: {
    program_id?: string
    study_id?: string
  }): Promise<{ data: HeritabilityData[] }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.study_id) searchParams.set('study_id', params.study_id)
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics/heritabilities${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getCorrelations(params?: {
    program_id?: string
    traits?: string[]
  }): Promise<{ traits: string[]; matrix: number[][]; method: string }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.traits) searchParams.set('traits', params.traits.join(','))
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics/correlations${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getSelectionResponse(params?: {
    program_id?: string
    generations?: number
  }): Promise<{ data: SelectionResponseData[]; trait: string; unit: string }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.generations) searchParams.set('generations', params.generations.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics/selection-response${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getInsights(params?: {
    program_id?: string
    limit?: number
  }): Promise<{ insights: QuickInsight[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.program_id) searchParams.set('program_id', params.program_id)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/analytics/insights${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async runGBLUP(params: {
    program_id?: string
    trait: string
  }): Promise<{ id: string; name: string; status: string; progress: number; engine: string }> {
    const searchParams = new URLSearchParams()
    if (params.program_id) searchParams.set('program_id', params.program_id)
    searchParams.set('trait', params.trait)
    return fetch(`/api/v2/analytics/compute/gblup?${searchParams}`, {
      method: 'POST'
    }).then(r => r.json())
  }

  async getComputeJobStatus(jobId: string): Promise<any> {
    return fetch(`/api/v2/analytics/compute/${jobId}`).then(r => r.json())
  }

  async getVeenaSummary(programId?: string): Promise<{
    summary: string
    generated_at: string
    confidence: number
    key_metrics: Record<string, any>
  }> {
    const query = programId ? `?program_id=${programId}` : ''
    return fetch(`/api/v2/analytics/veena-summary${query}`).then(r => r.json())
  }
}

export const analyticsDashboardAPI = new AnalyticsDashboardAPI()


// ============================================
// LINKAGE DISEQUILIBRIUM API
// ============================================

export interface LDPair {
  marker1: string
  marker2: string
  chromosome: string
  distance: number
  r2: number
  dprime: number
}

export interface LDDecayPoint {
  distance: number
  mean_r2: number
  n_pairs: number
}

export interface LDChromosomeStat {
  chromosome: string
  mean_r2: number
  n_pairs: number
}

export interface LDData {
  n_markers: number
  n_pairs: number
  n_high_ld: number
  mean_r2: number
  ld_decay_distance: number
  pairs: LDPair[]
  decay_curve: LDDecayPoint[]
  chromosome_stats: LDChromosomeStat[]
}

class LinkageDisequilibriumAPI {
  async getLDData(): Promise<LDData> {
    return fetch('/api/v2/gwas/ld/demo').then(r => r.json())
  }

  async calculateLD(params: {
    markers: string[]
    chromosome?: string
    max_distance?: number
  }): Promise<any> {
    return fetch('/api/v2/gwas/ld', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }

  async runLDPruning(params: {
    markers: string[]
    r2_threshold?: number
    window_size?: number
    step_size?: number
  }): Promise<any> {
    return fetch('/api/v2/gwas/ld/pruning', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(r => r.json())
  }
}

export const linkageDisequilibriumAPI = new LinkageDisequilibriumAPI()

// ============================================
// BREEDING VALUES API
// ============================================

export interface BreedingValueEntry {
  id: string
  name: string
  ebv: number
  accuracy: number
  rank: number
  parent_mean?: number
  mendelian_sampling?: number
}

export interface BreedingValueAnalysis {
  id: string
  trait: string
  method: string
  heritability: number
  genetic_variance: number
  mean: number
  breeding_values: BreedingValueEntry[]
}

class BreedingValuesAPI {
  async listAnalyses(): Promise<{ data: Array<{ id: string; trait: string; method: string; n_individuals: number; created_at: string }> }> {
    return fetch('/api/v2/breeding-value/analyses').then(r => r.json())
  }

  async getAnalysis(analysisId: string): Promise<{ data: BreedingValueAnalysis | null }> {
    return fetch(`/api/v2/breeding-value/analyses/${analysisId}`).then(r => r.json())
  }

  async getMethods(): Promise<{ data: Array<{ id: string; name: string; description: string }> }> {
    return fetch('/api/v2/breeding-value/methods').then(r => r.json())
  }

  async estimateBLUP(data: {
    phenotypes: Array<{ id: string; value: number }>
    trait?: string
    heritability?: number
    pedigree?: Array<{ id: string; sire?: string; dam?: string }>
  }): Promise<any> {
    return fetch('/api/v2/breeding-value/blup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async estimateGBLUP(data: {
    phenotypes: Array<{ id: string; value: number }>
    markers: Array<{ id: string; markers: number[] }>
    trait?: string
    heritability?: number
  }): Promise<any> {
    return fetch('/api/v2/breeding-value/gblup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async predictCross(data: {
    parent1_ebv: number
    parent2_ebv: number
    trait_mean: number
    heritability?: number
  }): Promise<any> {
    return fetch('/api/v2/breeding-value/predict-cross', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async rankCandidates(data: {
    breeding_values: Array<{ id: string; ebv: number; [key: string]: any }>
    selection_intensity?: number
    ebv_key?: string
  }): Promise<any> {
    return fetch('/api/v2/breeding-value/rank', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }
}

export const breedingValuesAPI = new BreedingValuesAPI()

// ============================================
// PHENOTYPE COMPARISON API
// ============================================

export interface PhenotypeGermplasm {
  germplasmDbId: string
  germplasmName: string
  defaultDisplayName?: string
  species?: string
  isCheck?: boolean
}

export interface PhenotypeObservation {
  observationDbId: string
  germplasmDbId: string
  observationVariableName: string
  observationVariableDbId: string
  value: string
}

class PhenotypeComparisonAPI {
  async getGermplasm(params?: {
    limit?: number
    search?: string
    species?: string
  }): Promise<{ result: { data: PhenotypeGermplasm[] } }> {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.species) searchParams.set('species', params.species)
    const query = searchParams.toString()
    return fetch(`/api/v2/phenotype-comparison/germplasm${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getObservations(germplasmIds: string[], traits?: string[]): Promise<{ result: { data: PhenotypeObservation[] } }> {
    return fetch('/api/v2/phenotype-comparison/observations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ germplasm_ids: germplasmIds, traits })
    }).then(r => r.json())
  }

  async getTraits(): Promise<{
    data: Array<{ id: string; name: string; unit: string; higher_is_better: boolean }>
  }> {
    return fetch('/api/v2/phenotype-comparison/traits').then(r => r.json())
  }

  async compare(germplasmIds: string[], checkId?: string): Promise<{
    data: Array<{
      germplasm_id: string
      germplasm_name: string
      traits: Record<string, number>
      vs_check?: Record<string, number>
    }>
    check_id: string
    check_name: string
  }> {
    return fetch('/api/v2/phenotype-comparison/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ germplasm_ids: germplasmIds, check_id: checkId })
    }).then(r => r.json())
  }

  async getStatistics(germplasmIds?: string[]): Promise<any> {
    const query = germplasmIds ? `?germplasm_ids=${germplasmIds.join(',')}` : ''
    return fetch(`/api/v2/phenotype-comparison/statistics${query}`).then(r => r.json())
  }
}

export const phenotypeComparisonAPI = new PhenotypeComparisonAPI()


// ============================================
// GERMPLASM ATTRIBUTES API (BrAPI)
// ============================================

export interface GermplasmAttribute {
  attributeDbId: string
  attributeName: string
  attributeCategory?: string
  attributeDescription?: string
  dataType?: string
  commonCropName?: string
  values?: string[]
}

class GermplasmAttributesAPI {
  async getAttributes(params?: {
    attributeCategory?: string
    pageSize?: number
    page?: number
  }): Promise<{ result: { data: GermplasmAttribute[] } }> {
    const searchParams = new URLSearchParams()
    if (params?.attributeCategory) searchParams.set('attributeCategory', params.attributeCategory)
    if (params?.pageSize) searchParams.set('pageSize', params.pageSize.toString())
    if (params?.page) searchParams.set('page', params.page.toString())
    const query = searchParams.toString()
    return fetch(`/brapi/v2/attributes${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getAttribute(attributeDbId: string): Promise<{ result: GermplasmAttribute }> {
    return fetch(`/brapi/v2/attributes/${attributeDbId}`).then(r => r.json())
  }

  async getCategories(): Promise<{ result: { data: string[] } }> {
    return fetch('/brapi/v2/attributes/categories').then(r => r.json())
  }

  async createAttribute(data: Partial<GermplasmAttribute>): Promise<{ result: { data: GermplasmAttribute[] } }> {
    return fetch('/brapi/v2/attributes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([data])
    }).then(r => r.json())
  }

  async updateAttribute(attributeDbId: string, data: Partial<GermplasmAttribute>): Promise<{ result: GermplasmAttribute }> {
    return fetch(`/brapi/v2/attributes/${attributeDbId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }
}

export const germplasmAttributesAPI = new GermplasmAttributesAPI()

// ============================================
// CROSSING PROJECTS API (BrAPI)
// ============================================

export interface CrossingProject {
  crossingProjectDbId: string
  crossingProjectName: string
  crossingProjectDescription?: string
  programDbId?: string
  programName?: string
  commonCropName?: string
  plannedCrossCount?: number
  completedCrossCount?: number
  status?: string
  startDate?: string
  endDate?: string
}

class CrossingProjectsAPI {
  async getProjects(params?: {
    commonCropName?: string
    programDbId?: string
    pageSize?: number
    page?: number
  }): Promise<{ result: { data: CrossingProject[] } }> {
    const searchParams = new URLSearchParams()
    if (params?.commonCropName) searchParams.set('commonCropName', params.commonCropName)
    if (params?.programDbId) searchParams.set('programDbId', params.programDbId)
    if (params?.pageSize) searchParams.set('pageSize', params.pageSize.toString())
    if (params?.page) searchParams.set('page', params.page.toString())
    const query = searchParams.toString()
    return fetch(`/brapi/v2/crossingprojects${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getProject(crossingProjectDbId: string): Promise<{ result: CrossingProject }> {
    return fetch(`/brapi/v2/crossingprojects/${crossingProjectDbId}`).then(r => r.json())
  }

  async createProject(data: Partial<CrossingProject>): Promise<{ result: { data: CrossingProject[] } }> {
    return fetch('/brapi/v2/crossingprojects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([data])
    }).then(r => r.json())
  }

  async updateProject(crossingProjectDbId: string, data: Partial<CrossingProject>): Promise<{ result: CrossingProject }> {
    return fetch(`/brapi/v2/crossingprojects/${crossingProjectDbId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async deleteProject(crossingProjectDbId: string): Promise<void> {
    return fetch(`/brapi/v2/crossingprojects/${crossingProjectDbId}`, {
      method: 'DELETE'
    }).then(() => undefined)
  }
}

export const crossingProjectsAPI = new CrossingProjectsAPI()

// ============================================
// HARVEST PLANNER API
// ============================================

export interface HarvestTask {
  id: string
  plot: string
  germplasm: string
  expectedDate: string
  status: 'pending' | 'ready' | 'harvested' | 'processed'
  priority: 'high' | 'medium' | 'low'
  notes: string
  completed: boolean
}

class HarvestPlannerAPI {
  async getTasks(params?: {
    status?: string
    priority?: string
    plot?: string
  }): Promise<{ data: HarvestTask[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.priority) searchParams.set('priority', params.priority)
    if (params?.plot) searchParams.set('plot', params.plot)
    const query = searchParams.toString()
    return fetch(`/api/v2/harvest/tasks${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getTask(taskId: string): Promise<{ data: HarvestTask }> {
    return fetch(`/api/v2/harvest/tasks/${taskId}`).then(r => r.json())
  }

  async createTask(data: Partial<HarvestTask>): Promise<{ data: HarvestTask }> {
    return fetch('/api/v2/harvest/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateTask(taskId: string, data: Partial<HarvestTask>): Promise<{ data: HarvestTask }> {
    return fetch(`/api/v2/harvest/tasks/${taskId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getStats(): Promise<{
    total: number
    pending: number
    ready: number
    harvested: number
    processed: number
    progress: number
  }> {
    return fetch('/api/v2/harvest/stats').then(r => r.json())
  }
}

export const harvestPlannerAPI = new HarvestPlannerAPI()

// ============================================
// VARIETY COMPARISON API
// ============================================

export interface VarietyData {
  id: string
  name: string
  type: 'check' | 'test' | 'elite'
  trials: number
  locations: number
  years: number[]
  avgYield: number
  stability: number
  traits: Record<string, number>
}

class VarietyComparisonAPI {
  async getVarieties(params?: {
    type?: string
    crop?: string
    year?: number
  }): Promise<{ data: VarietyData[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.type) searchParams.set('type', params.type)
    if (params?.crop) searchParams.set('crop', params.crop)
    if (params?.year) searchParams.set('year', params.year.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/variety-comparison/varieties${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getVariety(varietyId: string): Promise<{ data: VarietyData }> {
    return fetch(`/api/v2/variety-comparison/varieties/${varietyId}`).then(r => r.json())
  }

  async compare(varietyIds: string[], checkId?: string): Promise<{
    data: Array<{
      variety: VarietyData
      vs_check: { yield_diff: number; yield_pct: number }
    }>
    check: VarietyData
  }> {
    return fetch('/api/v2/variety-comparison/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variety_ids: varietyIds, check_id: checkId })
    }).then(r => r.json())
  }

  async getTraitComparison(varietyIds: string[], traits?: string[]): Promise<{
    data: Record<string, Record<string, number>>
    traits: string[]
  }> {
    return fetch('/api/v2/variety-comparison/traits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variety_ids: varietyIds, traits })
    }).then(r => r.json())
  }
}

export const varietyComparisonAPI = new VarietyComparisonAPI()

// ============================================
// SAMPLE TRACKING API
// ============================================

export interface Sample {
  id: string
  sampleId: string
  type: 'leaf' | 'seed' | 'dna'
  source: string
  status: 'collected' | 'processing' | 'stored' | 'shipped'
  location: string
  collectedAt: string
  processedAt?: string
}

class SampleTrackingAPI {
  async getSamples(params?: {
    status?: string
    type?: string
    search?: string
  }): Promise<{ data: Sample[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.type) searchParams.set('type', params.type)
    if (params?.search) searchParams.set('search', params.search)
    const query = searchParams.toString()
    return fetch(`/api/v2/samples/tracking${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getSample(sampleId: string): Promise<{ data: Sample }> {
    return fetch(`/api/v2/samples/tracking/${sampleId}`).then(r => r.json())
  }

  async createSample(data: Partial<Sample>): Promise<{ data: Sample }> {
    return fetch('/api/v2/samples/tracking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateSample(sampleId: string, data: Partial<Sample>): Promise<{ data: Sample }> {
    return fetch(`/api/v2/samples/tracking/${sampleId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async getStats(): Promise<{
    total: number
    collected: number
    processing: number
    stored: number
    shipped: number
  }> {
    return fetch('/api/v2/samples/tracking/stats').then(r => r.json())
  }
}

export const sampleTrackingAPI = new SampleTrackingAPI()

// ============================================
// PEDIGREE VIEWER API
// ============================================

export interface PedigreeNode {
  id: string
  name: string
  type: 'germplasm' | 'cross' | 'unknown'
  generation: number
  parent1?: PedigreeNode
  parent2?: PedigreeNode
  children?: PedigreeNode[]
}

class PedigreeViewerAPI {
  async getPedigree(germplasmId: string, generations?: number): Promise<{ data: PedigreeNode }> {
    const query = generations ? `?generations=${generations}` : ''
    return fetch(`/api/v2/pedigree/tree/${germplasmId}${query}`).then(r => r.json())
  }

  async getGermplasmList(params?: {
    search?: string
    limit?: number
  }): Promise<{ data: Array<{ id: string; name: string }> }> {
    const searchParams = new URLSearchParams()
    if (params?.search) searchParams.set('search', params.search)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    const query = searchParams.toString()
    return fetch(`/api/v2/pedigree/germplasm${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getAncestors(germplasmId: string, generations?: number): Promise<{ data: PedigreeNode[] }> {
    const query = generations ? `?generations=${generations}` : ''
    return fetch(`/api/v2/pedigree/ancestors/${germplasmId}${query}`).then(r => r.json())
  }

  async getDescendants(germplasmId: string, generations?: number): Promise<{ data: PedigreeNode[] }> {
    const query = generations ? `?generations=${generations}` : ''
    return fetch(`/api/v2/pedigree/descendants/${germplasmId}${query}`).then(r => r.json())
  }
}

export const pedigreeViewerAPI = new PedigreeViewerAPI()

// ============================================
// SEED REQUEST API
// ============================================

export interface SeedRequest {
  id: string
  requester: string
  organization: string
  germplasm: string
  quantity: number
  unit: string
  purpose: string
  status: 'pending' | 'approved' | 'shipped' | 'delivered' | 'rejected'
  requestDate: string
}

class SeedRequestAPI {
  async getRequests(params?: {
    status?: string
    requester?: string
  }): Promise<{ data: SeedRequest[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.requester) searchParams.set('requester', params.requester)
    const query = searchParams.toString()
    return fetch(`/api/v2/seed-requests${query ? `?${query}` : ''}`).then(r => r.json())
  }

  async getRequest(requestId: string): Promise<{ data: SeedRequest }> {
    return fetch(`/api/v2/seed-requests/${requestId}`).then(r => r.json())
  }

  async createRequest(data: Partial<SeedRequest>): Promise<{ data: SeedRequest }> {
    return fetch('/api/v2/seed-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  async updateStatus(requestId: string, status: SeedRequest['status']): Promise<{ data: SeedRequest }> {
    return fetch(`/api/v2/seed-requests/${requestId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    }).then(r => r.json())
  }

  async getStats(): Promise<{
    total: number
    pending: number
    approved: number
    shipped: number
    delivered: number
  }> {
    return fetch('/api/v2/seed-requests/stats').then(r => r.json())
  }
}

export const seedRequestAPI = new SeedRequestAPI()

// ============================================
// WORKSPACE PREFERENCES API
// Gateway-Workspace Architecture
// ============================================

export interface WorkspacePreferences {
  user_id: number
  default_workspace: string | null
  recent_workspaces: string[]
  show_gateway_on_login: boolean
  last_workspace: string | null
  updated_at: string
}

export interface UpdateWorkspacePreferencesRequest {
  default_workspace?: string | null
  recent_workspaces?: string[]
  show_gateway_on_login?: boolean
  last_workspace?: string | null
}

class WorkspacePreferencesAPI {
  private baseUrl = '/api/v2/profile'

  private getAuthHeaders(): HeadersInit {
    const token = apiClient.getToken()
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  }

  /**
   * Get user workspace preferences
   */
  async getPreferences(userId: number = 1): Promise<{ status: string; data: WorkspacePreferences }> {
    try {
      const response = await fetch(`${this.baseUrl}/workspace?user_id=${userId}`, {
        headers: this.getAuthHeaders()
      })
      if (!response.ok && response.status !== 401) {
        // Return default preferences on error (except auth errors)
        return { status: 'error', data: { user_id: userId, default_workspace: null, recent_workspaces: [], show_gateway_on_login: true, last_workspace: null, updated_at: '' } }
      }
      return response.json()
    } catch {
      // Return default preferences on network error
      return { status: 'error', data: { user_id: userId, default_workspace: null, recent_workspaces: [], show_gateway_on_login: true, last_workspace: null, updated_at: '' } }
    }
  }

  /**
   * Update workspace preferences
   */
  async updatePreferences(
    data: UpdateWorkspacePreferencesRequest,
    userId: number = 1,
    organizationId: number = 1
  ): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/workspace?user_id=${userId}&organization_id=${organizationId}`, {
        method: 'PATCH',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(data)
      })
      if (!response.ok) {
        return { status: 'error', message: 'Failed to update preferences' }
      }
      return response.json()
    } catch {
      return { status: 'error', message: 'Network error' }
    }
  }

  /**
   * Set default workspace
   */
  async setDefaultWorkspace(
    workspaceId: string,
    userId: number = 1,
    organizationId: number = 1
  ): Promise<{ status: string; message: string; data: { default_workspace: string; show_gateway_on_login: boolean } }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/workspace/default?workspace_id=${workspaceId}&user_id=${userId}&organization_id=${organizationId}`,
        { method: 'PUT', headers: this.getAuthHeaders() }
      )
      if (!response.ok) {
        return { status: 'error', message: 'Failed to set default workspace', data: { default_workspace: workspaceId, show_gateway_on_login: false } }
      }
      return response.json()
    } catch {
      return { status: 'error', message: 'Network error', data: { default_workspace: workspaceId, show_gateway_on_login: false } }
    }
  }

  /**
   * Clear default workspace (show gateway on login)
   */
  async clearDefaultWorkspace(userId: number = 1): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/workspace/default?user_id=${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      })
      if (!response.ok) {
        return { status: 'error', message: 'Failed to clear default workspace' }
      }
      return response.json()
    } catch {
      return { status: 'error', message: 'Network error' }
    }
  }

  /**
   * Record workspace switch (updates last_workspace and recent_workspaces)
   */
  async recordWorkspaceSwitch(
    workspaceId: string,
    userId: number = 1,
    organizationId: number = 1
  ): Promise<{ status: string; message: string }> {
    return this.updatePreferences(
      { last_workspace: workspaceId },
      userId,
      organizationId
    )
  }
}

export const workspacePreferencesAPI = new WorkspacePreferencesAPI()


// ============ WAREHOUSE MANAGEMENT API ============

interface StorageLocation {
  id: string
  code: string
  name: string
  storage_type: 'cold' | 'ambient' | 'controlled' | 'cryo'
  capacity_kg: number
  used_kg: number
  current_temperature: number | null
  current_humidity: number | null
  target_temperature: number | null
  target_humidity: number | null
  lot_count: number
  status: 'normal' | 'warning' | 'critical' | 'maintenance'
  utilization_percent: number
  created_at: string
  updated_at: string
}

interface WarehouseSummary {
  total_locations: number
  total_capacity_kg: number
  total_used_kg: number
  utilization_percent: number
  total_lots: number
  locations_by_type: Record<string, { count: number; capacity_kg: number; used_kg: number }>
  alerts_count: number
}

interface WarehouseAlert {
  id: string
  location_id: string
  location_name: string
  alert_type: 'capacity' | 'temperature' | 'humidity'
  severity: 'warning' | 'critical'
  message: string
  current_value: number
  threshold_value: number
  created_at: string
}

class WarehouseAPI {
  private baseUrl = '/api/v2/warehouse'

  /**
   * List all storage locations
   */
  async getLocations(params?: { storage_type?: string; status?: string }): Promise<StorageLocation[]> {
    const searchParams = new URLSearchParams()
    if (params?.storage_type) searchParams.append('storage_type', params.storage_type)
    if (params?.status) searchParams.append('status', params.status)
    const query = searchParams.toString()
    return fetch(`${this.baseUrl}/locations${query ? `?${query}` : ''}`).then(r => r.json())
  }

  /**
   * Get a specific storage location
   */
  async getLocation(locationId: string): Promise<StorageLocation> {
    return fetch(`${this.baseUrl}/locations/${locationId}`).then(r => r.json())
  }

  /**
   * Create a new storage location
   */
  async createLocation(data: {
    name: string
    code: string
    storage_type: 'cold' | 'ambient' | 'controlled' | 'cryo'
    capacity_kg: number
    target_temperature?: number
    target_humidity?: number
    description?: string
  }): Promise<StorageLocation> {
    return fetch(`${this.baseUrl}/locations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  /**
   * Update a storage location
   */
  async updateLocation(locationId: string, data: {
    name?: string
    storage_type?: string
    capacity_kg?: number
    used_kg?: number
    current_temperature?: number
    current_humidity?: number
    target_temperature?: number
    target_humidity?: number
    status?: string
    description?: string
  }): Promise<StorageLocation> {
    return fetch(`${this.baseUrl}/locations/${locationId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }

  /**
   * Delete a storage location
   */
  async deleteLocation(locationId: string): Promise<{ message: string; id: string }> {
    return fetch(`${this.baseUrl}/locations/${locationId}`, {
      method: 'DELETE'
    }).then(r => r.json())
  }

  /**
   * Get warehouse summary statistics
   */
  async getSummary(): Promise<WarehouseSummary> {
    return fetch(`${this.baseUrl}/summary`).then(r => r.json())
  }

  /**
   * Get warehouse alerts
   */
  async getAlerts(severity?: 'warning' | 'critical'): Promise<WarehouseAlert[]> {
    const query = severity ? `?severity=${severity}` : ''
    return fetch(`${this.baseUrl}/alerts${query}`).then(r => r.json())
  }
}

export const warehouseAPI = new WarehouseAPI()

/**
 * Quality Control API
 * Endpoints for seed quality testing and certification
 */
class QualityControlAPI {
  private baseUrl = '/api/v2/quality'

  /**
   * Get QC samples by status
   */
  async getQCSamples(status?: string): Promise<{ samples: any[] }> {
    const query = status ? `?status=${status}` : ''
    return fetch(`${this.baseUrl}/samples${query}`).then(r => r.json())
  }

  /**
   * Get QC certificates
   */
  async getQCCertificates(): Promise<{ certificates: any[] }> {
    return fetch(`${this.baseUrl}/certificates`).then(r => r.json())
  }

  /**
   * Issue a QC certificate
   */
  async issueQCCertificate(data: {
    sample_id: string
    seed_class: string
    valid_months: number
  }): Promise<{ certificate_id: string; message: string }> {
    return fetch(`${this.baseUrl}/certificates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.json())
  }
}

export const qualityControlAPI = new QualityControlAPI()
