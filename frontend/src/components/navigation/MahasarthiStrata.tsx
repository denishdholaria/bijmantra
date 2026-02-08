/**
 * Mahasarthi Strata Component
 * 
 * New Generation "Web-OS" App Launcher.
 * Features a folder-based navigation structure, glassmorphism, and infinite scalability.
 */

import { useState, useMemo, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useDivisionRegistry } from '@/framework/registry';
import { useActiveWorkspace, useWorkspaceStore } from '@/store/workspaceStore';
import { useDockStore } from '@/store/dockStore';
import { futureDivisions } from '@/framework/registry/futureDivisions';
import { StrataFolder, type StrataItem } from './StrataFolder';
import {
  X, Search, ExternalLink,
  Sprout, Wheat, FlaskConical, Dna, Map, BarChart3, Cpu,
  Building2, Globe, Sun, Radio, Rocket, Wrench, Settings,
  BookOpen, Home, Shield, Package, Truck, FileText,
  Mountain, Droplets, TrendingUp, Leaf, ClipboardList, Bot, Fish, Beef,
  LayoutGrid
} from 'lucide-react';

// ============================================================================
// Icon Mapping
// ============================================================================

const divisionIcons: Record<string, typeof Sprout> = {
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
  'Mountain': Mountain,
  'Droplets': Droplets,
  'TrendingUp': TrendingUp,
  'Leaf': Leaf,
  'ClipboardList': ClipboardList,
  'Bot': Bot,
  'Fish': Fish,
  'Beef': Beef,
};

