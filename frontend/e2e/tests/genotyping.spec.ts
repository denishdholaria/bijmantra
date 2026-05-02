/**
 * Genotyping Module E2E Tests
 * 
 * Tests for:
 * - VariantSets page (VCF Import)
 * - GenomicSelection page (Train from Storage)
 */

import { test, expect } from '@playwright/test'
import { navigateAuthenticated } from '../helpers/auth.helper'

test.describe('Genotyping Module Tests', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })

  test.describe('VariantSets Page', () => {
    test('should load variant sets page', async ({ page }) => {
      await navigateAuthenticated(page, '/variantsets')
      expect(page.url()).toContain('/variantsets')
      
      // Page title should be visible
      const heading = page.locator('h1').first()
      await expect(heading).toContainText(/variant/i, { timeout: 10000 })
    })

    test('should display variant sets summary cards', async ({ page }) => {
      await navigateAuthenticated(page, '/variantsets')
      
      // Summary cards should be visible
      const cards = page.locator('[class*="card"]')
      await expect(cards.first()).toBeVisible({ timeout: 10000 })
    })

    test('should open create variant set dialog', async ({ page }) => {
      await navigateAuthenticated(page, '/variantsets')
      
      // Click "New Variant Set" button
      const newButton = page.getByRole('button', { name: /new variant set/i })
      await expect(newButton).toBeVisible({ timeout: 10000 })
      await newButton.click()
      
      // Dialog should appear
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      
      // Dialog should have title
      await expect(dialog.getByText(/create variant set/i)).toBeVisible()
    })

    test('should have Import VCF and Create Empty tabs', async ({ page }) => {
      await navigateAuthenticated(page, '/variantsets')
      
      // Open dialog
      await page.getByRole('button', { name: /new variant set/i }).click()
      
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      
      // Check for Import VCF tab
      const importTab = dialog.getByRole('tab', { name: /import vcf/i })
      await expect(importTab).toBeVisible()
      
      // Check for Create Empty tab
      const createTab = dialog.getByRole('tab', { name: /create empty/i })
      await expect(createTab).toBeVisible()
    })

    test('should show file input in Import VCF tab', async ({ page }) => {
      await navigateAuthenticated(page, '/variantsets')
      
      // Open dialog
      await page.getByRole('button', { name: /new variant set/i }).click()
      
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      
      // Click Import VCF tab (should be default)
      const importTab = dialog.getByRole('tab', { name: /import vcf/i })
      await importTab.click()
      
      // File input should be visible
      const fileInput = dialog.locator('input[type="file"]')
      await expect(fileInput).toBeVisible()
      
      // Should accept VCF files
      const accept = await fileInput.getAttribute('accept')
      expect(accept).toContain('.vcf')
    })
  })

  test.describe('Genomic Selection Page', () => {
    test('should load genomic selection page', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      expect(page.url()).toContain('/genomic-selection')
      
      // Page title should be visible
      const heading = page.locator('h1').first()
      await expect(heading).toContainText(/genomic selection/i, { timeout: 10000 })
    })

    test('should display summary statistics', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      
      // Summary cards should be visible
      const cards = page.locator('[class*="card"]')
      await expect(cards.first()).toBeVisible({ timeout: 10000 })
    })

    test('should have Train New Model button', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      
      // Train button should be visible
      const trainButton = page.getByRole('button', { name: /train new model/i })
      await expect(trainButton).toBeVisible({ timeout: 10000 })
    })

    test('should open training dialog with correct fields', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      
      // Click Train button
      await page.getByRole('button', { name: /train new model/i }).click()
      
      // Dialog should appear
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      
      // Should have model name field
      await expect(dialog.getByLabel(/name/i)).toBeVisible()
      
      // Should have trait field
      await expect(dialog.getByLabel(/trait/i)).toBeVisible()
      
      // Should have genotypes selector
      await expect(dialog.getByText(/genotypes/i)).toBeVisible()
      
      // Should have phenotypes upload
      await expect(dialog.getByText(/phenotypes/i)).toBeVisible()
    })

    test('should have file input for phenotype CSV', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      
      // Click Train button
      await page.getByRole('button', { name: /train new model/i }).click()
      
      const dialog = page.getByRole('dialog')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      
      // File input should be visible
      const fileInput = dialog.locator('input[type="file"]')
      await expect(fileInput).toBeVisible()
      
      // Should accept CSV files
      const accept = await fileInput.getAttribute('accept')
      expect(accept).toContain('.csv')
    })

    test('should have tabs for Models, Predictions, Selection, Methods', async ({ page }) => {
      await navigateAuthenticated(page, '/genomic-selection')
      
      // Check for tabs
      const tabs = page.getByRole('tablist')
      await expect(tabs).toBeVisible({ timeout: 10000 })
      
      await expect(page.getByRole('tab', { name: /models/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /predictions/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /selection/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /methods/i })).toBeVisible()
    })
  })

  test.describe('Navigation Integration', () => {
    test('should navigate between genotyping pages', async ({ page }) => {
      // Start at variant sets
      await navigateAuthenticated(page, '/variantsets')
      await expect(page.locator('h1')).toContainText(/variant/i, { timeout: 10000 })
      
      // Navigate to genomic selection
      await page.goto('/genomic-selection')
      await expect(page.locator('h1')).toContainText(/genomic selection/i, { timeout: 10000 })
    })
  })
})
