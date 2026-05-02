import { Plus, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useCrossPlans } from './hooks/useCrossPlans';

interface CrossPlanListPageProps {
  onCreateRequested?: () => void;
}

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === 'completed') {
    return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300';
  }
  if (normalized === 'in_progress' || normalized === 'scheduled') {
    return 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300';
  }
  if (normalized === 'failed') {
    return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300';
  }
  return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
}

export function CrossPlanListPage({ onCreateRequested }: CrossPlanListPageProps) {
  const plansQuery = useCrossPlans();
  const plans = plansQuery.data?.items ?? [];

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle className="text-2xl">Cross Planning</CardTitle>
            <CardDescription>
              Review saved plans and create new crosses for the current breeding program.
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => plansQuery.refetch()}
              disabled={plansQuery.isFetching}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${plansQuery.isFetching ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={onCreateRequested}>
              <Plus className="mr-2 h-4 w-4" />
              Create New Plan
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {plansQuery.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-20 w-full" />
            ))}
          </div>
        ) : plansQuery.isError ? (
          <Card className="border-destructive/40">
            <CardHeader>
              <CardTitle className="text-lg">Unable to load cross plans</CardTitle>
              <CardDescription>
                {plansQuery.error instanceof Error
                  ? plansQuery.error.message
                  : 'The cross-plan list request failed.'}
              </CardDescription>
            </CardHeader>
          </Card>
        ) : plans.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">No cross plans yet</CardTitle>
              <CardDescription>
                Start with a planned cross to capture parents, objective, and target date for the breeding team.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-3">
            {plans.map((plan) => (
              <div key={plan.crossId} className="rounded-lg border p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold">{plan.crossName}</h3>
                      <Badge className={getStatusTone(plan.status)}>{plan.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {plan.femaleParentName ?? 'Unknown female'} × {plan.maleParentName ?? 'Unknown male'}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {plan.objective || 'No objective recorded'}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <div>Planned date: {plan.targetDate || 'Not scheduled'}</div>
                    <div>Expected progeny: {plan.expectedProgeny}</div>
                    <div>Priority: {plan.priority}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
