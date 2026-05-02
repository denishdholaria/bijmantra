import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type DesktopToolSurface = 'filesystem' | 'editor'

interface SystemState {
  // Shell state
  isInShell: boolean
  setIsInShell: (value: boolean) => void

  // Desktop shortcuts
  shortcutOrder: string[]
  setShortcutOrder: (order: string[]) => void

  // Sidebar
  sidebarCollapsed: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void

  // Strata Launcher
  isStrataOpen: boolean
  setStrataOpen: (open: boolean) => void

  // Desktop tools
  desktopToolSurface: DesktopToolSurface | null
  lastDesktopToolSurface: DesktopToolSurface | null
  openDesktopTool: (surface: DesktopToolSurface) => void
  closeDesktopTool: () => void
}

export const useSystemStore = create<SystemState>()(
  persist(
    (set) => ({
      isInShell: false,
      setIsInShell: (value) => set({ isInShell: value }),

      shortcutOrder: [],
      setShortcutOrder: (order) => set({ shortcutOrder: order }),

      sidebarCollapsed: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      isStrataOpen: false,
      setStrataOpen: (open) => set({ isStrataOpen: open }),

      desktopToolSurface: null,
      lastDesktopToolSurface: 'editor',
      openDesktopTool: (surface) => set({ desktopToolSurface: surface, lastDesktopToolSurface: surface }),
      closeDesktopTool: () => set({ desktopToolSurface: null }),
    }),
    {
      name: 'bijmantra-system-storage',
      partialize: (state) => ({
        shortcutOrder: state.shortcutOrder,
        sidebarCollapsed: state.sidebarCollapsed,
        lastDesktopToolSurface: state.lastDesktopToolSurface,
      }),
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<
          Pick<SystemState, 'shortcutOrder' | 'sidebarCollapsed' | 'lastDesktopToolSurface'>
        > | undefined

        return {
          ...currentState,
          shortcutOrder: persisted?.shortcutOrder ?? currentState.shortcutOrder,
          sidebarCollapsed: persisted?.sidebarCollapsed ?? currentState.sidebarCollapsed,
          lastDesktopToolSurface: persisted?.lastDesktopToolSurface ?? currentState.lastDesktopToolSurface,
        }
      },
    }
  )
)
