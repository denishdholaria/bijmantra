import { Aperture, Filter, TimerReset } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  ChatDiagnosticsNarrowingEffectiveness,
  ChatDiagnosticsStepExecutionTraceSummary,
} from "@/lib/api/system/chat-health";

interface StepExecutionTraceCardProps {
  stepExecutionTraces: ChatDiagnosticsStepExecutionTraceSummary;
  narrowingEffectiveness: ChatDiagnosticsNarrowingEffectiveness;
}

export function StepExecutionTraceCard({
  stepExecutionTraces,
  narrowingEffectiveness,
}: StepExecutionTraceCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Step Execution Trace</CardTitle>
        <CardDescription>
          Timing, status distribution, and narrowing behavior for multistep REEVU plans.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Aperture className="h-4 w-4" />
              Steps Observed
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {stepExecutionTraces.total_steps_observed}
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Filter className="h-4 w-4" />
              Narrowed Hits
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {narrowingEffectiveness.applied_non_empty}
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <TimerReset className="h-4 w-4" />
              Unnarrowed Fallbacks
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {narrowingEffectiveness.fell_back_to_unnarrowed}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium text-muted-foreground">Status distribution</div>
          <div className="flex flex-wrap gap-2">
            {stepExecutionTraces.status_distribution.length > 0 ? (
              stepExecutionTraces.status_distribution.map((status) => (
                <Badge key={status.status} variant="outline">
                  {status.status}: {status.count}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">
                No step execution traces recorded yet.
              </span>
            )}
          </div>
        </div>

        {stepExecutionTraces.domain_breakdown.length > 0 ? (
          <div className="space-y-3">
            {stepExecutionTraces.domain_breakdown.map((domain) => (
              <div key={domain.domain} className="rounded-lg border p-4">
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="text-sm font-semibold capitalize">{domain.domain}</div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      Avg {Math.round(domain.avg_duration_ms)}ms, P50{" "}
                      {Math.round(domain.p50_duration_ms)}ms
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="outline">success {domain.success}</Badge>
                    <Badge variant="outline">failed {domain.failed}</Badge>
                    <Badge variant="outline">skipped {domain.skipped}</Badge>
                    <Badge variant="outline">timed out {domain.timed_out}</Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {narrowingEffectiveness.domain_breakdown.length > 0 ? (
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground">
              Narrowing by domain
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {narrowingEffectiveness.domain_breakdown.map((domain) => (
                <div key={domain.domain} className="rounded-lg border p-4">
                  <div className="text-sm font-semibold capitalize">{domain.domain}</div>
                  <div className="mt-3 flex flex-wrap gap-2 text-sm">
                    <Badge variant="outline">
                      non-empty {domain.applied_non_empty}
                    </Badge>
                    <Badge variant="outline">empty {domain.applied_empty}</Badge>
                    <Badge variant="outline">
                      fallback {domain.fell_back_to_unnarrowed}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
