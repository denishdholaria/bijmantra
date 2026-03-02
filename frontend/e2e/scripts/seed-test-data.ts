import { chromium } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

/**
 * Seeds minimal test data required for detail page testing.
 * Creates one entity of each major type if none exist.
 */
async function seedTestData() {
  console.log('🌱 Seeding test data...')
  
  const browser = await chromium.launch()
  const context = await browser.newContext({ storageState: 'playwright/.auth/user.json' })
  const page = await context.newPage()
  
  const baseURL = process.env.E2E_BASE_URL || 'http://localhost:5173'
  const ids: Record<string, string> = {}

  try {
    // 1. Get/Create Program
    console.log('Checking Programs...')
    await page.goto(`${baseURL}/programs`)
    await page.waitForLoadState('networkidle')
    if (await page.getByText('No programs found').isVisible()) {
      await page.getByRole('button', { name: 'New Program' }).click()
      await page.getByLabel('Program Name').fill('Test Program A')
      await page.getByLabel('Description').fill('Automated Test Program')
      await page.getByRole('button', { name: 'Save' }).click()
      await page.waitForURL(/\/programs\/[^\/]+/)
    } else {
      // Click first row to get ID
      await page.locator('tbody tr').first().click()
      await page.waitForURL(/\/programs\/[^\/]+/)
    }
    const programUrl = page.url()
    const programId = programUrl.split('/programs/')[1]?.split('/')[0] || '1'
    ids['program'] = programId
    console.log(`Program ID: ${programId} (URL: ${programUrl})`)

    // 2. Get/Create Location
    console.log('Checking Locations...')
    await page.goto(`${baseURL}/locations`)
    await page.waitForLoadState('networkidle')
    if (await page.getByText('No locations found').isVisible()) {
      await page.getByRole('button', { name: 'New Location' }).click()
      await page.getByLabel('Name').fill('Test Field 1')
      await page.getByLabel('Type').selectOption('Field')
      await page.getByRole('button', { name: 'Save' }).click()
      await page.waitForURL(/\/locations\/[^\/]+/)
    } else {
       await page.locator('tbody tr').first().click()
       await page.waitForURL(/\/locations\/[^\/]+/)
    }
    const locUrl = page.url()
    ids['location'] = locUrl.split('/locations/')[1]?.split('/')[0] || '1'
    console.log(`Location ID: ${ids['location']}`)

    // 4. Get/Create Germplasm (Needs Program first)
    console.log('Checking Germplasm...')
    await page.goto(`${baseURL}/germplasm`)
    await page.waitForLoadState('networkidle')
    if (await page.getByText('No germplasm found').isVisible()) {
      await page.getByRole('button', { name: 'New Germplasm' }).click()
      await page.getByLabel('Germplasm Name').fill('Test Variety A')
      await page.getByLabel('Program').selectOption({ label: 'Test Program A' }).catch(() => {})
      await page.getByRole('button', { name: 'Save' }).click()
      await page.waitForURL(/\/germplasm\/[^\/]+/)
    } else {
       await page.locator('tbody tr').first().click()
       await page.waitForURL(/\/germplasm\/[^\/]+/)
    }
    const germUrl = page.url()
    ids['germplasm'] = germUrl.split('/germplasm/')[1]?.split('/')[0] || '1'
    console.log(`Germplasm ID: ${ids['germplasm']}`)

    // 5. Get/Create Trait
    console.log('Checking Traits...')
    await page.goto(`${baseURL}/traits`)
    await page.waitForLoadState('networkidle')
    if (await page.getByText('No traits found').isVisible()) {
      await page.getByRole('button', { name: 'New Trait' }).click()
      await page.getByLabel('Name').fill('Yield Test')
      await page.getByLabel('Method').fill('Weight')
      await page.getByLabel('Scale').fill('kg/ha')
      await page.getByRole('button', { name: 'Save' }).click()
      await page.waitForURL(/\/traits\/[^\/]+/)
    } else {
       await page.locator('tbody tr').first().click()
       await page.waitForURL(/\/traits\/[^\/]+/)
    }
    const traitUrl = page.url()
    ids['trait'] = traitUrl.split('/traits/')[1]?.split('/')[0] || '1'
    console.log(`Trait ID: ${ids['trait']}`)

    // 3. Save IDs
    const outputPath = path.join(__dirname, '../test-data.json')
    fs.writeFileSync(outputPath, JSON.stringify(ids, null, 2))
    console.log(`✅ Test data IDs saved to ${outputPath}`)

  } catch (error) {
    console.error('❌ Seeding failed:', error)
  } finally {
    await browser.close()
  }
}

seedTestData()
