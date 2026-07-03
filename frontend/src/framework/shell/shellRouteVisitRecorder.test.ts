import { describe, expect, it } from 'vitest'
import type { Division } from '@/framework/registry'
import { resolveShellVisitItem } from './shellRouteVisitRecorder'

const testDivisions: Division[] = [
  {
    id: 'home',
    name: 'Home',
    description: 'Dashboard, insights, and overview',
    icon: 'Home',
    route: '/dashboard',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'dashboard',
        name: 'Dashboard',
        route: '/dashboard',
        icon: 'BarChart3',
        isAbsolute: true,
      },
    ],
  },
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Breeding, genomics, phenotyping, and field operations',
    icon: 'Seedling',
    route: '/programs',
    requiredPermissions: [],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'breeding',
        name: 'Breeding',
        route: '/programs',
        icon: 'Wheat',
        isAbsolute: true,
        items: [
          { id: 'programs', name: 'Programs', route: '/programs', isAbsolute: true },
          { id: 'germplasm', name: 'Germplasm', route: '/germplasm', isAbsolute: true },
        ],
      },
      {
        id: 'phenotyping',
        name: 'Phenotyping',
        route: '/traits',
        icon: 'Microscope',
        isAbsolute: true,
        items: [
          { id: 'collect-data', name: 'Collect Data', route: '/observations/collect', isAbsolute: true },
        ],
      },
    ],
  },
]

describe('resolveShellVisitItem', () => {
  it('does not record desktop shell routes as recent app context', () => {
    expect(resolveShellVisitItem('/gateway', testDivisions)).toBeNull()
    expect(resolveShellVisitItem('/', testDivisions)).toBeNull()
  })

  it('uses the most specific registry item for recent route metadata', () => {
    expect(resolveShellVisitItem('/observations/collect/field-book', testDivisions)).toEqual({
      id: 'plant-sciences-phenotyping-collect-data',
      path: '/observations/collect',
      label: 'Collect Data',
      icon: 'Microscope',
    })
  })

  it('prefers item metadata over section and division metadata for shared routes', () => {
    expect(resolveShellVisitItem('/programs', testDivisions)).toEqual({
      id: 'plant-sciences-breeding-programs',
      path: '/programs',
      label: 'Programs',
      icon: 'Wheat',
    })
  })

  it('falls back to readable route labels for unregistered app routes', () => {
    expect(resolveShellVisitItem('/unknown-lab-route?tab=notes', testDivisions)).toEqual({
      id: 'unknown-lab-route',
      path: '/unknown-lab-route',
      label: 'Unknown Lab Route',
      icon: 'LayoutDashboard',
    })
  })
})