function getIcon(iconName: string): typeof Sprout {
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

type NavigationLevel = {
  id: string;
  title: string;
  items: StrataItem[];
  icon?: typeof Sprout;
};

// ============================================================================
// Component
// ============================================================================

export function MahasarthiStrata({ isOpen, onClose, onNavigate, isMobile = false }: MahasarthiStrataProps) {
  const navigate = useNavigate();
  const { navigableDivisions } = useDivisionRegistry();
  const { pinnedItems, recentItems } = useDockStore();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [navigationStack, setNavigationStack] = useState<NavigationLevel[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus search input when opened
  useEffect(() => {
    if (isOpen) {
      // Small delay to allow animation to start
      requestAnimationFrame(() => {
        searchInputRef.current?.focus();
      });
    } else {
      // Reset state on close
      setTimeout(() => {
        setSearchQuery('');
        setNavigationStack([]);
      }, 300);
    }
  }, [isOpen]);

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (searchQuery) {
          setSearchQuery('');
        } else if (navigationStack.length > 0) {
          setNavigationStack(prev => prev.slice(0, -1));
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, searchQuery, navigationStack, onClose]);

  // 1. Build Root Items (Divisions)
  const rootItems = useMemo<StrataItem[]>(() => {
    // Basic Active Divisions
    const items: StrataItem[] = navigableDivisions.map(div => ({
      id: div.id,
      label: div.name,
      icon: getIcon(div.icon),
      type: 'folder',
      description: div.description,
      badge: div.status === 'beta' ? 'Beta' : undefined
    }));

    // Add Future/Planned (if not in navigable)
    // Note: In a real app we might filter these more strictly
    const planned = futureDivisions.map(div => ({
      id: div.id,
      label: div.name,
      icon: getIcon(div.icon),
      type: 'link' as const, // Future ones are usually just links for now or placeholders
      path: div.route,
      description: div.description,
      badge: 'Soon',
      badgeColor: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-300'
    }));
    
    return [...items, ...planned];
  }, [navigableDivisions]);

  // 2. Prepare Current View Data
  const currentView = useMemo(() => {
    if (navigationStack.length > 0) {
      return navigationStack[navigationStack.length - 1];
    }
    
    // Root View
    return {
      id: 'root',
      title: 'Apps',
      items: rootItems,
      icon: LayoutGrid
    };
  }, [navigationStack, rootItems]);

  // 3. Search Features
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return [];
    
    // Flatten everything for search
    const allSearchable: StrataItem[] = [];
    
    navigableDivisions.forEach(div => {
      // Add division itself
      allSearchable.push({
        id: div.id,
        label: div.name,
        icon: getIcon(div.icon),
        type: 'folder',
        description: div.description
      });
      
      // Add sections/pages
      div.sections?.forEach(section => {
        const sectionIcon = getIcon(section.icon || div.icon);
        
        if (section.items) {
          // It's a folder
          allSearchable.push({
            id: `${div.id}-${section.id}`,
            label: section.name,
            icon: sectionIcon,
            type: 'folder',
            description: `In ${div.name}`
          });
          
          // Add items
          section.items.forEach(item => {
            const itemPath = item.isAbsolute ? item.route : `${div.route}${item.route}`;
            allSearchable.push({
              id: item.id,
              label: item.name,
              icon: sectionIcon,
              type: 'link',
              path: itemPath,
              description: `${div.name} > ${section.name}`
            });
          });
        } else {
          // Standalone section link
          const path = section.isAbsolute ? section.route : `${div.route}${section.route}`;
          allSearchable.push({
            id: section.id,
            label: section.name,
            icon: sectionIcon,
            type: 'link',
            path: path,
            description: `In ${div.name}`
          });
        }
      });
    });

    const q = searchQuery.toLowerCase();
    return allSearchable.filter(item => 
      item.label.toLowerCase().includes(q) || 
      item.description?.toLowerCase().includes(q)
    ).slice(0, 20); // Limit results
  }, [searchQuery, navigableDivisions]);

  // Action Handlers
  const handleItemClick = (item: StrataItem) => {
    if (item.type === 'link' && item.path) {
      // Navigate via React Router (unified routing, no more window manager)
      navigate(item.path);
      
      onClose();
      onNavigate?.();
      return;
    }

    if (item.type === 'folder') {
      // Find the division or section data to push to stack
      const division = navigableDivisions.find(d => d.id === item.id);
      if (division) {
        // Entered a Division -> Show Sections
        const sectionItems: StrataItem[] = division.sections?.map(sec => ({
          id: sec.id,
          label: sec.name,
          icon: getIcon(sec.icon || division.icon),
          // If section has items, it's a folder. If not, it's a link.
          type: sec.items ? 'folder' : 'link', 
          path: sec.items ? undefined : (sec.isAbsolute ? sec.route : `${division.route}${sec.route}`),
          description: sec.description
        })) || [];

        setNavigationStack(prev => [...prev, {
          id: division.id,
          title: division.name,
          items: sectionItems,
          icon: getIcon(division.icon)
        }]);
        return;
      }

      // Entered a Section (Sub-folder)
      // Current level = division?
      const currentLevelId = navigationStack[navigationStack.length - 1]?.id;
      const currentDivision = navigableDivisions.find(d => d.id === currentLevelId);
      
      if (currentDivision) {
         const section = currentDivision.sections?.find(s => s.id === item.id);
         if (section && section.items) {
           const subItems: StrataItem[] = section.items.map(sub => ({
             id: sub.id,
             label: sub.name,
             icon: getIcon(section.icon || currentDivision.icon), // Inherit icons
             type: 'link',
             path: sub.isAbsolute ? sub.route : `${currentDivision.route}${sub.route}`,
           }));

           setNavigationStack(prev => [...prev, {
             id: section.id,
             title: section.name,
             items: subItems,
             icon: getIcon(section.icon || currentDivision.icon)
           }]);
         }
      }
    }
  };

  const handleBack = () => {
    setNavigationStack(prev => prev.slice(0, -1));
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      <div className={cn(
        "fixed z-50 overflow-hidden shadow-2xl transition-all duration-300 ease-out",
        isMobile 
          ? "inset-x-0 bottom-0 h-[85vh] rounded-t-3xl bg-slate-50 dark:bg-slate-900"
          : "inset-0 md:inset-x-32 md:inset-y-24 md:max-w-6xl md:mx-auto rounded-3xl bg-slate-50/95 dark:bg-slate-900/95 border border-white/20 ring-1 ring-slate-900/10"
      )}>
        <div className="flex flex-col h-full w-full">
          {/* Top Bar: Search & Controls */}
          <div className="flex-none flex items-center gap-4 p-6 border-b border-slate-200/50 dark:border-slate-800/50 bg-white/50 dark:bg-slate-900/50 backdrop-blur-xl">
            <div className="relative flex-1 max-w-2xl mx-auto w-full group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-primary transition-colors" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search apps, pages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-12 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm text-lg outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all placeholder:text-slate-400"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {searchQuery && (
                  <button 
                    onClick={() => setSearchQuery('')}
                    className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                )}
                {!isMobile && !searchQuery && (
                  <kbd className="hidden md:inline-flex items-center gap-1 px-2 py-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs text-slate-500 font-medium font-mono">
                    <span className="text-xs">ESC</span>
                  </kbd>
                )}
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 -mr-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 overflow-hidden relative">
            {searchQuery ? (
              // Search Results
              <StrataFolder
                key="search-results"
                title="Search Results"
                icon={Search}
                items={filteredItems}
                onItemClick={handleItemClick}
                isRoot={true}
                className="bg-transparent"
                description={filteredItems.length === 0 ? "No results found" : `Found ${filteredItems.length} items`}
              />
            ) : (
              // Browser / Folder View
              <AnimatePresence mode="popLayout" initial={false}>
                <motion.div
                  key={currentView.id}
                  initial={{ opacity: 0, x: navigationStack.length > 0 ? 20 : -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: navigationStack.length > 0 ? -20 : 20 }}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  className="absolute inset-0"
                >
                  <StrataFolder
                    title={currentView.title}
                    icon={currentView.icon}
                    items={currentView.items}
                    onItemClick={handleItemClick}
                    onBack={navigationStack.length > 0 ? handleBack : undefined}
                    isRoot={navigationStack.length === 0}
                    className="bg-transparent"
                  />
                </motion.div>
              </AnimatePresence>
            )}
          </div>

          {/* Bottom Dock / Quick Access (Only on Root View and if no search) */}
          {!searchQuery && navigationStack.length === 0 && (
            <div className="flex-none p-4 bg-slate-50/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800">
              <div className="max-w-6xl mx-auto w-full">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-2">
                  Quick Access
                </div>
                <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                  {/* Pinned & Recent merged logic */}
                  {[...pinnedItems, ...recentItems.slice(0, 4)].map((item, idx) => {
                     const ItemIcon = getIcon(item.icon);
                     return (
                       <button
                         key={`${item.path}-${idx}`}
                         onClick={() => { navigate(item.path); onClose(); onNavigate?.(); }}
                         className="flex flex-col items-center gap-2 min-w-[4.5rem] p-2 hover:bg-white dark:hover:bg-slate-800 rounded-xl transition-colors group"
                       >
                         <div className="p-2.5 bg-white dark:bg-slate-800 rounded-xl shadow-sm ring-1 ring-slate-900/5 group-hover:ring-primary/20 dark:group-hover:ring-primary/40 transition-all">
                           <ItemIcon className="w-5 h-5 text-slate-600 dark:text-slate-300 group-hover:text-primary transition-colors" />
                         </div>
                         <span className="text-[10px] font-medium text-slate-600 dark:text-slate-400 text-center line-clamp-1 w-full">
                           {item.label}
                         </span>
                       </button>
                     );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default MahasarthiStrata;
