/**
 * Breeding Dashboard
 * 
 * Workspace-specific dashboard for Plant Breeding workspace.
 * Shows programs, trials, crosses, and germplasm stats.
 */

import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Wheat, FlaskConical, GitBranch, Sprout, 
  ArrowRight, Plus, TrendingUp, Calendar,
  CheckCircle2, Clock
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api-client';

export function BreedingDashboard() {
  // Fetch programs from API
  const { data: programsData, isLoading: programsLoading } = useQuery({
    queryKey: ['programs', 'recent'],
    queryFn: () => apiClient.programService.getPrograms(0, 4),
  });

  // Fetch trials from API
  const { data: trialsData, isLoading: trialsLoading } = useQuery({
    queryKey: ['trials', 'recent'],
    queryFn: () => apiClient.trialService.getTrials(0, 4),
  });

  // Fetch germplasm count
  const { data: germplasmData, isLoading: germplasmLoading } = useQuery({
    queryKey: ['germplasm', 'count'],
    queryFn: () => apiClient.germplasmService.getGermplasm(0, 1),
  });

  // Fetch Selection Stats
  const { data: selectionStats } = useQuery({
    queryKey: ['selection-stats'],
    queryFn: () => apiClient.selectionDecisionsService.getStatistics()
  });

  // Extract data from API responses
  const programs = programsData?.result?.data || [];
  const trials = trialsData?.result?.data || [];
  const programCount = programsData?.metadata?.pagination?.totalCount || 0;
  const trialCount = trialsData?.metadata?.pagination?.totalCount || 0;
  const germplasmCount = germplasmData?.metadata?.pagination?.totalCount || 0;
  const pendingSelections = selectionStats?.data?.pending || 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wheat className="h-6 w-6 text-green-600" />
            Plant Breeding Dashboard
          </h1>
          <p className="text-muted-foreground">
            Manage breeding programs, trials, and germplasm
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/programs/new"><Plus className="h-4 w-4 mr-2" />New Program</Link>
          </Button>
          <Button asChild>
            <Link to="/crosses/new"><GitBranch className="h-4 w-4 mr-2" />New Cross</Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Programs</CardTitle>
            <Wheat className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{programCount}</div>
            <p className="text-xs text-muted-foreground">Breeding programs in progress</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Trials</CardTitle>
            <FlaskConical className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{trialCount}</div>
            <p className="text-xs text-muted-foreground">Field trials running</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Germplasm</CardTitle>
            <Sprout className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{germplasmCount.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Accessions in database</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending Selections</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingSelections}</div>
            <p className="text-xs text-muted-foreground">Awaiting decision</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Programs List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Active Programs</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/programs">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Current breeding programs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {programsLoading ? (
                <>{[1,2,3,4].map((i) => <Skeleton key={i} className="h-16 w-full" />)}</>
              ) : programs.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No programs yet</p>
              ) : (
                programs.map((program: any) => (
                  <Link
                    key={program.programDbId}
                    to={`/programs/${program.programDbId}`}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div>
                      <div className="font-medium">{program.programName}</div>
                      <div className="text-sm text-muted-foreground">{program.commonCropName || 'Unknown crop'}</div>
                    </div>
                    <Badge variant="outline">{program.programType || 'Breeding'}</Badge>
                  </Link>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Trials List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Recent Trials</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/trials">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Field trials in progress</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {trialsLoading ? (
                <>{[1,2,3,4].map((i) => <Skeleton key={i} className="h-16 w-full" />)}</>
              ) : trials.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">No trials yet</p>
              ) : (
                trials.map((trial: any) => (
                  <Link
                    key={trial.trialDbId}
                    to={`/trials/${trial.trialDbId}`}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div>
                      <div className="font-medium">{trial.trialName}</div>
                      <div className="text-sm text-muted-foreground">{trial.programName || 'Unknown program'}</div>
                    </div>
                    {trial.active !== false ? (
                      <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="secondary">Completed</Badge>
                    )}
                  </Link>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Common breeding tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/observations/collect">
                <Calendar className="h-5 w-5 mb-2" />
                <span>Record Data</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/selection-decision">
                <TrendingUp className="h-5 w-5 mb-2" />
                <span>Make Selection</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/germplasm">
                <Sprout className="h-5 w-5 mb-2" />
                <span>Browse Germplasm</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/pedigree">
                <GitBranch className="h-5 w-5 mb-2" />
                <span>View Pedigree</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default BreedingDashboard;
