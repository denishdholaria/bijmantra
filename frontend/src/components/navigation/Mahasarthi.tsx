/**
 * Mahasarthi Navigation System
 * 
 * "The Great Charioteer" - Complete navigation system for BijMantra.
 * Like Krishna guided Arjuna through Kurukshetra, Mahasarthi guides users through BijMantra.
 * 
 * Components:
 * - MahasarthiDock: Personal pinned pages (icon-only vertical dock on desktop, bottom tabs on mobile)
 * - MahasarthiBrowser: Full domain mega-panel browser (side panel on desktop, full screen on mobile)
 * - MahasarthiSearch: Enhanced command palette / spotlight search
 * 
 * Responsive Behavior:
 * - Desktop Collapsed: Vertical icon dock in sidebar
 * - Desktop Expanded: Full navigation with labels, search, pinned items, and divisions
 * - Mobile (<lg): Bottom tab bar, browser as full-screen overlay
 * 
 * @see docs/gupt/1-MAHASARTHI.md for full specification (section 8.5)
 */


import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { MahasarthiDock } from './MahasarthiDock';
import { MahasarthiStrata } from './MahasarthiStrata';
import { MahasarthiSearch } from './MahasarthiSearch';
import { MahasarthiGateway } from './MahasarthiGateway';
import { useDockStore } from '@/store/dockStore';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { useDivisionRegistry } from '@/framework/registry';
import { useActiveWorkspace, useWorkspaceStore } from '@/store/workspaceStore';
import { getWorkspaceModules, isRouteInWorkspace } from '@/framework/registry/workspaces';
import { GATEWAYS, GatewayId, getGatewayForRoute } from '@/config/MahasarthiConfig';
import { cn } from '@/lib/utils';
import {
  Search, Pin, ChevronRight, Grid3X3,
  LayoutDashboard, Wheat, FlaskConical, Sprout, GitMerge, BarChart3,
  Dna, Settings, TestTube2, Shield, Package, Truck, FileCheck, FileText,
  Building2, RefreshCw, Globe, Target, Cpu, Rocket, BookOpen, Eye,
  type LucideIcon,
} from 'lucide-react';

// ============================================================================
// Icon Mapping (shared with MahasarthiDock)
// ============================================================================

const iconMap: Record<string, LucideIcon> = {
  LayoutDashboard,
  Wheat,
  FlaskConical,
  Sprout,
  GitMerge,
  BarChart3,
  Dna,
  Settings,
  TestTube2,
  Shield,
  Package,
  Truck,
  FileCheck,
  FileText,
  Building2,
  RefreshCw,
  Globe,
  Target,
  Cpu,
  Rocket,
  BookOpen,
  Eye,
};

function getIcon(iconName: string): LucideIcon {
  return iconMap[iconName] || LayoutDashboard;
}

// ============================================================================
// Types
// ============================================================================

interface MahasarthiProps {
  collapsed?: boolean;
  onNavigate?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export function Mahasarthi({ collapsed = false, onNavigate }: MahasarthiProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { pinnedItems, recentItems, recordVisit } = useDockStore();
  const { navigableDivisions } = useDivisionRegistry();
  const activeWorkspace = useActiveWorkspace();
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId);

  // Gateway State
  const [activeGateway, setActiveGateway] = useState<GatewayId>('srijan');

  // Sync active gateway with route
  useEffect(() => {
    const gateway = getGatewayForRoute(location.pathname);
    if (gateway) {
      setActiveGateway(gateway);
    }
  }, [location.pathname]);

  const handleGatewaySelect = (id: GatewayId) => {
    setActiveGateway(id);
    navigate(GATEWAYS[id].landingRoute);
  };

