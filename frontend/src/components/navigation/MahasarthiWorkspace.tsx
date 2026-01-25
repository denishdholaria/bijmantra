/**
 * Workspace Switcher Component
 * 
 * Dropdown in header for switching between workspaces.
 * Shows current workspace and allows quick switching.
 * Supports both system workspaces and custom (MyWorkspace) workspaces.
 * 
 * Phase 5 Polish:
 * - Full keyboard navigation
 * - ARIA labels and roles
 * - Screen reader announcements
 * - Focus management
 * 
 * @see docs/gupt/archieve/GATEWAY-WORKSPACE.md for specification
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkspaceIcon } from '@/lib/workspace-icons';
import { 
  Wheat, 
  Factory, 
  Microscope, 
  Building2, 
  Settings,
  ChevronDown,
  Check,
  Star,
  LayoutGrid,
  Clock,
  Sparkles,
  User,
  CloudSun,
  Droplets,
  Mountain,
  Leaf,
  type LucideIcon,
} from 'lucide-react';
import { 
  useWorkspaceStore, 
  useActiveWorkspace, 
  useAllWorkspaces 
} from '@/store/workspaceStore';
import {
  useCustomWorkspaceStore,
  useCustomWorkspaces,
  useActiveCustomWorkspace,
} from '@/store/customWorkspaceStore';
import type { WorkspaceId } from '@/types/workspace';
import type { CustomWorkspace } from '@/types/customWorkspace';
import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Icon mapping for system workspaces
const workspaceIcons: Record<WorkspaceId, React.ElementType> = {
  breeding: Wheat,
  'seed-ops': Factory,
  research: Microscope,
  genebank: Building2,
  admin: Settings,
  atmosphere: CloudSun,
  hydrology: Droplets,
  lithosphere: Mountain,
  biosphere: Leaf,
};

// Gradient backgrounds for system workspace icons
const workspaceGradients: Record<WorkspaceId, string> = {
  breeding: 'from-green-500 to-emerald-600',
  'seed-ops': 'from-blue-500 to-indigo-600',
  research: 'from-purple-500 to-violet-600',
  genebank: 'from-amber-500 to-orange-600',
  admin: 'from-slate-500 to-gray-600',
  atmosphere: 'from-sky-400 to-blue-500',
  hydrology: 'from-blue-400 to-cyan-500',
  lithosphere: 'from-amber-700 to-orange-800',
  biosphere: 'from-emerald-400 to-green-500',
};

// Text colors for system workspace names
const workspaceTextColors: Record<WorkspaceId, string> = {
  breeding: 'text-green-600 dark:text-green-400',
  'seed-ops': 'text-blue-600 dark:text-blue-400',
  research: 'text-purple-600 dark:text-purple-400',
  genebank: 'text-amber-600 dark:text-amber-400',
  admin: 'text-slate-600 dark:text-slate-400',
  atmosphere: 'text-sky-600 dark:text-sky-400',
  hydrology: 'text-cyan-600 dark:text-cyan-400',
  lithosphere: 'text-amber-600 dark:text-amber-400',
  biosphere: 'text-emerald-600 dark:text-emerald-400',
};

// Color gradients for custom workspaces
const customWorkspaceGradients: Record<string, string> = {
  green: 'from-green-500 to-emerald-600',
  blue: 'from-blue-500 to-indigo-600',
  purple: 'from-purple-500 to-violet-600',
  amber: 'from-amber-500 to-orange-600',
  slate: 'from-slate-500 to-gray-600',
};

// Text colors for custom workspace names
const customWorkspaceTextColors: Record<string, string> = {
  green: 'text-green-600 dark:text-green-400',
  blue: 'text-blue-600 dark:text-blue-400',
  purple: 'text-purple-600 dark:text-purple-400',
  amber: 'text-amber-600 dark:text-amber-400',
  slate: 'text-slate-600 dark:text-slate-400',
};

// Get Lucide icon by name
function getIconByName(iconName: string): LucideIcon {
  return getWorkspaceIcon(iconName, Sparkles);
}

interface MahasarthiWorkspaceProps {
  /** Compact mode for mobile */
  compact?: boolean;
  /** Show label text */
  showLabel?: boolean;
}

