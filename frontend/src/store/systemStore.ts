import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SystemState {
  // Shell state
  isInShell: boolean
  setIsInShell: (value: boolean) => void

  // Desktop shortcuts
  shortcutOrder: string[]
  setShortcutOrder: (order: string[]) => void

  // Wallpaper
  activeWallpaperId: string
  setActiveWallpaperId: (id: string) => void
  customWallpaperUrl: string | null
  setCustomWallpaperUrl: (url: string | null) => void

  // Sidebar
  sidebarCollapsed: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
}

export const useSystemStore = create<SystemState>()(
  persist(
    (set) => ({
      isInShell: false,
      setIsInShell: (value) => set({ isInShell: value }),

      shortcutOrder: [],
      setShortcutOrder: (order) => set({ shortcutOrder: order }),

      activeWallpaperId: 'bijmantrags',
      setActiveWallpaperId: (id) => set({ activeWallpaperId: id }),
      customWallpaperUrl: null,
      setCustomWallpaperUrl: (url) => set({ customWallpaperUrl: url }),

      sidebarCollapsed: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: 'bijmantra-system-storage',
      partialize: (state) => ({
        shortcutOrder: state.shortcutOrder,
        activeWallpaperId: state.activeWallpaperId,
        customWallpaperUrl: state.customWallpaperUrl,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)
