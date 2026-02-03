/**
 * Authentication Helper for E2E Tests
 * 
 * Handles Zustand persist hydration timing issues.
 * 
 * ROOT CAUSE: Zustand's persist middleware hydrates asynchronously from localStorage.
 * When Playwright restores storageState and navigates to a protected route:
 * 1. React app loads
 * 2. Zustand initializes with default state (isAuthenticated: false)
 * 3. ProtectedRoute checks isAuthenticated immediately → redirects to /login
 * 4. THEN Zustand hydrates from localStorage (too late)
 * 
 * SOLUTION: Inject auth state into localStorage before navigation, then navigate.
 */

import { Page } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

// Cache the auth state to avoid reading file multiple times
let cachedAuthState: { localStorage: Array<{ name: string; value: string }> } | null = null

/**
 * Load auth state from the saved storage state file
 */
function loadAuthState(): { localStorage: Array<{ name: string; value: string }> } | null {
  if (cachedAuthState) return cachedAuthState
  
  try {
    const authFilePath = path.join(__dirname, '../playwright/.auth/user.json')
    const content = fs.readFileSync(authFilePath, 'utf-8')
    const parsed = JSON.parse(content)
    
    // Extract localStorage from origins
    const origin = parsed.origins?.find((o: any) => o.origin.includes('localhost'))
    if (origin?.localStorage) {
      cachedAuthState = { localStorage: origin.localStorage }
      return cachedAuthState
    }
  } catch (error) {
    console.error('Failed to load auth state:', error)
  }
  return null
}

/**
 * Inject auth state into localStorage before navigation
 */
async function injectAuthState(page: Page): Promise<boolean> {
  const authState = loadAuthState()
  if (!authState) return false
  
  // Inject localStorage items
  await page.evaluate((items) => {
    for (const item of items) {
      localStorage.setItem(item.name, item.value)
    }
  }, authState.localStorage)
  
  return true
}

/**
 * Wait for Zustand auth store to hydrate from localStorage
 */
export async function waitForAuthHydration(page: Page, timeout = 5000): Promise<boolean> {
  try {
    await page.waitForFunction(() => {
      const authData = localStorage.getItem('bijmantra-auth')
      if (!authData) return false
      try {
        const parsed = JSON.parse(authData)
        return parsed.state?.isAuthenticated === true
      } catch {
        return false
      }
    }, { timeout })
    return true
  } catch {
    return false
  }
}

/**
 * Navigate to a protected route with auth handling
 * 
 * Strategy:
 * 1. Go to a blank page first to establish context
 * 2. Inject auth state into localStorage
 * 3. Navigate to target page
 * 4. If still redirected to login, retry with reload
 */
export async function navigateAuthenticated(
  page: Page, 
  targetPath: string,
  options: { waitForSelector?: string; timeout?: number; maxRetries?: number } = {}
): Promise<void> {
  const { waitForSelector, timeout = 15000, maxRetries = 3 } = options
  
  // First, check if we already have auth in localStorage
  let hasAuth = await page.evaluate(() => {
    const authData = localStorage.getItem('bijmantra-auth')
    if (!authData) return false
    try {
      const parsed = JSON.parse(authData)
      return parsed.state?.isAuthenticated === true
    } catch {
      return false
    }
  }).catch(() => false)
  
  // If no auth, inject it
  if (!hasAuth) {
    // Navigate to a page first to establish the origin context
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await injectAuthState(page)
    
    // Verify injection worked
    hasAuth = await page.evaluate(() => {
      const authData = localStorage.getItem('bijmantra-auth')
      if (!authData) return false
      try {
        const parsed = JSON.parse(authData)
        return parsed.state?.isAuthenticated === true
      } catch {
        return false
      }
    }).catch(() => false)
    
    if (!hasAuth) {
      throw new Error(`Failed to inject auth state for ${targetPath}`)
    }
  }
  
  // Now navigate to the target
  let attempts = 0
  while (attempts < maxRetries) {
    attempts++
    
    await page.goto(targetPath, { waitUntil: 'domcontentloaded', timeout })
    
    // Give the app time to initialize
    await page.waitForTimeout(500)
    
    // Check if we're on the target path
    const currentUrl = page.url()
    if (!currentUrl.includes('/login')) {
      // Success
      break
    }
    
    // Still on login - Zustand didn't hydrate in time
    // Re-inject auth and try again
    await injectAuthState(page)
    await page.waitForTimeout(300)
    
    if (attempts >= maxRetries) {
      // Last attempt - reload
      await page.reload({ waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(500)
      
      if (page.url().includes('/login')) {
        throw new Error(`Auth hydration failed after ${maxRetries} attempts for ${targetPath}`)
      }
    }
  }
  
  // Wait for page content
  if (waitForSelector) {
    await page.waitForSelector(waitForSelector, { timeout })
  } else {
    try {
      await page.waitForSelector('main, .min-h-screen, [role="main"]', { timeout: 10000 })
    } catch {
      // Some pages may not have main element
    }
  }
}

/**
 * Ensure auth state is properly set before navigation
 */
export async function ensureAuthenticated(page: Page): Promise<void> {
  const isAuthenticated = await page.evaluate(() => {
    const authData = localStorage.getItem('bijmantra-auth')
    if (!authData) return false
    try {
      const parsed = JSON.parse(authData)
      return parsed.state?.isAuthenticated === true
    } catch {
      return false
    }
  })
  
  if (!isAuthenticated) {
    throw new Error('Not authenticated - storage state may not have loaded correctly')
  }
}

/**
 * Debug helper to log auth state
 */
export async function debugAuthState(page: Page): Promise<void> {
  const authState = await page.evaluate(() => {
    const authData = localStorage.getItem('bijmantra-auth')
    const authToken = localStorage.getItem('auth_token')
    return {
      authData: authData ? JSON.parse(authData) : null,
      authToken,
      url: window.location.href,
    }
  })
  console.log('Auth State Debug:', JSON.stringify(authState, null, 2))
}
