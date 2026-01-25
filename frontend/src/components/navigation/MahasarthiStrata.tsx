/**
 * Mahasarthi Strata Component
 * 
 * Full domain mega-panel browser for the Mahasarthi navigation system.
 * Shows all divisions/pages filtered by active workspace.
 * 
 * Features:
 * - Workspace-filtered view (only shows relevant divisions)
 * - Cross-domain "Related" section
 * - Multi-column layout for quick scanning
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Pin/unpin pages from browser
 * - Search within browser
 * 
 * @see docs/gupt/1-MAHASARTHI.md for full specification
 */

import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useDivisionRegistry } from '@/framework/registry';
import { useActiveWorkspace, useWorkspaceStore } from '@/store/workspaceStore';
import { useDockStore } from '@/store/dockStore';
import { getWorkspaceModules, isRouteInWorkspace } from '@/framework/registry/workspaces';
import { futureDivisions, type FutureDivision } from '@/framework/registry/futureDivisions';
import { GATEWAYS, getGatewayForRoute } from '@/config/MahasarthiConfig';
import {
  X, Search, Pin, PinOff, ExternalLink, ChevronRight, ChevronDown,
  Sprout, Wheat, FlaskConical, Dna, Map, BarChart3, Cpu,
  Building2, Globe, Sun, Radio, Rocket, Wrench, Settings,
  BookOpen, Home, Shield, Package, Truck, FileText, Sparkles,
  Mountain, Droplets, TrendingUp, Leaf, ClipboardList, Bot, Fish, Beef,
  ArrowRight, History, LayoutGrid,
  type LucideIcon,
} from 'lucide-react';

// ============================================================================
// Icon Mapping
// ============================================================================

const divisionIcons: Record<string, LucideIcon> = {
  'Seedling': Sprout,
  'Sprout': Sprout,
  'Wheat': Wheat,
  'Warehouse': Building2,
  'Globe': Globe,
  'Sun': Sun,
  'Radio': Radio,
  'Building2': Building2,
  'Factory': Building2,
  'Rocket': Rocket,
  'Plug': ExternalLink,
  'BookOpen': BookOpen,
  'Wrench': Wrench,
  'Settings': Settings,
  'Home': Home,
  'Dna': Dna,
  'FlaskConical': FlaskConical,
  'Microscope': FlaskConical,
  'Map': Map,
  'BarChart3': BarChart3,
  'Cpu': Cpu,
  'Shield': Shield,
  'Package': Package,
  'Truck': Truck,
  'FileText': FileText,
  // Future division icons
  'Mountain': Mountain,
  'Droplets': Droplets,
  'TrendingUp': TrendingUp,
  'Leaf': Leaf,
  'ClipboardList': ClipboardList,
  'Bot': Bot,
  'Fish': Fish,
  'Beef': Beef,
};

function getIcon(iconName: string): LucideIcon {
  return divisionIcons[iconName] || Sprout;
}

// ============================================================================
// Types
// ============================================================================

