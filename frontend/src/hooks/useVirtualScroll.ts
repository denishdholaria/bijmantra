/**
 * Virtual Scroll Hook
 * 
 * Wrapper around @tanstack/react-virtual for common use cases.
 */

import { useRef, useCallback, useMemo } from 'react';
import { useVirtualizer, VirtualizerOptions } from '@tanstack/react-virtual';

export interface UseVirtualScrollOptions<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  overscan?: number;
  horizontal?: boolean;
  getItemKey?: (index: number) => string | number;
}

export function useVirtualScroll<T>({
  items,
  itemHeight,
  overscan = 5,
  horizontal = false,
  getItemKey,
}: UseVirtualScrollOptions<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: typeof itemHeight === 'function' ? itemHeight : () => itemHeight,
    overscan,
    horizontal,
    getItemKey,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();

  const scrollToIndex = useCallback((index: number, options?: { align?: 'start' | 'center' | 'end' }) => {
    virtualizer.scrollToIndex(index, options);
  }, [virtualizer]);

  const scrollToOffset = useCallback((offset: number) => {
    virtualizer.scrollToOffset(offset);
  }, [virtualizer]);

  // Get the actual item for a virtual item
  const getItem = useCallback((virtualIndex: number): T | undefined => {
    return items[virtualIndex];
  }, [items]);

  // Map virtual items to actual items
  const mappedItems = useMemo(() => {
    return virtualItems.map(virtualItem => ({
      ...virtualItem,
      item: items[virtualItem.index],
    }));
  }, [virtualItems, items]);

  return {
    parentRef,
    virtualItems: mappedItems,
    totalSize,
    scrollToIndex,
    scrollToOffset,
    getItem,
    measureElement: virtualizer.measureElement,
  };
}

/**
 * Hook for infinite scroll with virtual list
 */
export interface UseInfiniteVirtualScrollOptions<T> extends UseVirtualScrollOptions<T> {
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  threshold?: number;
}

export function useInfiniteVirtualScroll<T>({
  items,
  itemHeight,
  overscan = 5,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  threshold = 5,
  getItemKey,
}: UseInfiniteVirtualScrollOptions<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: hasNextPage ? items.length + 1 : items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: typeof itemHeight === 'function' ? itemHeight : () => itemHeight,
    overscan,
    getItemKey,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Check if we need to load more
  const lastItem = virtualItems[virtualItems.length - 1];
  if (
    lastItem &&
    lastItem.index >= items.length - threshold &&
    hasNextPage &&
    !isFetchingNextPage
  ) {
    fetchNextPage();
  }

  const mappedItems = useMemo(() => {
    return virtualItems.map(virtualItem => ({
      ...virtualItem,
      item: items[virtualItem.index],
      isLoaderRow: virtualItem.index >= items.length,
    }));
  }, [virtualItems, items]);

  return {
    parentRef,
    virtualItems: mappedItems,
    totalSize: virtualizer.getTotalSize(),
    isLoading: isFetchingNextPage,
  };
}

/**
 * Hook for windowed list with dynamic heights
 */
export function useDynamicVirtualScroll<T>({
  items,
  estimatedItemHeight = 50,
  overscan = 5,
  getItemKey,
}: {
  items: T[];
  estimatedItemHeight?: number;
  overscan?: number;
  getItemKey?: (index: number) => string | number;
}) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimatedItemHeight,
    overscan,
    getItemKey,
  });

  const virtualItems = virtualizer.getVirtualItems();

  const mappedItems = useMemo(() => {
    return virtualItems.map(virtualItem => ({
      ...virtualItem,
      item: items[virtualItem.index],
    }));
  }, [virtualItems, items]);

  return {
    parentRef,
    virtualItems: mappedItems,
    totalSize: virtualizer.getTotalSize(),
    measureElement: virtualizer.measureElement,
  };
}
