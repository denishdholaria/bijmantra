/**
 * Hybrid Dock Navigation Component
 *
 * macOS-style vertical dock on the left side with:
 * - Pinned favorites at top
 * - Division icons below
 * - Settings at bottom
 * - Hover tooltips
 * - Active indicator
 */

import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useFavorites, FavoriteItem } from "@/hooks/useFavorites";
import { useWorkspace, WorkspaceType, WORKSPACES } from "@/hooks/useWorkspace";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sprout,
  Wheat,
  Warehouse,
  Globe,
  Sun,
  Radio,
  Building2,
  Factory,
  Rocket,
  Plug,
  BookOpen,
  Wrench,
  Settings,
  Home,
  LayoutDashboard,
  Plus,
  Star,
  ChevronRight,
  FlaskConical,
  Microscope,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

// Icon mapping for divisions
const divisionIcons: Record<string, LucideIcon> = {
  home: Home,
  "plant-sciences": Sprout,
  "seed-bank": Warehouse,
  "earth-systems": Globe,
  environment: Globe,
  "sun-earth-systems": Sun,
  "sensor-networks": Radio,
  "seed-operations": Factory,
  "seed-commerce": Building2,
  commercial: Building2,
  "space-research": Rocket,
  integrations: Plug,
  knowledge: BookOpen,
  tools: Wrench,
  settings: Settings,
};

// Icon mapping for favorite types
const favoriteIcons: Record<FavoriteItem["type"], LucideIcon> = {
  program: FlaskConical,
  trial: Microscope,
  study: BarChart3,
  germplasm: Wheat,
  accession: Warehouse,
  page: LayoutDashboard,
  report: BarChart3,
  division: Sprout,
};

// Workspace icons (using new WorkspaceId values)
const workspaceIcons: Record<WorkspaceType, LucideIcon> = {
  breeding: Wheat,
  "seed-ops": Factory,
  research: Microscope,
  genebank: Building2,
  admin: Settings,
};

// Division colors for active state
const divisionColors: Record<string, string> = {
  home: "bg-blue-500",
  "plant-sciences": "bg-green-500",
  "seed-bank": "bg-amber-500",
  "earth-systems": "bg-cyan-500",
  environment: "bg-cyan-500",
  "sun-earth-systems": "bg-orange-500",
  "sensor-networks": "bg-teal-500",
  "seed-operations": "bg-indigo-500",
  "seed-commerce": "bg-indigo-500",
  commercial: "bg-purple-500",
  "space-research": "bg-violet-500",
  integrations: "bg-slate-500",
  knowledge: "bg-pink-500",
  tools: "bg-gray-500",
  settings: "bg-zinc-500",
};

interface DockProps {
  className?: string;
  onDivisionSelect?: (divisionId: string) => void;
}

