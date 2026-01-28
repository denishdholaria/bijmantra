/**
 * Favorites Management Hook
 * 
 * Manages user's pinned/favorite items with localStorage persistence.
 * Max 8 favorites to keep the dock clean.
 */

import { useState, useEffect, useCallback } from 'react'

export interface FavoriteItem {
  id: string
  name: string
  route: string
  icon: string
  type: 'program' | 'trial' | 'study' | 'germplasm' | 'accession' | 'page' | 'report' | 'division'
  addedAt: number
}

const STORAGE_KEY = 'bijmantra-favorites'
const MAX_FAVORITES = 8

function loadFavorites(): FavoriteItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function saveFavorites(favorites: FavoriteItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites))
  } catch (e) {
    console.error('Failed to save favorites:', e)
  }
}

export function useFavorites() {
  const [favorites, setFavorites] = useState<FavoriteItem[]>(loadFavorites)

  // Sync with localStorage on mount
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setFavorites(loadFavorites())
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const addFavorite = useCallback((item: Omit<FavoriteItem, 'addedAt'>) => {
    setFavorites(prev => {
      // Check if already exists
      if (prev.some(f => f.id === item.id && f.type === item.type)) {
        return prev
      }
      // Check max limit
      if (prev.length >= MAX_FAVORITES) {
        console.warn(`Max favorites (${MAX_FAVORITES}) reached`)
        return prev
      }
      const newFavorites = [...prev, { ...item, addedAt: Date.now() }]
      saveFavorites(newFavorites)
      return newFavorites
    })
  }, [])

  const removeFavorite = useCallback((id: string, type: FavoriteItem['type']) => {
    setFavorites(prev => {
      const newFavorites = prev.filter(f => !(f.id === id && f.type === type))
      saveFavorites(newFavorites)
      return newFavorites
    })
  }, [])

  const isFavorite = useCallback((id: string, type: FavoriteItem['type']) => {
    return favorites.some(f => f.id === id && f.type === type)
  }, [favorites])

  const toggleFavorite = useCallback((item: Omit<FavoriteItem, 'addedAt'>) => {
    if (isFavorite(item.id, item.type)) {
      removeFavorite(item.id, item.type)
    } else {
      addFavorite(item)
    }
  }, [isFavorite, removeFavorite, addFavorite])

  const clearFavorites = useCallback(() => {
    setFavorites([])
    saveFavorites([])
  }, [])

  const reorderFavorites = useCallback((fromIndex: number, toIndex: number) => {
    setFavorites(prev => {
      const newFavorites = [...prev]
      const [removed] = newFavorites.splice(fromIndex, 1)
      newFavorites.splice(toIndex, 0, removed)
      saveFavorites(newFavorites)
      return newFavorites
    })
  }, [])

  return {
    favorites,
    count: favorites.length,
    maxFavorites: MAX_FAVORITES,
    canAddMore: favorites.length < MAX_FAVORITES,
    addFavorite,
    removeFavorite,
    isFavorite,
    toggleFavorite,
    clearFavorites,
    reorderFavorites,
  }
}

export default useFavorites
