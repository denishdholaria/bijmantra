/**
 * Role-Based Navigation Hook
 * Filters navigation items based on user role for reduced cognitive load
 */

import { useMemo } from 'react'
import { useAuthStore } from '@/store/auth'

export type UserRole = 'breeder' | 'field_tech' | 'analyst' | 'admin' | 'researcher' | 'all'

interface NavItem {
  path: string
  label: string
  icon: string
}

interface NavSection {
  title: string
  icon: string
  items: NavItem[]
}

// Define which sections are relevant for each role
const ROLE_SECTIONS: Record<UserRole, string[]> = {
  breeder: [
    'Core', 'Germplasm', 'Phenotyping', 'Genomics', 'Advanced', 
    'Tools', 'Planning', 'Analytics'
  ],
  field_tech: [
    'Core', 'Phenotyping', 'Tools', 'AI', 'System'
  ],
  analyst: [
    'Core', 'Genomics', 'Advanced', 'Analytics', 'WASM Engine', 
    'Tools', 'System'
  ],
  admin: [
    'Core', 'System', 'Collaboration', 'Help'
  ],
  researcher: [
    'Core', 'Germplasm', 'Phenotyping', 'Genotyping', 'Genomics', 
    'Advanced', 'Analytics', 'WASM Engine', 'Tools'
  ],
  all: [] // Empty means show all
}

// Priority items per role (shown first in favorites)
const ROLE_PRIORITIES: Record<UserRole, string[]> = {
  breeder: [
    '/germplasm', '/crosses', '/trials', '/genomic-selection', 
    '/breeding-values', '/parent-selection'
  ],
  field_tech: [
    '/observations', '/scanner', '/field-scanner', '/weather', 
    '/data-sync', '/offline'
  ],
  analyst: [
    '/analytics', '/wasm-genomics', '/visualization', '/advanced-reports',
    '/genetic-diversity', '/qtl-mapping'
  ],
  admin: [
    '/users', '/system-health', '/backup', '/auditlog',
    '/team-management', '/settings'
  ],
  researcher: [
    '/germplasm', '/genomic-selection', '/qtl-mapping', '/wasm-genomics',
    '/genetic-diversity', '/publications'
  ],
  all: ['/dashboard', '/germplasm', '/trials', '/observations']
}

// Quick actions per role
export const ROLE_QUICK_ACTIONS: Record<UserRole, { id: string; label: string; icon: string; path: string }[]> = {
  breeder: [
    { id: 'new-cross', label: 'Create Cross', icon: '🧬', path: '/crosses/new' },
    { id: 'parent-select', label: 'Select Parents', icon: '👨‍👩‍👧', path: '/parent-selection' },
    { id: 'view-pipeline', label: 'Breeding Pipeline', icon: '🔀', path: '/pipeline' },
    { id: 'genomic-sel', label: 'Genomic Selection', icon: '🎯', path: '/genomic-selection' },
  ],
  field_tech: [
    { id: 'collect-data', label: 'Collect Data', icon: '📋', path: '/observations/collect' },
    { id: 'scan-barcode', label: 'Scan Barcode', icon: '📱', path: '/scanner' },
    { id: 'field-scan', label: 'Field Scanner', icon: '🌿', path: '/field-scanner' },
    { id: 'sync-data', label: 'Sync Data', icon: '🔄', path: '/data-sync' },
  ],
  analyst: [
    { id: 'run-analysis', label: 'Run Analysis', icon: '📊', path: '/wasm-genomics' },
    { id: 'create-report', label: 'Create Report', icon: '📑', path: '/advanced-reports' },
    { id: 'visualize', label: 'Visualize Data', icon: '📈', path: '/visualization' },
    { id: 'qtl-map', label: 'QTL Mapping', icon: '🎯', path: '/qtl-mapping' },
  ],
  admin: [
    { id: 'manage-users', label: 'Manage Users', icon: '👥', path: '/users' },
    { id: 'system-health', label: 'System Health', icon: '💚', path: '/system-health' },
    { id: 'backup', label: 'Backup Data', icon: '💾', path: '/backup' },
    { id: 'audit', label: 'View Audit Log', icon: '📋', path: '/auditlog' },
  ],
  researcher: [
    { id: 'search-germplasm', label: 'Search Germplasm', icon: '🔍', path: '/germplasm-search' },
    { id: 'analyze-diversity', label: 'Genetic Diversity', icon: '🌈', path: '/genetic-diversity' },
    { id: 'gwas', label: 'QTL/GWAS', icon: '🎯', path: '/qtl-mapping' },
    { id: 'publications', label: 'Publications', icon: '📰', path: '/publications' },
  ],
  all: [
    { id: 'new-observation', label: 'Add Observation', icon: '➕', path: '/observations/collect' },
    { id: 'new-germplasm', label: 'Add Germplasm', icon: '🌱', path: '/germplasm/new' },
    { id: 'new-cross', label: 'Create Cross', icon: '🧬', path: '/crosses/new' },
    { id: 'ai-chat', label: 'Ask AI Assistant', icon: '💬', path: '/ai-assistant' },
  ],
}

export function useRoleBasedNav(navSections: NavSection[]) {
  const { user } = useAuthStore()
  
  // Determine user role - default to 'all' if not set
  const userRole: UserRole = useMemo(() => {
    if (!user) return 'all'
    if (user.is_superuser) return 'all' // Superusers see everything
    // In production, this would come from user.role or similar
    // For now, default to 'all'
    return 'all'
  }, [user])

  // Filter sections based on role
  const filteredSections = useMemo(() => {
    if (userRole === 'all') return navSections
    
    const allowedSections: string[] = ROLE_SECTIONS[userRole] || []
    return navSections.filter(section => 
      allowedSections.includes(section.title)
    )
  }, [navSections, userRole])

  // Get priority items for the role
  const priorityItems = useMemo(() => {
    return ROLE_PRIORITIES[userRole]
  }, [userRole])

  // Get quick actions for the role
  const quickActions = useMemo(() => {
    return ROLE_QUICK_ACTIONS[userRole]
  }, [userRole])

  return {
    userRole,
    filteredSections,
    priorityItems,
    quickActions,
    setRole: () => {}, // Placeholder for role switching UI
  }
}

// Hook for role switching (for demo/testing)
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface RoleStore {
  overrideRole: UserRole | null
  setOverrideRole: (role: UserRole | null) => void
}

export const useRoleStore = create<RoleStore>()(
  persist(
    (set) => ({
      overrideRole: null,
      setOverrideRole: (role) => set({ overrideRole: role }),
    }),
    { name: 'bijmantra-role-override' }
  )
)
