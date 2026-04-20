import type { WorkspaceId } from '@/types/workspace'
import type { DomainMode, Division, DivisionSection } from '@/framework/registry/types'
import { resolveShellNavPath } from './shellNavigationResolver'

type RoutePage = {
  route: string
}

type RouteModule = {
  pages: RoutePage[]
}

function getBaseRoute(route: string): string | null {
  const baseRoute = route.split('/')[1]
  return baseRoute ? `/${baseRoute}` : null
}

export function collectModuleRoutes(modules: RouteModule[]): Set<string> {
  const routes = new Set<string>()

  for (const module of modules) {
    for (const page of module.pages) {
      routes.add(page.route)
      const baseRoute = getBaseRoute(page.route)
      if (baseRoute) {
        routes.add(baseRoute)
      }
    }
  }

  return routes
}

function divisionHasAccessibleRoute(
  division: Division,
  canAccessRoute: (route: string) => boolean,
): boolean {
  if (canAccessRoute(division.route)) {
    return true
  }

  if (!division.sections?.length) {
    return false
  }

  return division.sections.some(section => sectionHasAccessibleRoute(division.route, section, canAccessRoute))
}

function sectionHasAccessibleRoute(
  divisionRoute: string,
  section: DivisionSection,
  canAccessRoute: (route: string) => boolean,
): boolean {
  const sectionRoute = resolveShellNavPath(divisionRoute, section.route, section.isAbsolute)
  if (canAccessRoute(sectionRoute)) {
    return true
  }

  if (!section.items?.length) {
    return false
  }

  return section.items.some(item => canAccessRoute(resolveShellNavPath(divisionRoute, item.route, item.isAbsolute)))
}

function filterDivisionSectionsByAccess(
  division: Division,
  canAccessRoute: (route: string) => boolean,
): Division {
  if (!division.sections?.length) {
    return division
  }

  const filteredSections = division.sections
    .map(section => {
      if (!section.items?.length) {
        const sectionRoute = resolveShellNavPath(division.route, section.route, section.isAbsolute)
        return canAccessRoute(sectionRoute) ? section : null
      }

      const filteredItems = section.items.filter(item =>
        canAccessRoute(resolveShellNavPath(division.route, item.route, item.isAbsolute)),
      )

      if (filteredItems.length === 0) {
        return null
      }

      return {
        ...section,
        items: filteredItems,
      }
    })
    .filter(Boolean) as DivisionSection[]

  return {
    ...division,
    sections: filteredSections,
  }
}

export function projectDivisionsByRouteAccess(
  divisions: Division[],
  canAccessRoute: (route: string) => boolean,
): Division[] {
  return divisions
    .filter(division => divisionHasAccessibleRoute(division, canAccessRoute))
    .map(division => filterDivisionSectionsByAccess(division, canAccessRoute))
}

export function applyDivisionDomainProjection(
  divisions: Division[],
  activeDomain: DomainMode,
): Division[] {
  if (activeDomain === 'all') {
    return divisions
  }

  return divisions.map(division => {
    if (!division.sections?.length) {
      return division
    }

    const domainFilteredSections = division.sections.filter(section => {
      if (!section.domains || section.domains.length === 0) {
        return true
      }

      return section.domains.includes(activeDomain)
    })

    return {
      ...division,
      sections: domainFilteredSections,
    }
  })
}

export function projectDivisionsForCustomWorkspace(
  divisions: Division[],
  customWorkspacePages: RouteModule[],
): Division[] {
  const customRoutes = collectModuleRoutes(customWorkspacePages)
  return projectDivisionsByRouteAccess(divisions, route => customRoutes.has(route))
}

export function projectDivisionsForSystemWorkspace(
  divisions: Division[],
  activeWorkspaceId: WorkspaceId | null,
  canAccessRoute: (route: string, workspaceId: WorkspaceId) => boolean,
): Division[] {
  if (!activeWorkspaceId) {
    return divisions
  }

  return projectDivisionsByRouteAccess(divisions, route => canAccessRoute(route, activeWorkspaceId))
}