/**
 * Sentry Error Tracking Integration
 * Captures errors, performance metrics, and user feedback
 */

import * as Sentry from '@sentry/react'
import { API_URL, SENTRY_DSN, APP_VERSION, MODE, IS_PROD } from '@/config'

// Configuration — ADR-007: sourced from centralized config
const SENTRY_CONFIG = {
  dsn: SENTRY_DSN,
  environment: MODE || 'development',
  release: APP_VERSION,
  tracesSampleRate: IS_PROD ? 0.1 : 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
}

function escapeForRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function buildTracePropagationTargets(): Array<string | RegExp> {
  const targets: Array<string | RegExp> = [
    /^https?:\/\/localhost(?::\d+)?\/(api|brapi)\//,
    /^https?:\/\/127\.0\.0\.1(?::\d+)?\/(api|brapi)\//,
  ]

  if (API_URL) {
    targets.push(new RegExp(`^${escapeForRegExp(API_URL)}(?:/|$)`))
  }

  if (typeof window !== 'undefined') {
    targets.push(new RegExp(`^${escapeForRegExp(window.location.origin)}\/(api|brapi)\/`))
  }

  return targets
}

/**
 * Initialize Sentry
 */
export function initSentry(): void {
  if (!SENTRY_CONFIG.dsn) {
    return
  }

  Sentry.init({
    dsn: SENTRY_CONFIG.dsn,
    environment: SENTRY_CONFIG.environment,
    release: `bijmantra@${SENTRY_CONFIG.release}`,
    tracePropagationTargets: buildTracePropagationTargets(),
    
    // Performance monitoring
    tracesSampleRate: SENTRY_CONFIG.tracesSampleRate,
    
    // Session replay
    replaysSessionSampleRate: SENTRY_CONFIG.replaysSessionSampleRate,
    replaysOnErrorSampleRate: SENTRY_CONFIG.replaysOnErrorSampleRate,

    // Integrations
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],

    // Filter out non-critical errors
    beforeSend(event, hint) {
      const error = hint.originalException

      // Ignore network errors in development
      if (SENTRY_CONFIG.environment === 'development') {
        if (error instanceof TypeError && error.message.includes('fetch')) {
          return null
        }
      }

      // Ignore cancelled requests
      if (error instanceof Error && error.name === 'AbortError') {
        return null
      }

      return event
    },

    // Add custom tags
    initialScope: {
      tags: {
        app: 'bijmantra',
        module: 'frontend',
      },
    },
  })
}

/**
 * Set user context for error tracking
 */
export function setUser(user: {
  id: string | number
  email?: string
  name?: string
  organization?: string
}): void {
  Sentry.setUser({
    id: String(user.id),
    email: user.email,
    username: user.name,
    organization: user.organization,
  })
}

/**
 * Clear user context (on logout)
 */
export function clearUser(): void {
  Sentry.setUser(null)
}

/**
 * Capture an exception manually
 */
export function captureException(
  error: Error,
  context?: {
    tags?: Record<string, string>
    extra?: Record<string, unknown>
    level?: Sentry.SeverityLevel
  }
): string {
  return Sentry.captureException(error, {
    tags: context?.tags,
    extra: context?.extra,
    level: context?.level,
  })
}

/**
 * Capture a message
 */
export function captureMessage(
  message: string,
  level: Sentry.SeverityLevel = 'info'
): string {
  return Sentry.captureMessage(message, level)
}

/**
 * Add breadcrumb for debugging
 */
export function addBreadcrumb(breadcrumb: {
  category: string
  message: string
  level?: Sentry.SeverityLevel
  data?: Record<string, unknown>
}): void {
  Sentry.addBreadcrumb({
    category: breadcrumb.category,
    message: breadcrumb.message,
    level: breadcrumb.level || 'info',
    data: breadcrumb.data,
  })
}

/**
 * Start a performance transaction
 */
export function startTransaction(
  name: string,
  op: string
): Sentry.Span | undefined {
  return Sentry.startInactiveSpan({
    name,
    op,
  })
}

/**
 * Create a custom span for performance tracking
 */
export function withSpan<T>(
  name: string,
  op: string,
  fn: () => T
): T {
  return Sentry.startSpan({ name, op }, fn)
}

/**
 * Track a specific operation's performance
 */
export async function trackOperation<T>(
  name: string,
  operation: () => Promise<T>,
  tags?: Record<string, string>
): Promise<T> {
  const span = startTransaction(name, 'operation')
  
  if (tags && span) {
    Object.entries(tags).forEach(([key, value]) => {
      span.setAttribute(key, value)
    })
  }

  try {
    const result = await operation()
    span?.setStatus({ code: 1, message: 'ok' })
    return result
  } catch (error) {
    span?.setStatus({ code: 2, message: 'error' })
    throw error
  } finally {
    span?.end()
  }
}

/**
 * Show user feedback dialog
 */
export function showFeedbackDialog(options?: {
  title?: string
  subtitle?: string
  submitButtonLabel?: string
  cancelButtonLabel?: string
  email?: string
  name?: string
}): void {
  // Note: Feedback widget requires additional setup
  // This is a placeholder for the feedback functionality
  console.log('[Sentry] Feedback dialog requested', options)
}

/**
 * React Error Boundary component
 */
export const ErrorBoundary = Sentry.ErrorBoundary

/**
 * HOC for wrapping components with error boundary
 */
export const withErrorBoundary = Sentry.withErrorBoundary

/**
 * Profiler component for performance monitoring
 */
export const Profiler = Sentry.withProfiler

// Export Sentry for advanced usage
export { Sentry }
