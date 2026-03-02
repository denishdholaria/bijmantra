import { describe, expect, it } from 'vitest'
import type { RouteObject } from 'react-router-dom'

import {
  adminRoutes,
  aiRoutes,
  agronomyRoutes,
  breedingRoutes,
  commercialRoutes,
  coreRoutes,
  fieldRoutes,
  futureRoutes,
  genomicsRoutes,
  seedOpsRoutes,
  weatherRoutes,
} from '@/routes'
import { workspaceModules } from '@/framework/registry/workspaces'

function flattenPaths(routes: RouteObject[]): Set<string> {
  const paths = new Set<string>()

  const walk = (nodes: RouteObject[]) => {
    for (const node of nodes) {
      if (typeof node.path === 'string') {
        paths.add(node.path)
      }
      if (node.children?.length) {
        walk(node.children)
      }
    }
  }

  walk(routes)
  return paths
}

function isStaticWorkspaceRoute(route: string): boolean {
  return !route.includes(':')
}

describe('Workspace route coverage', () => {
  const appRouteSet = flattenPaths([
    ...coreRoutes,
    ...breedingRoutes,
    ...seedOpsRoutes,
    ...genomicsRoutes,
    ...commercialRoutes,
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
