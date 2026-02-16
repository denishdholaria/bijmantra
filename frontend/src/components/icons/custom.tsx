/**
 * Custom Agriculture Icons for BijMantra
 * 
 * SVG icons specific to plant breeding and agriculture
 * that aren't available in standard icon libraries.
 */

import { cn } from '@/lib/utils';

interface CustomIconProps {
  className?: string;
  strokeWidth?: number;
}

/**
 * Germplasm Accession Icon
 * Represents a seed with genetic helix pattern
 */
export function GermplasmIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Seed shape */}
      <ellipse cx="12" cy="12" rx="5" ry="8" />
      {/* Genetic helix inside */}
      <path d="M12 4v16" />
      <path d="M9 7c0 2 3 2 3 4s-3 2-3 4" />
      <path d="M15 9c0 2-3 2-3 4s3 2 3 4" />
    </svg>
  );
}

/**
 * Breeding Cross Icon
 * Two parent plants merging into offspring
 */
export function BreedingCrossIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Female parent */}
      <path d="M6 20V12c0-3 2-5 6-6" />
      <circle cx="6" cy="9" r="2" />
      {/* Male parent */}
      <path d="M18 20V12c0-3-2-5-6-6" />
      <circle cx="18" cy="9" r="2" />
      {/* Offspring */}
      <circle cx="12" cy="4" r="2" />
      <path d="M12 6v4" />
    </svg>
  );
}

/**
 * Field Plot Icon
 * Grid of experimental plots
 */
export function FieldPlotIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Plot grid */}
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      {/* Plants in plots */}
      <circle cx="6.5" cy="6.5" r="1.5" fill="currentColor" />
      <circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" />
      <circle cx="6.5" cy="17.5" r="1.5" fill="currentColor" />
      <circle cx="17.5" cy="17.5" r="1.5" fill="currentColor" />
    </svg>
  );
}

/**
 * Pedigree Tree Icon
 * Family tree structure for plant lineage
 */
export function PedigreeTreeIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Root/offspring */}
      <circle cx="12" cy="19" r="2" />
      {/* Parents */}
      <circle cx="6" cy="12" r="2" />
      <circle cx="18" cy="12" r="2" />
      {/* Grandparents */}
      <circle cx="3" cy="5" r="2" />
      <circle cx="9" cy="5" r="2" />
      <circle cx="15" cy="5" r="2" />
      <circle cx="21" cy="5" r="2" />
      {/* Connections */}
      <path d="M12 17v-3h-6v-2" />
      <path d="M12 14h6v-2" />
      <path d="M6 10v-3h-3v-2" />
      <path d="M6 7h3v-2" />
      <path d="M18 10v-3h-3v-2" />
      <path d="M18 7h3v-2" />
    </svg>
  );
}

/**
 * Seed Lot Icon
 * Bag of seeds with label
 */
export function SeedLotIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Bag shape */}
      <path d="M6 8h12l-1 12H7L6 8z" />
      <path d="M6 8c0-2 2-4 6-4s6 2 6 4" />
      {/* Tie */}
      <path d="M9 8v-1c0-1 1-2 3-2s3 1 3 2v1" />
      {/* Label */}
      <rect x="8" y="11" width="8" height="5" rx="0.5" />
      <path d="M10 13h4" />
      <path d="M10 15h2" />
    </svg>
  );
}

/**
 * Viability Test Icon
 * Germination test representation
 */
export function ViabilityTestIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Petri dish */}
      <ellipse cx="12" cy="14" rx="9" ry="4" />
      <path d="M3 14v2c0 2.2 4 4 9 4s9-1.8 9-4v-2" />
      {/* Germinating seeds */}
      <circle cx="8" cy="13" r="1" />
      <path d="M8 12v-2" />
      <circle cx="12" cy="14" r="1" />
      <path d="M12 13v-3" />
      <path d="M11 11l1-1 1 1" />
      <circle cx="16" cy="13" r="1" />
      <path d="M16 12v-1" />
    </svg>
  );
}

/**
 * Selection Index Icon
 * Multi-trait selection representation
 */
export function SelectionIndexIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Target rings */}
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" fill="currentColor" />
      {/* Selection arrows */}
      <path d="M12 3v3" />
      <path d="M12 18v3" />
      <path d="M3 12h3" />
      <path d="M18 12h3" />
      {/* Trait indicators */}
      <path d="M5.6 5.6l2.1 2.1" />
      <path d="M16.3 16.3l2.1 2.1" />
    </svg>
  );
}

/**
 * Harvest Icon
 * Wheat bundle being harvested
 */
export function HarvestIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Wheat stalks */}
      <path d="M8 21v-8" />
      <path d="M12 21v-10" />
      <path d="M16 21v-8" />
      {/* Wheat heads */}
      <ellipse cx="8" cy="10" rx="2" ry="3" />
      <ellipse cx="12" cy="8" rx="2" ry="3" />
      <ellipse cx="16" cy="10" rx="2" ry="3" />
      {/* Tie */}
      <path d="M6 18h12" />
    </svg>
  );
}

/**
 * Quality Gate Icon
 * Shield with checkmark for quality control
 */
export function QualityGateIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Shield */}
      <path d="M12 2l8 4v6c0 5.5-3.8 10.7-8 12-4.2-1.3-8-6.5-8-12V6l8-4z" />
      {/* Checkmark */}
      <path d="M9 12l2 2 4-4" />
      {/* Gate bars */}
      <path d="M8 18h8" />
    </svg>
  );
}

/**
 * Photoperiod Icon
 * Sun with clock for day length
 */
export function PhotoperiodIcon({ className, strokeWidth = 2 }: CustomIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('h-5 w-5', className)}
    >
      {/* Sun */}
      <circle cx="12" cy="12" r="4" />
      {/* Rays */}
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="M4.93 4.93l1.41 1.41" />
      <path d="M17.66 17.66l1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="M6.34 17.66l-1.41 1.41" />
      <path d="M19.07 4.93l-1.41 1.41" />
      {/* Clock hands */}
      <path d="M12 10v2l1.5 1.5" />
    </svg>
  );
}

// Export all custom icons
export const CustomIcons = {
  germplasm: GermplasmIcon,
  breedingCross: BreedingCrossIcon,
  fieldPlot: FieldPlotIcon,
  pedigreeTree: PedigreeTreeIcon,
  seedLot: SeedLotIcon,
  viabilityTest: ViabilityTestIcon,
  selectionIndex: SelectionIndexIcon,
  harvest: HarvestIcon,
  qualityGate: QualityGateIcon,
  photoperiod: PhotoperiodIcon,
} as const;

export type CustomIconName = keyof typeof CustomIcons;
