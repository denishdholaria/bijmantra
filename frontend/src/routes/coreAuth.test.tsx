import type { ReactElement } from 'react'
import { describe, expect, it } from 'vitest'

import { ProtectedRoute } from '@/components/ProtectedRoute'
import { coreRoutes } from './core'

function getRouteElement(path: string): ReactElement | null {
  return (coreRoutes.find((route) => route.path === path)?.element as ReactElement | undefined) ?? null
}

describe('Core auth routes', () => {
  it('protects desktop redirect entry points', () => {
    expect(getRouteElement('/')?.type).toBe(ProtectedRoute)
    expect(getRouteElement('/gateway')?.type).toBe(ProtectedRoute)
  })

  it('keeps the login route public', () => {
    expect(getRouteElement('/login')?.type).not.toBe(ProtectedRoute)
  })
})
