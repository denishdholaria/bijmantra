/**
 * Global Setup for Playwright E2E Tests
 * 
 * Handles:
 * - Rate limit reset (for clean test runs)
 * - Authentication state persistence
 * - Test user creation
 * - Environment validation
 */

import { chromium, FullConfig } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

// Test credentials
const TEST_USER = {
  email: process.env.E2E_TEST_EMAIL || 'demo@bijmantra.org',
  password: process.env.E2E_TEST_PASSWORD || 'Demo123!',
}

const ADMIN_USER = {
  email: process.env.E2E_ADMIN_EMAIL || 'admin@bijmantra.org',
  password: process.env.E2E_ADMIN_PASSWORD || 'Admin123!',
}

// Backend API URL
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'

async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use
  
  // Ensure auth directory exists
  const authDir = path.join(__dirname, '../playwright/.auth')
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true })
  }
  
  // Launch browser for authentication
  const browser = await chromium.launch()
  
  try {
    // Reset rate limits before authentication (development mode only)
    await resetRateLimits()
    
    // Authenticate regular user
    const userContext = await browser.newContext()
    const userPage = await userContext.newPage()
    
    console.log('🔐 Authenticating test user...')
    await authenticateUser(userPage, baseURL!, TEST_USER)
    
    // Save user authentication state
    await userContext.storageState({ path: path.join(authDir, 'user.json') })
    console.log('✅ User authentication saved')
    
    await userContext.close()
    
    // Authenticate admin user
    const adminContext = await browser.newContext()
    const adminPage = await adminContext.newPage()
    
    console.log('🔐 Authenticating admin user...')
    await authenticateUser(adminPage, baseURL!, ADMIN_USER)
    
    // Save admin authentication state
    await adminContext.storageState({ path: path.join(authDir, 'admin.json') })
    console.log('✅ Admin authentication saved')
    
    await adminContext.close()
    
  } finally {
    await browser.close()
  }
  
  console.log('🚀 Global setup complete')
}

/**
 * Reset rate limits by calling the backend endpoint.
 * This only works in development mode (DEBUG=True).
 */
async function resetRateLimits() {
  try {
    const response = await fetch(`${API_URL}/api/auth/reset-rate-limit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (response.ok) {
      console.log('🔄 Rate limits reset successfully')
    } else if (response.status === 403) {
      console.log('⚠️ Rate limit reset not available (production mode)')
    } else {
      console.log(`⚠️ Rate limit reset failed: ${response.status}`)
    }
  } catch (error) {
    console.log('⚠️ Could not reset rate limits (backend may be unavailable)')
  }
}

async function authenticateUser(
  page: any,
  baseURL: string,
  credentials: { email: string; password: string }
) {
  // Navigate to login page
  await page.goto(`${baseURL}/login`, { waitUntil: 'networkidle' })
  
  // Wait for login form
  await page.waitForSelector('input[type="email"], input[name="email"], input[placeholder*="email" i]', {
    timeout: 10000,
  })
  
  // Fill credentials
  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first()
  const passwordInput = page.locator('input[type="password"]').first()
  
  await emailInput.fill(credentials.email)
  await passwordInput.fill(credentials.password)
  
  // Submit form
  const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first()
  await submitButton.click()
  
  // Wait for successful login (redirect to dashboard or gateway)
  await page.waitForURL(/\/(dashboard|gateway)/, { timeout: 15000 })
  
  // Verify authentication
  const token = await page.evaluate(() => localStorage.getItem('auth_token'))
  if (!token) {
    throw new Error('Authentication failed - no token found')
  }
  
  // Verify it's a real JWT token, not a demo token
  if (token.startsWith('demo_')) {
    console.log('⚠️ Warning: Using demo token - backend may not be available')
  }
}

export default globalSetup
