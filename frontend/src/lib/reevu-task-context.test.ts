import { describe, expect, it } from 'vitest'

import { buildReevuTaskContext, mergeReevuTaskContext } from './reevu-task-context'

describe('buildReevuTaskContext', () => {
  it('builds scoped trial context from route and filters', () => {
    const context = buildReevuTaskContext({
      pathname: '/trials/BR-2025-A',
      search: '?status=Harvested&season=Kharif%202025',
      activeWorkspaceId: 'breeding',
    })

    expect(context).toEqual({
      active_route: '/trials/BR-2025-A',
      workspace: 'Plant Breeding',
      entity_type: 'trial',
      selected_entity_ids: ['BR-2025-A'],
      active_filters: {
        season: 'Kharif 2025',
        status: 'Harvested',
      },
      visible_columns: [],
      attached_context: [
        {
          kind: 'trial',
          entity_id: 'BR-2025-A',
          metadata: {
            route_pattern: '/trials/:id',
          },
        },
      ],
    })
  })

  it('prefers descriptive route parameter names when inferring entity type', () => {
    const context = buildReevuTaskContext({
      pathname: '/plant-vision/annotate/dataset-42',
      activeWorkspaceId: 'research',
    })

    expect(context.entity_type).toBe('dataset')
    expect(context.selected_entity_ids).toEqual(['dataset-42'])
    expect(context.attached_context[0]).toMatchObject({
      kind: 'dataset',
      entity_id: 'dataset-42',
    })
  })

  it('merges explicit page context on top of route-derived context', () => {
    const context = mergeReevuTaskContext(
      buildReevuTaskContext({
        pathname: '/germplasm-search',
        search: '?workspace=breeding',
        activeWorkspaceId: 'breeding',
      }),
      {
        entity_type: 'germplasm',
        selected_entity_ids: ['G-001', 'G-002'],
        active_filters: {
          search: 'blast resistant',
          species: 'Rice',
        },
        visible_columns: ['name', 'accession', 'species'],
        attached_context: [
          {
            kind: 'germplasm',
            entity_id: 'G-001',
            label: 'IR64',
          },
        ],
      },
    )

    expect(context).toEqual({
      active_route: '/germplasm-search',
      workspace: 'Plant Breeding',
      entity_type: 'germplasm',
      selected_entity_ids: ['G-001', 'G-002'],
      active_filters: {
        search: 'blast resistant',
        species: 'Rice',
        workspace: 'breeding',
      },
      visible_columns: ['name', 'accession', 'species'],
      attached_context: [
        {
          kind: 'germplasm',
          entity_id: 'G-001',
          label: 'IR64',
        },
      ],
    })
  })
})