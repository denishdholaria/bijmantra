/**
 * useMediaQuery Hook
 * 
 * React hook for responsive design that listens to CSS media query changes.
 * Returns true when the media query matches, false otherwise.
 * 
 * @example
 * const isMobile = useMediaQuery('(max-width: 1023px)');
 * const isDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
 * const isReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
 */

import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  // Initialize with the current match state (SSR-safe default to false)
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);
    
    // Update state when query changes
    setMatches(mediaQuery.matches);

    // Handler for media query changes
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      // Legacy browsers (Safari < 14)
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [query]);

  return matches;
}

export default useMediaQuery;
