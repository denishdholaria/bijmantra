/**
 * Season Planning Page
 * Seasonal crop planning and resource allocation
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
import { Calendar, Leaf, BarChart3, DollarSign, Clock, Sun, CloudRain, Snowflake } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function SeasonPlanning() {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedYear, setSelectedYear] = useState('2025')

  // Fetch season plans
  const { data: seasonPlans = [], isLoading: loadingSeasons } = useQuery({
    queryKey: ['season-plans', selectedYear],
    queryFn: () => apiClient.fieldPlanningService.getSeasonPlans({
      year: parseInt(selectedYear)
    })
  })

  // Fetch statistics
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['field-planning-statistics'],
    queryFn: () => apiClient.fieldPlanningService.getFieldPlanningStatistics()
  })

  // Fetch calendar
  const { data: calendar = [], isLoading: loadingCalendar } = useQuery({
    queryKey: ['field-planning-calendar', selectedYear],
    queryFn: () => apiClient.fieldPlanningService.getFieldPlanningCalendar(parseInt(selectedYear))
  })

  const getSeasonIcon = (seasonType: string) => {
    switch (seasonType?.toLowerCase()) {
      case 'kharif': return <CloudRain className="h-5 w-5 text-blue-500" />
      case 'rabi': return <Snowflake className="h-5 w-5 text-cyan-500" />
      case 'summer': return <Sun className="h-5 w-5 text-amber-500" />
      default: return <Calendar className="h-5 w-5" />
    }
  }

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
            <Calendar className="h-7 w-7 text-primary" />
            Season Planning
          </h1>
          <p className="text-muted-foreground mt-1">Plan crops and resources by season</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
            </SelectContent>
          </Select>
          <Button>
            <Calendar className="h-4 w-4 mr-2" />
            New Season
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_season_plans || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Season Plans</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Leaf className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {seasonPlans.reduce((acc: number, p: any) => acc + (p.crops?.length || 0), 0)}
                </p>
                <p className="text-xs text-muted-foreground">Crops Planned</p>
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
                <p className="text-2xl font-bold">
                  {seasonPlans.reduce((acc: number, p: any) => acc + (p.total_trials || 0), 0)}
                </p>
                <p className="text-xs text-muted-foreground">Total Trials</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <DollarSign className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  ${(seasonPlans.reduce((acc: number, p: any) => acc + (p.budget || 0), 0) / 1000).toFixed(0)}K
                </p>
                <p className="text-xs text-muted-foreground">Total Budget</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Season Overview</TabsTrigger>
          <TabsTrigger value="calendar">Calendar</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-4">
          {loadingSeasons ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2].map(i => <Skeleton key={i} className="h-64 w-full" />)}
            </div>
          ) : seasonPlans.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No season plans for {selectedYear}</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {seasonPlans.map((plan: any) => (
                <Card key={plan.id} className="overflow-hidden">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        {getSeasonIcon(plan.season_type)}
                        {plan.name}
                      </CardTitle>
                      <Badge className={getStatusColor(plan.status)}>
                        {plan.status}
                      </Badge>
                    </div>
                    <CardDescription>
                      {plan.start_date} to {plan.end_date}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground">Trials</p>
                        <p className="text-xl font-bold">{plan.total_trials}</p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground">Plots</p>
                        <p className="text-xl font-bold">{plan.total_plots?.toLocaleString()}</p>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Budget Allocation</span>
                        <span className="font-medium">${plan.budget?.toLocaleString()}</span>
                      </div>
                      <Progress value={75} className="h-2" />
                    </div>

                    {plan.crops && plan.crops.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Crops</p>
                        <div className="flex flex-wrap gap-1">
                          {plan.crops.map((crop: string) => (
                            <Badge key={crop} variant="outline" className="text-xs">
                              <Leaf className="h-3 w-3 mr-1" />
                              {crop}
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

        <TabsContent value="calendar" className="space-y-6 mt-4">
          {loadingCalendar ? (
            <Skeleton className="h-96 w-full" />
          ) : calendar.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Calendar className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No calendar events</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Activity Calendar - {selectedYear}</CardTitle>
                <CardDescription>Planned activities across all fields</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {calendar.slice(0, 30).map((event: any) => (
                    <div key={event.id} className="flex items-center gap-4 p-3 border rounded-lg hover:bg-muted/50">
                      <div className="w-24 text-sm font-medium">{event.date}</div>
                      <Badge variant="outline">{event.activity}</Badge>
                      <span className="text-sm text-muted-foreground">{event.field}</span>
                      <span className="text-sm text-muted-foreground ml-auto">{event.trial}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
