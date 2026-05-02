/**
 * Hook for managing pinned navigation items
 * Persists to localStorage for user preferences
 */

import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'bijmantra-pinned-nav'

const DEFAULT_PINNED = [
  '/dashboard',
  '/germplasm',
  '/trials',
  '/observations',
]

export function usePinnedNav() {
  const [pinnedItems, setPinnedItems] = useState<string[]>([])

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        setPinnedItems(JSON.parse(stored))
      } catch {
        setPinnedItems(DEFAULT_PINNED)
      }
    } else {
      setPinnedItems(DEFAULT_PINNED)
    }
  }, [])

  // Save to localStorage when changed
  const savePinned = useCallback((items: string[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
    setPinnedItems(items)
  }, [])

  const togglePin = useCallback((path: string) => {
    const newPinned = pinnedItems.includes(path)
      ? pinnedItems.filter(p => p !== path)
      : [...pinnedItems, path]
    savePinned(newPinned)
  }, [pinnedItems, savePinned])

  const isPinned = useCallback((path: string) => {
    return pinnedItems.includes(path)
  }, [pinnedItems])

  const reorderPinned = useCallback((fromIndex: number, toIndex: number) => {
    const newPinned = [...pinnedItems]
    const [removed] = newPinned.splice(fromIndex, 1)
    newPinned.splice(toIndex, 0, removed)
    savePinned(newPinned)
  }, [pinnedItems, savePinned])

  return {
    pinnedItems,
    togglePin,
    isPinned,
    reorderPinned,
  }
}
