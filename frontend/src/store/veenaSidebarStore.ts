/**
 * veenaSidebarStore - Global toggle for the Veena AI sidebar panel.
 *
 * Shared between SystemBar (trigger) and VeenaSidebar (panel).
 * Keyboard shortcut (Ctrl+/) is handled inside VeenaSidebar.
 */

import { create } from 'zustand'

interface VeenaSidebarState {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

export const useVeenaSidebarStore = create<VeenaSidebarState>((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
}))