export function Dock({ className, onDivisionSelect }: DockProps) {
  const location = useLocation();
  const { favorites, removeFavorite, canAddMore } = useFavorites();
  const {
    workspace,
    filteredDivisions,
    setWorkspace,
    workspaces,
    currentWorkspace,
  } = useWorkspace();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Get current active division from path
  const getActiveDivision = () => {
    const path = location.pathname;
    if (path === "/" || path === "/dashboard") return "home";

    for (const div of filteredDivisions) {
      if (path.startsWith(div.route)) return div.id;
    }
    return null;
  };

  const activeDivision = getActiveDivision();
  const WorkspaceIcon = workspaceIcons[currentWorkspace];

  return (
    <TooltipProvider delayDuration={200}>
      <div
        className={cn(
          "flex flex-col h-full w-14 bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800",
          className
        )}
      >
        {/* Logo */}
        <div className="h-14 flex items-center justify-center border-b border-gray-200 dark:border-slate-800">
          <Link to="/dashboard" className="group">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow overflow-hidden">
              <img
                src="/icons/icon-72x72.png"
                alt="Bijmantra"
                className="w-full h-full object-contain"
              />
            </div>
          </Link>
        </div>

        {/* Workspace Switcher */}
        <div className="px-2 py-2 border-b border-gray-200 dark:border-slate-800">
          <DropdownMenu>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenuTrigger asChild>
                  <button
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                      "bg-gradient-to-br",
                      workspace.color,
                      "text-white shadow-md hover:shadow-lg"
                    )}
                  >
                    <WorkspaceIcon className="h-5 w-5" />
                  </button>
                </DropdownMenuTrigger>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={8}>
                <p className="font-medium">{workspace.name}</p>
                <p className="text-xs text-muted-foreground">
                  {workspace.description}
                </p>
              </TooltipContent>
            </Tooltip>
            <DropdownMenuContent side="right" align="start" className="w-56">
              <DropdownMenuLabel>Switch Workspace</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {workspaces.map((ws) => {
                const WsIcon = workspaceIcons[ws.id];
                return (
                  <DropdownMenuItem
                    key={ws.id}
                    onClick={() => setWorkspace(ws.id)}
                    className={cn(
                      "flex items-center gap-2 cursor-pointer",
                      currentWorkspace === ws.id && "bg-accent"
                    )}
                  >
                    <div
                      className={cn(
                        "w-6 h-6 rounded-md flex items-center justify-center bg-gradient-to-br text-white",
                        ws.color
                      )}
                    >
                      <WsIcon className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{ws.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {ws.description}
                      </p>
                    </div>
                    {currentWorkspace === ws.id && (
                      <span className="text-green-500">✓</span>
                    )}
                  </DropdownMenuItem>
                );
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Favorites Section */}
        {favorites.length > 0 && (
          <div className="px-2 py-2 border-b border-gray-200 dark:border-slate-800">
            <div className="flex items-center justify-center mb-1">
              <Star className="h-3 w-3 text-yellow-500" />
            </div>
            <div className="space-y-1">
              {favorites.slice(0, 4).map((fav) => {
                const FavIcon = favoriteIcons[fav.type] || LayoutDashboard;
                const isActive = location.pathname === fav.route;
                return (
                  <Tooltip key={`${fav.type}-${fav.id}`}>
                    <TooltipTrigger asChild>
                      <Link
                        to={fav.route}
                        className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center transition-all relative group",
                          isActive
                            ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                            : "hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400"
                        )}
                        onMouseEnter={() => setHoveredItem(fav.id)}
                        onMouseLeave={() => setHoveredItem(null)}
                      >
                        <FavIcon className="h-5 w-5" />
                        {isActive && (
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-yellow-500 rounded-r-full" />
                        )}
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="right" sideOffset={8}>
                      <p className="font-medium">{fav.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">
                        {fav.type}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </div>
        )}

        {/* Divisions */}
        <div className="flex-1 px-2 py-2 overflow-y-auto">
          <div className="space-y-1">
            {filteredDivisions.map((division) => {
              const DivIcon = divisionIcons[division.id] || Sprout;
              const isActive = activeDivision === division.id;
              const bgColor = divisionColors[division.id] || "bg-gray-500";

              return (
                <Tooltip key={division.id}>
                  <TooltipTrigger asChild>
                    <Link
                      to={division.route}
                      onClick={() => onDivisionSelect?.(division.id)}
                      className={cn(
                        "w-10 h-10 rounded-xl flex items-center justify-center transition-all relative group",
                        isActive
                          ? `${bgColor} text-white shadow-md`
                          : "hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400"
                      )}
                      onMouseEnter={() => setHoveredItem(division.id)}
                      onMouseLeave={() => setHoveredItem(null)}
                    >
                      <DivIcon className="h-5 w-5" />
                      {isActive && (
                        <div
                          className={cn(
                            "absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full",
                            bgColor
                          )}
                        />
                      )}
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent
                    side="right"
                    sideOffset={8}
                    className="max-w-xs"
                  >
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{division.name}</p>
                      {division.status !== "active" && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-gray-100 dark:bg-gray-800 uppercase">
                          {division.status}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {division.description}
                    </p>
                    {division.sections && division.sections.length > 0 && (
                      <div className="mt-1 pt-1 border-t border-gray-200 dark:border-gray-700">
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <ChevronRight className="h-3 w-3" />
                          {division.sections.length} sections
                        </p>
                      </div>
                    )}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="px-2 py-2 border-t border-gray-200 dark:border-slate-800 space-y-1">
          {/* Add Favorite */}
          {canAddMore && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="w-10 h-10 rounded-xl flex items-center justify-center text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-800 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                  <Plus className="h-5 w-5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={8}>
                <p>Add to favorites</p>
                <p className="text-xs text-muted-foreground">
                  Star items to pin them here
                </p>
              </TooltipContent>
            </Tooltip>
          )}

          {/* Settings */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Link
                to="/settings"
                className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                  location.pathname === "/settings"
                    ? "bg-zinc-500 text-white shadow-md"
                    : "hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-400"
                )}
              >
                <Settings className="h-5 w-5" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={8}>
              <p>Settings</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default Dock;
