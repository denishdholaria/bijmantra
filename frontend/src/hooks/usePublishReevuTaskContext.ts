import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

import type { ReevuTaskContextOverride } from '@/lib/reevu-task-context'
import { useReevuTaskContextStore } from '@/store/reevuTaskContextStore'

export function usePublishReevuTaskContext(context: ReevuTaskContextOverride | null) {
  const location = useLocation()
  const setRouteContext = useReevuTaskContextStore(state => state.setRouteContext)
  const clearRouteContext = useReevuTaskContextStore(state => state.clearRouteContext)

  useEffect(() => {
    if (context) {
      setRouteContext(location.pathname, context)
    } else {
      clearRouteContext(location.pathname)
    }

    return () => {
      clearRouteContext(location.pathname)
    }
  }, [clearRouteContext, context, location.pathname, setRouteContext])
}