import { describe, expect, it } from 'vitest'
import type { Division } from '@/framework/registry/types'
import {
  applyDivisionDomainProjection,
  collectModuleRoutes,
  projectDivisionsForCustomWorkspace,
  projectDivisionsForSystemWorkspace,
} from './divisionNavigationProjection'

const divisions: Division[] = [
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Plant science tools',
    icon: 'leaf',
    route: '/plant-sciences',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'programs',
        name: 'Programs',
        route: '/programs',
        isAbsolute: true,
      },
      {
        id: 'crossing',
        name: 'Crossing',
        route: '/crosses',
        isAbsolute: true,
        domains: ['breeding'],
        items: [
          { id: 'crosses', name: 'Crosses', route: '/crosses', isAbsolute: true },
          { id: 'planned', name: 'Planned Crosses', route: '/plannedcrosses', isAbsolute: true },
        ],
      },
    ],
  },
  {
    id: 'settings',
    name: 'Settings',
    description: 'System settings',
    icon: 'settings',
    route: '/settings',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'admin',
        name: 'Admin',
        route: '/admin',
        domains: ['admin'],
      },
    ],
  },
]

describe('divisionNavigationProjection', () => {
  it('collects explicit and base routes from modules', () => {
    const routes = collectModuleRoutes([
      { pages: [{ route: '/programs' }, { route: '/plannedcrosses/:id' }] },
    ])

    expect(Array.from(routes).sort()).toEqual(['/plannedcrosses', '/plannedcrosses/:id', '/programs'])
  })

  it('projects divisions for custom workspaces using route membership', () => {
    const projected = projectDivisionsForCustomWorkspace(divisions, [
      { pages: [{ route: '/plannedcrosses' }] },
    ])

    expect(projected).toHaveLength(1)
    expect(projected[0].id).toBe('plant-sciences')
    expect(projected[0].sections?.[0].id).toBe('crossing')
    expect(projected[0].sections?.[0].items?.map(item => item.id)).toEqual(['planned'])
  })

  it('projects divisions for system workspaces using the provided access policy', () => {
    const projected = projectDivisionsForSystemWorkspace(
      divisions,
      'breeding',
      (route, workspaceId) => workspaceId === 'breeding' && ['/programs', '/crosses'].includes(route),
    )

    expect(projected).toHaveLength(1)
    expect(projected[0].id).toBe('plant-sciences')
    expect(projected[0].sections?.map(section => section.id)).toEqual(['programs', 'crossing'])
    expect(projected[0].sections?.[1].items?.map(item => item.id)).toEqual(['crosses'])
  })

  it('applies domain projection to sections without removing domainless sections', () => {
    const projected = applyDivisionDomainProjection(divisions, 'admin')
    expect(projected[0].sections?.map(section => section.id)).toEqual(['programs'])
    expect(projected[1].sections?.map(section => section.id)).toEqual(['admin'])
  })
})