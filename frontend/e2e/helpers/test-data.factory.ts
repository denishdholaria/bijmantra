/**
 * Test Data Factory
 * 
 * Generates consistent test data for E2E tests:
 * - Unique identifiers
 * - Valid data structures
 * - Edge case data
 */

const TEST_PREFIX = 'E2E_TEST_'

export class TestDataFactory {
  private counter = 0
  
  /**
   * Generate unique ID
   */
  uniqueId(): string {
    this.counter++
    return `${TEST_PREFIX}${Date.now()}_${this.counter}`
  }
  
  /**
   * Generate unique name with prefix
   */
  uniqueName(prefix: string): string {
    return `${TEST_PREFIX}${prefix}_${Date.now()}_${this.counter++}`
  }
  
  // ============ Program Data ============
  
  program(overrides: Partial<{
    programName: string
    abbreviation: string
    objective: string
    commonCropName: string
  }> = {}) {
    return {
      programName: this.uniqueName('Program'),
      abbreviation: `PRG${this.counter}`,
      objective: 'E2E Test Program Objective',
      commonCropName: 'Rice',
      ...overrides,
    }
  }
  
  // ============ Trial Data ============
  
  trial(overrides: Partial<{
    trialName: string
    trialDescription: string
    programDbId: string
    startDate: string
    endDate: string
  }> = {}) {
    const startDate = new Date()
    const endDate = new Date()
    endDate.setMonth(endDate.getMonth() + 6)
    
    return {
      trialName: this.uniqueName('Trial'),
      trialDescription: 'E2E Test Trial Description',
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
      ...overrides,
    }
  }
  
  // ============ Study Data ============
  
  study(overrides: Partial<{
    studyName: string
    studyDescription: string
    studyType: string
    trialDbId: string
    locationDbId: string
  }> = {}) {
    return {
      studyName: this.uniqueName('Study'),
      studyDescription: 'E2E Test Study Description',
      studyType: 'Phenotyping',
      ...overrides,
    }
  }
  
  // ============ Location Data ============
  
  location(overrides: Partial<{
    locationName: string
    locationType: string
    countryCode: string
    countryName: string
    abbreviation: string
    coordinates: { latitude: number; longitude: number }
  }> = {}) {
    return {
      locationName: this.uniqueName('Location'),
      locationType: 'Field',
      countryCode: 'IND',
      countryName: 'India',
      abbreviation: `LOC${this.counter}`,
      coordinates: {
        latitude: 23.0225 + Math.random() * 0.1,
        longitude: 72.5714 + Math.random() * 0.1,
      },
      ...overrides,
    }
  }
  
  // ============ Germplasm Data ============
  
  germplasm(overrides: Partial<{
    germplasmName: string
    defaultDisplayName: string
    genus: string
    species: string
    commonCropName: string
    accessionNumber: string
    germplasmOrigin: string[]
  }> = {}) {
    return {
      germplasmName: this.uniqueName('Germplasm'),
      defaultDisplayName: `Display_${this.counter}`,
      genus: 'Oryza',
      species: 'sativa',
      commonCropName: 'Rice',
      accessionNumber: `ACC${Date.now()}`,
      germplasmOrigin: [{ countryOfOriginCode: 'IND' }],
      ...overrides,
    }
  }
  
  // ============ Trait/Observation Variable Data ============
  
  trait(overrides: Partial<{
    observationVariableName: string
    trait: { traitName: string; traitDescription: string }
    method: { methodName: string; methodDescription: string }
    scale: { scaleName: string; dataType: string }
  }> = {}) {
    return {
      observationVariableName: this.uniqueName('Trait'),
      trait: {
        traitName: `Trait_${this.counter}`,
        traitDescription: 'E2E Test Trait',
      },
      method: {
        methodName: `Method_${this.counter}`,
        methodDescription: 'E2E Test Method',
      },
      scale: {
        scaleName: `Scale_${this.counter}`,
        dataType: 'Numerical',
      },
      ...overrides,
    }
  }
  
  // ============ Seed Lot Data ============
  
  seedLot(overrides: Partial<{
    seedLotName: string
    seedLotDescription: string
    amount: number
    units: string
    storageLocation: string
    germplasmDbId: string
  }> = {}) {
    return {
      seedLotName: this.uniqueName('SeedLot'),
      seedLotDescription: 'E2E Test Seed Lot',
      amount: Math.floor(Math.random() * 1000) + 100,
      units: 'seeds',
      storageLocation: 'Vault A',
      ...overrides,
    }
  }
  
  // ============ Cross Data ============
  
  cross(overrides: Partial<{
    crossName: string
    crossType: string
    crossingProjectDbId: string
    parent1: { germplasmDbId: string; parentType: string }
    parent2: { germplasmDbId: string; parentType: string }
  }> = {}) {
    return {
      crossName: this.uniqueName('Cross'),
      crossType: 'BIPARENTAL',
      ...overrides,
    }
  }
  
  // ============ Person Data ============
  
  person(overrides: Partial<{
    firstName: string
    lastName: string
    emailAddress: string
    userID: string
    description: string
  }> = {}) {
    const id = this.counter++
    return {
      firstName: `TestFirst${id}`,
      lastName: `TestLast${id}`,
      emailAddress: `test${id}@e2e.bijmantra.com`,
      userID: `user_${id}`,
      description: 'E2E Test Person',
      ...overrides,
    }
  }
  
  // ============ Observation Data ============
  
  observation(overrides: Partial<{
    observationUnitDbId: string
    observationVariableDbId: string
    value: string
    observationTimeStamp: string
    collector: string
  }> = {}) {
    return {
      value: String(Math.random() * 100),
      observationTimeStamp: new Date().toISOString(),
      collector: 'E2E Test',
      ...overrides,
    }
  }
  
  // ============ Accession Data (Seed Bank) ============
  
  accession(overrides: Partial<{
    accessionNumber: string
    accessionName: string
    genus: string
    species: string
    countryOfOrigin: string
    collectionDate: string
    status: string
  }> = {}) {
    return {
      accessionNumber: `ACC_${this.uniqueId()}`,
      accessionName: this.uniqueName('Accession'),
      genus: 'Oryza',
      species: 'sativa',
      countryOfOrigin: 'India',
      collectionDate: new Date().toISOString().split('T')[0],
      status: 'active',
      ...overrides,
    }
  }
  
  // ============ Edge Case Data ============
  
  /**
   * Generate data with special characters
   */
  withSpecialChars(base: string): string {
    return `${base}_<>&"'特殊字符`
  }
  
  /**
   * Generate very long string
   */
  longString(length: number = 1000): string {
    return 'A'.repeat(length)
  }
  
  /**
   * Generate empty/whitespace data
   */
  emptyData() {
    return {
      empty: '',
      whitespace: '   ',
      null: null,
      undefined: undefined,
    }
  }
  
  /**
   * Generate boundary values
   */
  boundaryValues() {
    return {
      zero: 0,
      negative: -1,
      maxInt: Number.MAX_SAFE_INTEGER,
      minInt: Number.MIN_SAFE_INTEGER,
      float: 0.123456789,
      scientific: 1e10,
    }
  }
  
  /**
   * Generate date edge cases
   */
  dateEdgeCases() {
    return {
      today: new Date().toISOString().split('T')[0],
      past: '1900-01-01',
      future: '2100-12-31',
      leapYear: '2024-02-29',
      endOfYear: '2025-12-31',
    }
  }
}
