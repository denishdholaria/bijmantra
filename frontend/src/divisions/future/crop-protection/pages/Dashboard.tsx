/**
 * Crop Protection Dashboard
 * Overview of pest observations, disease forecasts, spray applications, and IPM strategies
 */
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'
import { Link } from 'react-router-dom'
import { Bug, AlertTriangle, Droplets, Shield, AlertCircle, ArrowRight } from 'lucide-react'

export function CropProtectionDashboard() {
  const { data: pestsData, isLoading: pestsLoading } = useQuery({
    queryKey: ['future', 'pest-observations'],
    queryFn: () => apiClient.get('/api/v2/future/pest-observation/'),
  })

  const { data: diseaseData, isLoading: diseaseLoading } = useQuery({
    queryKey: ['future', 'disease-risk-forecast'],
    queryFn: () => apiClient.get('/api/v2/future/disease-risk-forecast/'),
  })

  const { data: sprayData, isLoading: sprayLoading } = useQuery({
    queryKey: ['future', 'spray-applications'],
    queryFn: () => apiClient.get('/api/v2/future/spray-application/'),
  })

  const { data: ipmData, isLoading: ipmLoading } = useQuery({
    queryKey: ['future', 'ipm-strategies'],
    queryFn: () => apiClient.get('/api/v2/future/ipm-strategy/'),
  })

  const isLoading = pestsLoading || diseaseLoading || sprayLoading || ipmLoading

  const stats = {
    pests: Array.isArray(pestsData) ? pestsData.length : 0,
    diseases: Array.isArray(diseaseData) ? diseaseData.length : 0,
    sprays: Array.isArray(sprayData) ? sprayData.length : 0,
    ipm: Array.isArray(ipmData) ? ipmData.length : 0,
  }

  const modules = [
    {
      title: 'Pest Observations',
      description: 'Field scouting records and pest identification',
      icon: Bug,
      count: stats.pests,
      route: '/crop-protection/pest-observations',
      color: 'text-amber-500',
      bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    },
    {
      title: 'Disease Risk Forecast',
      description: 'Weather-based disease prediction models',
      icon: AlertTriangle,
      count: stats.diseases,
      route: '/crop-protection/disease-risk-forecast',
      color: 'text-red-500',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
    },
    {
      title: 'Spray Applications',
      description: 'Pesticide application records and scheduling',
      icon: Droplets,
      count: stats.sprays,
      route: '/crop-protection/spray-applications',
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      title: 'IPM Strategies',
      description: 'Integrated pest management action thresholds',
      icon: Shield,
      count: stats.ipm,
      route: '/crop-protection/ipm-strategies',
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Shield className="h-8 w-8 text-emerald-600" />
            Crop Protection
          </h1>
          <p className="text-muted-foreground mt-1">
            Integrated pest and disease management
          </p>
        </div>
        <Badge variant="outline" className="text-xs">Future Module • Preview</Badge>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-40" />)}
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
                    <Link to={module.route}><ArrowRight className="h-4 w-4" /></Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isLoading && stats.pests === 0 && stats.diseases === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No crop protection data yet. Start by recording pest observations or disease forecasts.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
