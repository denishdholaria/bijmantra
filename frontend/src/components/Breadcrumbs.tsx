/**
 * Breadcrumbs Component
 * 
 * Dynamic breadcrumb navigation based on current route.
 * Supports custom labels, icons, and workspace context.
 */

import { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home, Wheat, Factory, Microscope, Building2, Settings,
  CloudRain,
  Droplets,
  Mountain,
  Leaf,
} from "lucide-react";
import { cn } from '@/lib/utils';
import { useActiveWorkspace } from '@/store/workspaceStore';
import type { WorkspaceId } from '@/types/workspace';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
  showHome?: boolean;
  showWorkspace?: boolean;
  separator?: React.ReactNode;
}

// Workspace icons
const workspaceIcons: Record<WorkspaceId, React.ReactNode> = {
  breeding: <Wheat className="h-4 w-4" />,
  'seed-ops': <Factory className="h-4 w-4" />,
  research: <Microscope className="h-4 w-4" />,
  genebank: <Building2 className="h-4 w-4" />,
  admin: <Settings className="h-4 w-4" />,
  atmosphere: <CloudRain className="h-4 w-4" />,
  hydrology: <Droplets className="h-4 w-4" />,
  lithosphere: <Mountain className="h-4 w-4" />,
  biosphere: <Leaf className="h-4 w-4" />,
};

// Route to label mapping
const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  programs: 'Programs',
  trials: 'Trials',
  studies: 'Studies',
  locations: 'Locations',
  germplasm: 'Germplasm',
  seedlots: 'Seed Lots',
  crosses: 'Crosses',
  traits: 'Traits',
  observations: 'Observations',
  samples: 'Samples',
  variants: 'Variants',
  people: 'People',
  lists: 'Lists',
  settings: 'Settings',
  profile: 'Profile',
  help: 'Help',
  about: 'About',
  vision: 'Vision',
  'dev-progress': 'Dev Progress',
  'server-info': 'Server Info',
  'system-settings': 'System Settings',
  // Divisions
  'seed-bank': 'Seed Bank',
  'seed-operations': 'Seed Operations',
  'earth-systems': 'Earth Systems',
  'sun-earth-systems': 'Sun-Earth Systems',
  'sensor-networks': 'Sensor Networks',
  'space-research': 'Space Research',
  commercial: 'Commercial',
  knowledge: 'Knowledge',
  integrations: 'Integrations',
  // Sub-pages
  new: 'New',
  edit: 'Edit',
  detail: 'Details',
  accessions: 'Accessions',
  vaults: 'Vaults',
  conservation: 'Conservation',
  viability: 'Viability Testing',
  regeneration: 'Regeneration',
  exchange: 'Exchange',
  'quality-gate': 'Quality Gate',
  'lab-samples': 'Lab Samples',
  'lab-testing': 'Lab Testing',
  certificates: 'Certificates',
  warehouse: 'Warehouse',
  dispatch: 'Dispatch',
  traceability: 'Traceability',
  weather: 'Weather',
  'soil-data': 'Soil Data',
  'input-log': 'Input Log',
  irrigation: 'Irrigation',
  'solar-activity': 'Solar Activity',
  photoperiod: 'Photoperiod',
  'uv-index': 'UV Index',
  devices: 'Devices',
  'live-data': 'Live Data',
  alerts: 'Alerts',
  crops: 'Space Crops',
  radiation: 'Radiation',
  'life-support': 'Life Support',
  'dus-trials': 'DUS Trials',
  'dus-crops': 'DUS Crops',
  varieties: 'Varieties',
  agreements: 'Agreements',
  training: 'Training Hub',
  forums: 'Forums',
  glossary: 'Glossary',
  faq: 'FAQ',
};

export function Breadcrumbs({ 
  items, 
  className, 
  showHome = true,
  showWorkspace = true,
  separator = <ChevronRight className="h-4 w-4 text-muted-foreground" />
}: BreadcrumbsProps) {
  const location = useLocation();
  const activeWorkspace = useActiveWorkspace();

  // Generate breadcrumbs from current path if items not provided
  const breadcrumbs = useMemo(() => {
    if (items) return items;

    const pathSegments = location.pathname.split('/').filter(Boolean);
    const crumbs: BreadcrumbItem[] = [];

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      
      // Check if this is an ID (UUID or numeric)
      const isId = /^[0-9a-f-]{36}$|^\d+$/.test(segment);
      
      if (isId) {
        // For IDs, use "Details" as label
        crumbs.push({
          label: 'Details',
          href: index < pathSegments.length - 1 ? currentPath : undefined,
        });
      } else {
        crumbs.push({
          label: ROUTE_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
          href: index < pathSegments.length - 1 ? currentPath : undefined,
        });
      }
    });

    return crumbs;
  }, [items, location.pathname]);

  if (breadcrumbs.length === 0 && !activeWorkspace) return null;

  return (
    <nav 
      aria-label="Breadcrumb" 
      className={cn('flex items-center text-sm', className)}
    >
      <ol className="flex items-center gap-1">
        {showHome && (
          <>
            <li>
              <Link 
                to="/dashboard" 
                className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <Home className="h-4 w-4" />
                <span className="sr-only">Home</span>
              </Link>
            </li>
            {(breadcrumbs.length > 0 || activeWorkspace) && (
              <li className="flex items-center">{separator}</li>
            )}
          </>
        )}
        
        {/* Workspace breadcrumb */}
        {showWorkspace && activeWorkspace && (
          <>
            <li>
              <Link
                to={activeWorkspace.landingRoute}
                className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
              >
                {workspaceIcons[activeWorkspace.id]}
                <span className="hidden sm:inline">{activeWorkspace.name}</span>
              </Link>
            </li>
            {breadcrumbs.length > 0 && (
              <li className="flex items-center">{separator}</li>
            )}
          </>
        )}
        
        {breadcrumbs.map((crumb, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && <span className="mx-1">{separator}</span>}
            {crumb.href ? (
              <Link
                to={crumb.href}
                className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
              >
                {crumb.icon}
                <span>{crumb.label}</span>
              </Link>
            ) : (
              <span className="flex items-center gap-1 font-medium text-foreground">
                {crumb.icon}
                <span>{crumb.label}</span>
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

// Compact breadcrumb for mobile
export function BreadcrumbsCompact({ className }: { className?: string }) {
  const location = useLocation();
  
  const pathSegments = location.pathname.split('/').filter(Boolean);
  
  if (pathSegments.length <= 1) return null;

  const parentPath = '/' + pathSegments.slice(0, -1).join('/');
  const parentLabel = ROUTE_LABELS[pathSegments[pathSegments.length - 2]] || 
    pathSegments[pathSegments.length - 2];

  return (
    <Link 
      to={parentPath}
      className={cn(
        'flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors',
        className
      )}
    >
      <ChevronRight className="h-4 w-4 rotate-180" />
      <span>{parentLabel}</span>
    </Link>
  );
}

// Hook for getting current breadcrumb path
export function useBreadcrumbs() {
  const location = useLocation();

  return useMemo(() => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const crumbs: { label: string; path: string }[] = [];

    let currentPath = '';
    pathSegments.forEach((segment) => {
      currentPath += `/${segment}`;
      const isId = /^[0-9a-f-]{36}$|^\d+$/.test(segment);
      
      crumbs.push({
        label: isId ? 'Details' : (ROUTE_LABELS[segment] || segment),
        path: currentPath,
      });
    });

    return crumbs;
  }, [location.pathname]);
}
