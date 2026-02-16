import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { LucideIcon } from 'lucide-react'
import type { DomainMode } from '@/framework/registry/types'

export interface ContextTool {
  id: string
  label: string
  icon?: LucideIcon
  action?: () => void
  href?: string
}

interface NavigationState {
  activeDomain: DomainMode
  setActiveDomain: (domain: DomainMode) => void

  contextTools: ContextTool[]
  setContextTools: (tools: ContextTool[]) => void
}

export const useNavigationStore = create<NavigationState>()(
  persist(
    (set) => ({
      activeDomain: 'breeding',
      setActiveDomain: (domain) => set({ activeDomain: domain }),

      contextTools: [],
      setContextTools: (tools) => set({ contextTools: tools }),
    }),
    {
      name: 'bijmantra-navigation-storage',
      partialize: (state) => ({ activeDomain: state.activeDomain }), // Don't persist context tools
    }
  )
)
