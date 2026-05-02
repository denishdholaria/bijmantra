import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface WindowState {
  id: string;
  title: string;
  component?: React.ReactNode; 
  icon?: any; // Lucide icon
  route?: string; // If it's a routed module
  
  isMinimized: boolean;
  isMaximized: boolean;
  
  position: { x: number; y: number };
  size: { width: number; height: number };
  zIndex: number;
}

interface WindowStore {
  windows: Record<string, WindowState>;
  activeWindowId: string | null;
  zCounter: number;

  openWindow: (params: { id: string; title: string; icon?: any; route?: string; component?: React.ReactNode }) => void;
  closeWindow: (id: string) => void;
  focusWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  maximizeWindow: (id: string) => void;
  restoreWindow: (id: string) => void;
  updateWindowPosition: (id: string, position: { x: number; y: number }) => void;
  updateWindowSize: (id: string, size: { width: number; height: number }) => void;
}

export const useWindowStore = create<WindowStore>()(
  persist(
    (set, get) => ({
      windows: {},
      activeWindowId: null,
      zCounter: 100,

      openWindow: ({ id, title, icon, route, component }) => {
        const { windows, zCounter } = get();
        
        // If already open, focus it
        if (windows[id]) {
          get().focusWindow(id);
          if (windows[id].isMinimized) {
            get().restoreWindow(id);
          }
          return;
        }

        // Create new window
        const newZ = zCounter + 1;
        // Default position: cascade slightly
        const count = Object.keys(windows).length;
        const offset = count * 30;

        const newWindow: WindowState = {
          id,
          title,
          icon,
          route,
          component,
          isMinimized: false,
          isMaximized: false,
          position: { x: 100 + (offset % 200), y: 50 + (offset % 200) },
          size: { width: 800, height: 600 },
          zIndex: newZ,
        };

        set({
          windows: { ...windows, [id]: newWindow },
          activeWindowId: id,
          zCounter: newZ,
        });
      },

      closeWindow: (id) => {
        const { windows } = get();
        const { [id]: _, ...remaining } = windows;
        set({ windows: remaining, activeWindowId: null });
      },

      focusWindow: (id) => {
        const { windows, zCounter } = get();
        if (!windows[id]) return;

        const newZ = zCounter + 1;
        set({
          windows: {
            ...windows,
            [id]: { ...windows[id], zIndex: newZ },
          },
          activeWindowId: id,
          zCounter: newZ,
        });
      },

      minimizeWindow: (id) => {
        const { windows } = get();
        if (!windows[id]) return;
        set({
          windows: {
            ...windows,
            [id]: { ...windows[id], isMinimized: true },
          },
          activeWindowId: null, // Lose focus
        });
      },

      maximizeWindow: (id) => {
        const { windows, zCounter } = get();
        if (!windows[id]) return;
        // Bring to front too
        set({
          windows: {
            ...windows,
            [id]: { ...windows[id], isMaximized: true, zIndex: zCounter + 1, isMinimized: false },
          },
          activeWindowId: id,
          zCounter: zCounter + 1,
        });
      },

      restoreWindow: (id) => {
        const { windows, zCounter } = get();
        if (!windows[id]) return;
        set({
          windows: {
            ...windows,
            [id]: { ...windows[id], isMaximized: false, isMinimized: false, zIndex: zCounter + 1 },
          },
          activeWindowId: id,
          zCounter: zCounter + 1,
        });
      },

      updateWindowPosition: (id, position) => {
         const { windows } = get();
         if (!windows[id]) return;
         set({
           windows: {
             ...windows,
             [id]: { ...windows[id], position }
           }
         });
      },

      updateWindowSize: (id, size) => {
        const { windows } = get();
        if (!windows[id]) return;
        set({
          windows: {
            ...windows,
            [id]: { ...windows[id], size }
           }
        });
      }
    }),
    {
      name: 'bijmantra-window-store',
      // Avoid persisting component objects (they are not serializable)
        partialize: (state) => ({
          windows: Object.fromEntries(
            Object.entries(state.windows).map(([k, v]) => [k, { ...v, component: undefined, icon: undefined }])
          ),
        }),
    }
  )
);
