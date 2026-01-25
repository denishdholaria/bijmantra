/**
 * API Helper for E2E Tests
 * 
 * Direct API interactions for:
 * - Test data setup/teardown
 * - API contract validation
 * - Backend health checks
 */

import { APIRequestContext } from '@playwright/test'

const API_BASE_URL = process.env.E2E_API_URL || 'http://localhost:8000'

export class ApiHelper {
  private request: APIRequestContext
  private token: string | null = null
  
  constructor(request: APIRequestContext) {
    this.request = request
  }
  
  /**
   * Set authentication token
   */
  setToken(token: string) {
    this.token = token
  }
  
  /**
   * Get default headers
   */
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    return headers
  }
  
  /**
   * Authenticate and get token
   */
  async authenticate(email: string, password: string): Promise<string> {
    const response = await this.request.post(`${API_BASE_URL}/api/auth/login`, {
      form: {
        username: email,
        password: password,
      },
    })
    
    if (!response.ok()) {
      throw new Error(`Authentication failed: ${response.status()}`)
    }
    
    const data = await response.json()
    this.token = data.access_token
    return this.token
  }
  
  /**
   * Check API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.request.get(`${API_BASE_URL}/api/health`)
      return response.ok()
    } catch {
      return false
    }
  }
  
  /**
   * Get server info
   */
  async getServerInfo(): Promise<any> {
    const response = await this.request.get(`${API_BASE_URL}/brapi/v2/serverinfo`, {
      headers: this.getHeaders(),
    })
    return response.json()
  }
  
  // ============ Programs ============
  
  async getPrograms(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/programs?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createProgram(data: {
    programName: string
    abbreviation?: string
    objective?: string
    leadPersonDbId?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/programs`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteProgram(programDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/programs/${programDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Trials ============
  
  async getTrials(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/trials?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createTrial(data: {
    trialName: string
    programDbId?: string
    startDate?: string
    endDate?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/trials`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteTrial(trialDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/trials/${trialDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Studies ============
  
  async getStudies(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/studies?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createStudy(data: {
    studyName: string
    trialDbId?: string
    locationDbId?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/studies`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteStudy(studyDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/studies/${studyDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Locations ============
  
  async getLocations(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/locations?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createLocation(data: {
    locationName: string
    locationType?: string
    countryCode?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/locations`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteLocation(locationDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/locations/${locationDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Germplasm ============
  
  async getGermplasm(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/germplasm?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createGermplasm(data: {
    germplasmName: string
    defaultDisplayName?: string
    genus?: string
    species?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/germplasm`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteGermplasm(germplasmDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/germplasm/${germplasmDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Observation Variables (Traits) ============
  
  async getObservationVariables(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/variables?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createObservationVariable(data: {
    observationVariableName: string
    trait?: { traitName: string }
    method?: { methodName: string }
    scale?: { scaleName: string }
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/variables`, {
      headers: this.getHeaders(),
      data: [data],
    })
    return response.json()
  }
  
  // ============ Seed Lots ============
  
  async getSeedLots(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/seedlots?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createSeedLot(data: {
    seedLotName: string
    germplasmDbId?: string
    amount?: number
    units?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/seedlots`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  async deleteSeedLot(seedLotDbId: string): Promise<void> {
    await this.request.delete(`${API_BASE_URL}/brapi/v2/seedlots/${seedLotDbId}`, {
      headers: this.getHeaders(),
    })
  }
  
  // ============ Crosses ============
  
  async getCrosses(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/crosses?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createCross(data: {
    crossName?: string
    crossType?: string
    parent1?: { germplasmDbId: string }
    parent2?: { germplasmDbId: string }
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/crosses`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  // ============ People ============
  
  async getPeople(page = 0, pageSize = 100): Promise<any> {
    const response = await this.request.get(
      `${API_BASE_URL}/brapi/v2/people?page=${page}&pageSize=${pageSize}`,
      { headers: this.getHeaders() }
    )
    return response.json()
  }
  
  async createPerson(data: {
    firstName: string
    lastName: string
    emailAddress?: string
  }): Promise<any> {
    const response = await this.request.post(`${API_BASE_URL}/brapi/v2/people`, {
      headers: this.getHeaders(),
      data,
    })
    return response.json()
  }
  
  // ============ Cleanup Utilities ============
  
  /**
   * Delete all test data created during tests
   */
  async cleanupTestData(testPrefix: string = 'E2E_TEST_'): Promise<void> {
    // Cleanup programs
    const programs = await this.getPrograms()
    for (const program of programs.result?.data || []) {
      if (program.programName?.startsWith(testPrefix)) {
        await this.deleteProgram(program.programDbId).catch(() => {})
      }
    }
    
    // Cleanup trials
    const trials = await this.getTrials()
    for (const trial of trials.result?.data || []) {
      if (trial.trialName?.startsWith(testPrefix)) {
        await this.deleteTrial(trial.trialDbId).catch(() => {})
      }
    }
    
    // Cleanup studies
    const studies = await this.getStudies()
    for (const study of studies.result?.data || []) {
      if (study.studyName?.startsWith(testPrefix)) {
        await this.deleteStudy(study.studyDbId).catch(() => {})
      }
    }
    
    // Cleanup locations
    const locations = await this.getLocations()
    for (const location of locations.result?.data || []) {
      if (location.locationName?.startsWith(testPrefix)) {
        await this.deleteLocation(location.locationDbId).catch(() => {})
      }
    }
    
    // Cleanup germplasm
    const germplasm = await this.getGermplasm()
    for (const germ of germplasm.result?.data || []) {
      if (germ.germplasmName?.startsWith(testPrefix)) {
        await this.deleteGermplasm(germ.germplasmDbId).catch(() => {})
      }
    }
    
    // Cleanup seed lots
    const seedLots = await this.getSeedLots()
    for (const lot of seedLots.result?.data || []) {
      if (lot.seedLotName?.startsWith(testPrefix)) {
        await this.deleteSeedLot(lot.seedLotDbId).catch(() => {})
      }
    }
  }
}
