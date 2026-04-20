import { useEffect, useRef } from 'react'
import type { EditorViewMode, WorkbenchDensity } from '../workbenchTypes'
import { WORKBENCH_DENSITY_STORAGE_KEY, WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY, WORKBENCH_SESSION_STORAGE_KEY } from '../workbenchTypes'

interface PersistenceProps {
  workbenchDensity: WorkbenchDensity
  explorerCollapsed: boolean
  expandedPaths: string[]
  openFileIds: string[]
  activeFileId: string | null
  editorViewMode: EditorViewMode
}

export function useWorkbenchPersistence({
  workbenchDensity,
  explorerCollapsed,
  expandedPaths,
  openFileIds,
  activeFileId,
  editorViewMode,
}: PersistenceProps) {
  useEffect(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(WORKBENCH_DENSITY_STORAGE_KEY, workbenchDensity)
    }
  }, [workbenchDensity])

  useEffect(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(WORKBENCH_EXPLORER_COLLAPSED_STORAGE_KEY, String(explorerCollapsed))
    }
  }, [explorerCollapsed])

  useEffect(() => {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(
        WORKBENCH_SESSION_STORAGE_KEY,
        JSON.stringify({
          expandedPaths,
          openFileIds,
          activeFileId,
          editorViewMode,
        })
      )
    }
  }, [expandedPaths, openFileIds, activeFileId, editorViewMode])
}
