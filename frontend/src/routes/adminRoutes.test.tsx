import type { ReactElement } from 'react'
import { describe, expect, it } from 'vitest'

import { adminRoutes } from './admin'

function getRoute(path: string) {
  return adminRoutes.find((route) => route.path === path)
}

function getProtectedRouteProps(path: string) {
  return (getRoute(path)?.element as ReactElement | undefined)?.props ?? null
}

describe('Admin routes', () => {
  it('registers the hidden developer master board as a superuser-only route', () => {
    expect(getRoute('/admin/developer/master-board')).toBeDefined()
    expect(getProtectedRouteProps('/admin/developer/master-board')).toMatchObject({ requireSuperuser: true })
  })
})