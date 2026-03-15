import { 
  Wheat, 
  Factory, 
  Microscope, 
  Building2, 
  Settings,
  CloudSun,
  Droplets,
  Mountain,
  Leaf,
} from 'lucide-react';
import type { WorkspaceId } from '@/types/workspace';

// Icon mapping for workspaces
export const WORKSPACE_ICONS: Record<WorkspaceId, React.ElementType> = {
  breeding: Wheat,
  'seed-ops': Factory,
  research: Microscope,
  genebank: Building2,
  admin: Settings,
  atmosphere: CloudSun,
  hydrology: Droplets,
  lithosphere: Mountain,
  biosphere: Leaf,
};

// Gradient backgrounds for hero cards - Prakruti Design System
export const WORKSPACE_GRADIENTS: Record<WorkspaceId, string> = {
  breeding: 'from-prakruti-patta via-prakruti-patta-light to-emerald-600',      // Leaf green
  'seed-ops': 'from-prakruti-neela via-prakruti-neela-light to-blue-600',       // Sky blue
  research: 'from-purple-600 via-fuchsia-500 to-pink-500',                       // Innovation purple
  genebank: 'from-prakruti-sona via-prakruti-sona-light to-amber-500',          // Gold harvest
  admin: 'from-prakruti-mitti via-prakruti-mitti-light to-prakruti-dhool-600',  // Earth tones
  atmosphere: 'from-sky-400 via-sky-500 to-blue-600',
  hydrology: 'from-blue-400 via-cyan-500 to-teal-600',
  lithosphere: 'from-amber-600 via-orange-600 to-red-700',
  biosphere: 'from-emerald-500 via-green-600 to-teal-700',
};

// Accent colors for pills - Prakruti Design System
export const WORKSPACE_PILL_COLORS: Record<WorkspaceId, string> = {
  breeding: 'bg-prakruti-patta-pale text-prakruti-patta dark:bg-prakruti-patta/20 dark:text-prakruti-patta-light hover:bg-prakruti-patta-100 dark:hover:bg-prakruti-patta/30',
  'seed-ops': 'bg-prakruti-neela-pale text-prakruti-neela dark:bg-prakruti-neela/20 dark:text-prakruti-neela-light hover:bg-prakruti-neela-100 dark:hover:bg-prakruti-neela/30',
  research: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/60',
  genebank: 'bg-prakruti-sona-pale text-prakruti-sona-dark dark:bg-prakruti-sona/20 dark:text-prakruti-sona-light hover:bg-prakruti-sona-100 dark:hover:bg-prakruti-sona/30',
  admin: 'bg-prakruti-mitti-50 text-prakruti-mitti-dark dark:bg-prakruti-mitti/20 dark:text-prakruti-mitti-light hover:bg-prakruti-mitti-100 dark:hover:bg-prakruti-mitti/30',
  atmosphere: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300 hover:bg-sky-200 dark:hover:bg-sky-900/60',
  hydrology: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300 hover:bg-cyan-200 dark:hover:bg-cyan-900/60',
  lithosphere: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/60',
  biosphere: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 hover:bg-emerald-200 dark:hover:bg-emerald-900/60',
};

// Ring colors for active pills - Prakruti Design System
export const WORKSPACE_RING_COLORS: Record<WorkspaceId, string> = {
  breeding: 'ring-prakruti-patta',
  'seed-ops': 'ring-prakruti-neela',
  research: 'ring-purple-500',
  genebank: 'ring-prakruti-sona',
  admin: 'ring-prakruti-mitti',
  atmosphere: 'ring-sky-500',
  hydrology: 'ring-cyan-500',
  lithosphere: 'ring-amber-600',
  biosphere: 'ring-emerald-500',
};

// Decorative emojis for each workspace
export const WORKSPACE_EMOJIS: Record<WorkspaceId, string> = {
  breeding: '🌾',
  'seed-ops': '📦',
  research: '🔬',
  genebank: '🏛️',
  admin: '⚙️',
  atmosphere: '🌤️',
  hydrology: '💧',
  lithosphere: '🏔️',
  biosphere: '🌿',
};

// Feature highlights for each workspace
export const WORKSPACE_FEATURES: Record<WorkspaceId, string[]> = {
  breeding: ['BrAPI v2.1 Compliant', 'Genomic Selection', 'Cross Prediction', 'Pedigree Tracking'],
  'seed-ops': ['Quality Testing', 'Inventory Management', 'Dispatch Logistics', 'DUS Testing'],
  research: ['AI Plant Vision', 'WASM Analytics', 'Space Agriculture', 'Advanced Tools'],
  genebank: ['Vault Management', 'Conservation', 'Germplasm Exchange', 'Environmental Monitoring'],
  admin: ['User Management', 'System Health', 'Integrations', 'Audit Logs'],
  atmosphere: ['Weather Forecasting', 'Climate Risk', 'Air Quality', 'GDD Tracking'],
  hydrology: ['Irrigation Planning', 'Water Balance', 'Drought Monitoring', 'Reservoirs'],
  lithosphere: ['Soil Health', 'Nutrient Mapping', 'Topography', 'Land Use'],
  biosphere: ['Biodiversity', 'Carbon Sequestration', 'Pest Monitoring', 'Ecology'],
};
