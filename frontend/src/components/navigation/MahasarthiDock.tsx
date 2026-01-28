/**
 * Mahasarthi Dock Component
 * 
 * Personal pinned pages dock for the Mahasarthi navigation system.
 * 
 * Desktop: Icon-only vertical dock with tooltips, drag-to-reorder, and right-click context menu.
 * Mobile: Bottom tab bar with labels for top 4 pinned items + "More" button.
 * 
 * Features:
 * - Pinned pages (user-controlled, max 8)
 * - Recent pages (auto-tracked, max 4)
 * - Drag-to-reorder pinned items (desktop only)
 * - Right-click to unpin (desktop only)
 * - Active state indicator (glowing edge)
 * - Workspace indicator at top
 * - Responsive: vertical dock on desktop, bottom tabs on mobile
 * 
 * @see docs/gupt/1-MAHASARTHI.md for full specification (section 8.5)
 */

import { useCallback, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useDockStore } from '@/store/dockStore';
import { useActiveWorkspace, useWorkspaceStore } from '@/store/workspaceStore';
import { isRouteInWorkspace } from '@/framework/registry/workspaces';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import {
  LayoutDashboard, LayoutGrid, Wheat, FlaskConical, Sprout, GitMerge, BarChart3,
  Dna, Settings, TestTube2, Shield, Package, Truck, FileCheck, FileText,
  Building2, RefreshCw, Globe, Target, Cpu, Rocket, BookOpen, Eye,
  Pin, PinOff, GripVertical, Minus, MoreHorizontal, Home, Search,
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

interface MahasarthiDockProps {
  onBrowserOpen: () => void;
  onSearchOpen: () => void;
  onNavigate?: () => void;
  isMobile?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function MahasarthiDock({ onBrowserOpen, onSearchOpen, onNavigate, isMobile = false }: MahasarthiDockProps) {
  const location = useLocation();
  const activeWorkspace = useActiveWorkspace();
  const activeWorkspaceId = useWorkspaceStore(state => state.activeWorkspaceId);
  const { pinnedItems, recentItems, unpinItem, reorderPinned } = useDockStore();

  // Filter items by active workspace
  const workspacePinnedItems = pinnedItems.filter(item => 
    !activeWorkspaceId || isRouteInWorkspace(item.path, activeWorkspaceId)
  );

  const workspaceRecentItems = recentItems.filter(item => 
    !activeWorkspaceId || isRouteInWorkspace(item.path, activeWorkspaceId)
  );
  
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Drag handlers for reordering (desktop only)
  const handleDragStart = useCallback((index: number) => {
    setDraggedIndex(index);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    setDragOverIndex(index);
  }, []);

  const handleDrop = useCallback((index: number) => {
    if (draggedIndex !== null && draggedIndex !== index) {
      reorderPinned(draggedIndex, index);
    }
    setDraggedIndex(null);
    setDragOverIndex(null);
  }, [draggedIndex, reorderPinned]);

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  }, []);

  // ========================================================================
  // Mobile Bottom Tab Bar
  // ========================================================================
  if (isMobile) {
    // Show top 4 pinned items + More button
    const mobileItems = workspacePinnedItems.slice(0, 4);
    
    return (
      <nav 
        className="fixed bottom-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur-lg border-t border-slate-700/50 safe-area-pb"
        role="navigation"
        aria-label="Mobile navigation"
      >
        <div className="flex items-center justify-around h-16 px-2">
          {/* Home/Dashboard - always first */}
          <Link
            to="/dashboard"
            onClick={onNavigate}
            className={cn(
              'flex flex-col items-center justify-center flex-1 py-2 rounded-lg transition-colors',
              location.pathname === '/dashboard'
                ? 'text-emerald-400'
                : 'text-slate-400 active:bg-white/5'
            )}
            aria-label="Dashboard"
            aria-current={location.pathname === '/dashboard' ? 'page' : undefined}
          >
            <Home className="w-5 h-5" strokeWidth={1.75} />
            <span className="text-[10px] mt-1 font-medium">Home</span>
          </Link>

          {/* Pinned items (max 3 to leave room for Home and More) */}
          {mobileItems.slice(0, 3).map((item) => {
            const IconComponent = getIcon(item.icon);
            const isActive = location.pathname === item.path || 
                            location.pathname.startsWith(item.path + '/');
            // Truncate label for mobile
            const shortLabel = item.label.length > 8 ? item.label.slice(0, 7) + '…' : item.label;

            return (
              <Link
                key={item.id}
                to={item.path}
                onClick={onNavigate}
                className={cn(
                  'flex flex-col items-center justify-center flex-1 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'text-emerald-400'
                    : 'text-slate-400 active:bg-white/5'
                )}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
              >
                <IconComponent className="w-5 h-5" strokeWidth={1.75} />
                <span className="text-[10px] mt-1 font-medium">{shortLabel}</span>
              </Link>
            );
          })}

          {/* More button - opens browser */}
          <button
            onClick={onBrowserOpen}
            className="flex flex-col items-center justify-center flex-1 py-2 rounded-lg text-slate-400 active:bg-white/5 transition-colors"
            aria-label="More pages"
          >
            <MoreHorizontal className="w-5 h-5" strokeWidth={1.75} />
            <span className="text-[10px] mt-1 font-medium">More</span>
          </button>
        </div>
      </nav>
    );
  }

  // ========================================================================
  // Desktop Vertical Dock
  // ========================================================================
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex flex-col h-full py-2 px-1">
        {/* Workspace Indicator */}
        {activeWorkspace && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onBrowserOpen}
                className={cn(
                  'flex items-center justify-center p-2.5 mb-2 rounded-lg transition-all',
                  'bg-gradient-to-br text-white shadow-md',
                  activeWorkspace.color
                )}
                aria-label={`Current workspace: ${activeWorkspace.name}. Click to open browser.`}
              >
                <span className="text-lg font-bold">
                  {activeWorkspace.name.charAt(0)}
                </span>
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-slate-800 text-slate-100 border-slate-700">
              <div className="text-xs">
                <div className="font-medium">{activeWorkspace.name}</div>
                <div className="text-slate-400">Click to browse all pages</div>
              </div>
            </TooltipContent>
          </Tooltip>
        )}

        {/* Search Trigger */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={onSearchOpen}
              className={cn(
                'flex items-center justify-center p-2.5 mb-2 rounded-lg transition-all',
                'bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200',
                'border border-white/10'
              )}
              aria-label="Search pages (⌘K)"
            >
              <span className="text-xs font-mono">⌘K</span>
            </button>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-slate-800 text-slate-100 border-slate-700">
            Search pages
          </TooltipContent>
        </Tooltip>

        {/* Pinned Items */}
        <div className="flex-1 space-y-1">
          {workspacePinnedItems.length === 0 ? (
            /* Empty state for pinned items */
            <div className="flex flex-col items-center justify-center py-4 px-2 text-center">
              <Pin className="w-5 h-5 text-slate-600 mb-2" />
              <p className="text-[10px] text-slate-500 leading-tight">
                Pin pages for quick access
              </p>
            </div>
          ) : (
            workspacePinnedItems.map((item, index) => {
            const IconComponent = getIcon(item.icon);
            const isActive = location.pathname === item.path || 
                            location.pathname.startsWith(item.path + '/');
            const isDragging = draggedIndex === index;
            const isDragOver = dragOverIndex === index;

            return (
              <ContextMenu key={item.id}>
                <ContextMenuTrigger>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        to={item.path}
                        onClick={onNavigate}
                        draggable
                        onDragStart={() => handleDragStart(index)}
                        onDragOver={(e) => handleDragOver(e, index)}
                        onDrop={() => handleDrop(index)}
                        onDragEnd={handleDragEnd}
                        className={cn(
                          'relative flex items-center justify-center p-2.5 rounded-lg',
                          'transition-all duration-150 ease-out',
                          isActive
                            ? 'bg-emerald-500/15 text-emerald-400'
                            : 'text-slate-400 hover:bg-white/5 hover:text-slate-200',
                          isDragging && 'opacity-50 scale-95',
                          isDragOver && 'ring-2 ring-emerald-500/50'
                        )}
                        aria-label={item.label}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <IconComponent className={cn(
                          'w-5 h-5',
                          'transition-transform duration-150 ease-out',
                          isActive && 'scale-110'
                        )} strokeWidth={1.75} />
                        
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
                    <TooltipContent side="right" className="bg-slate-800 text-slate-100 border-slate-700">
                      <div className="flex items-center gap-2">
                        <span>{item.label}</span>
                        <Pin className="w-3 h-3 text-emerald-400" />
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </ContextMenuTrigger>
                <ContextMenuContent className="bg-slate-800 border-slate-700 text-slate-200">
                  <ContextMenuItem 
                    onClick={() => unpinItem(item.path)}
                    className="hover:bg-slate-700 focus:bg-slate-700"
                  >
                    <PinOff className="w-4 h-4 mr-2" />
                    Unpin from dock
                  </ContextMenuItem>
                  <ContextMenuSeparator className="bg-slate-700" />
                  <ContextMenuItem disabled className="text-slate-500">
                    <GripVertical className="w-4 h-4 mr-2" />
                    Drag to reorder
                  </ContextMenuItem>
                </ContextMenuContent>
              </ContextMenu>
            );
          })
          )}
        </div>

        {/* Separator */}
        {workspaceRecentItems.length > 0 && (
          <div className="flex items-center justify-center py-2">
            <Minus className="w-4 h-4 text-slate-600" />
          </div>
        )}

        {/* Recent Items */}
        <div className="space-y-1">
          {workspaceRecentItems.map((item) => {
            const IconComponent = getIcon(item.icon);
            const isActive = location.pathname === item.path;

            return (
              <Tooltip key={item.id}>
                <TooltipTrigger asChild>
                  <Link
                    to={item.path}
                    onClick={onNavigate}
                    className={cn(
                      'relative flex items-center justify-center p-2.5 rounded-lg transition-all duration-200',
                      isActive
                        ? 'bg-slate-500/15 text-slate-300'
                        : 'text-slate-500 hover:bg-white/5 hover:text-slate-400'
                    )}
                    aria-label={`Recent: ${item.label}`}
                  >
                    <IconComponent className="w-4 h-4" strokeWidth={1.75} />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" className="bg-slate-800 text-slate-100 border-slate-700">
                  <div className="text-xs">
                    <div>{item.label}</div>
                    <div className="text-slate-400">Recent</div>
                  </div>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>

        {/* STRATA Trigger */}
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={onBrowserOpen}
              className={cn(
                'flex items-center justify-center p-2.5 mt-2 rounded-lg transition-all',
                'bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200',
                'border border-white/10'
              )}
              aria-label="Open STRATA navigation"
            >
              <LayoutGrid className="w-5 h-5" strokeWidth={1.75} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-slate-800 text-slate-100 border-slate-700">
            STRATA
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

export default MahasarthiDock;
