import type { WorkspaceId } from '@/types/workspace'
import {
  getAllWorkspaces,
  getPrimaryWorkspaceForRoute,
  getWorkspace,
  getWorkspaceModules,
} from '@/framework/registry/workspaces'

export interface ReevuTaskContextAttachment {
  kind: string
  entity_id: string
  label?: string
  metadata?: Record<string, unknown>
}

export interface ReevuTaskContext {
  active_route: string
  workspace?: string
  entity_type?: string
  selected_entity_ids: string[]
  active_filters: Record<string, unknown>
  visible_columns: string[]
  attached_context: ReevuTaskContextAttachment[]
}

export interface ReevuTaskContextOverride {
  workspace?: string
  entity_type?: string
  selected_entity_ids?: string[]
  active_filters?: Record<string, unknown>
  visible_columns?: string[]
  attached_context?: ReevuTaskContextAttachment[]
}

interface BuildReevuTaskContextOptions {
  pathname: string
  search?: string
  activeWorkspaceId?: WorkspaceId | null
}

interface RoutePatternMatch {
  pattern: string
  paramNames: string[]
  paramValues: string[]
}

const ACTION_SEGMENTS = new Set(['annotate', 'edit', 'view', 'detail', 'details'])

function dedupeStrings(values: string[]): string[] {
  return [...new Set(values.filter(value => value.trim().length > 0))]
}

function normalizePath(path: string): string {
  if (!path) {
    return '/'
  }

  const normalized = path.replace(/\/+$/, '')
  return normalized || '/'
}

function collectRegisteredRoutes(): string[] {
  const routes = new Set<string>()

  for (const workspace of getAllWorkspaces()) {
    for (const module of getWorkspaceModules(workspace.id)) {
      for (const page of module.pages) {
        routes.add(normalizePath(page.route))
      }
    }
  }

  return [...routes].sort((left, right) => {
    const leftSegments = left.split('/').filter(Boolean)
    const rightSegments = right.split('/').filter(Boolean)
    const leftDynamic = leftSegments.filter(segment => segment.startsWith(':')).length
    const rightDynamic = rightSegments.filter(segment => segment.startsWith(':')).length

    if (leftDynamic !== rightDynamic) {
      return leftDynamic - rightDynamic
    }

    return rightSegments.length - leftSegments.length
  })
}

const REGISTERED_ROUTES = collectRegisteredRoutes()

function matchRoutePattern(pathname: string): RoutePatternMatch | null {
  const normalizedPath = normalizePath(pathname)
  const pathSegments = normalizedPath.split('/').filter(Boolean)

  for (const pattern of REGISTERED_ROUTES) {
    const patternSegments = pattern.split('/').filter(Boolean)
    if (patternSegments.length !== pathSegments.length) {
      continue
    }

    const paramNames: string[] = []
    const paramValues: string[] = []
    let isMatch = true

    for (let index = 0; index < patternSegments.length; index += 1) {
      const patternSegment = patternSegments[index]
      const pathSegment = pathSegments[index]

      if (patternSegment.startsWith(':')) {
        paramNames.push(patternSegment.slice(1))
        paramValues.push(decodeURIComponent(pathSegment))
        continue
      }

      if (patternSegment !== pathSegment) {
        isMatch = false
        break
      }
    }

    if (isMatch) {
      return { pattern, paramNames, paramValues }
    }
  }

  return null
}

function singularize(word: string): string {
  if (word.endsWith('ies') && word.length > 3) {
    return `${word.slice(0, -3)}y`
  }

  if (word.endsWith('sses')) {
    return word.slice(0, -2)
  }

  if (word.endsWith('s') && !word.endsWith('ss') && word.length > 1) {
    return word.slice(0, -1)
  }

  return word
}

function normalizeEntityType(raw: string): string {
  return singularize(raw)
    .replace(/dbid$/i, '')
    .replace(/id$/i, '')
    .replace(/([a-z])([A-Z])/g, '$1_$2')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase()
}

