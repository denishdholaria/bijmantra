/**
 * Dashboard Page - Enhanced
 * Overview of breeding programs with activity feed and getting started guide
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, RefreshCw, ArrowRight, CheckCircle2, Sparkles, TrendingUp, Clock } from 'lucide-react'

// Helper to format relative time
function formatRelativeTime(dateString: string | undefined): string {
  if (!dateString) return 'Recently'
  
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
    return date.toLocaleDateString()
  } catch {
    return 'Recently'
  }
}

export function Dashboard() {
  const { data: programsData, isLoading: programsLoading, error: programsError, refetch: refetchPrograms } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.getPrograms(0, 10),
  })

  const { data: trialsData, isLoading: trialsLoading, error: trialsError, refetch: refetchTrials } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 10),
  })

  const { data: studiesData, isLoading: studiesLoading, error: studiesError, refetch: refetchStudies } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 10),
  })

  const { data: locationsData, isLoading: locationsLoading, error: locationsError, refetch: refetchLocations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.getLocations(0, 10),
  })

  const { data: germplasmData, isLoading: germplasmLoading, error: germplasmError, refetch: refetchGermplasm } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 10),
  })

  const { data: traitsData, isLoading: traitsLoading, error: traitsError, refetch: refetchTraits } = useQuery({
    queryKey: ['variables'],
    queryFn: () => apiClient.getObservationVariables(0, 10),
  })

  const { data: observationsData, isLoading: observationsLoading, error: observationsError, refetch: refetchObservations } = useQuery({
    queryKey: ['observations'],
    queryFn: () => apiClient.getObservations(undefined, 0, 10),
  })

  const { data: seedlotsData, isLoading: seedlotsLoading, error: seedlotsError, refetch: refetchSeedlots } = useQuery({
    queryKey: ['seedlots'],
    queryFn: () => apiClient.getSeedLots(undefined, 0, 10),
  })

  const programs = programsData?.result?.data || []
  const trials = trialsData?.result?.data || []
  const observations = observationsData?.result?.data || []
  const germplasm = germplasmData?.result?.data || []

  // Calculate totals for "Getting Started" progress
  const totalPrograms = programsData?.metadata?.pagination?.totalCount || 0
  const totalGermplasm = germplasmData?.metadata?.pagination?.totalCount || 0
  const totalTrials = trialsData?.metadata?.pagination?.totalCount || 0
  const totalObservations = observationsData?.metadata?.pagination?.totalCount || 0

  const isNewUser = totalPrograms === 0 && totalGermplasm === 0 && totalTrials === 0

  // Check for any errors
  const hasErrors = programsError || trialsError || studiesError || locationsError || 
                    germplasmError || traitsError || observationsError || seedlotsError

  const refetchAll = () => {
    refetchPrograms()
    refetchTrials()
    refetchStudies()
    refetchLocations()
    refetchGermplasm()
    refetchTraits()
    refetchObservations()
    refetchSeedlots()
  }

  return (
    <div className="space-y-4 lg:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl lg:rounded-2xl shadow-xl p-4 lg:p-8 text-white">
        <h1 className="text-2xl lg:text-4xl font-bold mb-1 lg:mb-2">Dashboard</h1>
        <p className="text-green-100 text-sm lg:text-lg">Overview of your breeding programs and activities</p>
      </div>

      {/* Error Banner */}
      {hasErrors && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span className="text-red-700">Some data failed to load. Check your connection or backend status.</span>
            </div>
            <Button variant="outline" size="sm" onClick={refetchAll} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Retry All
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 lg:gap-4">
        <StatCard
          title="Programs"
          count={programsData?.metadata?.pagination?.totalCount || 0}
          icon="🌾"
          link="/programs"
          isLoading={programsLoading}
          error={programsError}
          onRetry={refetchPrograms}
        />
        <StatCard
          title="Germplasm"
          count={germplasmData?.metadata?.pagination?.totalCount || 0}
          icon="🌱"
          link="/germplasm"
          isLoading={germplasmLoading}
          error={germplasmError}
          onRetry={refetchGermplasm}
        />
        <StatCard
          title="Trials"
          count={trialsData?.metadata?.pagination?.totalCount || 0}
          icon="🧪"
          link="/trials"
          isLoading={trialsLoading}
          error={trialsError}
          onRetry={refetchTrials}
        />
        <StatCard
          title="Studies"
          count={studiesData?.metadata?.pagination?.totalCount || 0}
          icon="📊"
          link="/studies"
          isLoading={studiesLoading}
          error={studiesError}
          onRetry={refetchStudies}
        />
        <StatCard
          title="Traits"
          count={traitsData?.metadata?.pagination?.totalCount || 0}
          icon="🔬"
          link="/traits"
          isLoading={traitsLoading}
          error={traitsError}
          onRetry={refetchTraits}
        />
        <StatCard
          title="Locations"
          count={locationsData?.metadata?.pagination?.totalCount || 0}
          icon="📍"
          link="/locations"
          isLoading={locationsLoading}
          error={locationsError}
          onRetry={refetchLocations}
        />
        <StatCard
          title="Observations"
          count={observationsData?.metadata?.pagination?.totalCount || 0}
          icon="📋"
          link="/observations"
          isLoading={observationsLoading}
          error={observationsError}
          onRetry={refetchObservations}
        />
        <StatCard
          title="Seed Lots"
          count={seedlotsData?.metadata?.pagination?.totalCount || 0}
          icon="📦"
          link="/seedlots"
          isLoading={seedlotsLoading}
          error={seedlotsError}
          onRetry={refetchSeedlots}
        />
      </div>


      {/* Getting Started Section - Show for new users */}
      {isNewUser && !programsLoading && !germplasmLoading && (
        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <Sparkles className="h-5 w-5" />
              Getting Started with Bijmantra
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-6">
              Welcome! Follow these steps to set up your first breeding program.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <GettingStartedStep
                step={1}
                title="Create a Program"
                description="Set up your breeding program with objectives and team"
                link="/programs/new"
                completed={totalPrograms > 0}
              />
              <GettingStartedStep
                step={2}
                title="Add Germplasm"
                description="Register your plant genetic resources"
                link="/germplasm/new"
                completed={totalGermplasm > 0}
              />
              <GettingStartedStep
                step={3}
                title="Set Up a Trial"
                description="Create field trials to evaluate germplasm"
                link="/trials/new"
                completed={totalTrials > 0}
              />
              <GettingStartedStep
                step={4}
                title="Collect Data"
                description="Record observations and measurements"
                link="/observations/collect"
                completed={totalObservations > 0}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Progress Summary - Show for returning users with data */}
      {!isNewUser && !programsLoading && (
        <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-blue-800 text-lg">
              <TrendingUp className="h-5 w-5" />
              Your Breeding Progress
            </CardTitle>
            <CardDescription>Overview of your data collection journey</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <ProgressItem label="Programs" count={totalPrograms} target={5} />
              <ProgressItem label="Germplasm" count={totalGermplasm} target={100} />
              <ProgressItem label="Trials" count={totalTrials} target={10} />
              <ProgressItem label="Observations" count={totalObservations} target={1000} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-2 gap-4 lg:gap-6">
        {/* Recent Programs */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Recent Programs</CardTitle>
            <Link
              to="/programs"
              className="text-sm text-green-600 hover:text-green-700 font-medium flex items-center gap-1"
            >
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {programsLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="p-4 border rounded-lg">
                    <Skeleton className="h-5 w-3/4 mb-2" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                ))}
              </div>
            ) : programsError ? (
              <ErrorState message="Failed to load programs" onRetry={refetchPrograms} />
            ) : programs.length === 0 ? (
              <EmptyState
                icon="🌾"
                message="No programs yet"
                actionLabel="Create your first program"
                actionLink="/programs/new"
              />
            ) : (
              <div className="space-y-3">
                {programs.slice(0, 5).map((program: any) => (
                  <Link
                    key={program.programDbId}
                    to={`/programs/${program.programDbId}`}
                    className="block p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{program.programName}</h3>
                        {program.abbreviation && (
                          <span className="text-sm text-gray-500">{program.abbreviation}</span>
                        )}
                        {program.objective && (
                          <p className="text-sm text-gray-600 mt-1 line-clamp-1">{program.objective}</p>
                        )}
                      </div>
                      <ArrowRight className="h-4 w-4 text-gray-400" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity Feed */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {(observationsLoading || trialsLoading || germplasmLoading) ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 border rounded-lg">
                    <Skeleton className="h-8 w-8 rounded-full" />
                    <div className="flex-1">
                      <Skeleton className="h-4 w-3/4 mb-1" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (observationsError && trialsError && germplasmError) ? (
              <ErrorState message="Failed to load activity" onRetry={refetchAll} />
            ) : (
              <RecentActivityFeed
                observations={observations}
                trials={trials}
                germplasm={germplasm}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4">
            <QuickActionButton to="/programs/new" icon="🌾" label="New Program" />
            <QuickActionButton to="/germplasm/new" icon="🌱" label="New Germplasm" />
            <QuickActionButton to="/traits/new" icon="🔬" label="New Trait" />
            <QuickActionButton to="/trials/new" icon="🧪" label="New Trial" />
            <QuickActionButton to="/studies/new" icon="📊" label="New Study" />
            <QuickActionButton to="/locations/new" icon="📍" label="New Location" />
            <QuickActionButton to="/observations/collect" icon="📝" label="Collect Data" primary />
            <QuickActionButton to="/seedlots/new" icon="📦" label="New Seed Lot" />
            <QuickActionButton to="/crosses/new" icon="🧬" label="New Cross" />
            <QuickActionButton to="/search" icon="🔍" label="Search" />
            <QuickActionButton to="/import-export" icon="🔄" label="Import/Export" />
            <QuickActionButton to="/reports" icon="📈" label="Reports" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


/* ============================================
   HELPER COMPONENTS
   ============================================ */

interface StatCardProps {
  title: string
  count: number
  icon: string
  link: string
  isLoading: boolean
  error: unknown
  onRetry: () => void
}

function StatCard({ title, count, icon, link, isLoading, error, onRetry }: StatCardProps) {
  if (isLoading) {
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 text-center">
          <Skeleton className="h-8 w-8 mx-auto mb-2 rounded" />
          <Skeleton className="h-6 w-12 mx-auto mb-1" />
          <Skeleton className="h-4 w-16 mx-auto" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="hover:shadow-md transition-shadow border-red-200">
        <CardContent className="p-4 text-center">
          <span className="text-2xl mb-1 block">⚠️</span>
          <p className="text-xs text-red-600 mb-2">{title}</p>
          <Button variant="ghost" size="sm" onClick={onRetry} className="h-6 text-xs">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Link to={link}>
      <Card className="hover:shadow-md hover:border-green-300 transition-all cursor-pointer">
        <CardContent className="p-4 text-center">
          <span className="text-2xl mb-1 block">{icon}</span>
          <p className="text-2xl font-bold text-gray-900">{count}</p>
          <p className="text-xs text-gray-500">{title}</p>
        </CardContent>
      </Card>
    </Link>
  )
}

interface GettingStartedStepProps {
  step: number
  title: string
  description: string
  link: string
  completed: boolean
}

function GettingStartedStep({ step, title, description, link, completed }: GettingStartedStepProps) {
  return (
    <Link
      to={link}
      className={`block p-4 rounded-lg border-2 transition-all ${
        completed
          ? 'border-green-300 bg-green-50'
          : 'border-gray-200 hover:border-green-300 hover:bg-white'
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        {completed ? (
          <CheckCircle2 className="h-5 w-5 text-green-600" />
        ) : (
          <span className="w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs flex items-center justify-center font-bold">
            {step}
          </span>
        )}
        <h4 className={`font-medium ${completed ? 'text-green-700' : 'text-gray-900'}`}>{title}</h4>
      </div>
      <p className="text-sm text-gray-600">{description}</p>
    </Link>
  )
}

interface ErrorStateProps {
  message: string
  onRetry: () => void
}

function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="text-center py-8">
      <AlertCircle className="h-10 w-10 text-red-400 mx-auto mb-3" />
      <p className="text-gray-600 mb-3">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
        <RefreshCw className="h-4 w-4" />
        Retry
      </Button>
    </div>
  )
}

interface EmptyStateProps {
  icon: string
  message: string
  actionLabel: string
  actionLink: string
}

function EmptyState({ icon, message, actionLabel, actionLink }: EmptyStateProps) {
  return (
    <div className="text-center py-8">
      <span className="text-4xl mb-3 block">{icon}</span>
      <p className="text-gray-600 mb-3">{message}</p>
      <Link to={actionLink}>
        <Button variant="outline" size="sm" className="gap-2">
          {actionLabel}
          <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>
    </div>
  )
}

interface RecentActivityFeedProps {
  observations: any[]
  trials: any[]
  germplasm: any[]
}

function RecentActivityFeed({ observations, trials, germplasm }: RecentActivityFeedProps) {
  // Combine and sort recent items
  const activities: { type: string; icon: string; title: string; subtitle: string; time: string; link?: string }[] = []

  observations.slice(0, 3).forEach((obs: any) => {
    activities.push({
      type: 'observation',
      icon: '📋',
      title: `Observation recorded`,
      subtitle: obs.observationVariableName || 'Unknown trait',
      time: formatRelativeTime(obs.observationTimeStamp),
      link: '/observations',
    })
  })

  trials.slice(0, 2).forEach((trial: any) => {
    activities.push({
      type: 'trial',
      icon: '🧪',
      title: trial.trialName || 'Trial',
      subtitle: trial.programName || 'Unknown program',
      time: formatRelativeTime(trial.startDate),
      link: trial.trialDbId ? `/trials/${trial.trialDbId}` : '/trials',
    })
  })

  germplasm.slice(0, 2).forEach((germ: any) => {
    activities.push({
      type: 'germplasm',
      icon: '🌱',
      title: germ.germplasmName || 'Germplasm',
      subtitle: germ.commonCropName || germ.genus || 'Unknown',
      time: formatRelativeTime(germ.acquisitionDate),
      link: germ.germplasmDbId ? `/germplasm/${germ.germplasmDbId}` : '/germplasm',
    })
  })

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <span className="text-4xl mb-3 block">📊</span>
        <p className="text-gray-600">No recent activity</p>
        <p className="text-sm text-gray-500 mt-1">Start by creating programs and collecting data</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {activities.slice(0, 5).map((activity, i) => (
        <Link
          key={i}
          to={activity.link || '#'}
          className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 hover:border-green-200 transition-all cursor-pointer"
        >
          <span className="text-xl">{activity.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-gray-900 truncate">{activity.title}</p>
            <p className="text-sm text-gray-500 truncate">{activity.subtitle}</p>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-400 whitespace-nowrap">
            <Clock className="h-3 w-3" />
            {activity.time}
          </div>
        </Link>
      ))}
    </div>
  )
}

interface QuickActionButtonProps {
  to: string
  icon: string
  label: string
  primary?: boolean
}

function QuickActionButton({ to, icon, label, primary }: QuickActionButtonProps) {
  return (
    <Link to={to}>
      <Button
        variant={primary ? 'default' : 'outline'}
        className={`w-full h-auto py-4 flex flex-col gap-2 ${
          primary ? 'bg-green-600 hover:bg-green-700' : ''
        }`}
      >
        <span className="text-2xl">{icon}</span>
        <span className="text-xs">{label}</span>
      </Button>
    </Link>
  )
}

interface ProgressItemProps {
  label: string
  count: number
  target: number
}

function ProgressItem({ label, count, target }: ProgressItemProps) {
  const percentage = Math.min((count / target) * 100, 100)
  
  return (
    <div className="text-center">
      <p className="text-2xl font-bold text-blue-900">{count.toLocaleString()}</p>
      <p className="text-xs text-gray-600 mb-2">{label}</p>
      <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden">
        <div 
          className="h-full bg-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-1">
        {percentage >= 100 ? '🎉 Goal reached!' : `${Math.round(percentage)}% of ${target}`}
      </p>
    </div>
  )
}
