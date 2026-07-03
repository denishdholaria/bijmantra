import { useEffect, useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { useDivisionRegistry, type Division } from '@/framework/registry'
import { useDockStore, type DockItem } from '@/store/dockStore'
import { SHELL_DESKTOP_ROUTES, resolveShellNavPath } from './shellNavigationResolver'

type ShellVisitItem = Omit<DockItem, 'isPinned' | 'lastVisited' | 'visitCount'>

type VisitCandidate = ShellVisitItem & {
  routeLength: number
  priority: number
}

const ROUTE_VISIT_EXCLUSIONS = new Set(['/login'])

function normalizeVisitPath(pathname: string) {
  const [pathWithoutQuery] = pathname.split(/[?#]/, 1)
  const normalized = (pathWithoutQuery || '/').replace(/\/+/g, '/')
  if (normalized === '/') return normalized
  return normalized.replace(/\/+$/, '')
}

function routeMatchesPath(pathname: string, route: string) {
  const normalizedRoute = normalizeVisitPath(route)
  if (normalizedRoute === '/') {
    return pathname === '/'
  }

  return pathname === normalizedRoute || pathname.startsWith(`${normalizedRoute}/`)
}

function routeToId(pathname: string) {
  return normalizeVisitPath(pathname)
    .replace(/^\/+/, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'route'
}

function routeToLabel(pathname: string) {
  const path = normalizeVisitPath(pathname)
  const segments = path.split('/').filter(Boolean)
  const segment = segments[segments.length - 1] ?? 'Workspace'

  return decodeURIComponent(segment)
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function candidateForRoute(
  pathname: string,
  route: string,
  item: Omit<ShellVisitItem, 'path'>,
  priority: number,
): VisitCandidate | null {
  const normalizedRoute = normalizeVisitPath(route)
  if (!routeMatchesPath(pathname, normalizedRoute)) {
    return null
  }

  return {
    ...item,
    path: normalizedRoute,
    routeLength: normalizedRoute.length,
    priority,
  }
}

export function resolveShellVisitItem(
  pathname: string,
  divisions: Division[],
): ShellVisitItem | null {
  const normalizedPath = normalizeVisitPath(pathname)
  if (SHELL_DESKTOP_ROUTES.has(normalizedPath) || ROUTE_VISIT_EXCLUSIONS.has(normalizedPath)) {
    return null
  }

  const candidates: VisitCandidate[] = []

  for (const division of divisions) {
    const divisionCandidate = candidateForRoute(
      normalizedPath,
      division.route,
      {
        id: division.id,
        label: division.name,
        icon: division.icon,
      },
      1,
    )
    if (divisionCandidate) {
      candidates.push(divisionCandidate)
    }

    for (const section of division.sections ?? []) {
      const sectionRoute = resolveShellNavPath(division.route, section.route, section.isAbsolute)
      const sectionCandidate = candidateForRoute(
        normalizedPath,
        sectionRoute,
        {
          id: `${division.id}-${section.id}`,
          label: section.name,
          icon: section.icon ?? division.icon,
        },
        2,
      )
      if (sectionCandidate) {
        candidates.push(sectionCandidate)
      }

      for (const item of section.items ?? []) {
        const itemRoute = resolveShellNavPath(division.route, item.route, item.isAbsolute)
        const itemCandidate = candidateForRoute(
          normalizedPath,
          itemRoute,
          {
            id: `${division.id}-${section.id}-${item.id}`,
            label: item.name,
            icon: item.icon ?? section.icon ?? division.icon,
          },
          3,
        )
        if (itemCandidate) {
          candidates.push(itemCandidate)
        }
      }
    }
  }

  const [bestMatch] = candidates.sort((left, right) => {
    if (right.routeLength !== left.routeLength) {
      return right.routeLength - left.routeLength
    }
    return right.priority - left.priority
  })

  if (bestMatch) {
    const { routeLength: _routeLength, priority: _priority, ...visitItem } = bestMatch
    return visitItem
  }

  return {
    id: routeToId(normalizedPath),
    path: normalizedPath,
    label: routeToLabel(normalizedPath),
    icon: 'LayoutDashboard',
  }
}

export function useShellRouteVisitRecorder() {
  const { pathname } = useLocation()
  const { activeDivisions } = useDivisionRegistry()
  const recordVisit = useDockStore((state) => state.recordVisit)

  const visitItem = useMemo(
    () => resolveShellVisitItem(pathname, activeDivisions),
    [activeDivisions, pathname],
  )

  useEffect(() => {
    if (!visitItem) {
      return
    }

    recordVisit(visitItem)
  }, [recordVisit, visitItem])
}
