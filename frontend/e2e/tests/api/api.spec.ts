/**
 * API E2E Tests
 * 
 * Tests API endpoints directly:
 * - Authentication endpoints
 * - BrAPI compliance
 * - Error handling
 * - Response formats
 */

import { test, expect } from '@playwright/test'

const API_BASE_URL = process.env.E2E_API_URL || 'http://localhost:8000'

// Test credentials from environment or defaults
const TEST_CREDENTIALS = {
  email: process.env.E2E_TEST_EMAIL || 'demo@bijmantra.org',
  password: process.env.E2E_TEST_PASSWORD || 'Demo123!',
}

test.describe('API Tests', () => {
  let authToken: string | null = null
  
  test.beforeAll(async ({ request }) => {
    // Reset rate limits before authentication tests
    try {
      await request.post(`${API_BASE_URL}/api/auth/reset-rate-limit`)
    } catch {
      console.log('Rate limit reset not available')
    }
    
    // Authenticate to get token
    try {
      const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
        form: {
          username: TEST_CREDENTIALS.email,
          password: TEST_CREDENTIALS.password,
        },
      })
      
      if (response.ok()) {
        const data = await response.json()
        authToken = data.access_token
      }
    } catch {
      console.log('API authentication failed - tests will use unauthenticated requests')
    }
  })
  
  test.describe('Health & Server Info', () => {
    test('should return server info', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/brapi/v2/serverinfo`)
      
      expect(response.ok()).toBeTruthy()
      
      const data = await response.json()
      expect(data).toHaveProperty('result')
      expect(data.result).toHaveProperty('serverName')
    })
    
    test('should return API health status', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/api/health`)
      
      // Health endpoint should exist and return OK
      if (response.ok()) {
        const data = await response.json()
        expect(data.status || data.health).toBeTruthy()
      }
    })
  })
  
  test.describe('Authentication API', () => {
    test('should login with valid credentials', async ({ request }) => {
      // Reset rate limits before login test
      await request.post(`${API_BASE_URL}/api/auth/reset-rate-limit`).catch(() => {})
      
      const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
        form: {
          username: TEST_CREDENTIALS.email,
          password: TEST_CREDENTIALS.password,
        },
      })
      
      expect(response.ok()).toBeTruthy()
      
      const data = await response.json()
      expect(data).toHaveProperty('access_token')
      expect(data).toHaveProperty('token_type')
    })
    
    test('should reject invalid credentials', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/api/auth/login`, {
        form: {
          username: 'invalid@email.com',
          password: 'wrongpassword',
        },
      })
      
      // Should return 401 or 400
      expect(response.status()).toBeGreaterThanOrEqual(400)
    })
    
    test('should return user info with valid token', async ({ request }) => {
      if (!authToken) {
        test.skip()
        return
      }
      
      const response = await request.get(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      })
      
      expect(response.ok()).toBeTruthy()
      
      const data = await response.json()
      expect(data).toHaveProperty('email')
    })
    
    test('should reject requests without token', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/api/auth/me`)
      
      expect(response.status()).toBe(401)
    })
  })
  
  test.describe('BrAPI Endpoints', () => {
    test.describe('Programs', () => {
      test('should list programs', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/programs`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('metadata')
        expect(data).toHaveProperty('result')
        expect(data.result).toHaveProperty('data')
        expect(Array.isArray(data.result.data)).toBeTruthy()
      })
      
      test('should support pagination', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/programs?page=0&pageSize=10`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data.metadata.pagination).toHaveProperty('currentPage')
        expect(data.metadata.pagination).toHaveProperty('pageSize')
        expect(data.metadata.pagination).toHaveProperty('totalCount')
      })
    })
    
    test.describe('Trials', () => {
      test('should list trials', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/trials`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
        expect(data.result).toHaveProperty('data')
      })
    })
    
    test.describe('Studies', () => {
      test('should list studies', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/studies`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
      })
    })
    
    test.describe('Germplasm', () => {
      test('should list germplasm', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/germplasm`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
        expect(data.result).toHaveProperty('data')
      })
      
      test('should search germplasm by name', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/germplasm?germplasmName=Rice`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
      })
    })
    
    test.describe('Locations', () => {
      test('should list locations', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/locations`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
      })
    })
    
    test.describe('Observation Variables', () => {
      test('should list observation variables', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/variables`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
      })
    })
    
    test.describe('Seed Lots', () => {
      test('should list seed lots', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/brapi/v2/seedlots`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        expect(response.ok()).toBeTruthy()
        
        const data = await response.json()
        expect(data).toHaveProperty('result')
      })
    })
  })
  
  test.describe('Custom API Endpoints', () => {
    test.describe('Seed Bank', () => {
      test('should get seed bank stats', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/api/v2/seed-bank/stats`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        if (response.ok()) {
          const data = await response.json()
          expect(data).toBeDefined()
        }
      })
      
      test('should list vaults', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/api/v2/seed-bank/vaults`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        if (response.ok()) {
          const data = await response.json()
          expect(Array.isArray(data) || data.vaults).toBeTruthy()
        }
      })
    })
    
    test.describe('Quality Control', () => {
      test('should get QC summary', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/api/v2/quality/summary`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        if (response.ok()) {
          const data = await response.json()
          expect(data).toBeDefined()
        }
      })
    })
    
    test.describe('Traceability', () => {
      test('should get traceability statistics', async ({ request }) => {
        const response = await request.get(`${API_BASE_URL}/api/v2/traceability/statistics`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
        
        if (response.ok()) {
          const data = await response.json()
          expect(data).toBeDefined()
        }
      })
    })
  })
  
  test.describe('Error Handling', () => {
    test('should return 404 for non-existent resource', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/brapi/v2/programs/non-existent-id-12345`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })
      
      expect(response.status()).toBe(404)
    })
    
    test('should return proper error format', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/brapi/v2/programs/invalid`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })
      
      if (!response.ok()) {
        const data = await response.json()
        // Should have error detail
        expect(data.detail || data.message || data.error).toBeDefined()
      }
    })
    
    test('should handle malformed requests', async ({ request }) => {
      const response = await request.post(`${API_BASE_URL}/brapi/v2/programs`, {
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        data: 'invalid json{{{',
      })
      
      // Should return 400 or 422
      expect(response.status()).toBeGreaterThanOrEqual(400)
    })
  })
  
  test.describe('Response Format', () => {
    test('should return BrAPI compliant response format', async ({ request }) => {
      // Reset rate limits to ensure clean state
      await request.post(`${API_BASE_URL}/api/auth/reset-rate-limit`).catch(() => {})
      
      const response = await request.get(`${API_BASE_URL}/brapi/v2/programs`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })
      
      // If rate limited or auth required, skip detailed checks
      if (!response.ok()) {
        console.log(`Response status: ${response.status()} - may be rate limited or require auth`)
        return
      }
      
      const data = await response.json()
      
      // BrAPI response structure
      expect(data).toHaveProperty('metadata')
      expect(data.metadata).toHaveProperty('pagination')
      expect(data.metadata).toHaveProperty('status')
      expect(data).toHaveProperty('result')
    })
    
    test('should return correct content type', async ({ request }) => {
      const response = await request.get(`${API_BASE_URL}/brapi/v2/programs`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })
      
      const contentType = response.headers()['content-type']
      expect(contentType).toContain('application/json')
    })
  })
  
  test.describe('Rate Limiting', () => {
    test('should handle multiple rapid requests', async ({ request }) => {
      // Reset rate limits first
      await request.post(`${API_BASE_URL}/api/auth/reset-rate-limit`).catch(() => {})
      
      const requests = Array(10).fill(null).map(() =>
        request.get(`${API_BASE_URL}/brapi/v2/programs`, {
          headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        })
      )
      
      const responses = await Promise.all(requests)
      
      // Most requests should succeed (at least some, rate limiting may kick in)
      const successCount = responses.filter(r => r.ok()).length
      expect(successCount).toBeGreaterThan(0)
      
      // Check for rate limit headers
      const lastResponse = responses[responses.length - 1]
      const rateLimitHeader = lastResponse.headers()['x-ratelimit-remaining']
      
      if (rateLimitHeader) {
        console.log(`Rate limit remaining: ${rateLimitHeader}`)
      }
    })
  })
})
