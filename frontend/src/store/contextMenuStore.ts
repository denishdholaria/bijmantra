import { create } from 'zustand'

export interface ContextMenuItem {
  label: string
  action: () => void
  icon?: any
  shortcut?: string
  danger?: boolean
  disabled?: boolean
  separator?: boolean
  submenu?: ContextMenuItem[]
}

interface ContextMenuState {
  isOpen: boolean
  position: { x: number; y: number }
  items: ContextMenuItem[]
  
  openContextMenu: (x: number, y: number, items: ContextMenuItem[]) => void
  closeContextMenu: () => void
}

export const useContextMenuStore = create<ContextMenuState>((set) => ({
  isOpen: false,
  position: { x: 0, y: 0 },
  items: [],

  openContextMenu: (x, y, items) => set({
    isOpen: true,
    position: { x, y },
    items
  }),

  closeContextMenu: () => set({
    isOpen: false,
    items: [] // Clear items on close to prevent flash on next open? Or keep for fade out? keeping empty is safer.
  })
}))
