import { ApiClientCore } from "../core/client";

export interface ChatHealthResponse {
  status: string;
  assistant: string;
  active_provider: string;
  active_model: string;
  active_provider_source: string;
  active_provider_source_label: string;
  capabilities: string[];
  rag_enabled: boolean;
  llm_enabled: boolean;
  free_tier_available: boolean;
}

export interface ChatMetricsRequestSummary {
  domain: string;
  function_name: string;
  status: string;
  count: number;
}

export interface ChatMetricsLatencySummary {
  count: number;
  min: number;
  max: number;
  mean: number;
  p50: number;
  p95: number | null;
  p99: number | null;
}

export interface ChatMetricsPolicyFlagSummary {
  flag: string;
  count: number;
}

export interface ChatDiagnosticsProviderSummary {
  provider: string;
  available: boolean;
  free_tier: boolean;
}

export interface ChatDiagnosticsStatusSummary {
  status: string;
  count: number;
}

export interface ChatDiagnosticsProviderLatencySummary {
  provider: string;
  count: number;
  p50: number;
  p95: number | null;
  p99: number | null;
}

export interface ChatDiagnosticsSafeFailureSummary {
  reason: string;
  count: number;
}

export interface ChatDiagnosticsRoutingState {
  preferred_provider: string | null;
  preferred_provider_only: boolean;
  selection_mode: string;
}

export interface ChatDiagnosticsRoutingDecisionSummary {
  decision: string;
  count: number;
}

export interface ChatMetricsResponse {
  uptime_seconds: number;
  total_requests: number;
  requests: ChatMetricsRequestSummary[];
  latency: Record<string, ChatMetricsLatencySummary>;
  policy_flags: ChatMetricsPolicyFlagSummary[];
}

export interface ChatDiagnosticsResponse {
  assistant: string;
  active_provider: string;
  active_model: string;
  active_provider_source: string;
  active_provider_source_label: string;
  uptime_seconds: number;
  total_requests: number;
  providers: ChatDiagnosticsProviderSummary[];
  routing_state: ChatDiagnosticsRoutingState;
  request_statuses: ChatDiagnosticsStatusSummary[];
  provider_latencies: ChatDiagnosticsProviderLatencySummary[];
  safe_failures: ChatDiagnosticsSafeFailureSummary[];
  routing_decisions: ChatDiagnosticsRoutingDecisionSummary[];
  policy_flags: ChatMetricsPolicyFlagSummary[];
}

export class ChatHealthService {
  constructor(private client: ApiClientCore) {}

  async getChatHealth() {
    return this.client.get<ChatHealthResponse>("/api/v2/chat/health");
  }

  async getChatMetrics() {
    return this.client.get<ChatMetricsResponse>("/api/v2/chat/metrics");
  }

  async getChatDiagnostics() {
    return this.client.get<ChatDiagnosticsResponse>("/api/v2/chat/diagnostics");
  }
}