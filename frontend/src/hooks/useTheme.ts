/**
 * Theme Hook
 * 
 * Provides current theme state for components.
 */

import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('bijmantra-theme');
      if (stored === 'nasa') return 'dark';
      if (stored === 'light' || stored === 'dark') return stored;
      return 'light';
    }
    return 'light';
  });

  useEffect(() => {
    const handleStorage = () => {
      const stored = localStorage.getItem('bijmantra-theme');
      if (stored === 'nasa') {
        setTheme('dark');
      } else if (stored === 'light' || stored === 'dark') {
        setTheme(stored);
      }
    };
    
    // Also check for class changes on document
    const checkTheme = () => {
      const isDark = document.documentElement.classList.contains('dark');
      setTheme(isDark ? 'dark' : 'light');
    };

    // Initial check
    checkTheme();
    
    window.addEventListener('storage', handleStorage);
    
    // Watch for class changes
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => {
      window.removeEventListener('storage', handleStorage);
      observer.disconnect();
    };
  }, []);

  return { theme, isDark: theme === 'dark' };
}

export default useTheme;