export function MahasarthiWorkspace({ compact = false, showLabel = true }: MahasarthiWorkspaceProps) {
  const navigate = useNavigate();
  const workspaces = useAllWorkspaces();
  const activeWorkspace = useActiveWorkspace();
  const { 
    setActiveWorkspace, 
    setDefaultWorkspace,
    preferences,
    resetGateway 
  } = useWorkspaceStore();
  
  // Custom workspaces
  const customWorkspaces = useCustomWorkspaces();
  const activeCustomWorkspace = useActiveCustomWorkspace();
  const { 
    setActiveCustomWorkspace, 
    clearActiveCustomWorkspace 
  } = useCustomWorkspaceStore();
  
  const [isOpen, setIsOpen] = useState(false);
  const [announcement, setAnnouncement] = useState('');

  // Determine what's currently active
  const isCustomActive = activeCustomWorkspace !== null;
  const currentName = isCustomActive 
    ? activeCustomWorkspace.name 
    : activeWorkspace?.name || 'Select Workspace';

  // Announce workspace changes for screen readers
  useEffect(() => {
    if (isCustomActive && activeCustomWorkspace) {
      setAnnouncement(`Switched to ${activeCustomWorkspace.name} custom workspace`);
      const timer = setTimeout(() => setAnnouncement(''), 1000);
      return () => clearTimeout(timer);
    } else if (activeWorkspace) {
      setAnnouncement(`Switched to ${activeWorkspace.name} workspace`);
      const timer = setTimeout(() => setAnnouncement(''), 1000);
      return () => clearTimeout(timer);
    }
  }, [activeWorkspace, activeCustomWorkspace, isCustomActive]);

  const handleWorkspaceSelect = (workspaceId: WorkspaceId) => {
    const workspace = workspaces.find(w => w.id === workspaceId);
    if (workspace) {
      // Clear custom workspace when selecting system workspace
      clearActiveCustomWorkspace();
      setActiveWorkspace(workspaceId);
      navigate(workspace.landingRoute);
      setIsOpen(false);
    }
  };

  const handleCustomWorkspaceSelect = (customWorkspace: CustomWorkspace) => {
    setActiveCustomWorkspace(customWorkspace.id);
    // Navigate to first page in custom workspace
    if (customWorkspace.pageIds.length > 0) {
      // For now, just go to dashboard - the sidebar will show filtered pages
      navigate('/dashboard');
    }
    setIsOpen(false);
  };

  const handleSetDefault = (workspaceId: WorkspaceId, e: React.MouseEvent) => {
    e.stopPropagation();
    setDefaultWorkspace(workspaceId);
    setAnnouncement(`${workspaces.find(w => w.id === workspaceId)?.name} set as default workspace`);
  };

  const handleOpenGateway = () => {
    resetGateway();
    navigate('/gateway');
    setIsOpen(false);
  };

  // Get recent workspaces (excluding current)
  const recentWorkspaces = preferences.recentWorkspaces
    .filter(id => id !== activeWorkspace?.id)
    .slice(0, 3)
    .map(id => workspaces.find(w => w.id === id))
    .filter(Boolean);

  // Get icon for current workspace
  const getActiveIcon = () => {
    if (isCustomActive && activeCustomWorkspace) {
      return getIconByName(activeCustomWorkspace.icon);
    }
    if (activeWorkspace) {
      return workspaceIcons[activeWorkspace.id];
    }
    return LayoutGrid;
  };

  const getActiveGradient = () => {
    if (isCustomActive && activeCustomWorkspace) {
      return customWorkspaceGradients[activeCustomWorkspace.color] || customWorkspaceGradients.slate;
    }
    if (activeWorkspace) {
      return workspaceGradients[activeWorkspace.id];
    }
    return '';
  };

  const getActiveTextColor = () => {
    if (isCustomActive && activeCustomWorkspace) {
      return customWorkspaceTextColors[activeCustomWorkspace.color] || customWorkspaceTextColors.slate;
    }
    if (activeWorkspace) {
      return workspaceTextColors[activeWorkspace.id];
    }
    return 'text-gray-600 dark:text-gray-300';
  };

  const ActiveIcon = getActiveIcon();

  return (
    <>
      {/* Screen reader announcement */}
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
      >
        {announcement}
      </div>
      
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <button
            aria-label={`Current workspace: ${currentName}. Click to switch workspace.`}
            aria-haspopup="menu"
            aria-expanded={isOpen}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg transition-all",
              "hover:bg-gray-100 dark:hover:bg-slate-800",
              "focus:outline-none focus:ring-2 focus:ring-green-500/20",
              compact && "px-2"
            )}
          >
            {/* Workspace Icon */}
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              (isCustomActive || activeWorkspace)
                ? `bg-gradient-to-br ${getActiveGradient()}` 
                : "bg-gray-200 dark:bg-slate-700"
            )}>
              <ActiveIcon className="w-4 h-4 text-white" aria-hidden="true" />
            </div>
            
            {/* Workspace Name */}
            {showLabel && !compact && (
              <div className="hidden sm:block text-left">
                <p className={cn("text-sm font-medium", getActiveTextColor())}>
                  {currentName}
                </p>
                {isCustomActive && (
                  <p className="text-[10px] text-gray-500 dark:text-gray-400">Custom</p>
                )}
              </div>
            )}
            
            <ChevronDown className={cn(
              "w-4 h-4 text-gray-400 transition-transform",
              isOpen && "rotate-180"
            )} aria-hidden="true" />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="start" className="w-72" role="menu" aria-label="Workspace selection menu">
          <DropdownMenuLabel className="flex items-center gap-2">
            <LayoutGrid className="w-4 h-4" aria-hidden="true" />
            <span>Switch Workspace</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {/* Custom Workspaces Section */}
          {customWorkspaces.length > 0 && (
            <>
              <DropdownMenuLabel className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <User className="w-3 h-3" aria-hidden="true" />
                My Workspaces
              </DropdownMenuLabel>
              {customWorkspaces.map((customWs) => {
                const CustomIcon = getIconByName(customWs.icon);
                const isActive = isCustomActive && activeCustomWorkspace?.id === customWs.id;
                const gradient = customWorkspaceGradients[customWs.color] || customWorkspaceGradients.slate;
                
                return (
                  <DropdownMenuItem
                    key={customWs.id}
                    onClick={() => handleCustomWorkspaceSelect(customWs)}
                    className={cn(
                      "flex items-center gap-3 py-2 cursor-pointer",
                      isActive && "bg-gray-100 dark:bg-slate-800"
                    )}
                    role="menuitem"
                    aria-label={`Switch to ${customWs.name} custom workspace with ${customWs.pageIds.length} pages${isActive ? ' (current)' : ''}`}
                    aria-current={isActive ? 'true' : undefined}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center",
                      `bg-gradient-to-br ${gradient}`
                    )}>
                      <CustomIcon className="w-4 h-4 text-white" aria-hidden="true" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{customWs.name}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {customWs.pageIds.length} pages
                      </p>
                    </div>
                    {isActive && (
                      <Check className="w-4 h-4 text-green-500" aria-label="Current workspace" />
                    )}
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
            </>
          )}

          {/* Recent Workspaces */}
          {recentWorkspaces.length > 0 && !isCustomActive && (
            <>
              <DropdownMenuLabel className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" aria-hidden="true" />
                Recent
              </DropdownMenuLabel>
              {recentWorkspaces.map((workspace) => {
                if (!workspace) return null;
                const Icon = workspaceIcons[workspace.id];
                const isDefault = preferences.defaultWorkspace === workspace.id;
                
                return (
                  <DropdownMenuItem
                    key={workspace.id}
                    onClick={() => handleWorkspaceSelect(workspace.id)}
                    className="flex items-center gap-3 py-2 cursor-pointer"
                    role="menuitem"
                    aria-label={`Switch to ${workspace.name}${isDefault ? ' (default)' : ''}`}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center",
                      `bg-gradient-to-br ${workspaceGradients[workspace.id]}`
                    )}>
                      <Icon className="w-4 h-4 text-white" aria-hidden="true" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{workspace.name}</p>
                    </div>
                    {isDefault && (
                      <Star className="w-4 h-4 text-amber-500 fill-amber-500" aria-label="Default workspace" />
                    )}
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
            </>
          )}

          {/* All System Workspaces */}
          <DropdownMenuLabel className="text-xs text-gray-500 dark:text-gray-400">
            System Workspaces
          </DropdownMenuLabel>
          {workspaces.map((workspace) => {
            const Icon = workspaceIcons[workspace.id];
            const isActive = !isCustomActive && activeWorkspace?.id === workspace.id;
            const isDefault = preferences.defaultWorkspace === workspace.id;
            
            return (
              <DropdownMenuItem
                key={workspace.id}
                onClick={() => handleWorkspaceSelect(workspace.id)}
                className={cn(
                  "flex items-center gap-3 py-2 cursor-pointer group",
                  isActive && "bg-gray-100 dark:bg-slate-800"
                )}
                role="menuitem"
                aria-label={`${workspace.name}: ${workspace.description}${isActive ? ' (current)' : ''}${isDefault ? ' (default)' : ''}`}
                aria-current={isActive ? 'true' : undefined}
              >
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center",
                  `bg-gradient-to-br ${workspaceGradients[workspace.id]}`
                )}>
                  <Icon className="w-4 h-4 text-white" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{workspace.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {workspace.description}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {isDefault && (
                    <Star className="w-4 h-4 text-amber-500 fill-amber-500" aria-label="Default" />
                  )}
                  {isActive && (
                    <Check className="w-4 h-4 text-green-500" aria-label="Current workspace" />
                  )}
                  {!isDefault && (
                    <button
                      onClick={(e) => handleSetDefault(workspace.id, e)}
                      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Set as default"
                      aria-label={`Set ${workspace.name} as default workspace`}
                    >
                      <Star className="w-3.5 h-3.5 text-gray-400 hover:text-amber-500" aria-hidden="true" />
                    </button>
                  )}
                </div>
              </DropdownMenuItem>
            );
          })}

          <DropdownMenuSeparator />

          {/* Open Gateway */}
          <DropdownMenuItem
            onClick={handleOpenGateway}
            className="flex items-center gap-3 py-2 cursor-pointer text-gray-600 dark:text-gray-300"
            role="menuitem"
            aria-label="Open full workspace gateway for detailed selection"
          >
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gray-100 dark:bg-slate-700">
              <LayoutGrid className="w-4 h-4" aria-hidden="true" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Open Workspace Gateway</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Full workspace selection view
              </p>
            </div>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}

export default MahasarthiWorkspace;
