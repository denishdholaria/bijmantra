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

export interface ChatDiagnosticsDatabaseAuthority {
  backend: string;
  server: string;
  port: number;
  database: string;
  user: string;
  url_redacted: string;
}

export interface ChatDiagnosticsRetrievalFunctionSummary {
  function_name: string;
  count: number;
}

export interface ChatDiagnosticsRetrievalDomainSummary {
  domain: string;
  count: number;
}

export interface ChatDiagnosticsRetrievalServiceSummary {
  service: string;
  count: number;
}

export interface ChatDiagnosticsRetrievalExecutionSummary {
  traced_requests: number;
  compound_requests: number;
  functions: ChatDiagnosticsRetrievalFunctionSummary[];
  domains: ChatDiagnosticsRetrievalDomainSummary[];
  services: ChatDiagnosticsRetrievalServiceSummary[];
}

export interface ChatDiagnosticsStepTraceDistribution {
  status: string;
  count: number;
}

export interface ChatDiagnosticsStepTraceDomainSummary {
  domain: string;
  count: number;
  avg_duration_ms: number;
  p50_duration_ms: number;
  success: number;
  failed: number;
  skipped: number;
  timed_out: number;
}

export interface ChatDiagnosticsStepExecutionTraceSummary {
  total_steps_observed: number;
  status_distribution: ChatDiagnosticsStepTraceDistribution[];
  domain_breakdown: ChatDiagnosticsStepTraceDomainSummary[];
}

export interface ChatDiagnosticsNarrowingDomainSummary {
  domain: string;
  applied_non_empty: number;
  applied_empty: number;
  fell_back_to_unnarrowed: number;
}

export interface ChatDiagnosticsNarrowingEffectiveness {
  applied_non_empty: number;
  applied_empty: number;
  fell_back_to_unnarrowed: number;
  domain_breakdown: ChatDiagnosticsNarrowingDomainSummary[];
}

export interface ChatDiagnosticsRetrievalOutcomeSummary {
  domain: string;
  success: number;
  partial: number;
  failure: number;
}

export interface ChatDiagnosticsSafeFailureCategorySummary {
  error_category: string;
  count: number;
}

export interface ChatDiagnosticsSafeFailureDistributionSummary {
  domain: string;
  count: number;
  categories: ChatDiagnosticsSafeFailureCategorySummary[];
}

export interface ChatDiagnosticsBenchmarkStatus {
  available: boolean;
  runtime_status: string;
  generated_at: string | null;
  runtime_target: string | null;
  runtime_path: string | null;
  local_organization_id: number | null;
  passed_cases: number;
  failed_cases: number;
  total_cases: number;
  pass_rate: number | null;
  readiness_blockers: string[];
  readiness_warnings: string[];
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
  database_authority: ChatDiagnosticsDatabaseAuthority;
  uptime_seconds: number;
  total_requests: number;
  providers: ChatDiagnosticsProviderSummary[];
  routing_state: ChatDiagnosticsRoutingState;
  request_statuses: ChatDiagnosticsStatusSummary[];
  provider_latencies: ChatDiagnosticsProviderLatencySummary[];
  safe_failures: ChatDiagnosticsSafeFailureSummary[];
  routing_decisions: ChatDiagnosticsRoutingDecisionSummary[];
  retrieval_execution: ChatDiagnosticsRetrievalExecutionSummary;
  step_execution_traces: ChatDiagnosticsStepExecutionTraceSummary;
  narrowing_effectiveness: ChatDiagnosticsNarrowingEffectiveness;
  retrieval_outcomes: ChatDiagnosticsRetrievalOutcomeSummary[];
  safe_failure_distribution: ChatDiagnosticsSafeFailureDistributionSummary[];
  benchmark_status: ChatDiagnosticsBenchmarkStatus;
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
