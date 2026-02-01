/**
 * Workspace Templates
 * 
 * Predefined templates for quick custom workspace creation.
 * Users can start from these templates and customize them.
 */

import type { WorkspaceTemplate } from '@/types/customWorkspace';

/**
 * 10 predefined templates for common workflows
 */
export const workspaceTemplates: WorkspaceTemplate[] = [
  {
    id: 'template-field-day',
    name: 'Field Day',
    description: 'Essential pages for field data collection',
    icon: 'Sprout',
    color: 'green',
    pageIds: [
      'observations',
      'field-book',
      'quick-entry',
      'harvest',
      'weather',
      'soil',
      'scanner',
      'labels',
    ],
    targetRole: 'Field Technician',
    category: 'breeding',
  },
  {
    id: 'template-breeders-desk',
    name: "Breeder's Desk",
    description: 'Core breeding program management tools',
    icon: 'Wheat',
    color: 'green',
    pageIds: [
      'programs',
      'trials',
      'crosses',
      'crossing-planner',
      'selection-decision',
      'parent-selection',
      'pipeline',
      'pedigree',
      'genetic-gain-tracker',
      'performance-ranking',
      'germplasm-comparison',
      'progeny',
    ],
    targetRole: 'Plant Breeder',
    category: 'breeding',
  },
  {
    id: 'template-lab-analyst',
    name: 'Lab Analyst',
    description: 'Genotyping and lab analysis tools',
    icon: 'FlaskConical',
    color: 'blue',
    pageIds: [
      'samples',
      'plates',
      'calls',
      'variants',
      'call-sets',
      'quality-gate',
      'data-quality',
    ],
    targetRole: 'Lab Technician',
    category: 'breeding',
  },
  {
    id: 'template-seed-manager',
    name: 'Seed Manager',
    description: 'Seed inventory and dispatch management',
    icon: 'Package',
    color: 'blue',
    pageIds: [
      'seed-inventory',
      'seed-lots-inv',
      'warehouse',
      'create-dispatch',
      'dispatch-history',
      'certificates',
      'stock-alerts',
      'track-lot',
      'barcode',
      'firms',
    ],
    targetRole: 'Seed Company',
    category: 'seed-ops',
  },
  {
    id: 'template-genebank-curator',
    name: 'Genebank Curator',
    description: 'Germplasm conservation and exchange',
    icon: 'Building2',
    color: 'amber',
    pageIds: [
      'seed-bank-dashboard',
      'accessions',
      'vault-management',
      'vault-monitoring',
      'viability',
      'regeneration',
      'exchange',
      'mta',
      'conservation',
    ],
    targetRole: 'Conservation Officer',
    category: 'genebank',
  },
  {
    id: 'template-data-scientist',
    name: 'Data Scientist',
    description: 'Analytics and computational tools',
    icon: 'LineChart',
    color: 'purple',
    pageIds: [
      'analytics',
      'wasm-genomics',
      'wasm-gblup',
      'wasm-popgen',
      'statistics',
      'visualization',
      'yield-predictor',
      'breeding-simulator',
      'spatial-analysis',
      'apex-analytics',
      'experiment-designer',
    ],
    targetRole: 'Data Analyst',
    category: 'research',
  },
  {
    id: 'template-weekly-reports',
    name: 'Weekly Reports',
    description: 'Reporting and activity tracking',
    icon: 'FileText',
    color: 'slate',
    pageIds: [
      'dashboard',
      'reports',
      'advanced-reports',
      'activity',
      'apex-analytics',
    ],
    targetRole: 'Manager',
    category: 'admin',
  },
  {
    id: 'template-genomics-focus',
    name: 'Genomics Focus',
    description: 'Advanced genomic analysis tools',
    icon: 'Dna',
    color: 'purple',
    pageIds: [
      'variants',
      'variant-sets',
      'calls',
      'call-sets',
      'allele-matrix',
      'genome-maps',
      'marker-positions',
      'qtl-mapping',
      'genomic-selection',
      'ld-analysis',
      'haplotype-analysis',
      'population-genetics',
      'genetic-diversity',
      'molecular-breeding',
    ],
    targetRole: 'Geneticist',
    category: 'breeding',
  },
  {
    id: 'template-trial-manager',
    name: 'Trial Manager',
    description: 'Trial planning and coordination',
    icon: 'ClipboardList',
    color: 'green',
    pageIds: [
      'trials',
      'studies',
      'locations',
      'field-map',
      'trial-design',
      'trial-planning',
      'season-planning',
      'resource-allocation',
      'resource-calendar',
      'field-layout',
    ],
    targetRole: 'Trial Coordinator',
    category: 'breeding',
  },
  {
    id: 'template-quick-access',
    name: 'Quick Access',
    description: 'Essential navigation shortcuts',
    icon: 'Zap',
    color: 'slate',
    pageIds: [
      'dashboard',
      'search',
      'notifications',
      'help',
      'settings-page',
      'activity',
    ],
    targetRole: 'Any User',
    category: 'admin',
  },
];

/**
 * Get a template by ID
 */
export function getTemplate(id: string): WorkspaceTemplate | undefined {
  return workspaceTemplates.find(t => t.id === id);
}

/**
 * Get templates by category
 */
export function getTemplatesByCategory(category: WorkspaceTemplate['category']): WorkspaceTemplate[] {
  return workspaceTemplates.filter(t => t.category === category);
}
