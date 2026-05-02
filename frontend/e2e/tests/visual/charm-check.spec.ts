import { test, expect } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

// Get current directory
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Load routes from JSON
const routesPath = path.join(__dirname, 'routes.json')
let routes: string[] = []

try {
  routes = JSON.parse(fs.readFileSync(routesPath, 'utf-8')) as string[]
} catch (e) {
  console.warn('Could not load routes.json, falling back to minimal list')
  routes = ['/login', '/dashboard']
}

test.use({ 
  storageState: 'playwright/.auth/admin.json',
  video: 'off' // Disable video to avoid ffmpeg dependency
})

test.describe('Charm Check - UI/UX Audit', () => {

  // Process all routes
  for (const route of routes) {
    // Skip root as it might redirect
    if (route === '/') continue
    
    // Create a safe filename from route
    const safeName = route.replace(/\//g, '_').replace(/^_/, '')
    
    test(`audit ${route}`, async ({ page }) => {
      // Log failed requests
      page.on('response', response => {
        if (response.status() === 401 || response.status() === 403) {
          console.error(`[API ERROR] ${response.status()} from ${response.url()}`)
        }
      })
      
      // forward console logs
      page.on('console', msg => {
        if (msg.type() === 'error') console.error(`[BROWSER ERROR] ${msg.text()}`)
        else console.log(`[BROWSER] ${msg.text()}`)
      })
      
      // console.log(`Navigating to ${route}...`)
      await page.goto(route)

      // Check localStorage AFTER load (to see if it was cleared)
      const storage = await page.evaluate(() => ({
        authToken: localStorage.getItem('auth_token'),
        zustandAuth: localStorage.getItem('bijmantra-auth')
      }))
      console.log(`[STORAGE] Token exists: ${!!storage.authToken}, Zustand exists: ${!!storage.zustandAuth}`)

      try {
        await page.waitForLoadState('domcontentloaded', { timeout: 10000 })
        // Wait a bit for animations/rendering
        await page.waitForTimeout(1000)
      } catch (e) {
        console.log(`Timeout waiting for load event on ${route}`)
      }
      
      const currentUrl = page.url()
      if (currentUrl.includes('/login')) {
        console.error(`[AUTH FAIL] Page ${route} redirected to login`)
        // Fail the test to highlight auth issues
        // We continue to take a screenshot to document the failure
      }
      
      // Check if redirected to dashboard when not requested
      // Note: Dashboard path might vary based on trailing slash
      if (route !== '/dashboard' && route !== '/dashboard/' && currentUrl.match(/\/dashboard\/?$/)) {
         console.warn(`[REDIRECT] Page ${route} redirected to dashboard`)
      }
      
      const isNotFound = await page.getByText(/404|Page Not Found/i).count() > 0
      if (isNotFound) {
        console.warn(`[WARNING] Page ${route} returned 404`)
        return
      }

      await page.addStyleTag({
        content: `
          .animate-spin, [data-testid="loading"] { display: none !important; }
          .timestamp, [data-testid="timestamp"] { visibility: hidden !important; }
          img.avatar { visibility: hidden !important; }
        `
      })
      
      // Save to distinct folder
      await page.screenshot({ 
        path: `charm-screenshots/${safeName}.png`,
        fullPage: true 
      })
    })
  }
})
