import { AlertTriangle, Bot, Database, RefreshCw, ShieldAlert } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { formatRoutingLabel, formatTimestamp, formatUptime } from "../settings/helpers";
import { RetrievalOutcomesCard } from "./RetrievalOutcomesCard";
import { SafeFailureDistributionCard } from "./SafeFailureDistributionCard";
import { StepExecutionTraceCard } from "./StepExecutionTraceCard";
import { useDiagnostics } from "./useDiagnostics";

interface DiagnosticsDashboardProps {
  refetchIntervalMs?: number;
}

function formatPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "Unavailable";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function DiagnosticsSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-1">
      <span className="sr-only">Loading diagnostics</span>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-4 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-[420px] w-full rounded-lg" />
        <Skeleton className="h-[420px] w-full rounded-lg" />
      </div>
      <Skeleton className="h-[280px] w-full rounded-lg" />
    </div>
  );
}

export function DiagnosticsDashboard({
  refetchIntervalMs = 30_000,
}: DiagnosticsDashboardProps) {
  const diagnosticsQuery = useDiagnostics({ refetchIntervalMs });
  const diagnostics = diagnosticsQuery.data;
  const safeFailureCount = (diagnostics?.safe_failures || []).reduce(
    (sum, item) => sum + item.count,
    0,
  );

  if (diagnosticsQuery.isLoading) {
    return <DiagnosticsSkeleton />;
  }

  if (diagnosticsQuery.isError) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Diagnostics unavailable</AlertTitle>
        <AlertDescription className="space-y-3">
          <p>
            REEVU diagnostics could not be loaded from the operator endpoint.
          </p>
          <Button
            variant="outline"
            onClick={() => void diagnosticsQuery.refetch()}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!diagnostics) {
    return (
      <Alert>
        <Bot className="h-4 w-4" />
        <AlertTitle>No diagnostics yet</AlertTitle>
        <AlertDescription>
          REEVU has not recorded diagnostics telemetry in this runtime window.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-1">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold lg:text-3xl">
            REEVU Intelligence Diagnostics
          </h1>
          <p className="mt-1 text-muted-foreground">
            Operator telemetry for step execution, retrieval quality, and grounded safe failures.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            refresh every {Math.round(refetchIntervalMs / 1000)}s
          </Badge>
          <Badge variant="outline">
            {formatRoutingLabel(diagnostics.routing_state.selection_mode)}
          </Badge>
          <Button
            variant="outline"
            onClick={() => void diagnosticsQuery.refetch()}
            disabled={diagnosticsQuery.isFetching}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {diagnosticsQuery.isFetching ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Runtime Provider</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{diagnostics.active_provider}</div>
            <p className="text-sm text-muted-foreground">
              {diagnostics.active_model}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {diagnostics.active_provider_source_label}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Benchmark Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatPercent(diagnostics.benchmark_status.pass_rate)}
            </div>
            <p className="text-sm text-muted-foreground">
              {diagnostics.benchmark_status.passed_cases}/
              {diagnostics.benchmark_status.total_cases} passing for org{" "}
              {diagnostics.benchmark_status.local_organization_id ?? "?"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {diagnostics.benchmark_status.generated_at
                ? `Updated ${formatTimestamp(diagnostics.benchmark_status.generated_at)}`
                : "Local benchmark artifact unavailable"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Execution Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {diagnostics.step_execution_traces.total_steps_observed}
            </div>
            <p className="text-sm text-muted-foreground">
              {diagnostics.retrieval_execution.traced_requests} traced requests
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              uptime {formatUptime(diagnostics.uptime_seconds)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Safe Failure Pressure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{safeFailureCount}</div>
            <p className="text-sm text-muted-foreground">
              {diagnostics.safe_failure_distribution.length} affected domains
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {diagnostics.safe_failures[0]
                ? `Top reason: ${diagnostics.safe_failures[0].reason}`
                : "No safe failures recorded"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Operator Context</CardTitle>
          <CardDescription>
            Shared routing posture, benchmark blockers, and backend authority for this runtime.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-lg border p-4">
            <div className="text-sm font-medium text-muted-foreground">Routing posture</div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge variant="outline">
                {formatRoutingLabel(diagnostics.routing_state.selection_mode)}
              </Badge>
              {diagnostics.routing_state.preferred_provider ? (
                <Badge variant="outline">
                  preferred {diagnostics.routing_state.preferred_provider}
                </Badge>
              ) : null}
              {diagnostics.providers.map((provider) => (
                <Badge key={provider.provider} variant="outline">
                  {provider.provider} {provider.available ? "ready" : "offline"}
                </Badge>
              ))}
            </div>
          </div>

          <div className="rounded-lg border p-4">
            <div className="text-sm font-medium text-muted-foreground">Benchmark blockers</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {diagnostics.benchmark_status.readiness_blockers.length > 0 ? (
                diagnostics.benchmark_status.readiness_blockers.map((blocker) => (
                  <Badge key={blocker} variant="outline">
                    {blocker}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">
                  No readiness blockers captured.
                </span>
              )}
            </div>
            {diagnostics.benchmark_status.readiness_warnings.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {diagnostics.benchmark_status.readiness_warnings.map((warning) => (
                  <Badge key={warning} variant="outline">
                    warning {warning}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>

          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Database className="h-4 w-4" />
              Backend authority
            </div>
            <div className="mt-3 space-y-2 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Database</span>
                <span className="font-medium">
                  {diagnostics.database_authority.database}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Server</span>
                <span className="font-medium">
                  {diagnostics.database_authority.server}:
                  {diagnostics.database_authority.port}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-muted-foreground">Runtime status</span>
                <span className="font-medium">
                  {diagnostics.benchmark_status.runtime_status}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <StepExecutionTraceCard
          stepExecutionTraces={diagnostics.step_execution_traces}
          narrowingEffectiveness={diagnostics.narrowing_effectiveness}
        />
        <RetrievalOutcomesCard
          outcomes={diagnostics.retrieval_outcomes}
          retrievalExecution={diagnostics.retrieval_execution}
        />
      </div>

      <SafeFailureDistributionCard
        safeFailures={diagnostics.safe_failures}
        safeFailureDistribution={diagnostics.safe_failure_distribution}
      />

      {diagnostics.policy_flags.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Policy Flags</CardTitle>
            <CardDescription>
              Validation and evidence policy signals captured during recent requests.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {diagnostics.policy_flags.map((flag) => (
              <Badge key={flag.flag} variant="outline">
                {flag.flag}: {flag.count}
              </Badge>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {diagnostics.safe_failure_distribution.length > 0 ? (
        <Alert variant="narangi">
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle>Grounded safe failures remain active</AlertTitle>
          <AlertDescription>
            These failures are visible by design so operators can distinguish runtime gaps
            from successful grounded retrieval.
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
