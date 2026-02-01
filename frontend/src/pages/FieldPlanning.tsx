/**
 * Field Planning Page
 * Field and season planning for trials
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { MapPin, Calendar, Leaf, BarChart3, Grid3X3, Clock, DollarSign, Users } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function FieldPlanning() {
  const [activeTab, setActiveTab] = useState('fields')
  const [selectedSeason, setSelectedSeason] = useState('all')

  // Fetch field plans
  const { data: fieldPlans = [], isLoading: loadingFields } = useQuery({
    queryKey: ['field-plans', selectedSeason],
    queryFn: () => apiClient.fieldPlanningService.getFieldPlans({
      season: selectedSeason !== 'all' ? selectedSeason : undefined
    })
  })

  // Fetch season plans
  const { data: seasonPlans = [], isLoading: loadingSeasons } = useQuery({
    queryKey: ['season-plans'],
    queryFn: () => apiClient.fieldPlanningService.getSeasonPlans()
  })

  // Fetch statistics
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['field-planning-statistics'],
    queryFn: () => apiClient.fieldPlanningService.getFieldPlanningStatistics()
  })

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'bg-green-100 text-green-700'
      case 'planning': return 'bg-blue-100 text-blue-700'
      case 'completed': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <MapPin className="h-7 w-7 text-primary" />
            Field Planning
          </h1>
          <p className="text-muted-foreground mt-1">Plan and manage field trials</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Season" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Seasons</SelectItem>
              <SelectItem value="kharif">Kharif</SelectItem>
              <SelectItem value="rabi">Rabi</SelectItem>
              <SelectItem value="summer">Summer</SelectItem>
            </SelectContent>
          </Select>
          <Button>
            <Grid3X3 className="h-4 w-4 mr-2" />
            New Plan
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <MapPin className="h-5 w-5 text-primary" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_field_plans || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Field Plans</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Grid3X3 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_plots_planned?.toLocaleString() || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Total Plots</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <BarChart3 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.utilization_rate || 0}%</p>
                )}
                <p className="text-xs text-muted-foreground">Utilization</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <Calendar className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.active_plans || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Active Plans</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="fields">Field Plans</TabsTrigger>
          <TabsTrigger value="seasons">Season Plans</TabsTrigger>
        </TabsList>

        <TabsContent value="fields" className="space-y-6 mt-4">
          {loadingFields ? (
            <div className="space-y-4">
              {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full" />)}
            </div>
          ) : fieldPlans.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <MapPin className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No field plans found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {fieldPlans.map((plan: any) => (
                <Card key={plan.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-bold text-lg">{plan.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {plan.field_name} • {plan.season}
                        </p>
                      </div>
                      <Badge className={getStatusColor(plan.status)}>
                        {plan.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="flex items-center gap-2">
                        <Leaf className="h-4 w-4 text-green-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Crop</p>
                          <p className="text-sm font-medium">{plan.crop}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Grid3X3 className="h-4 w-4 text-blue-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Plots</p>
                          <p className="text-sm font-medium">{plan.allocated_plots}/{plan.total_plots}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-amber-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Start</p>
                          <p className="text-sm font-medium">{plan.start_date}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-red-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">End</p>
                          <p className="text-sm font-medium">{plan.end_date}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Plot Allocation</span>
                        <span className="font-medium">
                          {Math.round((plan.allocated_plots / plan.total_plots) * 100)}%
                        </span>
                      </div>
                      <Progress value={(plan.allocated_plots / plan.total_plots) * 100} className="h-2" />
                    </div>
                    {plan.trials && plan.trials.length > 0 && (
                      <div className="pt-3 border-t">
                        <p className="text-xs text-muted-foreground mb-2">Trials ({plan.trials.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {plan.trials.map((trial: any) => (
                            <Badge key={trial.trial_id} variant="outline" className="text-xs">
                              {trial.name} ({trial.plots} plots)
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="seasons" className="space-y-6 mt-4">
          {loadingSeasons ? (
            <div className="space-y-4">
              {[1, 2].map(i => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : seasonPlans.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No season plans found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {seasonPlans.map((plan: any) => (
                <Card key={plan.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-bold text-lg">{plan.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {plan.start_date} to {plan.end_date}
                        </p>
                      </div>
                      <Badge className={getStatusColor(plan.status)}>
                        {plan.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="flex items-center gap-2">
                        <Leaf className="h-4 w-4 text-green-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Crops</p>
                          <p className="text-sm font-medium">{plan.crops?.length || 0}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-blue-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Trials</p>
                          <p className="text-sm font-medium">{plan.total_trials}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Grid3X3 className="h-4 w-4 text-purple-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Plots</p>
                          <p className="text-sm font-medium">{plan.total_plots?.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-amber-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Budget</p>
                          <p className="text-sm font-medium">${plan.budget?.toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                    {plan.crops && plan.crops.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs text-muted-foreground mb-2">Crops</p>
                        <div className="flex flex-wrap gap-1">
                          {plan.crops.map((crop: string) => (
                            <Badge key={crop} variant="secondary" className="text-xs">{crop}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
