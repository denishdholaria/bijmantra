/**
 * Theme Hook
 * 
 * Provides current theme state for components.
 * Theme is initialized in index.html before React loads.
 */

import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

// Get initial theme from DOM (set by index.html script)
function getInitialTheme(): Theme {
  if (typeof window !== 'undefined') {
    // First check the DOM class (most reliable, set by index.html)
    if (document.documentElement.classList.contains('dark')) {
      return 'dark';
    }
    if (document.documentElement.classList.contains('light')) {
      return 'light';
    }
    // Fallback to localStorage
    const stored = localStorage.getItem('bijmantra-theme');
    if (stored === 'nasa') return 'dark';
    if (stored === 'light' || stored === 'dark') return stored;
  }
  return 'light';
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    // Listen for theme changes from ThemeToggle
    const handleThemeChange = (e: CustomEvent<Theme>) => {
      setTheme(e.detail);
    };
    
    // Listen for storage changes (cross-tab sync)
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'bijmantra-theme') {
        const newTheme = e.newValue;
        if (newTheme === 'light' || newTheme === 'dark') {
          setTheme(newTheme);
        }
      }
    };
    
    // Watch for class changes on document
    const checkTheme = () => {
      const isDark = document.documentElement.classList.contains('dark');
      setTheme(isDark ? 'dark' : 'light');
    };

    // Initial check
    checkTheme();
    
    window.addEventListener('theme-change', handleThemeChange as EventListener);
    window.addEventListener('storage', handleStorage);
    
    // Watch for class changes
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => {
      window.removeEventListener('theme-change', handleThemeChange as EventListener);
      window.removeEventListener('storage', handleStorage);
      observer.disconnect();
    };
  }, []);

  return { theme, isDark: theme === 'dark' };
}

export default useTheme;
