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
 * Refactored Phase 6F: Navigation Intelligence & Cleanup
 * - Uses useMahasarthiNavigation hook
 * - Context-aware visibility (hides clutter when in workspace)
 */

import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MahasarthiDock } from './MahasarthiDock';
import { MahasarthiStrata } from './MahasarthiStrata';
import { MahasarthiSearch } from './MahasarthiSearch';
import { useDockStore } from '@/store/dockStore';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { useMahasarthiNavigation } from '@/hooks/useMahasarthiNavigation';
import { cn } from '@/lib/utils';
import {
  Search, Pin, Grid3X3,
  LayoutDashboard, Wheat, FlaskConical, Sprout, GitMerge, BarChart3,
  Dna, Settings, TestTube2, Shield, Package, Truck, FileCheck, FileText,
  Building2, RefreshCw, Globe, Target, Cpu, Rocket, BookOpen, Eye,
  ChevronDown, ChevronRight, type LucideIcon
} from 'lucide-react';

// ============================================================================
// Icon Mapping (shared with MahasarthiDock)
// ============================================================================

const iconMap: Record<string, LucideIcon> = {
  LayoutDashboard, Wheat, FlaskConical, Sprout, GitMerge, BarChart3,
  Dna, Settings, TestTube2, Shield, Package, Truck, FileCheck, FileText,
  Building2, RefreshCw, Globe, Target, Cpu, Rocket, BookOpen, Eye,
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
  const { recordVisit } = useDockStore();
  
  // Navigation Hook
  const {
    activeGateway,
    activeWorkspace,
    activeWorkspaceId,
    filteredDivisions,
    gatewayPinnedItems,
    workspaceModules,
    GATEWAYS
  } = useMahasarthiNavigation();

  // Detect mobile viewport (< lg breakpoint = 1024px)
  const isMobile = useMediaQuery('(max-width: 1023px)');
  
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSwitcherOpen, setIsSwitcherOpen] = useState(false); // New state for accordion switcher

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

  // Expanded view - Context-Aware Navigation
  return (
    <>
      <div className="flex flex-col h-full">
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
            <span className="truncate">Search {GATEWAYS[activeGateway]?.label || 'BijMantra'}...</span>
            <kbd className="ml-auto text-[10px] bg-white/10 px-1.5 py-0.5 rounded flex-shrink-0">⌘K</kbd>
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

        {/* =========================================================================== */}
        {/* CONTEXT-AWARE NAVIGATION (Refactored)                                     */}
        {/* =========================================================================== */}

        <div className="flex-1 overflow-y-auto p-3 space-y-6">
          
          {/* 1. CURRENT WORKSPACE MODULES (Primary Focus) */}
          {activeWorkspace ? (
            <div className="space-y-4">
              {workspaceModules.map(module => (
                <div key={module.id} className="space-y-1">
                  {/* Module Header */}
                  <div className="px-2 text-[10px] font-bold text-emerald-500/80 uppercase tracking-wider flex items-center gap-1.5 opacity-80">
                    {module.name}
                  </div>
                  
                  {/* Module Pages */}
                  <div className="space-y-0.5">
                    {module.pages.map(page => {
                      const isActive = location.pathname === page.route || location.pathname.startsWith(page.route + '/');
                      return (
                        <Link
                          key={page.id}
                          to={page.route}
                          onClick={onNavigate}
                          className={cn(
                            'block px-2 py-1.5 rounded-lg text-sm transition-all duration-200 border border-transparent',
                            isActive
                              ? cn('bg-emerald-500/15 text-emerald-300 border-emerald-500/20 font-medium')
                              : 'text-slate-300 hover:bg-white/5 hover:text-white hover:pl-3'
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <span className="truncate">{page.name}</span>
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
              
              {workspaceModules.length === 0 && (
                <div className="px-2 py-4 text-xs text-slate-500 italic">
                  No modules configured for this workspace.
                </div>
              )}
            </div>
          ) : (
            // Fallback for Global Mode (No specific workspace active)
            <div className="px-2 py-4 text-center">
              <p className="text-sm text-slate-400 mb-2">Select a workspace to begin</p>
              <button 
                onClick={handleBrowserOpen}
                className="text-emerald-400 text-xs hover:underline"
              >
                Open STRATA Menu
              </button>
            </div>
          )}


          {/* 2. SWITCH WORKSPACE (Collapsed by default to reduce clutter) */}
          <div className="pt-4 border-t border-white/5">
             <button 
               onClick={() => setIsSwitcherOpen(!isSwitcherOpen)}
               className="w-full flex items-center justify-between px-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 hover:text-slate-300 transition-colors"
             >
               <span>Switch Workspace</span>
               {isSwitcherOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
             </button>
             
             {isSwitcherOpen && (
               <div className="space-y-0.5 animate-in fade-in slide-in-from-top-1 duration-200">
                {filteredDivisions.map(division => {
                    const isActive = activeWorkspaceId === division.id;
                    const IconComponent = getIcon(division.icon);
                    if (isActive) return null; // Don't show current workspace in switcher
                    
                    return (
                      <Link
                        key={division.id}
                        to={division.route}
                        onClick={onNavigate}
                        className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
                      >
                        <IconComponent className="w-4 h-4 flex-shrink-0 opacity-70" strokeWidth={1.5} />
                        <span className="truncate">{division.name}</span>
                      </Link>
                    );
                  })}
               </div>
             )}
          </div>

        </div>

        {/* STRATA Button */}
        <div className="p-3 pb-6 lg:pb-3 border-t border-white/10 mt-auto">
          <button
            onClick={handleBrowserOpen}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-3 py-2 text-sm',
              'bg-gradient-to-r from-white/5 to-white/10 text-slate-200', 
              'rounded-lg border border-white/10',
              'hover:from-emerald-900/40 hover:to-emerald-800/40 hover:text-emerald-300 hover:border-emerald-500/30 transition-all duration-300'
            )}
          >
            <Grid3X3 className="w-4 h-4" />
            <span className="font-medium tracking-wide">STRATA</span>
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