  // Filter divisions by Active Gateway Workspaces
  const filteredDivisions = useMemo(() => {
    const gatewayWorkspaces = GATEWAYS[activeGateway].workspaces;
    
    return navigableDivisions.filter(division => {
      // Logic: A division belongs to the gateway if its route matches one of the gateway's workspaces
      // This might need refinement based on how `navigableDivisions` maps to workspaces
      // For now, simple string inclusion check on the route or division ID
      const divisionId = division.id;
      // You might need a more robust mapping here, but assuming division.id ~ workspaceId helps
      // Or check if division route starts with workspace route
      
      // Fallback: If no explicit mapping, show 'breeding' stuff in 'srijan' etc.
      if (activeGateway === 'srijan' && (divisionId === 'breeding' || divisionId === 'genomics' || divisionId === 'plant-sciences')) return true;
      if (activeGateway === 'sampada' && (divisionId === 'seed-bank' || divisionId === 'seed-operations' || divisionId === 'commercial')) return true;
      if (activeGateway === 'prakriti' && (divisionId === 'earth-systems' || divisionId === 'sun-earth-systems' || divisionId === 'space-research')) return true;
      if (activeGateway === 'drishti' && (divisionId === 'sensor-networks' || divisionId === 'knowledge' || divisionId === 'integrations')) return true;
      
      return false;
    });
  }, [navigableDivisions, activeGateway]);

  // Filter pinned items by Gateway Context
  const gatewayPinnedItems = useMemo(() => {
     // Show items if their path belongs to the current gateway
     return pinnedItems.filter(item => getGatewayForRoute(item.path) === activeGateway);
  }, [pinnedItems, activeGateway]);

  // Detect mobile viewport (< lg breakpoint = 1024px)
  const isMobile = useMediaQuery('(max-width: 1023px)');
  
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Record page visits for recent tracking
  useEffect(() => {
    const path = location.pathname;
    if (path === '/login' || path === '/') return;
    
    // Find the nav item for this path to get label and icon
    const pathParts = path.split('/').filter(Boolean);
    const label = pathParts[pathParts.length - 1]
      ?.split('-')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ') || 'Page';
    
    recordVisit({
      id: path.replace(/\//g, '-'),
      path,
      label,
      icon: 'LayoutDashboard',
    });
  }, [location.pathname, recordVisit]);

  // Global keyboard shortcut for search and browser
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle shortcuts if user is typing in an input
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // ⌘K or Ctrl+K to open search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        e.stopPropagation();
        requestAnimationFrame(() => {
          setIsBrowserOpen(false);
          setIsSearchOpen(prev => !prev);
        });
        return;
      }
      
