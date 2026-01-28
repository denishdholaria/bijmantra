/**
 * Breadcrumbs Component
 * 
 * Displays the current navigation path following the Navigation Gravity model:
 * Workspace > Division > Section > Page
 * 
 * Per Think-Tank §4.3: "Breadcrumbs display current position in gravity stack"
 * Per Think-Tank §7.1: "Time to Correct Orientation (TCO) < 3 seconds"
 * 
 * Features:
 * - Automatic path parsing from current route
 * - Workspace-aware context
 * - Clickable navigation links
 * - Responsive design (truncates on mobile)
 * - WCAG 2.1 AA compliant with aria-label
 * 
 * @see docs/gupt/think-tank/think-tank.md §4 Navigation Gravity Model
 */

import { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useActiveWorkspace } from '@/store/workspaceStore';
import { divisions } from '@/framework/registry/divisions';

// ============================================================================
// Types
// ============================================================================

interface BreadcrumbItem {
  label: string;
  path: string;
  isCurrentPage?: boolean;
}

interface BreadcrumbsProps {
  className?: string;
  showHome?: boolean;
  maxItems?: number;
}

// ============================================================================
// Route to Label Mapping
// ============================================================================

/**
 * Maps route segments to human-readable labels.
 * Falls back to title-casing the segment if not found.
 */
