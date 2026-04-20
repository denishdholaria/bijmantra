/**
 * Crop Protection Dashboard
 * Overview of pest observations, disease forecasts, spray applications, and IPM strategies
 */
import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api-client'
import { Link } from 'react-router-dom'
import {
  Bug,
  AlertTriangle,
  Droplets,
  Shield,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react'
import {
  DiseaseRiskForecastRecord,
  IPMStrategyRecord,
  PestObservationRecord,
  SprayApplicationRecord,
  SprayComplianceReport,
  average,
  riskRank,
} from '../lib/cropProtection'

export function CropProtectionDashboard() {
  const { data: pestsData, isLoading: pestsLoading } = useQuery<PestObservationRecord[]>({
    queryKey: ['future', 'pest-observations'],
    queryFn: async () => apiClient.get('/api/v2/future/pest-observations/'),
  })

  const { data: diseaseData, isLoading: diseaseLoading } = useQuery<DiseaseRiskForecastRecord[]>({
    queryKey: ['future', 'disease-risk-forecasts'],
    queryFn: async () => apiClient.get('/api/v2/future/disease-risk-forecasts/'),
  })

  const { data: sprayData, isLoading: sprayLoading } = useQuery<SprayApplicationRecord[]>({
    queryKey: ['future', 'spray-applications'],
    queryFn: async () => apiClient.get('/api/v2/future/spray-applications/'),
  })

  const { data: sprayCompliance, isLoading: complianceLoading } = useQuery<SprayComplianceReport>({
    queryKey: ['future', 'spray-applications', 'compliance-report'],
    queryFn: async () => apiClient.get('/api/v2/future/spray-applications/compliance-report'),
  })

  const { data: ipmData, isLoading: ipmLoading } = useQuery<IPMStrategyRecord[]>({
    queryKey: ['future', 'ipm-strategies'],
    queryFn: async () => apiClient.get('/api/v2/future/ipm-strategies/'),
  })

  const isLoading = pestsLoading || diseaseLoading || sprayLoading || ipmLoading || complianceLoading

  const summary = useMemo(() => {
    const pests = pestsData ?? []
    const diseaseForecasts = diseaseData ?? []
    const sprayApplications = sprayData ?? []
    const ipmStrategies = ipmData ?? []

    const highSeverityPests = pests.filter((entry) => (entry.severity_score ?? 0) >= 6)
    const highRiskForecasts = diseaseForecasts.filter((entry) => riskRank(entry.risk_level) >= 3)
    const avgPestSeverity = average(pests.map((entry) => entry.severity_score))
    const avgRiskScore = average(diseaseForecasts.map((entry) => entry.risk_score))

    return {
      pests: pests.length,
      highSeverityPests: highSeverityPests.length,
      avgPestSeverity,
      diseases: diseaseForecasts.length,
      highRiskForecasts: highRiskForecasts.length,
      avgRiskScore,
      sprays: sprayApplications.length,
      treatedArea: sprayApplications.reduce((sum, entry) => sum + (entry.total_area_ha ?? 0), 0),
      complianceRate: sprayCompliance?.compliance_rate ?? 0,
      ipm: ipmStrategies.length,
      activeStrategies: ipmStrategies.filter((entry) => {
        const now = Date.now()
        const hasStarted = !entry.implementation_start || new Date(entry.implementation_start).getTime() <= now
        const notEnded = !entry.implementation_end || new Date(entry.implementation_end).getTime() >= now
        return hasStarted && notEnded
      }).length,
    }
  }, [diseaseData, ipmData, pestsData, sprayCompliance, sprayData])

  const modules = [
    {
      title: 'Pest Observations',
      description: 'Scouting, incidence, and field severity tracking',
      icon: Bug,
      count: summary.pests,
      route: '/crop-protection/pest-observations',
      helperText: `${summary.highSeverityPests} urgent records`,
      color: 'text-amber-500',
      bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    },
    {
      title: 'Disease Risk Forecasts',
      description: 'Active disease pressure models and advisories',
      icon: AlertTriangle,
      count: summary.diseases,
      route: '/crop-protection/disease-risk-forecast',
      helperText: `${summary.highRiskForecasts} high-risk windows`,
      color: 'text-red-500',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
    },
    {
      title: 'Spray Applications',
      description: 'Operational records, rates, and compliance checks',
      icon: Droplets,
      count: summary.sprays,
      route: '/crop-protection/spray-applications',
      helperText: `${summary.treatedArea.toFixed(1)} ha treated`,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      title: 'IPM Strategies',
      description: 'Threshold-driven prevention and intervention plans',
      icon: Shield,
      count: summary.ipm,
      route: '/crop-protection/ipm-strategies',
      helperText: `${summary.activeStrategies} active strategies`,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Shield className="h-8 w-8 text-emerald-600" />
            Crop Protection
          </h1>
          <p className="text-muted-foreground mt-1 max-w-2xl">
            Coordinate scouting, forecast disease pressure, manage spray applications, and activate IPM playbooks from one domain workspace.
          </p>
        </div>
        <Badge variant="outline" className="text-xs uppercase tracking-[0.2em]">
          Preview
        </Badge>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
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
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{module.count}</p>
                      <p className="text-xs text-muted-foreground">{module.helperText}</p>
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

          <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <Card>
              <CardHeader>
                <CardTitle>Operational readiness</CardTitle>
                <CardDescription>Live indicators generated from the crop protection records already stored in the platform.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-amber-200/70 bg-amber-50/70 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                  <p className="text-xs uppercase tracking-[0.18em] text-amber-700 dark:text-amber-300">Scouting pressure</p>
                  <p className="mt-2 text-2xl font-semibold">{summary.avgPestSeverity?.toFixed(1) ?? '—'}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Average severity score across pest observations</p>
                </div>
                <div className="rounded-2xl border border-red-200/70 bg-red-50/70 p-4 dark:border-red-900/50 dark:bg-red-950/20">
                  <p className="text-xs uppercase tracking-[0.18em] text-red-700 dark:text-red-300">Disease model score</p>
                  <p className="mt-2 text-2xl font-semibold">{summary.avgRiskScore !== null ? `${Math.round(summary.avgRiskScore * 100)}%` : '—'}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Average risk score from model outputs</p>
                </div>
                <div className="rounded-2xl border border-blue-200/70 bg-blue-50/70 p-4 dark:border-blue-900/50 dark:bg-blue-950/20">
                  <p className="text-xs uppercase tracking-[0.18em] text-blue-700 dark:text-blue-300">Compliance rate</p>
                  <p className="mt-2 text-2xl font-semibold">{summary.complianceRate.toFixed(0)}%</p>
                  <p className="mt-1 text-xs text-muted-foreground">Applications with PHI and REI captured</p>
                </div>
                <div className="rounded-2xl border border-emerald-200/70 bg-emerald-50/70 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
                  <p className="text-xs uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Active plans</p>
                  <p className="mt-2 text-2xl font-semibold">{summary.activeStrategies}</p>
                  <p className="mt-1 text-xs text-muted-foreground">IPM strategies currently in force</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Immediate actions</CardTitle>
                <CardDescription>Navigate directly to the work queue that needs attention.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link className="flex items-center justify-between rounded-2xl border p-3 transition hover:bg-muted/40" to="/crop-protection/pest-observations">
                  <div>
                    <p className="font-medium">Urgent scouting follow-up</p>
                    <p className="text-sm text-muted-foreground">{summary.highSeverityPests} pest observations are above the action threshold.</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
                <Link className="flex items-center justify-between rounded-2xl border p-3 transition hover:bg-muted/40" to="/crop-protection/disease-risk-forecast">
                  <div>
                    <p className="font-medium">High-risk disease windows</p>
                    <p className="text-sm text-muted-foreground">{summary.highRiskForecasts} forecast windows need preventive planning.</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
                <Link className="flex items-center justify-between rounded-2xl border p-3 transition hover:bg-muted/40" to="/crop-protection/spray-applications">
                  <div>
                    <p className="font-medium">Compliance review</p>
                    <p className="text-sm text-muted-foreground">Inspect recorded PHI/REI intervals and treated area totals.</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
                <Link className="flex items-center justify-between rounded-2xl border p-3 transition hover:bg-muted/40" to="/crop-protection/ipm-strategies">
                  <div>
                    <p className="font-medium">Strategy coverage</p>
                    <p className="text-sm text-muted-foreground">Maintain prevention, monitoring, and intervention plans by crop.</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {!isLoading && summary.pests === 0 && summary.diseases === 0 && summary.sprays === 0 && summary.ipm === 0 && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            Crop Protection is ready for live use. Start by recording a scouting observation, generating a disease forecast, or logging a spray application.
          </AlertDescription>
        </Alert>
      )}

      {!isLoading && summary.highRiskForecasts > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {summary.highRiskForecasts} disease forecast{summary.highRiskForecasts === 1 ? '' : 's'} are currently high or critical. Review recommendations before the next field operation.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
