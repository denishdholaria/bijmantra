/**
 * PostHog Product Analytics
 * User behavior tracking, feature flags, and A/B testing
 */

import posthog from 'posthog-js'

// Configuration
const POSTHOG_CONFIG = {
  apiKey: import.meta.env.VITE_POSTHOG_API_KEY || '',
  host: import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
}

let isInitialized = false

/**
 * Initialize PostHog
 */
export function initPostHog(): void {
  if (isInitialized || !POSTHOG_CONFIG.apiKey) {
    if (!POSTHOG_CONFIG.apiKey) {
      console.log('[PostHog] No API key configured, skipping initialization')
    }
    return
  }

  posthog.init(POSTHOG_CONFIG.apiKey, {
    api_host: POSTHOG_CONFIG.host,
    
    // Capture settings
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true,
    
    // Privacy settings
    disable_session_recording: false,
    mask_all_text: false,
    mask_all_element_attributes: false,
    
    // Performance
    loaded: (posthog) => {
      if (import.meta.env.DEV) {
        // Disable in development
        posthog.opt_out_capturing()
      }
    },
    
    // Feature flags
    bootstrap: {
      featureFlags: {},
    },
  })

  isInitialized = true
  console.log('[PostHog] Initialized')
}

/**
 * Identify a user
 */
export function identifyUser(
  userId: string,
  properties?: {
    email?: string
    name?: string
    organization?: string
    role?: string
    [key: string]: unknown
  }
): void {
  if (!isInitialized) return
  
  posthog.identify(userId, {
    ...properties,
    app: 'bijmantra',
  })
}

/**
 * Reset user identity (on logout)
 */
export function resetUser(): void {
  if (!isInitialized) return
  posthog.reset()
}

/**
 * Track a custom event
 */
export function trackEvent(
  eventName: string,
  properties?: Record<string, unknown>
): void {
  if (!isInitialized) return
  
  posthog.capture(eventName, {
    ...properties,
    timestamp: new Date().toISOString(),
  })
}

/**
 * Track page view
 */
export function trackPageView(pageName: string, properties?: Record<string, unknown>): void {
  if (!isInitialized) return
  
  posthog.capture('$pageview', {
    $current_url: window.location.href,
    page_name: pageName,
    ...properties,
  })
}

// Pre-defined events for breeding platform
export const AnalyticsEvents = {
  // Navigation
  PAGE_VIEW: 'page_view',
  SEARCH_PERFORMED: 'search_performed',
  COMMAND_PALETTE_OPENED: 'command_palette_opened',
  
  // Data operations
  GERMPLASM_CREATED: 'germplasm_created',
  GERMPLASM_VIEWED: 'germplasm_viewed',
  GERMPLASM_EXPORTED: 'germplasm_exported',
  
  TRIAL_CREATED: 'trial_created',
  TRIAL_VIEWED: 'trial_viewed',
  
  OBSERVATION_RECORDED: 'observation_recorded',
  OBSERVATION_BATCH_UPLOADED: 'observation_batch_uploaded',
  
  CROSS_CREATED: 'cross_created',
  CROSS_PLANNED: 'cross_planned',
  
  // Analysis
  ANALYSIS_RUN: 'analysis_run',
  WASM_COMPUTATION: 'wasm_computation',
  REPORT_GENERATED: 'report_generated',
  
  // AI features
  AI_ASSISTANT_USED: 'ai_assistant_used',
  PLANT_VISION_SCAN: 'plant_vision_scan',
  YIELD_PREDICTION: 'yield_prediction',
  
  // Collaboration
  DATA_SYNCED: 'data_synced',
  TEAM_MEMBER_INVITED: 'team_member_invited',
  
  // Errors
  ERROR_OCCURRED: 'error_occurred',
  OFFLINE_MODE_ENTERED: 'offline_mode_entered',
} as const

/**
 * Track breeding-specific events
 */
export function trackBreedingEvent(
  event: keyof typeof AnalyticsEvents,
  properties?: Record<string, unknown>
): void {
  trackEvent(AnalyticsEvents[event], properties)
}

/**
 * Check if a feature flag is enabled
 */
export function isFeatureEnabled(flagKey: string): boolean {
  if (!isInitialized) return false
  return posthog.isFeatureEnabled(flagKey) ?? false
}

/**
 * Get feature flag value
 */
export function getFeatureFlag<T = unknown>(flagKey: string): T | undefined {
  if (!isInitialized) return undefined
  return posthog.getFeatureFlag(flagKey) as T | undefined
}

/**
 * Reload feature flags
 */
export function reloadFeatureFlags(): void {
  if (!isInitialized) return
  posthog.reloadFeatureFlags()
}

// Feature flag keys for Bijmantra
export const FeatureFlags = {
  ENABLE_AI_ASSISTANT: 'enable_ai_assistant',
  ENABLE_WASM_GENOMICS: 'enable_wasm_genomics',
  ENABLE_REALTIME_COLLAB: 'enable_realtime_collab',
  ENABLE_ADVANCED_ANALYTICS: 'enable_advanced_analytics',
  ENABLE_MOBILE_FEATURES: 'enable_mobile_features',
  SHOW_BETA_FEATURES: 'show_beta_features',
} as const

// React hook for feature flags
import { useState, useEffect } from 'react'

export function useFeatureFlag(flagKey: string): boolean {
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    setEnabled(isFeatureEnabled(flagKey))
    
    // Listen for flag changes
    const handleFlagsLoaded = () => {
      setEnabled(isFeatureEnabled(flagKey))
    }
    
    posthog.onFeatureFlags(handleFlagsLoaded)
  }, [flagKey])

  return enabled
}

export function useAnalytics() {
  return {
    trackEvent,
    trackPageView,
    trackBreedingEvent,
    isFeatureEnabled,
    getFeatureFlag,
  }
}

// Export posthog instance for advanced usage
export { posthog }
