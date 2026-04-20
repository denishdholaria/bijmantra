/**
 * Compatibility facade for the legacy Veena sidebar store name.
 *
 * Shared between SystemBar (trigger) and REEVU sidebar (panel).
 * Keyboard shortcut (Ctrl+/) is handled inside the sidebar component.
 */

import { useReevuSidebarStore } from '@/store/reevuSidebarStore'

/**
 * @deprecated Use `useReevuSidebarStore` from `@/store/reevuSidebarStore`.
 */
export const useVeenaSidebarStore = useReevuSidebarStore