      // ⌘\ or Ctrl+\ to open browser (Mahasarthi Browser shortcut)
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        e.stopPropagation();
        requestAnimationFrame(() => {
          setIsSearchOpen(false);
          setIsBrowserOpen(prev => !prev);
        });
        return;
      }
      
      // Escape to close
      if (e.key === 'Escape') {
        e.preventDefault();
        requestAnimationFrame(() => {
          setIsSearchOpen(false);
          setIsBrowserOpen(false);
        });
      }
    };

    document.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => document.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, []);

  // Handlers
  const handleBrowserOpen = useCallback(() => {
    setIsBrowserOpen(true);
    setIsSearchOpen(false);
  }, []);

  const handleBrowserClose = useCallback(() => {
    setIsBrowserOpen(false);
  }, []);

  const handleSearchOpen = useCallback(() => {
    setIsSearchOpen(true);
    setIsBrowserOpen(false);
  }, []);

  const handleSearchClose = useCallback(() => {
    setIsSearchOpen(false);
  }, []);

  const handleNavigate = useCallback(() => {
    setIsBrowserOpen(false);
    setIsSearchOpen(false);
    onNavigate?.();
  }, [onNavigate]);

  // Collapsed view - show Gateway Switcher + icon dock
  if (collapsed) {
    return (
      <>
        {/* Gateway Switcher at top */}
        {!isMobile && (
          <MahasarthiGateway 
            activeGateway={activeGateway} 
            onSelectGateway={handleGatewaySelect} 
            collapsed={true} 
          />
        )}

        {/* Desktop: Vertical dock in sidebar */}
        {!isMobile && (
          <MahasarthiDock
            onBrowserOpen={handleBrowserOpen}
            onSearchOpen={handleSearchOpen}
            onNavigate={handleNavigate}
            isMobile={false}
          />
        )}
        
        {/* Mobile: Bottom tab bar (rendered outside sidebar) */}
        {isMobile && (
          <MahasarthiDock
            onBrowserOpen={handleBrowserOpen}
            onSearchOpen={handleSearchOpen}
            onNavigate={handleNavigate}
            isMobile={true}
          />
        )}
        
        <MahasarthiStrata
          isOpen={isBrowserOpen}
          onClose={handleBrowserClose}
          onNavigate={handleNavigate}
          isMobile={isMobile}
        />
        
        <MahasarthiSearch
          isOpen={isSearchOpen}
          onClose={handleSearchClose}
          onNavigate={handleNavigate}
        />
      </>
    );
  }

  // Expanded view - full navigation with labels
  return (
    <>
      <div className="flex flex-col h-full">
        {/* Gateway Switcher */}
        <MahasarthiGateway 
          activeGateway={activeGateway} 
          onSelectGateway={handleGatewaySelect} 
          collapsed={false} 
        />

        {/* Search Bar */}
        <div className="p-3 border-b border-white/10">
          <button
            onClick={handleSearchOpen}
            className={cn(
              'w-full flex items-center gap-2 px-3 py-2 text-sm',
              'bg-white/5 text-slate-300 placeholder-slate-400',
              'rounded-lg border border-white/10',
              'hover:bg-white/10 hover:text-white transition-colors'
            )}
          >
            <Search className="w-4 h-4" />
            <span>Search {GATEWAYS[activeGateway].label}...</span>
            <kbd className="ml-auto text-[10px] bg-white/10 px-1.5 py-0.5 rounded">⌘K</kbd>
          </button>
        </div>

        {/* Pinned Items (Context-sensitive) */}
        {gatewayPinnedItems.length > 0 && (
          <div className="p-3 border-b border-white/10">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Pin className="w-3 h-3" /> Pinned
            </div>
            <div className="space-y-0.5">
              {gatewayPinnedItems.map(item => {
                const IconComponent = getIcon(item.icon);
                const isActive = location.pathname === item.path || 
                                location.pathname.startsWith(item.path + '/');
                return (
                  <Link
                    key={item.id}
                    to={item.path}
                    onClick={onNavigate}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors',
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'text-slate-200 hover:bg-white/5 hover:text-white'
                    )}
                  >
                    <IconComponent className="w-4 h-4 flex-shrink-0" strokeWidth={1.75} />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* Divisions Quick Access from Registry (Filtered by Gateway) */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Workspaces
          </div>
          <div className="space-y-0.5">
            {filteredDivisions.length > 0 ? (
              filteredDivisions.map(division => {
                const isActive = location.pathname.startsWith(division.route);
                const IconComponent = getIcon(division.icon);
                return (
                  <Link
                    key={division.id}
                    to={division.route}
                    onClick={onNavigate}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors',
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'text-slate-200 hover:bg-white/5 hover:text-white'
                    )}
                  >
                    <IconComponent className="w-4 h-4 flex-shrink-0" strokeWidth={1.75} />
                    <span className="truncate">{division.name}</span>
                  </Link>
                );
              })
            ) : (
               <div className="px-2 py-4 text-xs text-slate-500 text-center italic">
                 No workspaces available
               </div>
            )}
          </div>
        </div>

        {/* STRATA Button - with safe area padding for mobile */}
        <div className="p-3 pb-6 lg:pb-3 border-t border-white/10">
          <button
            onClick={handleBrowserOpen}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-3 py-2 text-sm',
              'bg-white/5 text-slate-200 rounded-lg border border-white/10',
              'hover:bg-white/10 hover:text-white transition-colors'
            )}
          >
            <Grid3X3 className="w-4 h-4" />
            <span>STRATA</span>
          </button>
        </div>
      </div>

      {/* Mobile: Bottom tab bar */}
      {isMobile && (
        <MahasarthiDock
          onBrowserOpen={handleBrowserOpen}
          onSearchOpen={handleSearchOpen}
          onNavigate={handleNavigate}
          isMobile={true}
        />
      )}
      
      <MahasarthiStrata
        isOpen={isBrowserOpen}
        onClose={handleBrowserClose}
        onNavigate={handleNavigate}
        isMobile={isMobile}
      />
      
      <MahasarthiSearch
        isOpen={isSearchOpen}
        onClose={handleSearchClose}
        onNavigate={handleNavigate}
      />
    </>
  );
}

export default Mahasarthi;

