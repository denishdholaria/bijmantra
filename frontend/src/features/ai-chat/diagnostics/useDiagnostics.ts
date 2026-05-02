import { useQuery } from "@tanstack/react-query";

import type { ChatDiagnosticsResponse } from "@/lib/api/system/chat-health";
import { useHydratedSuperuserQueryAccess } from "@/store/auth";

import { aiSettingsService } from "../services/aiSettingsService";

interface UseDiagnosticsOptions {
  refetchIntervalMs?: number;
  enabled?: boolean;
}

export function useDiagnostics(options: UseDiagnosticsOptions = {}) {
  const canQueryDiagnostics = useHydratedSuperuserQueryAccess();
  const queryEnabled = canQueryDiagnostics && (options.enabled ?? true);

  return useQuery<ChatDiagnosticsResponse>({
    queryKey: ["chat-diagnostics"],
    queryFn: () => aiSettingsService.getChatDiagnostics(),
    enabled: queryEnabled,
    retry: false,
    refetchInterval: queryEnabled ? (options.refetchIntervalMs ?? 30_000) : false,
    refetchIntervalInBackground: true,
  });
}
