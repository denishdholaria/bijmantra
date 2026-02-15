/**
 * Curated Workspace Icons
 * 
 * This module provides a curated set of icons for custom workspaces.
 * Instead of importing all 1,500+ lucide-react icons (~866KB),
 * we only import the ~40 icons actually used for workspace customization.
 * 
 * Savings: ~800KB from the main bundle
 */

import {
  // Agriculture & Plants
  Sprout,
  Wheat,
  Leaf,
  TreeDeciduous,
  Flower2,
  // Science & Lab
  FlaskConical,
  Microscope,
  Dna,
  TestTube,
  Beaker,
  // Charts & Analytics
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  Activity,
  // Industry & Logistics
  Factory,
  Building2,
  Warehouse,
  Package,
  Truck,
  // Documents & Data
  ClipboardList,
  FileText,
  FolderOpen,
  Database,
  Server,
  // Weather & Environment
  Sun,
  CloudSun,
  Droplets,
  Thermometer,
  Wind,
  // Actions & Focus
  Target,
  Crosshair,
  Focus,
  Zap,
  Rocket,
  // Users & Settings
  Users,
  UserCheck,
  Shield,
  Lock,
  Settings,
  // Fallbacks
  Folder,
  File,
  Plus,
  MoreVertical,
  Copy,
  Trash2,
  Sparkles,
} from 'lucide-react';

import type { LucideIcon } from 'lucide-react';

/**
 * Map of icon names to their components.
 * Only includes icons available for workspace customization.
 */
export const WORKSPACE_ICON_MAP: Record<string, LucideIcon> = {
  // Agriculture & Plants
  Sprout,
  Wheat,
  Leaf,
  TreeDeciduous,
  Flower2,
  // Science & Lab
  FlaskConical,
  Microscope,
  Dna,
  TestTube,
  Beaker,
  // Charts & Analytics
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  Activity,
  // Industry & Logistics
  Factory,
  Building2,
  Warehouse,
  Package,
  Truck,
  // Documents & Data
  ClipboardList,
  FileText,
  FolderOpen,
  Database,
  Server,
  // Weather & Environment
  Sun,
  CloudSun,
  Droplets,
  Thermometer,
  Wind,
  // Actions & Focus
  Target,
  Crosshair,
  Focus,
  Zap,
  Rocket,
  // Users & Settings
  Users,
  UserCheck,
  Shield,
  Lock,
  Settings,
  // Fallbacks (used in UI)
  Folder,
  File,
  Plus,
  MoreVertical,
  Copy,
  Trash2,
  Sparkles,
};

/**
 * Get an icon component by name.
 * Returns a fallback icon if the name is not found.
 * 
 * @param iconName - The name of the icon (e.g., 'Wheat', 'Microscope')
 * @param fallback - Optional fallback icon (defaults to Folder)
 * @returns The icon component
 */
export function getWorkspaceIcon(iconName: string, fallback: LucideIcon = Folder): LucideIcon {
  return WORKSPACE_ICON_MAP[iconName] || fallback;
}

/**
 * Check if an icon name is valid (exists in our curated set)
 */
export function isValidWorkspaceIcon(iconName: string): boolean {
  return iconName in WORKSPACE_ICON_MAP;
}

// Re-export commonly used fallback icons for convenience
export { Folder, File, Plus, MoreVertical, Copy, Trash2, Sparkles };
