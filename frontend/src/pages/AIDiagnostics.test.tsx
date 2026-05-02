import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AIDiagnostics } from "./AIDiagnostics";
import { apiClient } from "@/lib/api-client";
import { useHydratedSuperuserQueryAccess } from "@/store/auth";

vi.mock("@/store/auth", () => ({
  useHydratedSuperuserQueryAccess: vi.fn(),
}));

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    chatHealthService: {
      getChatDiagnostics: vi.fn(),
    },
  },
}));

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderPage() {
  const queryClient = createQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <AIDiagnostics />
    </QueryClientProvider>,
  );
}

describe("AIDiagnostics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useHydratedSuperuserQueryAccess).mockReturnValue(true);
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders the diagnostics dashboard with retrieval and safe-failure cards", async () => {
    vi.mocked(apiClient.chatHealthService.getChatDiagnostics).mockResolvedValue({
      assistant: "REEVU",
      active_provider: "openai",
      active_model: "gpt-4.1-mini",
      active_provider_source: "organization_config",
      active_provider_source_label: "Organization AI settings",
      database_authority: {
        backend: "postgresql",
        server: "localhost",
        port: 5432,
        database: "bijmantra_db",
        user: "bijmantra_user",
        url_redacted:
          "postgresql+asyncpg://bijmantra_user:***@localhost:5432/bijmantra_db",
      },
      uptime_seconds: 3600,
      total_requests: 12,
      providers: [
        { provider: "openai", available: true, free_tier: false },
        { provider: "template", available: true, free_tier: true },
      ],
      routing_state: {
        preferred_provider: "openai",
        preferred_provider_only: false,
        selection_mode: "preferred_with_fallback",
      },
      request_statuses: [
        { status: "ok", count: 10 },
        { status: "safe_failure", count: 2 },
      ],
      provider_latencies: [
        { provider: "openai", count: 12, p50: 0.24, p95: null, p99: null },
      ],
      safe_failures: [{ reason: "insufficient_evidence", count: 2 }],
      routing_decisions: [{ decision: "managed_preferred", count: 12 }],
      retrieval_execution: {
        traced_requests: 9,
        compound_requests: 6,
        functions: [],
        domains: [
          { domain: "trials", count: 4 },
          { domain: "weather", count: 2 },
        ],
        services: [{ service: "trial_search_service.search", count: 4 }],
      },
      step_execution_traces: {
        total_steps_observed: 14,
        status_distribution: [
          { status: "success", count: 10 },
          { status: "failed", count: 2 },
          { status: "skipped", count: 2 },
        ],
        domain_breakdown: [
          {
            domain: "trials",
            count: 6,
            avg_duration_ms: 120,
            p50_duration_ms: 100,
            success: 5,
            failed: 1,
            skipped: 0,
            timed_out: 0,
          },
        ],
      },
      narrowing_effectiveness: {
        applied_non_empty: 4,
        applied_empty: 1,
        fell_back_to_unnarrowed: 2,
        domain_breakdown: [
          {
            domain: "trials",
            applied_non_empty: 4,
            applied_empty: 1,
            fell_back_to_unnarrowed: 0,
          },
        ],
      },
      retrieval_outcomes: [
        { domain: "trials", success: 4, partial: 1, failure: 1 },
        { domain: "weather", success: 1, partial: 0, failure: 1 },
      ],
      safe_failure_distribution: [
        {
          domain: "weather",
          count: 2,
          categories: [{ error_category: "weather_service_unavailable", count: 2 }],
        },
      ],
      benchmark_status: {
        available: true,
        runtime_status: "blocked",
        generated_at: "2026-04-05T10:38:21.986969+00:00",
        runtime_target: "in_process_app",
        runtime_path: "local",
        local_organization_id: 1,
        passed_cases: 9,
        failed_cases: 5,
        total_cases: 14,
        pass_rate: 0.642857,
        readiness_blockers: ["observations.empty"],
        readiness_warnings: ["trials.sparse"],
      },
      policy_flags: [{ flag: "missing_evidence", count: 2 }],
    });

    renderPage();

    expect(
      await screen.findByText("REEVU Intelligence Diagnostics"),
    ).toBeInTheDocument();
    expect(screen.getByText("64.3%")).toBeInTheDocument();
    expect(screen.getByText("Step Execution Trace")).toBeInTheDocument();
    expect(screen.getByText("Retrieval Outcomes")).toBeInTheDocument();
    expect(screen.getByText("Safe Failure Distribution")).toBeInTheDocument();
    expect(
      screen.getByText("weather_service_unavailable: 2"),
    ).toBeInTheDocument();
  });

  it("shows a loading state while diagnostics are being fetched", () => {
    vi.mocked(apiClient.chatHealthService.getChatDiagnostics).mockReturnValue(
      new Promise(() => {}),
    );

    renderPage();

    expect(screen.getByText("Loading diagnostics")).toBeInTheDocument();
  });

  it("shows an error state when diagnostics loading fails", async () => {
    vi.mocked(apiClient.chatHealthService.getChatDiagnostics).mockRejectedValue(
      new Error("boom"),
    );

    renderPage();

    expect(await screen.findByText("Diagnostics unavailable")).toBeInTheDocument();
    expect(
      screen.getByText(
        "REEVU diagnostics could not be loaded from the operator endpoint.",
      ),
    ).toBeInTheDocument();
  });
});
