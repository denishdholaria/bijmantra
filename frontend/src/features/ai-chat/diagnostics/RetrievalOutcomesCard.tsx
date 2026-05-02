import { Activity, Microscope, Workflow } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type {
  ChatDiagnosticsRetrievalExecutionSummary,
  ChatDiagnosticsRetrievalOutcomeSummary,
} from "@/lib/api/system/chat-health";

interface RetrievalOutcomesCardProps {
  outcomes: ChatDiagnosticsRetrievalOutcomeSummary[];
  retrievalExecution: ChatDiagnosticsRetrievalExecutionSummary;
}

function getTotal(outcome: ChatDiagnosticsRetrievalOutcomeSummary) {
  return outcome.success + outcome.partial + outcome.failure;
}

function getSuccessRate(outcome: ChatDiagnosticsRetrievalOutcomeSummary) {
  const total = getTotal(outcome);
  if (total === 0) {
    return 0;
  }
  return Math.round((outcome.success / total) * 100);
}

export function RetrievalOutcomesCard({
  outcomes,
  retrievalExecution,
}: RetrievalOutcomesCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Retrieval Outcomes</CardTitle>
        <CardDescription>
          Domain-by-domain retrieval quality across recent REEVU requests.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Activity className="h-4 w-4" />
              Traced Requests
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {retrievalExecution.traced_requests}
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Workflow className="h-4 w-4" />
              Compound Plans
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {retrievalExecution.compound_requests}
            </div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Microscope className="h-4 w-4" />
              Services Touched
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {retrievalExecution.services.length}
            </div>
          </div>
        </div>

        {outcomes.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            No retrieval outcome telemetry has been recorded yet.
          </div>
        ) : (
          <div className="space-y-3">
            {outcomes.map((outcome) => {
              const total = getTotal(outcome);
              const successRate = getSuccessRate(outcome);

              return (
                <div key={outcome.domain} className="rounded-lg border p-4">
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="text-sm font-semibold capitalize">
                        {outcome.domain}
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        {total} observed retrieval outcomes
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">success {outcome.success}</Badge>
                      <Badge variant="outline">partial {outcome.partial}</Badge>
                      <Badge variant="outline">failure {outcome.failure}</Badge>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Success rate</span>
                      <span className="font-medium">{successRate}%</span>
                    </div>
                    <Progress
                      aria-label={`${outcome.domain} retrieval success rate`}
                      value={successRate}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {retrievalExecution.services.length > 0 ? (
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground">
              Most recent service surface
            </div>
            <div className="flex flex-wrap gap-2">
              {retrievalExecution.services.slice(0, 6).map((service) => (
                <Badge key={service.service} variant="outline">
                  {service.service}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
