import { create } from 'zustand'

import type { ReevuTaskContextOverride } from '@/lib/reevu-task-context'

interface ReevuTaskContextState {
  routeContexts: Record<string, ReevuTaskContextOverride>
  setRouteContext: (route: string, context: ReevuTaskContextOverride) => void
  clearRouteContext: (route: string) => void
}

export const useReevuTaskContextStore = create<ReevuTaskContextState>()(set => ({
  routeContexts: {},
  setRouteContext: (route, context) => {
    set(state => ({
      routeContexts: {
        ...state.routeContexts,
        [route]: context,
      },
    }))
  },
  clearRouteContext: route => {
    set(state => {
      const nextContexts = { ...state.routeContexts }
      delete nextContexts[route]

      return {
        routeContexts: nextContexts,
      }
    })
  },
}))