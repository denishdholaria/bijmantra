import { describe, expect, it } from 'vitest'
import type { RouteObject } from 'react-router-dom'

import {
  adminRoutes,
  aiRoutes,
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
import { agronomyRoutes } from '@/divisions/agronomy/routes'
import { divisions } from '@/framework/registry/divisions'

function getRegistryAbsoluteRoutes(): Set<string> {
  const routes = new Set<string>()

  for (const division of divisions) {
    if (!division.sections) continue

    for (const section of division.sections) {
      const sectionPath = section.isAbsolute ? section.route : `${division.route}${section.route}`
      routes.add(sectionPath)

      if (section.items) {
        for (const item of section.items) {
          const itemPath = item.isAbsolute ? item.route : `${division.route}${item.route}`
          routes.add(itemPath)
        }
      }
    }
  }

  return routes
}

describe('Route accessibility smoke checks', () => {
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

  it('covers all absolute registry routes in app routers', () => {
    const registryRoutes = getRegistryAbsoluteRoutes()
    const missing = [...registryRoutes].filter((route) => !appRouteSet.has(route))

    expect(missing).toEqual([])
  })

  it('includes high-risk navigation routes', () => {
    const critical = [
      '/plannedcrosses',
      '/crossingprojects',
      '/crossingplanner',
      '/seed-operations',
      '/seed-operations/samples',
      '/seed-operations/quality-gate',
      '/seed-operations/lots',
      '/knowledge/training',
      '/knowledge/forums',
      '/performance-ranking',
      '/spatial-analysis',
    ]

    for (const path of critical) {
      expect(appRouteSet.has(path), `missing critical route: ${path}`).toBe(true)
    }
  })
})
