/**
 * Mahasarthi Search Component
 * 
 * Enhanced command palette / spotlight search for the Mahasarthi navigation system.
 * Primary navigation method for power users.
 * 
 * Features:
 * - Recent pages (top section)
 * - Pinned pages
 * - All pages (grouped by division)
 * - Quick actions ("Create Trial", "Add Germplasm")
 * - Fuzzy search with frecency ranking
 * - Keyboard-first navigation
 * 
 * @see docs/gupt/1-MAHASARTHI.md for full specification
 */

import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useDockStore } from '@/store/dockStore';
import { allNavItems } from '@/components/SmartNavigation';
import {
  Search, Clock, Star, Zap, ArrowRight, Plus,
  LayoutDashboard, Wheat, FlaskConical, Sprout, GitMerge,
  Settings, FileText, Users, Package, Dna,
  type LucideIcon,
} from 'lucide-react';

// ============================================================================
// Icon Mapping
// ============================================================================

const iconMap: Record<string, LucideIcon> = {
  LayoutDashboard,
  Wheat,
  FlaskConical,
  Sprout,
  GitMerge,
  Settings,
  FileText,
  Users,
  Package,
  Dna,
};

// ============================================================================
// Quick Actions
// ============================================================================

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
  path: string;
  keywords: string[];
}

const quickActions: QuickAction[] = [
  {
    id: 'create-program',
    label: 'Create Program',
    description: 'Start a new breeding program',
    icon: Plus,
    path: '/programs?action=create',
    keywords: ['new', 'add', 'program', 'breeding'],
  },
  {
    id: 'create-trial',
    label: 'Create Trial',
    description: 'Set up a new field trial',
    icon: Plus,
    path: '/trials?action=create',
    keywords: ['new', 'add', 'trial', 'field'],
  },
  {
    id: 'add-germplasm',
    label: 'Add Germplasm',
    description: 'Register new germplasm',
    icon: Plus,
    path: '/germplasm?action=create',
    keywords: ['new', 'add', 'germplasm', 'accession'],
  },
  {
    id: 'create-cross',
    label: 'Plan Cross',
    description: 'Plan a new cross',
    icon: GitMerge,
    path: '/crossingplanner',
    keywords: ['new', 'cross', 'crossing', 'plan'],
  },
  {
    id: 'collect-data',
    label: 'Collect Data',
    description: 'Start data collection',
    icon: FlaskConical,
    path: '/observations/collect',
    keywords: ['collect', 'data', 'observation', 'phenotype'],
  },
  {
    id: 'quick-entry',
    label: 'Quick Entry',
    description: 'Fast data entry mode',
    icon: Zap,
    path: '/quick-entry',
    keywords: ['quick', 'fast', 'entry', 'data'],
  },
];

// ============================================================================
// Types
// ============================================================================

interface MahasarthiSearchProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: () => void;
}

type ResultType = 'recent' | 'pinned' | 'action' | 'page';

interface SearchResult {
  type: ResultType;
  id: string;
  label: string;
  description?: string;
  path: string;
  icon: LucideIcon;
}

// ============================================================================
// Component
// ============================================================================

