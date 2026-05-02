import { describe, expect, it } from 'vitest'
import type { RouteObject } from 'react-router-dom'

import {
  adminRoutes,
  aiRoutes,
  agronomyRoutes,
  breedingRoutes,
  commercialRoutes,
  coreRoutes,
  cropSystemsRoutes,
  fieldRoutes,
  futureRoutes,
  genomicsRoutes,
  seedOpsRoutes,
  weatherRoutes,
} from '@/routes'
import { flattenRoutePaths } from '@/framework/routing/routeTree'
import { workspaceModules } from '@/framework/registry/workspaces'

function isStaticWorkspaceRoute(route: string): boolean {
  return !route.includes(':')
}

describe('Workspace route coverage', () => {
  const appRouteSet = flattenRoutePaths([
    ...coreRoutes,
    ...breedingRoutes,
    ...seedOpsRoutes,
    ...genomicsRoutes,
    ...commercialRoutes,
    ...cropSystemsRoutes,
    ...futureRoutes,
    ...adminRoutes,
    ...aiRoutes,
    ...fieldRoutes,
    ...agronomyRoutes,
    ...weatherRoutes,
  ])

  it('covers all static workspace module page routes', () => {
    const workspaceRoutes = new Set<string>()

    for (const module of workspaceModules) {
      for (const page of module.pages) {
        if (isStaticWorkspaceRoute(page.route)) {
          workspaceRoutes.add(page.route)
        }
      }
    }

    const missing = [...workspaceRoutes].filter((route) => !appRouteSet.has(route))

    expect(missing).toEqual([])
  })
})
