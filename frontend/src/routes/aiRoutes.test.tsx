import type { ReactElement } from 'react'
import { describe, expect, it } from 'vitest'

import { LEGACY_REEVU_ROUTE } from '@/lib/legacyReevu'

import { aiRoutes } from './ai'

function getRoute(path: string) {
  return aiRoutes.find((route) => route.path === path)
}

function getElementProps(path: string) {
  return (getRoute(path)?.element as ReactElement | undefined)?.props ?? null
}

describe('AI routes', () => {
  it('keeps REEVU entry routes wired to the canonical page', () => {
    expect(getRoute('/reevu')).toBeDefined()
    expect(getRoute(LEGACY_REEVU_ROUTE)).toBeDefined()
  })

  it('does not register duplicate AI route paths', () => {
    const staticPaths = aiRoutes
      .map(route => route.path)
      .filter((path): path is string => typeof path === 'string')

    expect(new Set(staticPaths).size).toBe(staticPaths.length)
  })

  it('redirects legacy aliases to the canonical /reevu route', () => {
    expect(getElementProps('/reeva')).toMatchObject({ to: '/reevu', replace: true })
    expect(getElementProps('/ai-assistant')).toMatchObject({ to: '/reevu', replace: true })
  })
})
