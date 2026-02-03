/**
 * Mahasarthi Dock Store (Zustand)
 * 
 * Manages personal dock state for the Mahasarthi navigation system.
 * Persists pinned pages and recent pages to localStorage.
 * 
 * @see docs/gupt/1-MAHASARTHI.md for full specification
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// Types
// ============================================================================

export interface DockItem {
  id: string;
  path: string;
  label: string;
  icon: string;
  isPinned: boolean;
  lastVisited?: string;
  visitCount?: number;
}

export interface DockPreferences {
  maxPinned: number;
  maxRecent: number;
  showLabels: boolean;
  compactMode: boolean;
}

interface DockState {
  // State
  pinnedItems: DockItem[];
  recentItems: DockItem[];
  preferences: DockPreferences;
  hasAppliedRoleDefaults: boolean; // Track if role defaults have been applied
  
  // Actions
  pinItem: (item: Omit<DockItem, 'isPinned'>) => void;
  unpinItem: (path: string) => void;
  togglePin: (item: Omit<DockItem, 'isPinned'>) => void;
  reorderPinned: (fromIndex: number, toIndex: number) => void;
  recordVisit: (item: Omit<DockItem, 'isPinned' | 'lastVisited' | 'visitCount'>) => void;
  clearRecent: () => void;
  setPreferences: (prefs: Partial<DockPreferences>) => void;
  applyRoleDefaults: (role: string) => void; // Apply role-based dock defaults
  resetToDefaults: (role?: string) => void; // Reset dock to defaults
  
  // Queries
  isPinned: (path: string) => boolean;
  getDockItems: () => DockItem[];
}

// ============================================================================
// Default Docks by Role
// ============================================================================

export const defaultDocksByRole: Record<string, Omit<DockItem, 'isPinned'>[]> = {
  breeder: [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { id: 'programs', path: '/programs', label: 'Programs', icon: 'Wheat' },
    { id: 'trials', path: '/trials', label: 'Trials', icon: 'FlaskConical' },
    { id: 'germplasm', path: '/germplasm', label: 'Germplasm', icon: 'Sprout' },
    { id: 'crosses', path: '/crosses', label: 'Crosses', icon: 'GitMerge' },
    { id: 'statistics', path: '/statistics', label: 'Statistics', icon: 'BarChart3' },
    { id: 'breeding-values', path: '/breeding-values', label: 'Breeding Values', icon: 'Dna' },
    { id: 'settings', path: '/settings', label: 'Settings', icon: 'Settings' },
  ],
  seed_company: [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { id: 'lab-samples', path: '/seed-operations/samples', label: 'Lab Samples', icon: 'TestTube2' },
    { id: 'quality-gate', path: '/seed-operations/quality-gate', label: 'Quality Gate', icon: 'Shield' },
    { id: 'seed-lots', path: '/seed-operations/lots', label: 'Seed Lots', icon: 'Package' },
    { id: 'dispatch', path: '/seed-operations/dispatch', label: 'Dispatch', icon: 'Truck' },
    { id: 'certificates', path: '/seed-operations/certificates', label: 'Certificates', icon: 'FileCheck' },
    { id: 'reports', path: '/reports', label: 'Reports', icon: 'FileText' },
    { id: 'settings', path: '/settings', label: 'Settings', icon: 'Settings' },
  ],
  genebank_curator: [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { id: 'vault', path: '/seed-bank/vault', label: 'Vault Management', icon: 'Building2' },
    { id: 'accessions', path: '/seed-bank/accessions', label: 'Accessions', icon: 'Package' },
    { id: 'viability', path: '/seed-bank/viability', label: 'Viability Testing', icon: 'TestTube2' },
    { id: 'regeneration', path: '/seed-bank/regeneration', label: 'Regeneration', icon: 'RefreshCw' },
    { id: 'grin-search', path: '/seed-bank/grin-search', label: 'GRIN Search', icon: 'Globe' },
    { id: 'conservation', path: '/seed-bank/conservation', label: 'Conservation', icon: 'Shield' },
    { id: 'settings', path: '/settings', label: 'Settings', icon: 'Settings' },
  ],
  researcher: [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { id: 'genomic-selection', path: '/genomic-selection', label: 'Genomic Selection', icon: 'Dna' },
    { id: 'wasm-genomics', path: '/wasm-genomics', label: 'WASM Analytics', icon: 'Cpu' },
    { id: 'qtl-mapping', path: '/qtl-mapping', label: 'QTL Mapping', icon: 'Target' },
    { id: 'gxe', path: '/gxe-interaction', label: 'G×E Analysis', icon: 'Globe' },
    { id: 'space-research', path: '/space-research', label: 'Space Research', icon: 'Rocket' },
    { id: 'publications', path: '/publications', label: 'Publications', icon: 'BookOpen' },
    { id: 'settings', path: '/settings', label: 'Settings', icon: 'Settings' },
  ],
  default: [
    { id: 'dashboard', path: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { id: 'programs', path: '/programs', label: 'Programs', icon: 'Wheat' },
    { id: 'trials', path: '/trials', label: 'Trials', icon: 'FlaskConical' },
    { id: 'germplasm', path: '/germplasm', label: 'Germplasm', icon: 'Sprout' },
    { id: 'settings', path: '/settings', label: 'Settings', icon: 'Settings' },
  ],
};

// ============================================================================
// Initial State
// ============================================================================

const initialPreferences: DockPreferences = {
  maxPinned: 8,
  maxRecent: 4,
  showLabels: false,
  compactMode: false,
};

const initialPinned: DockItem[] = defaultDocksByRole.default.map(item => ({
  ...item,
  isPinned: true,
}));

// ============================================================================
// Store
// ============================================================================

export const useDockStore = create<DockState>()(
  persist(
    (set, get) => ({
      // Initial state
      pinnedItems: initialPinned,
      recentItems: [],
      preferences: initialPreferences,
      hasAppliedRoleDefaults: false, // Track if role defaults have been applied

      // Actions
      pinItem: (item) => {
        const { pinnedItems, preferences } = get();
        if (pinnedItems.length >= preferences.maxPinned) {
          console.warn(`Maximum pinned items (${preferences.maxPinned}) reached`);
          return;
        }
        if (pinnedItems.some(p => p.path === item.path)) {
          return; // Already pinned
        }
        set({
          pinnedItems: [...pinnedItems, { ...item, isPinned: true }],
          // Remove from recent if it was there
          recentItems: get().recentItems.filter(r => r.path !== item.path),
        });
      },

      unpinItem: (path) => {
        set((state) => ({
          pinnedItems: state.pinnedItems.filter(p => p.path !== path),
        }));
      },

      togglePin: (item) => {
        const { isPinned } = get();
        if (isPinned(item.path)) {
          get().unpinItem(item.path);
        } else {
          get().pinItem(item);
        }
      },

      reorderPinned: (fromIndex, toIndex) => {
        set((state) => {
          const items = [...state.pinnedItems];
          const [removed] = items.splice(fromIndex, 1);
          items.splice(toIndex, 0, removed);
          return { pinnedItems: items };
        });
      },

      recordVisit: (item) => {
        const { recentItems, pinnedItems, preferences } = get();
        
        // Don't add to recent if it's pinned
        if (pinnedItems.some(p => p.path === item.path)) {
          return;
        }

        const now = new Date().toISOString();
        const existing = recentItems.find(r => r.path === item.path);
        
        if (existing) {
          // Update existing
          set({
            recentItems: [
              { ...existing, lastVisited: now, visitCount: (existing.visitCount || 0) + 1 },
              ...recentItems.filter(r => r.path !== item.path),
            ].slice(0, preferences.maxRecent),
          });
        } else {
          // Add new
          set({
            recentItems: [
              { ...item, isPinned: false, lastVisited: now, visitCount: 1 },
              ...recentItems,
            ].slice(0, preferences.maxRecent),
          });
        }
      },

      clearRecent: () => {
        set({ recentItems: [] });
      },

      setPreferences: (prefs) => {
        set((state) => ({
          preferences: { ...state.preferences, ...prefs },
        }));
      },

      /**
       * Apply role-based dock defaults on first login.
       * Per Think-Tank §5.1: "Apply role-based dock on first login" - Priority P0
       * 
       * @param role - User role (breeder, seed_company, genebank_curator, researcher, or default)
       */
      applyRoleDefaults: (role: string) => {
        const { hasAppliedRoleDefaults } = get();
        
        // Only apply once per user
        if (hasAppliedRoleDefaults) {
          return;
        }
        
        const roleKey = role.toLowerCase().replace(/\s+/g, '_');
        const defaults = defaultDocksByRole[roleKey] || defaultDocksByRole.default;
        
        set({
          pinnedItems: defaults.map(item => ({ ...item, isPinned: true })),
          hasAppliedRoleDefaults: true,
        });
      },

      /**
       * Reset dock to role defaults (can be called manually from settings).
       * 
       * @param role - Optional role to reset to (defaults to 'default')
       */
      resetToDefaults: (role?: string) => {
        const roleKey = role?.toLowerCase().replace(/\s+/g, '_') || 'default';
        const defaults = defaultDocksByRole[roleKey] || defaultDocksByRole.default;
        
        set({
          pinnedItems: defaults.map(item => ({ ...item, isPinned: true })),
          recentItems: [],
        });
      },

      // Queries
      isPinned: (path) => {
        return get().pinnedItems.some(p => p.path === path);
      },

      getDockItems: () => {
        const { pinnedItems, recentItems } = get();
        return [...pinnedItems, ...recentItems];
      },
    }),
    {
      name: 'bijmantra-dock',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        pinnedItems: state.pinnedItems,
        recentItems: state.recentItems,
        preferences: state.preferences,
        hasAppliedRoleDefaults: state.hasAppliedRoleDefaults,
      }),
    }
  )
);

// ============================================================================
// Selectors
// ============================================================================

export const selectPinnedItems = (state: DockState) => state.pinnedItems;
export const selectRecentItems = (state: DockState) => state.recentItems;
export const selectDockPreferences = (state: DockState) => state.preferences;

// ============================================================================
// Hooks
// ============================================================================

export function usePinnedItems() {
  return useDockStore(selectPinnedItems);
}

export function useRecentItems() {
  return useDockStore(selectRecentItems);
}

export function useDockPreferences() {
  return useDockStore(selectDockPreferences);
}

export default useDockStore;
