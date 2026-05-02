import { ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  ChatDiagnosticsSafeFailureDistributionSummary,
  ChatDiagnosticsSafeFailureSummary,
} from "@/lib/api/system/chat-health";

interface SafeFailureDistributionCardProps {
  safeFailures: ChatDiagnosticsSafeFailureSummary[];
  safeFailureDistribution: ChatDiagnosticsSafeFailureDistributionSummary[];
}

export function SafeFailureDistributionCard({
  safeFailures,
  safeFailureDistribution,
}: SafeFailureDistributionCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Safe Failure Distribution</CardTitle>
        <CardDescription>
          Which domains fail safely most often, and the dominant grounded error categories.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <ShieldAlert className="h-4 w-4" />
            Safe failure reasons
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {safeFailures.length > 0 ? (
              safeFailures.map((failure) => (
                <Badge key={failure.reason} variant="outline">
                  {failure.reason}: {failure.count}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">
                No safe failures recorded in the current runtime window.
              </span>
            )}
          </div>
        </div>

        {safeFailureDistribution.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            No domain-specific failure distribution has been observed yet.
          </div>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {safeFailureDistribution.map((domain) => (
              <div key={domain.domain} className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold capitalize">{domain.domain}</div>
                  <Badge variant="outline">{domain.count} failures</Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {domain.categories.map((category) => (
                    <Badge key={`${domain.domain}-${category.error_category}`} variant="outline">
                      {category.error_category}: {category.count}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
