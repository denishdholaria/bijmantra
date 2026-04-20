/**
 * Command Palette Component
 * Global search and navigation with ⌘K / Ctrl+K
 * 
 * MIGRATED: Now uses derived navigation from single source of truth.
 * See: framework/registry/navigation-derived.ts
 * 
 * Validates: Requirements 9.4, 9.5
 */

import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Command } from "cmdk";

import {
  MessageSquare,
  Plus,
  Sprout,
  GitMerge,
  ScanLine,
  Search,
  Sprout as SproutIcon,
} from "lucide-react";

import {
  derivedCommands,
  type CommandPaletteItem,
} from "@/framework/registry/navigation-derived";

// Quick actions - these are action shortcuts, not navigation items
const quickActions = [
  {
    id: "new-observation",
    label: "Add Observation",
    icon: Plus,
    action: "navigate",
    path: "/observations/collect",
  },
  {
    id: "new-germplasm",
    label: "Add Germplasm",
    icon: Sprout,
    action: "navigate",
    path: "/germplasm/new",
  },
  {
    id: "new-cross",
    label: "Create Cross",
    icon: GitMerge,
    action: "navigate",
    path: "/crosses/new",
  },
  {
    id: "scan",
    label: "Scan Barcode",
    icon: ScanLine,
    action: "navigate",
    path: "/scanner",
  },
  {
    id: "ai-chat",
    label: "Ask REEVU",
    icon: MessageSquare,
    action: "navigate",
    path: "/ai-assistant",
  },
];

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [recentItems, setRecentItems] = useState<string[]>([]);

  // Use derived commands from single source of truth
  const allCommands = useMemo(() => derivedCommands, []);

  // Load recent items from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("bijmantra-recent-nav");
    if (stored) {
      setRecentItems(JSON.parse(stored));
    }
  }, [open]);

  const handleSelect = useCallback(
    (path: string) => {
      // Update recent items
      const updated = [path, ...recentItems.filter((p) => p !== path)].slice(
        0,
        5
      );
      localStorage.setItem("bijmantra-recent-nav", JSON.stringify(updated));
      setRecentItems(updated);

      onOpenChange(false);
      setSearch("");
      navigate(path);
    },
    [navigate, onOpenChange, recentItems]
  );

  // Get recent nav items from derived commands
  const recentNavItems = useMemo(() => {
    return recentItems
      .map((path) => allCommands.find((item) => item.route === path))
      .filter(Boolean) as CommandPaletteItem[];
  }, [recentItems, allCommands]);

  // Group items by division for organized display
  const groupedItems = useMemo(() => {
    return allCommands.reduce(
      (acc, item) => {
        const section = item.divisionId || "Other";
        if (!acc[section]) acc[section] = [];
        acc[section].push(item);
        return acc;
      },
      {} as Record<string, CommandPaletteItem[]>
    );
  }, [allCommands]);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={onOpenChange}
      label="Global Command Menu"
      className="fixed inset-0 z-[100]"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-2xl">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-gray-200 dark:border-slate-700 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <Search
              className="w-5 h-5 text-gray-400 dark:text-gray-500"
              strokeWidth={1.5}
            />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search pages, tools, or type a command..."
              className="flex-1 bg-transparent outline-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
              autoFocus
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-700 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <Command.List className="max-h-[60vh] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-gray-500">
              No results found. Try a different search term.
            </Command.Empty>

            {/* Quick Actions */}
            {!search && (
              <Command.Group heading="Quick Actions" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Quick Actions
                </div>
                {quickActions.map((action) => (
                  <Command.Item
                    key={action.id}
                    value={action.label}
                    onSelect={() => handleSelect(action.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-green-50 dark:hover:bg-green-900/30 hover:text-green-700 dark:hover:text-green-400 data-[selected=true]:bg-green-50 dark:data-[selected=true]:bg-green-900/30 data-[selected=true]:text-green-700 dark:data-[selected=true]:text-green-400"
                  >
                    <action.icon className="w-5 h-5" strokeWidth={1.75} />
                    <span className="font-medium">{action.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Recent */}
            {!search && recentNavItems.length > 0 && (
              <Command.Group heading="Recent" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Recent
                </div>
                {recentNavItems.map((item) => (
                  <Command.Item
                    key={`recent-${item.id}`}
                    value={`recent ${item.title}`}
                    onSelect={() => handleSelect(item.route)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                  >
                    <span className="w-5 h-5 flex items-center justify-center text-gray-400">
                      {item.icon ? (
                        <span className="text-xs">{item.icon.substring(0, 2)}</span>
                      ) : (
                        <span className="text-xs">•</span>
                      )}
                    </span>
                    <span>{item.title}</span>
                    <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">
                      {item.subtitle}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* All Sections - Grouped by Division */}
            {Object.entries(groupedItems).map(([section, items]) => (
              <Command.Group key={section} heading={section} className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {section}
                </div>
                {items.map((item) => (
                  <Command.Item
                    key={item.id}
                    value={`${item.title} ${item.subtitle || ""} ${(item.keywords || []).join(" ")}`}
                    onSelect={() => handleSelect(item.route)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                  >
                    <span className="w-5 h-5 flex items-center justify-center text-gray-400">
                      {item.icon ? (
                        <span className="text-xs">{item.icon.substring(0, 2)}</span>
                      ) : (
                        <span className="text-xs">•</span>
                      )}
                    </span>
                    <span>{item.title}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ↑↓
                </kbd>{" "}
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ↵
                </kbd>{" "}
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ESC
                </kbd>{" "}
                Close
              </span>
            </div>
            <span>
              <SproutIcon className="inline w-3 h-3 mr-1" strokeWidth={2.5} />{" "}
              Bijmantra
            </span>
          </div>
        </div>
      </div>
    </Command.Dialog>
  );
}
