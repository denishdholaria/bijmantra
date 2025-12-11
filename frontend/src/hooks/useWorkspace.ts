/**
 * Workspace Management Hook
 * 
 * Manages role-based workspace switching (Breeder, Seed Company, Admin).
 * Filters divisions based on current workspace.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { divisions } from '@/framework/registry/divisions'
import type { Division } from '@/framework/registry/types'

export type WorkspaceType = 'breeder' | 'seed_company' | 'researcher' | 'lab_tech' | 'admin'

export interface Workspace {
  id: WorkspaceType
  name: string
  description: string
  icon: string
  divisionIds: string[]
  color: string
}

// Predefined workspaces with their relevant divisions
export const WORKSPACES: Workspace[] = [
  {
    id: 'breeder',
    name: 'Breeder',
    description: 'Plant breeding, trials, germplasm, crosses',
    icon: 'Wheat',
    color: 'from-green-500 to-emerald-500',
    divisionIds: ['home', 'plant-sciences', 'seed-bank', 'earth-systems', 'knowledge', 'settings'],
  },
  {
    id: 'seed_company',
    name: 'Seed Company',
    description: 'Quality, processing, inventory, dispatch',
    icon: 'Factory',
    color: 'from-blue-500 to-indigo-500',
    divisionIds: ['home', 'seed-operations', 'commercial', 'plant-sciences', 'knowledge', 'settings'],
  },
  {
    id: 'researcher',
    name: 'Researcher',
    description: 'Genomics, GWAS, analytics, statistics',
    icon: 'Microscope',
    color: 'from-purple-500 to-violet-500',
    divisionIds: ['home', 'plant-sciences', 'sun-earth-systems', 'space-research', 'knowledge', 'settings'],
  },
  {
    id: 'lab_tech',
    name: 'Lab Tech',
    description: 'Samples, testing, certificates, quality',
    icon: 'FlaskConical',
    color: 'from-cyan-500 to-teal-500',
    divisionIds: ['home', 'seed-operations', 'sensor-networks', 'knowledge', 'settings'],
  },
  {
    id: 'admin',
    name: 'Admin',
    description: 'Full access to all modules',
    icon: 'Settings',
    color: 'from-gray-500 to-slate-600',
    divisionIds: divisions.map(d => d.id), // All divisions
  },
]

const STORAGE_KEY = 'bijmantra-workspace'

function loadWorkspace(): WorkspaceType {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && WORKSPACES.some(w => w.id === stored)) {
      return stored as WorkspaceType
    }
  } catch {
    // Ignore
  }
  return 'breeder' // Default workspace
}

function saveWorkspace(workspace: WorkspaceType) {
  try {
    localStorage.setItem(STORAGE_KEY, workspace)
  } catch (e) {
    console.error('Failed to save workspace:', e)
  }
}

export function useWorkspace() {
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceType>(loadWorkspace)

  // Sync with localStorage on mount
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setCurrentWorkspace(loadWorkspace())
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const workspace = useMemo(() => {
    return WORKSPACES.find(w => w.id === currentWorkspace) || WORKSPACES[0]
  }, [currentWorkspace])

  const setWorkspace = useCallback((workspaceId: WorkspaceType) => {
    setCurrentWorkspace(workspaceId)
    saveWorkspace(workspaceId)
  }, [])

  // Filter divisions based on current workspace
  const filteredDivisions = useMemo((): Division[] => {
    const allowedIds = new Set(workspace.divisionIds)
    return divisions.filter(d => allowedIds.has(d.id))
  }, [workspace])

  // Check if a division is visible in current workspace
  const isDivisionVisible = useCallback((divisionId: string) => {
    return workspace.divisionIds.includes(divisionId)
  }, [workspace])

  return {
    currentWorkspace,
    workspace,
    workspaces: WORKSPACES,
    setWorkspace,
    filteredDivisions,
    isDivisionVisible,
    isAdmin: currentWorkspace === 'admin',
  }
}

export default useWorkspace