const routeLabels: Record<string, string> = {
  // Core routes
  'dashboard': 'Dashboard',
  'programs': 'Programs',
  'trials': 'Trials',
  'studies': 'Studies',
  'locations': 'Locations',
  'seasons': 'Seasons',
  'germplasm': 'Germplasm',
  'seedlots': 'Seed Lots',
  'crosses': 'Crosses',
  'traits': 'Traits',
  'observations': 'Observations',
  'samples': 'Samples',
  'settings': 'Settings',
  'profile': 'Profile',
  
  // Plant Sciences
  'plant-sciences': 'Plant Sciences',
  'breeding': 'Breeding',
  'genomics': 'Genomics',
  'phenotyping': 'Phenotyping',
  'genotyping': 'Genotyping',
  'selection': 'Selection',
  'crossing': 'Crossing',
  'field': 'Field Operations',
  'analysis': 'Analysis',
  
  // Seed Bank
  'seed-bank': 'Seed Bank',
  'vault': 'Vault Management',
  'accessions': 'Accessions',
  'conservation': 'Conservation',
  'viability': 'Viability Testing',
  'regeneration': 'Regeneration',
  'exchange': 'Exchange',
  'grin-search': 'GRIN Search',
  'mcpd': 'MCPD Exchange',
  'mta': 'MTA Management',
  'taxonomy': 'Taxonomy',
  'monitoring': 'Monitoring',
  
  // Seed Operations
  'seed-operations': 'Seed Operations',
  'quality-gate': 'Quality Gate',
  'batches': 'Batches',
  'stages': 'Stages',
  'lots': 'Seed Lots',
  'warehouse': 'Warehouse',
  'alerts': 'Alerts',
  'dispatch': 'Dispatch',
  'dispatch-history': 'Dispatch History',
  'firms': 'Firms',
  'track': 'Track Lot',
  'lineage': 'Lineage',
  'certificates': 'Certificates',
  'testing': 'Testing',
  'varieties': 'Varieties',
  'agreements': 'Agreements',
  
  // Commercial / DUS
  'commercial': 'Commercial',
  'dus-trials': 'DUS Trials',
  'dus-crops': 'DUS Crops',
  
  // Environment
  'earth-systems': 'Earth Systems',
  'weather': 'Weather',
  'climate': 'Climate',
  'gdd': 'Growing Degrees',
  'drought': 'Drought Monitor',
  'soil': 'Soil',
  'inputs': 'Inputs',
  'irrigation': 'Irrigation',
  'map': 'Field Map',
  
  // Sun-Earth Systems
  'sun-earth-systems': 'Solar Systems',
  'photoperiod': 'Photoperiod',
  'uv-index': 'UV Index',
  'solar-activity': 'Solar Activity',
  
  // Sensor Networks
  'sensor-networks': 'Sensor Networks',
  'devices': 'Devices',
  'live': 'Live Data',
  'telemetry': 'Telemetry',
  'aggregates': 'Aggregates',
  
  // Space Research
  'space-research': 'Space Research',
  'crops': 'Space Crops',
  'radiation': 'Radiation',
  'life-support': 'Life Support',
  
  // AI Vision
  'ai-vision': 'AI Vision',
  'datasets': 'Datasets',
  'training': 'Training',
  'registry': 'Model Registry',
  'annotate': 'Annotate',
  
  // Analytics & WASM
  'wasm-genomics': 'WASM Genomics',
  'wasm-gblup': 'WASM GBLUP',
  'wasm-popgen': 'WASM PopGen',
  'wasm-ld': 'WASM LD',
  'wasm-selection': 'WASM Selection',
  'analytics': 'Analytics',
  'visualization': 'Visualization',
  'statistics': 'Statistics',
  
  // Genomics & Analysis
  'genetic-diversity': 'Genetic Diversity',
  'population-genetics': 'Population Genetics',
  'linkage-disequilibrium': 'LD Analysis',
  'haplotype-analysis': 'Haplotype Analysis',
  'breeding-values': 'Breeding Values',
  'breeding-value-calculator': 'BLUP Calculator',
  'genomic-selection': 'Genomic Selection',
  'genetic-correlation': 'Genetic Correlation',
  'qtl-mapping': 'QTL Mapping',
  'marker-assisted-selection': 'MAS',
  'parentage-analysis': 'Parentage Analysis',
  'gxe-interaction': 'G×E Interaction',
  'stability-analysis': 'Stability Analysis',
  'trial-network': 'Trial Network',
  'molecular-breeding': 'Molecular Breeding',
  'phenomic-selection': 'Phenomic Selection',
  'speed-breeding': 'Speed Breeding',
  'doubled-haploid': 'Doubled Haploid',
  
  // Selection & Prediction
  'selectionindex': 'Selection Index',
  'selection-index-calculator': 'Index Calculator',
  'selection-decision': 'Selection Decision',
  'parent-selection': 'Parent Selection',
  'cross-prediction': 'Cross Prediction',
  'performance-ranking': 'Rankings',
  'geneticgain': 'Genetic Gain',
  'genetic-gain-tracker': 'Gain Tracker',
  'genetic-gain-calculator': 'Gain Calculator',
  
  // Field Operations
  'fieldlayout': 'Field Layout',
  'fieldbook': 'Field Book',
  'field-map': 'Field Map',
  'field-planning': 'Field Planning',
  'field-scanner': 'Field Scanner',
  'trialdesign': 'Trial Design',
  'trialplanning': 'Trial Planning',
  'season-planning': 'Season Planning',
  'resource-allocation': 'Resources',
  'resource-calendar': 'Calendar',
  'harvest': 'Harvest',
  'harvest-management': 'Harvest Management',
  'nursery': 'Nursery',
  
  // Knowledge
  'help': 'Help',
  'knowledge': 'Knowledge',
  'devguru': 'DevGuru',
  'glossary': 'Glossary',
  'about': 'About',
  'vision': 'Vision',
  
  // Admin
  'users': 'Users',
  'people': 'People',
  'team-management': 'Team Management',
  'collaboration': 'Collaboration',
  'integrations': 'Integrations',
  'serverinfo': 'API Explorer',
  'system-health': 'System Health',
  'auditlog': 'Audit Log',
  'security': 'Security',
  'workflows': 'Workflows',
  'offline': 'Offline Mode',
  'backup': 'Backup',
  'data-sync': 'Data Sync',
  'data-validation': 'Data Validation',
  'import-export': 'Import/Export',
  'batch-operations': 'Batch Operations',
  'reports': 'Reports',
  'advanced-reports': 'Advanced Reports',
  'calculator': 'Calculator',
  'dev-progress': 'Dev Progress',
  'data-dictionary': 'Data Dictionary',
  'system-settings': 'System Settings',
  
  // Misc
  'pedigree': 'Pedigree',
  'pedigree-3d': '3D Pedigree',
  'crossingprojects': 'Crossing Projects',
  'plannedcrosses': 'Planned Crosses',
  'crossingplanner': 'Crossing Planner',
  'progeny': 'Progeny',
  'germplasm-comparison': 'Compare Germplasm',
  'germplasm-search': 'Germplasm Search',
  'germplasm-passport': 'Germplasm Passport',
  'germplasmattributes': 'Germplasm Attributes',
  'attributevalues': 'Attribute Values',
  'collections': 'Collections',
  'pipeline': 'Pipeline',
  'observationunits': 'Observation Units',
  'events': 'Events',
  'images': 'Images',
  'dataquality': 'Data Quality',
  'ontologies': 'Ontologies',
  'variants': 'Variants',
  'variantsets': 'Variant Sets',
  'calls': 'Calls',
  'callsets': 'Call Sets',
  'plates': 'Plates',
  'allelematrix': 'Allele Matrix',
  'genomemaps': 'Genome Maps',
  'markerpositions': 'Marker Positions',
  'references': 'References',
  'vendororders': 'Vendor Orders',
  'plant-vision': 'Plant Vision',
  'disease-atlas': 'Disease Atlas',
  'crop-health': 'Crop Health',
  'yield-predictor': 'Yield Predictor',
  'yieldmap': 'Yield Map',
  'disease-resistance': 'Disease Resistance',
  'abiotic-stress': 'Abiotic Stress',
  'bioinformatics': 'Bioinformatics',
  'crop-calendar': 'Crop Calendar',
  'spatial-analysis': 'Spatial Analysis',
  'pedigree-analysis': 'Pedigree Analysis',
  'phenotype-analysis': 'Phenotype Analysis',
  'trial-comparison': 'Trial Comparison',
  'trial-summary': 'Trial Summary',
  'breeding-simulator': 'Breeding Simulator',
  'variety-release': 'Variety Release',
  'varietycomparison': 'Variety Comparison',
  'quick-entry': 'Quick Entry',
  'labels': 'Labels',
  'scanner': 'Scanner',
  'barcode': 'Barcode Scanner',
  'ai-assistant': 'AI Assistant',
  'ai-settings': 'AI Settings',
  'notifications': 'Notifications',
  'activity': 'Activity',
  'search': 'Search',
  'insights': 'Insights',
  'apex-analytics': 'Analytics',
  'veena': 'Veena Chat',
  
  // Future modules
  'future': 'Coming Soon',
  'crop-intelligence': 'Crop Intelligence',
  'soil-nutrients': 'Soil & Nutrients',
  'crop-protection': 'Crop Protection',
  'water-irrigation': 'Water & Irrigation',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Converts a route segment to a human-readable label.
 */
function getLabel(segment: string): string {
  // Check direct mapping
  if (routeLabels[segment]) {
    return routeLabels[segment];
  }
  
  // Check if it's a dynamic segment (e.g., :id, UUID)
  if (segment.startsWith(':') || /^[0-9a-f-]{36}$/i.test(segment) || /^\d+$/.test(segment)) {
    return 'Detail';
  }
  
  // Title case the segment
  return segment
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Finds the division that contains the given route.
 */
function findDivisionForRoute(pathname: string): { division: string; section?: string } | null {
  for (const division of divisions) {
    if (pathname.startsWith(division.route)) {
      // Check sections
      if (division.sections) {
        for (const section of division.sections) {
          const sectionRoute = section.isAbsolute ? section.route : `${division.route}${section.route}`;
          if (pathname.startsWith(sectionRoute)) {
            return { division: division.name, section: section.name };
          }
          // Check items within section
          if (section.items) {
            for (const item of section.items) {
              const itemRoute = item.isAbsolute ? item.route : `${division.route}${item.route}`;
              if (pathname === itemRoute || pathname.startsWith(itemRoute + '/')) {
                return { division: division.name, section: section.name };
              }
            }
          }
        }
      }
      return { division: division.name };
    }
  }
  return null;
}

// ============================================================================
// Component
// ============================================================================

export function Breadcrumbs({ className, showHome = true, maxItems = 4 }: BreadcrumbsProps) {
  const location = useLocation();
  const activeWorkspace = useActiveWorkspace();
  
  const breadcrumbs = useMemo<BreadcrumbItem[]>(() => {
    const items: BreadcrumbItem[] = [];
    const pathname = location.pathname;
    
    // Skip breadcrumbs for root paths
    if (pathname === '/' || pathname === '/dashboard') {
      return [];
    }
    
    // Add workspace if active
    if (activeWorkspace && showHome) {
      items.push({
        label: activeWorkspace.name,
        path: activeWorkspace.landingRoute,
      });
    } else if (showHome) {
      items.push({
        label: 'Home',
        path: '/dashboard',
      });
    }
    
    // Parse path segments
    const segments = pathname.split('/').filter(Boolean);
    let currentPath = '';
    
    // Find division context
    const divisionContext = findDivisionForRoute(pathname);
    
    // Build breadcrumb trail
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      currentPath += `/${segment}`;
      
      // Skip if this is the workspace landing route we already added
      if (activeWorkspace && currentPath === activeWorkspace.landingRoute) {
        continue;
      }
      
      const label = getLabel(segment);
      const isLast = i === segments.length - 1;
      
      // Skip "new" segments in the middle
      if (segment === 'new' && !isLast) {
        continue;
      }
      
      items.push({
        label,
        path: currentPath,
        isCurrentPage: isLast,
      });
    }
    
    // Truncate if too many items
    if (items.length > maxItems) {
      const first = items[0];
      const last = items.slice(-2);
      return [
        first,
        { label: '...', path: '', isCurrentPage: false },
        ...last,
      ];
    }
    
    return items;
  }, [location.pathname, activeWorkspace, showHome, maxItems]);
  
  // Don't render if no breadcrumbs
  if (breadcrumbs.length === 0) {
    return null;
  }
  
  return (
    <nav 
      aria-label="Breadcrumb navigation"
      className={cn(
        'flex items-center text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400',
        className
      )}
    >
      <ol className="flex items-center flex-wrap gap-1">
        {breadcrumbs.map((item, index) => (
          <li key={item.path || index} className="flex items-center">
            {index > 0 && (
              <ChevronRight 
                className="w-4 h-4 mx-1 text-prakruti-dhool-400 dark:text-prakruti-dhool-500 flex-shrink-0" 
                aria-hidden="true"
              />
            )}
            {item.label === '...' ? (
              <span className="px-1 text-prakruti-dhool-400">...</span>
            ) : item.isCurrentPage ? (
              <span 
                className="font-medium text-prakruti-dhool-700 dark:text-prakruti-dhool-200 truncate max-w-[150px] sm:max-w-[200px]"
                aria-current="page"
              >
                {item.label}
              </span>
            ) : (
              <Link
                to={item.path}
                className={cn(
                  'hover:text-prakruti-patta dark:hover:text-prakruti-patta-light transition-colors',
                  'truncate max-w-[100px] sm:max-w-[150px]',
                  index === 0 && 'flex items-center gap-1'
                )}
              >
                {index === 0 && showHome && !activeWorkspace && (
                  <Home className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                )}
                <span>{item.label}</span>
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default Breadcrumbs;
