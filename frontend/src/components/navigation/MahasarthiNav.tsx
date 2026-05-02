/**
 * Mahasarthi Navigation Component
 * 
 * Navigation content styled for the Mahasarthi sidebar (dark theme).
 * Supports two modes:
 * - Legacy: SmartNavigation with DivisionNavigation accordion
 * - Mahasarthi: New dock + browser navigation system
 * 
 * Features:
 * - Proper Radix UI Tooltips on collapsed icons
 * - Active state indicator (glowing right-edge bar)
 * - Smooth icon transitions on collapse
 * - Mahasarthi integration (dock + browser + search)
 */

import { useState, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Star } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DivisionNavigation } from '@/framework/shell';
import { smartNavCategories, allNavItems, useSmartNav } from '@/components/SmartNavigation';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Mahasarthi } from './Mahasarthi';

// ============================================================================
// Types
// ============================================================================

interface MahasarthiNavigationProps {
  collapsed?: boolean;
  onNavigate?: () => void;
  useMahasarthi?: boolean; // Toggle between legacy and Mahasarthi navigation
}

// ============================================================================
// Component
// ============================================================================

export function MahasarthiNavigation({ collapsed = false, onNavigate, useMahasarthi = true }: MahasarthiNavigationProps) {
  const location = useLocation();
  const { favorites } = useSmartNav();
  const [searchQuery, setSearchQuery] = useState('');

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase();
    return allNavItems.filter(item =>
      item.label.toLowerCase().includes(q) ||
      item.path.toLowerCase().includes(q) ||
      item.keywords?.some(k => k.toLowerCase().includes(q))
    ).slice(0, 8);
  }, [searchQuery]);

  const favoriteItems = useMemo(() => {
    return favorites
      .map(path => allNavItems.find(item => item.path === path))
      .filter(Boolean) as typeof allNavItems;
  }, [favorites]);

  // Mahasarthi Navigation (new system)
  if (useMahasarthi) {
    return <Mahasarthi collapsed={collapsed} onNavigate={onNavigate} />;
  }

  // Legacy Navigation (accordion-based)
  // Collapsed view - icons only with proper Tooltips
  if (collapsed) {
    return (
      <TooltipProvider delayDuration={200}>
        <div className="py-2 px-1 space-y-1">
          {smartNavCategories.map(cat => {
            const IconComponent = cat.icon;
            const isActive = cat.items.some(item => 
              location.pathname === item.path || location.pathname.startsWith(item.path + '/')
            );
            
            return (
              <Tooltip key={cat.id}>
                <TooltipTrigger asChild>
                  <Link
                    to={cat.items[0].path}
                    onClick={onNavigate}
                    className={cn(
                      'relative flex items-center justify-center p-2.5 rounded-lg transition-all duration-200',
                      isActive
                        ? 'bg-emerald-500/15 text-emerald-400'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                    )}
                    aria-label={cat.title}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <IconComponent className={cn(
                      "w-5 h-5 transition-transform duration-200",
                      isActive && "scale-110"
                    )} />
                    {/* Active indicator - glowing right-edge bar */}
                    {isActive && (
                      <div 
                        className="absolute right-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.6)]"
                        style={{
                          background: 'linear-gradient(to bottom, #10b981, #06b6d4, #10b981)'
                        }}
                        aria-hidden="true"
                      />
                    )}
                  </Link>
                </TooltipTrigger>
                <TooltipContent 
                  side="right" 
                  className="bg-slate-800 text-slate-100 border-slate-700"
                >
                  {cat.title}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </TooltipProvider>
    );
  }

  // Expanded view
  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-white/10">
        <div className="relative">
          <input
            type="text"
            placeholder="Search pages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-white/5 text-slate-200 placeholder-slate-500 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
          />
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
        </div>
        
        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="mt-2 bg-slate-800 rounded-lg border border-white/10 shadow-xl max-h-64 overflow-y-auto">
            {searchResults.map(item => {
              const IconComponent = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => { setSearchQuery(''); onNavigate?.(); }}
                  className="flex items-center gap-3 px-3 py-2 hover:bg-white/5 transition-colors text-slate-300 hover:text-white"
                >
                  <IconComponent className="w-4 h-4 text-slate-500" />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Favorites */}
      {favoriteItems.length > 0 && (
        <div className="p-3 border-b border-white/10">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
            <Star className="w-3 h-3" /> Favorites
          </div>
          <div className="flex flex-wrap gap-1">
            {favoriteItems.map(item => {
              const IconComponent = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onNavigate}
                  className={cn(
                    'px-2 py-1 text-xs rounded-md transition-colors flex items-center gap-1.5',
                    isActive
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200'
                  )}
                >
                  <IconComponent className="w-3 h-3" />
                  <span className="truncate max-w-[70px]">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Navigation - Division Navigation with dark theme override */}
      <div className="flex-1 overflow-y-auto slashed-nav-theme">
        <DivisionNavigation collapsed={false} onNavigate={onNavigate} />
      </div>
    </div>
  );
}

export default MahasarthiNavigation;
