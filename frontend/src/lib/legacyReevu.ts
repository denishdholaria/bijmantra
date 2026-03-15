/**
 * Centralized legacy REEVU compatibility constants.
 *
 * These values intentionally preserve historic `veena` identifiers for
 * serialized state, routes, and compatibility aliases during migration.
 */

export const LEGACY_REEVU_ROUTE = '/veena' as const;
export const LEGACY_REEVU_ROUTE_SEGMENT = 'veena' as const;
export const LEGACY_REEVU_STORAGE_KEY = 'veena_conversation_history' as const;

export const LEGACY_REEVU_TOUR_TARGET = 'veena-ai' as const;
export const LEGACY_REEVU_ICON_KEY = 'veena' as const;
export const LEGACY_REEVU_LOGO_ICON = 'veena-logo' as const;

export const LEGACY_REEVU_ORCHESTRATOR_ID = 'veena' as const;
export const LEGACY_REEVU_NOTIFICATION_TYPE = 'veena' as const;
