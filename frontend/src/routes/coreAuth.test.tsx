import type { ReactElement } from 'react'
import { Navigate } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { coreRoutes } from './core'

function getRouteElement(path: string): ReactElement | null {
  return (coreRoutes.find((route) => route.path === path)?.element as ReactElement | undefined) ?? null
}

function getProtectedRouteChild(path: string): ReactElement | null {
  const element = getRouteElement(path)
  if (element?.type !== ProtectedRoute) return null
  return (element.props as { children?: ReactElement }).children ?? null
}

describe('Core auth routes', () => {
  it('protects desktop redirect entry points', () => {
    expect(getRouteElement('/')?.type).toBe(ProtectedRoute)
    expect(getRouteElement('/gateway')?.type).toBe(ProtectedRoute)
  })

  it('routes the root entry point to the gateway shell home', () => {
    const rootChild = getProtectedRouteChild('/')

    expect(rootChild?.type).toBe(Navigate)
    expect(rootChild?.props).toMatchObject({ to: '/gateway', replace: true })
  })

  it('keeps gateway as the shell home instead of redirecting to dashboard', () => {
    const gatewayChild = getProtectedRouteChild('/gateway')

    expect(gatewayChild?.type).not.toBe(Navigate)
    expect(gatewayChild?.props).not.toMatchObject({ to: '/dashboard' })
  })

  it('keeps the login route public', () => {
    expect(getRouteElement('/login')?.type).not.toBe(ProtectedRoute)
  })
})