export function MahasarthiSearch({ isOpen, onClose, onNavigate }: MahasarthiSearchProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { pinnedItems, recentItems, recordVisit } = useDockStore();
  
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Build search results
  const results = useMemo((): SearchResult[] => {
    const q = query.toLowerCase().trim();
    const results: SearchResult[] = [];

    if (!q) {
      // No query - show recent, pinned, and actions
      
      // Recent (max 3)
      recentItems.slice(0, 3).forEach(item => {
        results.push({
          type: 'recent',
          id: `recent-${item.id}`,
          label: item.label,
          path: item.path,
          icon: iconMap[item.icon] || LayoutDashboard,
        });
      });

      // Pinned (max 4)
      pinnedItems.slice(0, 4).forEach(item => {
        results.push({
          type: 'pinned',
          id: `pinned-${item.id}`,
          label: item.label,
          path: item.path,
          icon: iconMap[item.icon] || LayoutDashboard,
        });
      });

      // Quick actions (max 4)
      quickActions.slice(0, 4).forEach(action => {
        results.push({
          type: 'action',
          id: action.id,
          label: action.label,
          description: action.description,
          path: action.path,
          icon: action.icon,
        });
      });

      return results;
    }

    // With query - search everything
    
    // Search actions first
    quickActions.forEach(action => {
      if (
        action.label.toLowerCase().includes(q) ||
        action.keywords.some(k => k.includes(q))
      ) {
        results.push({
          type: 'action',
          id: action.id,
          label: action.label,
          description: action.description,
          path: action.path,
          icon: action.icon,
        });
      }
    });

    // Search all nav items
    allNavItems.forEach(item => {
      if (
        item.label.toLowerCase().includes(q) ||
        item.path.toLowerCase().includes(q) ||
        item.keywords?.some(k => k.toLowerCase().includes(q))
      ) {
        // Check if already in results (from pinned/recent)
        if (!results.some(r => r.path === item.path)) {
          results.push({
            type: 'page',
            id: `page-${item.path}`,
            label: item.label,
            path: item.path,
            icon: item.icon,
          });
        }
      }
    });

    return results.slice(0, 12); // Max 12 results
  }, [query, pinnedItems, recentItems]);

  // Reset selection when results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [results]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
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
          setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            handleSelect(results[selectedIndex]);
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => document.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [isOpen, selectedIndex, results, onClose]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current && selectedIndex >= 0) {
      const items = listRef.current.querySelectorAll('[data-result-item]');
      items[selectedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  // Handle selection
  const handleSelect = useCallback((result: SearchResult) => {
    // Record visit for frecency
    recordVisit({
      id: result.id,
      path: result.path,
      label: result.label,
      icon: result.icon.name || 'LayoutDashboard',
    });
    
    navigate(result.path);
    onClose();
    onNavigate?.();
  }, [navigate, onClose, onNavigate, recordVisit]);

  if (!isOpen) return null;

  // Group results by type for display
  const groupedResults = useMemo(() => {
    const groups: { type: ResultType; label: string; items: SearchResult[] }[] = [];
    
    const recent = results.filter(r => r.type === 'recent');
    const pinned = results.filter(r => r.type === 'pinned');
    const actions = results.filter(r => r.type === 'action');
    const pages = results.filter(r => r.type === 'page');

    if (recent.length) groups.push({ type: 'recent', label: 'Recent', items: recent });
    if (pinned.length) groups.push({ type: 'pinned', label: 'Pinned', items: pinned });
    if (actions.length) groups.push({ type: 'action', label: 'Actions', items: actions });
    if (pages.length) groups.push({ type: 'page', label: 'Pages', items: pages });

    return groups;
  }, [results]);

  // Calculate flat index for keyboard navigation
  let flatIndex = 0;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Search Dialog */}
      <div
        role="dialog"
        aria-label="Search"
        aria-modal="true"
        className={cn(
          'fixed left-1/2 top-[20%] -translate-x-1/2 z-50',
          'w-full max-w-xl',
          'bg-slate-900 border border-slate-700 rounded-xl',
          'shadow-2xl overflow-hidden',
          'animate-in fade-in zoom-in-95 duration-150'
        )}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800">
          <Search className="w-5 h-5 text-slate-500" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages, actions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={cn(
              'flex-1 bg-transparent text-slate-200 placeholder-slate-500',
              'text-base outline-none'
            )}
          />
          <kbd className="px-2 py-1 text-xs text-slate-500 bg-slate-800 rounded">
            esc
          </kbd>
        </div>

        {/* Results */}
        <div ref={listRef} className="max-h-[60vh] overflow-y-auto p-2">
          {groupedResults.map(group => (
            <div key={group.type} className="mb-2">
              <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {group.type === 'recent' && <Clock className="w-3 h-3" />}
                {group.type === 'pinned' && <Star className="w-3 h-3" />}
                {group.type === 'action' && <Zap className="w-3 h-3" />}
                {group.label}
              </div>
              
              {group.items.map(result => {
                const currentIndex = flatIndex++;
                const isSelected = currentIndex === selectedIndex;
                const IconComponent = result.icon;

                return (
                  <button
                    key={result.id}
                    data-result-item
                    onClick={() => handleSelect(result)}
                    className={cn(
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left',
                      isSelected
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'hover:bg-slate-800 text-slate-300'
                    )}
                  >
                    <div className={cn(
                      'flex items-center justify-center w-8 h-8 rounded-lg',
                      result.type === 'action' 
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-slate-800 text-slate-400'
                    )}>
                      <IconComponent className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{result.label}</div>
                      {result.description && (
                        <div className="text-xs text-slate-500 truncate">{result.description}</div>
                      )}
                    </div>
                    {isSelected && (
                      <ArrowRight className="w-4 h-4 text-emerald-400" />
                    )}
                  </button>
                );
              })}
            </div>
          ))}

          {results.length === 0 && query && (
            <div className="px-4 py-8 text-center text-slate-500">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <div className="text-sm">No results for "{query}"</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-slate-800 text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
          </div>
          <span>⌘K to toggle</span>
        </div>
      </div>
    </>
  );
}

export default MahasarthiSearch;
