/**
 * AI Settings Page (Thin Adapter)
 * 
 * Extracted as part of Titanium Path hot-file reduction (Task 13).
 * Original 2173-line hot file reduced to thin page adapter.
 * 
 * All logic moved to:
 * - features/ai-chat/settings/AISettingsPanel.tsx (UI orchestration)
 * - features/ai-chat/settings/useAISettings.ts (state management)
 * - features/ai-chat/settings/helpers.ts (utilities)
 * - features/ai-chat/services/aiSettingsService.ts (API calls)
 */

import { AISettingsPanel } from "@/features/ai-chat/settings";

export function AISettings() {
  return <AISettingsPanel />;
}

export default AISettings;
