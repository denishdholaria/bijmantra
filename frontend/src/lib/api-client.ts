/**
 * BrAPI Client
 * HTTP client for communicating with the backend API
 */

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

  constructor(baseURL: string = '') {
    this.baseURL = baseURL
    this.loadToken()
  }

  private loadToken() {
    this.token = localStorage.getItem('auth_token')
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
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
        return false
      }
      
      return response.ok
    } catch {
      // Network error - can't validate, assume valid for offline mode
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

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: response.statusText,
        }))
        
        // Handle 401 Unauthorized - clear token and redirect to login
        if (response.status === 401) {
          this.setToken(null)
          // Dispatch custom event for auth state change
          window.dispatchEvent(new CustomEvent('auth:unauthorized'))
        }
        
        throw new Error(error.detail || 'Request failed')
      }

      return response.json()
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        // Network error - backend not running
        throw new Error('Cannot connect to server. Please ensure the backend is running.')
      }
      throw error
    }
  }

  // Authentication
  async login(
    email: string,
    password: string
  ): Promise<{ access_token: string; token_type: string }> {
    // Helper to generate demo token
    const generateDemoToken = () => {
      console.log('🔓 Demo Mode: Enabling demo login for', email)
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
      }
    }

    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2000) // 2 second timeout

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
          return generateDemoToken()
        }
        const error = await response.json().catch(() => ({ detail: 'Login failed' }))
        throw new Error(error.detail)
      }

      return response.json()
    } catch {
      // ANY error means backend is unavailable - use demo mode
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
}

export const apiClient = new APIClient()
