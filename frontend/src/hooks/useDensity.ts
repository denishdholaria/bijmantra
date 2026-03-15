/**
 * Density Mode Hook
 *
 * User-configurable UI density for different use cases:
 * - compact: Power users, dense data
 * - comfortable: Default, balanced
 * - spacious: Accessibility, touch-friendly
 */

import { useEffect } from 'react';
import { useLocalStorage } from './useLocalStorage';

export type DensityMode = 'compact' | 'comfortable' | 'spacious';

interface DensityConfig {
  base: number;
  padding: {
    sm: string;
    md: string;
    lg: string;
  };
  gap: {
    sm: string;
    md: string;
    lg: string;
  };
  fontSize: {
    sm: string;
    base: string;
    lg: string;
  };
  touchTarget: string;
}

const DENSITY_CONFIGS: Record<DensityMode, DensityConfig> = {
  compact: {
    base: 4,
    padding: { sm: '0.25rem', md: '0.5rem', lg: '0.75rem' },
    gap: { sm: '0.25rem', md: '0.5rem', lg: '0.75rem' },
    fontSize: { sm: '0.7rem', base: '0.8rem', lg: '0.9rem' },
    touchTarget: '32px',
  },
  comfortable: {
    base: 8,
    padding: { sm: '0.5rem', md: '1rem', lg: '1.5rem' },
    gap: { sm: '0.5rem', md: '1rem', lg: '1.5rem' },
    fontSize: { sm: '0.75rem', base: '0.875rem', lg: '1rem' },
    touchTarget: '40px',
  },
  spacious: {
    base: 12,
    padding: { sm: '0.75rem', md: '1.5rem', lg: '2rem' },
    gap: { sm: '0.75rem', md: '1.5rem', lg: '2rem' },
    fontSize: { sm: '0.875rem', base: '1rem', lg: '1.125rem' },
    touchTarget: '48px',
  },
};

export function useDensity() {
  const [density, setDensity] = useLocalStorage<DensityMode>('uiDensity', 'comfortable');

  // Apply density attribute to document
  useEffect(() => {
    document.documentElement.setAttribute('data-density', density);
    return () => {
      document.documentElement.removeAttribute('data-density');
    };
  }, [density]);

  const config = DENSITY_CONFIGS[density];

  return {
    density,
    setDensity,
    config,
    // Utility classes based on density
    classes: {
      padding: {
        sm: `p-[${config.padding.sm}]`,
        md: `p-[${config.padding.md}]`,
        lg: `p-[${config.padding.lg}]`,
      },
      gap: {
        sm: `gap-[${config.gap.sm}]`,
        md: `gap-[${config.gap.md}]`,
        lg: `gap-[${config.gap.lg}]`,
      },
    },
    // Check if current density
    isCompact: density === 'compact',
    isComfortable: density === 'comfortable',
    isSpacious: density === 'spacious',
  };
}

export default useDensity;