interface MahasarthiStrataProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: () => void;
  isMobile?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function MahasarthiStrata({ isOpen, onClose, onNavigate, isMobile = false }: MahasarthiStrataProps) {
  const navigate = useNavigate();
  const { navigableDivisions } = useDivisionRegistry();
  const activeWorkspace = useActiveWorkspace();
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId);
  const { pinnedItems, recentItems, pinItem, unpinItem, isPinned } = useDockStore();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [showAllApps, setShowAllApps] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const searchInputRef = useRef<HTMLInputElement>(null);
  const browserRef = useRef<HTMLDivElement>(null);

  // Toggle section expansion
  const toggleSection = useCallback((sectionKey: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(sectionKey)) {
        next.delete(sectionKey);
      } else {
        next.add(sectionKey);
      }
      return next;
    });
  }, []);

  // Filter divisions by active gateway (Prakriti, Srijan, etc.)
  const { primaryDivisions, crossDomainDivisions, activeGateway } = useMemo(() => {
    if (!activeWorkspaceId) {
      return { primaryDivisions: navigableDivisions, crossDomainDivisions: [], activeGateway: null };
    }

    // 1. Identify current gateway
    // We derive this from the active workspace ID to find which Gateway it belongs to
    let currentGateway = null;
    let gatewayWorkspaces: string[] = [activeWorkspaceId]; // Default to just current workspace

    // Find the gateway that contains this workspace
    for (const gateway of Object.values(GATEWAYS)) {
      if (gateway.workspaces.includes(activeWorkspaceId)) {
        currentGateway = gateway;
        gatewayWorkspaces = gateway.workspaces;
        break;
      }
    }

    // 2. Collect all modules from ALL workspaces in this gateway
    const allGatewayModules = gatewayWorkspaces.flatMap(wsId => getWorkspaceModules(wsId as any));
    
    // Create a set of all routes belonging to this gateway
    const gatewayRoutes = new Set<string>();
    allGatewayModules.forEach(module => {
      module.pages.forEach(page => {
        gatewayRoutes.add(page.route);
        const baseRoute = page.route.split('/')[1];
        if (baseRoute) gatewayRoutes.add(`/${baseRoute}`);
      });
    });

    const primary: typeof navigableDivisions = [];
    const crossDomain: typeof navigableDivisions = [];

    // 3. Filter divisions based on Gateway membership
    navigableDivisions.forEach(division => {
      // Check if division belongs to ANY of the gateway's workspaces
      const isInGateway = gatewayWorkspaces.some(wsId => isRouteInWorkspace(division.route, wsId as any)) ||
        (division.sections?.some(section => {
          const sectionRoute = section.isAbsolute ? section.route : `${division.route}${section.route}`;
          return gatewayWorkspaces.some(wsId => isRouteInWorkspace(sectionRoute, wsId as any));
        }));

      if (isInGateway) {
        primary.push(division);
      } else if (division.sections?.some(s => s.items?.length)) {
        // Has content, check specific cross-domain rules or just basic cross-link
        crossDomain.push(division);
      }
    });

    return { 
      primaryDivisions: primary, 
      crossDomainDivisions: crossDomain.slice(0, 3),
      activeGateway: currentGateway
    };
  }, [navigableDivisions, activeWorkspaceId]);

  // Flatten all navigable items for keyboard navigation
  const allItems = useMemo(() => {
    const items: { path: string; label: string; icon: string; division: string }[] = [];
    
    primaryDivisions.forEach(division => {
      if (division.sections) {
        division.sections.forEach(section => {
          if (section.items) {
            section.items.forEach(item => {
              const path = item.isAbsolute ? item.route : `${division.route}${item.route}`;
              items.push({
                path,
                label: item.name,
                icon: division.icon,
                division: division.name,
              });
            });
          } else {
            const path = section.isAbsolute ? section.route : `${division.route}${section.route}`;
            items.push({
              path,
              label: section.name,
              icon: division.icon,
              division: division.name,
            });
          }
        });
      }
    });

    return items;
  }, [primaryDivisions]);

  // Filter items by search
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return allItems;
    const q = searchQuery.toLowerCase();
    return allItems.filter(item =>
      item.label.toLowerCase().includes(q) ||
      item.path.toLowerCase().includes(q) ||
      item.division.toLowerCase().includes(q)
    );
  }, [allItems, searchQuery]);

  // Focus search input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          e.stopPropagation();
          requestAnimationFrame(() => onClose());
          break;
        case 'ArrowDown':
          e.preventDefault();
          setFocusedIndex(prev => Math.min(prev + 1, filteredItems.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setFocusedIndex(prev => Math.max(prev - 1, -1));
          break;
        case 'Enter':
          if (focusedIndex >= 0 && filteredItems[focusedIndex]) {
            e.preventDefault();
            navigate(filteredItems[focusedIndex].path);
            requestAnimationFrame(() => {
              onClose();
              onNavigate?.();
            });
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => document.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [isOpen, focusedIndex, filteredItems, navigate, onClose, onNavigate]);

  // Handle pin toggle
  const handlePinToggle = useCallback((item: { path: string; label: string; icon: string }) => {
    if (isPinned(item.path)) {
      unpinItem(item.path);
    } else {
      pinItem({
        id: item.path.replace(/\//g, '-'),
        path: item.path,
        label: item.label,
        icon: item.icon,
      });
    }
  }, [isPinned, pinItem, unpinItem]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Browser Panel */}
      <div
        ref={browserRef}
        role="dialog"
        aria-label="Domain Browser"
        aria-modal="true"
        className={cn(
          'fixed z-50 bg-slate-900 shadow-2xl overflow-hidden',
          'animate-in duration-200',
          // Mobile: full screen with bottom padding for tab bar
          isMobile 
            ? 'inset-0 slide-in-from-bottom pb-20' 
            : 'left-16 top-0 bottom-0 w-[calc(100vw-4rem)] max-w-4xl border-r border-slate-700 slide-in-from-left'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            {activeGateway ? (
              <div className={cn(
                'px-3 py-1.5 rounded-lg text-white text-sm font-medium',
                activeGateway.color.replace('bg-', 'bg-gradient-to-r from-').replace('-500', '-500 to-emerald-600') // Create gradient on fly or use defined colors
              )}>
                {activeGateway.label}
              </div>
            ) : activeWorkspace && (
              <div className={cn(
                'px-3 py-1.5 rounded-lg text-white text-sm font-medium',
                'bg-gradient-to-r',
                activeWorkspace.color
              )}>
                {activeWorkspace.name}
              </div>
            )}
            <span className="text-slate-400 text-sm">STRATA</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            aria-label="Close STRATA"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search */}
        <div className="px-6 py-3 border-b border-slate-800">
          <div className="relative">
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search pages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                'w-full pl-10 pr-4 py-2.5 text-sm',
                'bg-slate-800 text-slate-200 placeholder-slate-500',
                'rounded-lg border border-slate-700',
                'focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50'
              )}
            />
            <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
          </div>
        </div>

        {/* Content */}
        <div className={cn(
          "overflow-y-auto p-6",
          isMobile ? "h-[calc(100%-10rem)]" : "h-[calc(100%-8rem)]"
        )}>
          {searchQuery ? (
            // Search Results
            <div className="space-y-1">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                {filteredItems.length} results
              </div>
              {filteredItems.map((item, index) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => { onClose(); onNavigate?.(); }}
                  className={cn(
                    'flex items-center justify-between px-3 py-2 rounded-lg transition-colors group',
                    focusedIndex === index
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'hover:bg-slate-800 text-slate-300'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm">{item.label}</span>
                    <span className="text-xs text-slate-500">{item.division}</span>
                  </div>
                  <button
                    onClick={(e) => { e.preventDefault(); handlePinToggle(item); }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-700 rounded transition-all"
                    aria-label={isPinned(item.path) ? 'Unpin' : 'Pin to dock'}
                  >
                    {isPinned(item.path) ? (
                      <PinOff className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Pin className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                </Link>
              ))}
            </div>
          ) : !showAllApps ? (
            // Progressive Disclosure View (Pinned + Recent)
            <div className="space-y-8">
              {/* Pinned Apps Zone */}
              <div>
                <div className="flex items-center gap-2 mb-4 text-emerald-400">
                  <Pin className="w-4 h-4" />
                  <span className="text-xs font-semibold uppercase tracking-wider">Pinned Apps</span>
                </div>
                {pinnedItems.length > 0 ? (
                  <div className={cn(
                    "grid gap-4",
                    isMobile ? "grid-cols-2" : "grid-cols-4"
                  )}>
                    {pinnedItems.map(item => {
                      const IconComponent = getIcon(item.icon);
                      return (
                        <Link
                          key={item.id}
                          to={item.path}
                          onClick={() => { onClose(); onNavigate?.(); }}
                          className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-800/50 border border-slate-700 hover:bg-slate-800 hover:border-emerald-500/50 transition-all group text-center"
                        >
                          <div className="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center mb-3 text-slate-300 group-hover:text-emerald-400 group-hover:bg-emerald-500/10 transition-colors">
                            <IconComponent className="w-5 h-5" />
                          </div>
                          <span className="text-sm font-medium text-slate-200 group-hover:text-white line-clamp-2">
                            {item.label}
                          </span>
                        </Link>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-8 rounded-xl border border-dashed border-slate-700 text-center text-slate-500 text-sm">
                    Pin your favorite apps for quick access
                  </div>
                )}
              </div>

              {/* Recent Items Zone */}
              <div>
                <div className="flex items-center gap-2 mb-4 text-blue-400">
                  <History className="w-4 h-4" />
                  <span className="text-xs font-semibold uppercase tracking-wider">Recent Work</span>
                </div>
                {recentItems.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {recentItems.slice(0, 6).map(item => {
                      const IconComponent = getIcon(item.icon);
                      return (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => { onClose(); onNavigate?.(); }}
                          className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 border border-slate-800 hover:bg-slate-800 hover:border-slate-700 transition-colors group"
                        >
                          <div className="p-2 rounded bg-slate-800 text-slate-400 group-hover:text-white transition-colors">
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-slate-300 group-hover:text-white truncate">
                              {item.label}
                            </div>
                            <div className="text-xs text-slate-500 truncate">
                              {item.path}
                            </div>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-sm text-slate-500 italic">
                    No recent history yet
                  </div>
                )}
              </div>

              {/* All Apps Trigger */}
              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => setShowAllApps(true)}
                  className="w-full flex items-center justify-center gap-2 p-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all group"
                >
                  <LayoutGrid className="w-5 h-5" />
                  <span className="font-medium">
                    {activeGateway ? `Explore All ${activeGateway.label} Apps` : 'Explore All Apps'}
                  </span>
                  <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity translate-x-1" />
                </button>
              </div>
            </div>
          ) : (
            // Full Division Grid (All Apps View)
            <div className={cn(
              "grid gap-6 animate-in fade-in zoom-in-95 duration-200",
              isMobile ? "grid-cols-1" : "grid-cols-2 lg:grid-cols-3"
            )}>
              {/* Back Button */}
              <div className="col-span-full mb-2 flex items-center justify-between">
                <button 
                  onClick={() => setShowAllApps(false)}
                  className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                  <ChevronRight className="w-4 h-4 rotate-180" />
                  Back to Pinned & Recent
                </button>
                {activeGateway && (
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">
                    {activeGateway.label} Gateway
                  </span>
                )}
              </div>

              {primaryDivisions.map(division => {
                const IconComponent = getIcon(division.icon);
                
                return (
                  <div key={division.id} className="space-y-2">
                    {/* Division Header */}
                    <div className="flex items-center gap-2 text-slate-200 font-medium">
                      <IconComponent className="w-4 h-4" />
                      <span className="text-sm uppercase tracking-wider">{division.name}</span>
                    </div>
                    
                    {/* Sections */}
                    <div className="space-y-3 pl-6 border-l border-slate-800">
                      {division.sections?.map(section => {
                        const sectionKey = `${division.id}-${section.id}`;
                        const isExpanded = expandedSections.has(sectionKey);
                        const INITIAL_SHOW = 6;
                        const hasMore = section.items && section.items.length > INITIAL_SHOW;
                        const visibleItems = section.items 
                          ? (isExpanded ? section.items : section.items.slice(0, INITIAL_SHOW))
                          : [];
                        const hiddenCount = section.items ? section.items.length - INITIAL_SHOW : 0;

                        return (
                          <div key={section.id}>
                            {section.items ? (
                              <>
                                <div className="text-xs text-slate-400 font-medium mb-1">
                                  {section.name}
                                </div>
                                <div className="space-y-0.5">
                                  {visibleItems.map(item => {
                                    const path = item.isAbsolute ? item.route : `${division.route}${item.route}`;
                                    return (
                                      <Link
                                        key={item.id}
                                        to={path}
                                        onClick={() => { onClose(); onNavigate?.(); }}
                                        className="flex items-center justify-between px-2 py-1 rounded text-sm text-slate-300 hover:text-white hover:bg-slate-800 transition-colors group"
                                      >
                                        <span>{item.name}</span>
                                        <button
                                          onClick={(e) => { 
                                            e.preventDefault(); 
                                            handlePinToggle({ path, label: item.name, icon: division.icon }); 
                                          }}
                                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-700 rounded transition-all"
                                          aria-label={isPinned(path) ? 'Unpin' : 'Pin to dock'}
                                        >
                                          {isPinned(path) ? (
                                            <PinOff className="w-4 h-4 text-emerald-400" />
                                          ) : (
                                            <Pin className="w-4 h-4 text-slate-400" />
                                          )}
                                        </button>
                                      </Link>
                                    );
                                  })}
                                  {hasMore && (
                                    <button
                                      onClick={() => toggleSection(sectionKey)}
                                      className="flex items-center gap-1 px-2 py-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors w-full text-left"
                                      aria-expanded={isExpanded}
                                    >
                                      {isExpanded ? (
                                        <>
                                          <ChevronDown className="w-3 h-3" />
                                          <span>Show less</span>
                                        </>
                                      ) : (
                                        <>
                                          <ChevronRight className="w-3 h-3" />
                                          <span>Show {hiddenCount} more</span>
                                        </>
                                      )}
                                    </button>
                                  )}
                                </div>
                              </>
                            ) : (
                              <Link
                                to={section.isAbsolute ? section.route : `${division.route}${section.route}`}
                                onClick={() => { onClose(); onNavigate?.(); }}
                                className="flex items-center gap-1 px-2 py-1 rounded text-sm text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                              >
                                <ChevronRight className="w-3 h-3" />
                                <span>{section.name}</span>
                              </Link>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Cross-Domain Section */}
          {!searchQuery && crossDomainDivisions.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-800">
              <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase tracking-wider mb-4">
                <ExternalLink className="w-4 h-4" />
                Cross-Domain Access
              </div>
              <div className="flex flex-wrap gap-2">
                {crossDomainDivisions.map(division => (
                  <Link
                    key={division.id}
                    to={division.route}
                    onClick={() => { onClose(); onNavigate?.(); }}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 text-sm hover:bg-slate-700 hover:text-slate-200 transition-colors"
                  >
                    {division.name}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Future Modules Section */}
          {!searchQuery && (
            <div className="mt-8 pt-6 border-t border-slate-800">
              <div className="flex items-center gap-2 text-purple-400 text-xs font-semibold uppercase tracking-wider mb-4">
                <Sparkles className="w-4 h-4" />
                Coming Soon
              </div>
              <div className={cn(
                "grid gap-3",
                isMobile ? "grid-cols-1" : "grid-cols-2 lg:grid-cols-3"
              )}>
                {futureDivisions.slice(0, 6).map(division => {
                  const IconComponent = getIcon(division.icon);
                  return (
                    <Link
                      key={division.id}
                      to={division.route}
                      onClick={() => { onClose(); onNavigate?.(); }}
                      className="group p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/50 hover:border-purple-500/30 transition-all"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                          <IconComponent className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-slate-300 group-hover:text-slate-100 truncate">
                              {division.name}
                            </span>
                            <span className="shrink-0 px-1.5 py-0.5 text-[10px] font-medium bg-purple-500/20 text-purple-300 rounded">
                              {division.timeline}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                            {division.description}
                          </p>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
              {futureDivisions.length > 6 && (
                <Link
                  to="/"
                  onClick={() => { onClose(); onNavigate?.(); }}
                  className="mt-3 flex items-center justify-center gap-2 px-4 py-2 text-sm text-purple-400 hover:text-purple-300 transition-colors"
                >
                  <span>View all {futureDivisions.length} planned modules</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={cn(
          "absolute bottom-0 left-0 right-0 px-6 py-3 border-t border-slate-800 bg-slate-900/95 backdrop-blur",
          isMobile && "bottom-16" // Account for mobile tab bar
        )}>
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-4">
              {!isMobile && (
                <>
                  <span>↑↓ Navigate</span>
                  <span>↵ Select</span>
                </>
              )}
              <span>Esc Close</span>
            </div>
            <span className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-[10px]">⌘\</kbd>
              <span>{allItems.length} pages</span>
            </span>
          </div>
        </div>
      </div>
    </>
  );
}

export default MahasarthiStrata;
