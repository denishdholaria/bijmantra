/**
 * Navigation Components Index
 * 
 * Exports all navigation-related components including the Mahasarthi system.
 */

// Mahasarthi Navigation System
export { Mahasarthi } from './Mahasarthi';
export { MahasarthiDock } from './MahasarthiDock';
export { MahasarthiBrowser } from './MahasarthiBrowser';
export { MahasarthiSearch } from './MahasarthiSearch';

// Existing Navigation Components
export { MahasarthiSidebar } from './MahasarthiSidebar';
export { MahasarthiNavigation } from './MahasarthiNavigation';
export { WorkspaceSwitcher } from './WorkspaceSwitcher';

// Re-export dock store for convenience
export { useDockStore, usePinnedItems, useRecentItems } from '@/store/dockStore';
