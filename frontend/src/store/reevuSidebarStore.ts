import { create } from "zustand";

interface ReevuSidebarState {
	isOpen: boolean;
	open: () => void;
	close: () => void;
	toggle: () => void;
}

/**
 * Canonical REEVU sidebar store.
 */
export const useReevuSidebarStore = create<ReevuSidebarState>((set) => ({
	isOpen: false,
	open: () => set({ isOpen: true }),
	close: () => set({ isOpen: false }),
	toggle: () => set((s) => ({ isOpen: !s.isOpen })),
}));
