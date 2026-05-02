/**
 * Color Scheme Hook
 *
 * Provides colorblind-safe and standard color palettes
 * for data visualization throughout the app.
 */

import { useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage';

export type ColorSchemeMode = 'standard' | 'colorblind';

// Okabe-Ito colorblind-safe palette
const COLORBLIND_SAFE_PALETTE = [
  '#0072B2', // Blue
  '#E69F00', // Orange
  '#009E73', // Teal
  '#CC79A7', // Pink
  '#56B4E9', // Sky Blue
  '#D55E00', // Vermillion
  '#F0E442', // Yellow
  '#000000', // Black
];

// Standard categorical palette
const STANDARD_PALETTE = [
  'hsl(230, 70%, 55%)', // Blue
  'hsl(35, 95%, 55%)', // Orange
  'hsl(150, 60%, 45%)', // Teal
  'hsl(325, 65%, 55%)', // Magenta
  'hsl(190, 75%, 50%)', // Cyan
  'hsl(0, 70%, 55%)', // Red
  'hsl(270, 60%, 55%)', // Purple
  'hsl(60, 70%, 50%)', // Yellow
];

// Sequential scales
const SEQUENTIAL_BLUE = [
  'hsl(210, 100%, 95%)',
  'hsl(210, 100%, 85%)',
  'hsl(210, 100%, 70%)',
  'hsl(210, 100%, 55%)',
  'hsl(210, 100%, 40%)',
  'hsl(210, 100%, 30%)',
];

const SEQUENTIAL_GREEN = [
  'hsl(142, 50%, 95%)',
  'hsl(142, 50%, 80%)',
  'hsl(142, 50%, 60%)',
  'hsl(142, 50%, 40%)',
  'hsl(142, 50%, 25%)',
];

// Diverging scale (red-white-green)
const DIVERGING_RWG = [
  'hsl(0, 70%, 40%)',
  'hsl(0, 70%, 55%)',
  'hsl(0, 70%, 75%)',
  'hsl(0, 0%, 95%)',
  'hsl(142, 70%, 75%)',
  'hsl(142, 70%, 55%)',
  'hsl(142, 70%, 40%)',
];

// Genotype colors
const GENOTYPE_COLORS = {
  standard: {
    aa: 'hsl(230, 70%, 55%)',
    ab: 'hsl(150, 60%, 50%)',
    bb: 'hsl(35, 95%, 55%)',
    missing: 'hsl(0, 0%, 85%)',
  },
  colorblind: {
    aa: '#0072B2',
    ab: '#009E73',
    bb: '#E69F00',
    missing: '#CCCCCC',
  },
};

export function useColorScheme() {
  const [mode, setMode] = useLocalStorage<ColorSchemeMode>('colorSchemeMode', 'standard');

  const colors = useMemo(() => {
    const isColorblind = mode === 'colorblind';

    return {
      // Categorical palette for charts
      categorical: isColorblind ? COLORBLIND_SAFE_PALETTE : STANDARD_PALETTE,

      // Get color by index (wraps around)
      getColor: (index: number) => {
        const palette = isColorblind ? COLORBLIND_SAFE_PALETTE : STANDARD_PALETTE;
        return palette[index % palette.length];
      },

      // Sequential scales
      sequential: {
        blue: SEQUENTIAL_BLUE,
        green: SEQUENTIAL_GREEN,
      },

      // Diverging scale
      diverging: DIVERGING_RWG,

      // Genotype-specific colors
      genotype: isColorblind ? GENOTYPE_COLORS.colorblind : GENOTYPE_COLORS.standard,

      // Status colors (same for both modes - already accessible)
      status: {
        success: 'hsl(142, 76%, 36%)',
        warning: 'hsl(43, 96%, 56%)',
        error: 'hsl(0, 84%, 60%)',
        info: 'hsl(217, 91%, 60%)',
      },
    };
  }, [mode]);

  return {
    mode,
    setMode,
    isColorblind: mode === 'colorblind',
    colors,
  };
}

export default useColorScheme;
