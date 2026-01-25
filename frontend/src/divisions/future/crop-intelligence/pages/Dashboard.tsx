/**
 * Crop Intelligence Dashboard
 * Overview of GDD tracking, crop calendars, suitability assessments, and yield predictions
 */
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'
import { Link } from 'react-router-dom'
import { 
  Thermometer, Calendar, MapPin, TrendingUp, 
  AlertCircle, ArrowRight, RefreshCw, Leaf 
} from 'lucide-react'

interface SummaryStats {
  gddLogs: number
  calendars: number
  suitabilityAssessments: number
  yieldPredictions: number
}

export function CropIntelligenceDashboard() {
  // Fetch summary counts from each endpoint
  const { data: gddData, isLoading: gddLoading } = useQuery({
    queryKey: ['future', 'gdd'],
    queryFn: () => apiClient.get('/api/v2/future/gdd/'),
  })

  const { data: calendarData, isLoading: calendarLoading } = useQuery({
    queryKey: ['future', 'crop-calendar'],
    queryFn: () => apiClient.get('/api/v2/future/crop-calendar/'),
  })

  const { data: suitabilityData, isLoading: suitabilityLoading } = useQuery({
    queryKey: ['future', 'crop-suitability'],
    queryFn: () => apiClient.get('/api/v2/future/crop-suitability/'),
  })

  const { data: predictionData, isLoading: predictionLoading } = useQuery({
    queryKey: ['future', 'yield-prediction'],
    queryFn: () => apiClient.get('/api/v2/future/yield-prediction/'),
  })

  const isLoading = gddLoading || calendarLoading || suitabilityLoading || predictionLoading

  const stats: SummaryStats = {
    gddLogs: Array.isArray(gddData) ? gddData.length : 0,
    calendars: Array.isArray(calendarData) ? calendarData.length : 0,
    suitabilityAssessments: Array.isArray(suitabilityData) ? suitabilityData.length : 0,
    yieldPredictions: Array.isArray(predictionData) ? predictionData.length : 0,
  }

  const modules = [
    {
      title: 'GDD Tracker',
      description: 'Monitor growing degree days for crop development',
      icon: Thermometer,
      count: stats.gddLogs,
      route: '/crop-intelligence/gdd-tracker',
      color: 'text-orange-500',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    },
    {
      title: 'Crop Calendar',
      description: 'Plan planting and harvest schedules',
      icon: Calendar,
      count: stats.calendars,
      route: '/crop-intelligence/crop-calendar',
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      title: 'Suitability Analysis',
      description: 'Assess crop-location compatibility using FAO framework',
      icon: MapPin,
      count: stats.suitabilityAssessments,
      route: '/crop-intelligence/crop-suitability',
      color: 'text-green-500',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      title: 'Yield Prediction',
      description: 'ML-based yield forecasting with confidence intervals',
      icon: TrendingUp,
      count: stats.yieldPredictions,
      route: '/crop-intelligence/yield-prediction',
      color: 'text-purple-500',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Leaf className="h-8 w-8 text-emerald-500" />
            Crop Intelligence
          </h1>
          <p className="text-muted-foreground mt-1">
            Data-driven insights for crop planning and management
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          Future Module • Preview
        </Badge>
      </div>

      {/* Module Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map((module) => (
            <Card key={module.title} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className={`w-10 h-10 rounded-lg ${module.bgColor} flex items-center justify-center mb-2`}>
                  <module.icon className={`h-5 w-5 ${module.color}`} />
                </div>
                <CardTitle className="text-base">{module.title}</CardTitle>
                <CardDescription className="text-xs">{module.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{module.count}</p>
                    <p className="text-xs text-muted-foreground">records</p>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link to={module.route}>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && stats.gddLogs === 0 && stats.calendars === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No crop intelligence data yet. Start by creating GDD logs or crop calendars.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
