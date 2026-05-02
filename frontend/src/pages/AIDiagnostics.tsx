/**
 * AI Diagnostics Page (Thin Adapter)
 *
 * Keeps route-level wiring thin while the diagnostics surface lives in the
 * feature module.
 */

import { DiagnosticsDashboard } from "@/features/ai-chat/diagnostics";

export function AIDiagnostics() {
  return <DiagnosticsDashboard />;
}

export default AIDiagnostics;