function inferEntityType(pathname: string, match: RoutePatternMatch | null): string | undefined {
  const namedParam = match?.paramNames.find(name => name.toLowerCase() !== 'id')
  if (namedParam) {
    const normalizedParam = normalizeEntityType(namedParam)
    if (normalizedParam) {
      return normalizedParam
    }
  }

  const pathSegments = normalizePath(pathname).split('/').filter(Boolean)
  if (pathSegments.length >= 2) {
    const trailingSegment = pathSegments[pathSegments.length - 1]
    const parentSegment = pathSegments[pathSegments.length - 2]
    const looksLikeEntityId = /\d/.test(trailingSegment) || /[-_]/.test(trailingSegment)
    const descriptivePrefix = trailingSegment.match(/^([a-zA-Z][a-zA-Z0-9]+)[-_]\d/i)?.[1]

    if (looksLikeEntityId && ACTION_SEGMENTS.has(parentSegment) && descriptivePrefix) {
      const normalizedPrefix = normalizeEntityType(descriptivePrefix)
      if (normalizedPrefix) {
        return normalizedPrefix
      }
    }

    const normalizedParent = normalizeEntityType(parentSegment)
    if (looksLikeEntityId && normalizedParent && normalizedParent !== 'id') {
      return normalizedParent
    }
  }

  const firstSegment = pathSegments[0]
  if (!firstSegment) {
    return undefined
  }

  return normalizeEntityType(firstSegment)
}

function inferSelectedEntityIds(pathname: string, match: RoutePatternMatch | null): string[] {
  if (match?.paramValues.length) {
    return match.paramValues
  }

  const pathSegments = normalizePath(pathname).split('/').filter(Boolean)
  const trailingSegment = pathSegments[pathSegments.length - 1]
  if (!trailingSegment) {
    return []
  }

  const looksLikeEntityId = /\d/.test(trailingSegment) || /[-_]/.test(trailingSegment)
  if (pathSegments.length >= 2 && looksLikeEntityId) {
    return [decodeURIComponent(trailingSegment)]
  }

  return []
}

function parseSearchFilters(search: string | undefined): Record<string, unknown> {
  if (!search) {
    return {}
  }

  const params = new URLSearchParams(search)
  const filters: Record<string, unknown> = {}

  for (const key of new Set(params.keys())) {
    const values = params.getAll(key).filter(value => value.trim().length > 0)
    if (values.length === 0) {
      continue
    }

    filters[key] = values.length === 1 ? values[0] : values
  }

  return filters
}

function resolveWorkspaceName(pathname: string, activeWorkspaceId?: WorkspaceId | null): string | undefined {
  if (activeWorkspaceId) {
    return getWorkspace(activeWorkspaceId)?.name
  }

  const primaryWorkspaceId = getPrimaryWorkspaceForRoute(normalizePath(pathname))
  return primaryWorkspaceId ? getWorkspace(primaryWorkspaceId)?.name : undefined
}

export function buildReevuTaskContext({
  pathname,
  search,
  activeWorkspaceId,
}: BuildReevuTaskContextOptions): ReevuTaskContext {
  const normalizedPath = normalizePath(pathname)
  const routeMatch = matchRoutePattern(normalizedPath)
  const selectedEntityIds = inferSelectedEntityIds(normalizedPath, routeMatch)
  const entityType = inferEntityType(normalizedPath, routeMatch)
  const activeFilters = parseSearchFilters(search)
  const workspaceName = resolveWorkspaceName(normalizedPath, activeWorkspaceId)

  return {
    active_route: normalizedPath,
    workspace: workspaceName,
    entity_type: entityType,
    selected_entity_ids: selectedEntityIds,
    active_filters: activeFilters,
    visible_columns: [],
    attached_context: entityType
      ? selectedEntityIds.map(entityId => ({
          kind: entityType,
          entity_id: entityId,
          metadata: {
            route_pattern: routeMatch?.pattern,
          },
        }))
      : [],
  }
}

export function mergeReevuTaskContext(
  baseContext: ReevuTaskContext,
  overrideContext?: ReevuTaskContextOverride | null,
): ReevuTaskContext {
  if (!overrideContext) {
    return baseContext
  }

  return {
    active_route: baseContext.active_route,
    workspace: overrideContext.workspace ?? baseContext.workspace,
    entity_type: overrideContext.entity_type ?? baseContext.entity_type,
    selected_entity_ids: overrideContext.selected_entity_ids
      ? dedupeStrings(overrideContext.selected_entity_ids)
      : baseContext.selected_entity_ids,
    active_filters: {
      ...baseContext.active_filters,
      ...(overrideContext.active_filters || {}),
    },
    visible_columns: overrideContext.visible_columns
      ? dedupeStrings(overrideContext.visible_columns)
      : baseContext.visible_columns,
    attached_context: overrideContext.attached_context ?? baseContext.attached_context,
  }
}