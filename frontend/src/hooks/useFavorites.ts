/**
 * Favorites/Pinned Items Hook
 *
 * Manage user-defined shortcuts for quick access to entities.
 * Persisted to localStorage.
 */

import { useCallback, useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage';

export interface FavoriteItem {
  id: string;
  type: 'program' | 'trial' | 'study' | 'germplasm' | 'accession' | 'page' | 'report';
  name: string;
  route: string;
  icon?: string;
  addedAt: string;
}

const MAX_FAVORITES = 20;

export function useFavorites() {
  const [favorites, setFavorites] = useLocalStorage<FavoriteItem[]>('userFavorites', []);

  const addFavorite = useCallback(
    (item: Omit<FavoriteItem, 'addedAt'>) => {
      setFavorites((prev) => {
        // Check if already exists
        if (prev.some((f) => f.id === item.id && f.type === item.type)) {
          return prev;
        }

        const newFavorite: FavoriteItem = {
          ...item,
          addedAt: new Date().toISOString(),
        };

        // Add to beginning, limit to max
        const updated = [newFavorite, ...prev].slice(0, MAX_FAVORITES);
        return updated;
      });
    },
    [setFavorites]
  );

  const removeFavorite = useCallback(
    (id: string, type: FavoriteItem['type']) => {
      setFavorites((prev) => prev.filter((f) => !(f.id === id && f.type === type)));
    },
    [setFavorites]
  );

  const toggleFavorite = useCallback(
    (item: Omit<FavoriteItem, 'addedAt'>) => {
      const exists = favorites.some((f) => f.id === item.id && f.type === item.type);
      if (exists) {
        removeFavorite(item.id, item.type);
      } else {
        addFavorite(item);
      }
    },
    [favorites, addFavorite, removeFavorite]
  );

  const isFavorite = useCallback(
    (id: string, type: FavoriteItem['type']) => {
      return favorites.some((f) => f.id === id && f.type === type);
    },
    [favorites]
  );

  const reorderFavorites = useCallback(
    (fromIndex: number, toIndex: number) => {
      setFavorites((prev) => {
        const updated = [...prev];
        const [removed] = updated.splice(fromIndex, 1);
        updated.splice(toIndex, 0, removed);
        return updated;
      });
    },
    [setFavorites]
  );

  const clearFavorites = useCallback(() => {
    setFavorites([]);
  }, [setFavorites]);

  // Group favorites by type
  const groupedFavorites = useMemo(() => {
    const groups: Record<FavoriteItem['type'], FavoriteItem[]> = {
      program: [],
      trial: [],
      study: [],
      germplasm: [],
      accession: [],
      page: [],
      report: [],
    };

    favorites.forEach((f) => {
      groups[f.type].push(f);
    });

    return groups;
  }, [favorites]);

  return {
    favorites,
    groupedFavorites,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isFavorite,
    reorderFavorites,
    clearFavorites,
    count: favorites.length,
    maxFavorites: MAX_FAVORITES,
  };
}

export default useFavorites;
