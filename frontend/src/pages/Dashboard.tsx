/**
 * Dashboard Page - Minimalist Role-Based Design
 * Clean, focused dashboard inspired by ProQRT patterns
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { 
  AlertCircle, RefreshCw, ArrowRight, Clock, 
  Beaker, Sprout, Package, Eye, BarChart3,
  FlaskConical, Dna, MapPin, FileText,
  ClipboardList, Wheat, Plus, QrCode, Truck,
  Cog, ScanLine, Warehouse, ShieldCheck
} from 'lucide-react'
import { FunFacts } from '@/components/FunFacts'

type UserRole = 'breeder' | 'seed_company' | 'admin'

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
    return date.toLocaleDateString()
  } catch {
    return 'Recently'
  }
}

export function Dashboard() {
  const [role, setRole] = useState<UserRole>('breeder')

  // Core data queries
  const { data: programsData, isLoading: programsLoading, refetch: refetchPrograms } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.getPrograms(0, 10),
  })

  const { data: trialsData, isLoading: trialsLoading, refetch: refetchTrials } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 10),
  })

  const { data: germplasmData, isLoading: germplasmLoading, refetch: refetchGermplasm } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 10),
  })

  const { data: observationsData, isLoading: observationsLoading, refetch: refetchObservations } = useQuery({
    queryKey: ['observations'],
    queryFn: () => apiClient.getObservations(undefined, 0, 10),
  })

  const { data: seedlotsData, isLoading: seedlotsLoading, refetch: refetchSeedlots } = useQuery({
    queryKey: ['seedlots'],
    queryFn: () => apiClient.getSeedLots(undefined, 0, 10),
  })

  const programs = programsData?.result?.data || []
  const trials = trialsData?.result?.data || []
  const germplasm = germplasmData?.result?.data || []
  const observations = observationsData?.result?.data || []

  const totalPrograms = programsData?.metadata?.pagination?.totalCount || 0
  const totalTrials = trialsData?.metadata?.pagination?.totalCount || 0
  const totalGermplasm = germplasmData?.metadata?.pagination?.totalCount || 0
  const totalObservations = observationsData?.metadata?.pagination?.totalCount || 0
  const totalSeedlots = seedlotsData?.metadata?.pagination?.totalCount || 0

  const isLoading = programsLoading || trialsLoading || germplasmLoading || observationsLoading

  const refetchAll = () => {
    refetchPrograms()
    refetchTrials()
    refetchGermplasm()
    refetchObservations()
    refetchSeedlots()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with Role Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-prakruti-dhool-800 dark:text-prakruti-dhool-100">Dashboard</h1>
          <p className="text-prakruti-dhool-500 dark:text-prakruti-dhool-300 text-sm mt-1">Welcome back! Here's your overview.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">View as:</span>
          <div className="flex bg-prakruti-dhool-100 dark:bg-prakruti-dhool-800 rounded-lg p-1">
            <RoleButton 
              active={role === 'breeder'} 
              onClick={() => setRole('breeder')}
              icon={<Dna className="h-4 w-4" />}
              label="Breeder"
            />
            <RoleButton 
              active={role === 'seed_company'} 
              onClick={() => setRole('seed_company')}
              icon={<Package className="h-4 w-4" />}
              label="Seed Co."
            />
          </div>
          <Button variant="ghost" size="icon" onClick={refetchAll} className="ml-2" aria-label="Refresh data">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Role-specific Dashboard */}
      {role === 'breeder' ? (
        <BreederDashboard 
          totalPrograms={totalPrograms}
          totalTrials={totalTrials}
          totalGermplasm={totalGermplasm}
          totalObservations={totalObservations}
          programs={programs}
          trials={trials}
          germplasm={germplasm}
          observations={observations}
          isLoading={isLoading}
        />
      ) : (
        <SeedCompanyDashboard 
          totalSeedlots={totalSeedlots}
          totalGermplasm={totalGermplasm}
          isLoading={seedlotsLoading}
        />
      )}
    </div>
  )
}

/* ============================================
   ROLE BUTTON
   ============================================ */
interface RoleButtonProps {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}

function RoleButton({ active, onClick, icon, label }: RoleButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
        active 
          ? 'bg-white dark:bg-prakruti-dhool-700 text-prakruti-patta dark:text-prakruti-patta-light shadow-sm' 
          : 'text-prakruti-dhool-600 dark:text-prakruti-dhool-300 hover:text-prakruti-dhool-800 dark:hover:text-prakruti-dhool-100'
      }`}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  )
}

/* ============================================
   BREEDER DASHBOARD
   ============================================ */
interface BreederDashboardProps {
  totalPrograms: number
  totalTrials: number
  totalGermplasm: number
  totalObservations: number
  programs: any[]
  trials: any[]
  germplasm: any[]
  observations: any[]
  isLoading: boolean
}

function BreederDashboard({ 
  totalPrograms, totalTrials, totalGermplasm, totalObservations,
  programs, trials, germplasm, observations, isLoading 
}: BreederDashboardProps) {
  return (
    <>
      {/* 4 Key Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Programs" 
          value={totalPrograms} 
          icon={<Wheat className="h-5 w-5" />}
          link="/programs"
          color="green"
          isLoading={isLoading}
        />
        <StatCard 
          title="Trials" 
          value={totalTrials} 
          icon={<FlaskConical className="h-5 w-5" />}
          link="/trials"
          color="blue"
          isLoading={isLoading}
        />
        <StatCard 
          title="Germplasm" 
          value={totalGermplasm} 
          icon={<Sprout className="h-5 w-5" />}
          link="/germplasm"
          color="emerald"
          isLoading={isLoading}
        />
        <StatCard 
          title="Observations" 
          value={totalObservations} 
          icon={<Eye className="h-5 w-5" />}
          link="/observations"
          color="purple"
          isLoading={isLoading}
        />
      </div>

      {/* Main Content: Activity + Quick Actions */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Activity - Takes 2 columns */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <ActivitySkeleton />
            ) : (
              <ActivityFeed 
                observations={observations}
                trials={trials}
                germplasm={germplasm}
              />
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuickAction to="/observations/collect" icon={<ClipboardList className="h-5 w-5" />} label="Collect Data" primary />
            <QuickAction to="/programs/new" icon={<Plus className="h-5 w-5" />} label="New Program" />
            <QuickAction to="/trials/new" icon={<FlaskConical className="h-5 w-5" />} label="New Trial" />
            <QuickAction to="/germplasm/new" icon={<Sprout className="h-5 w-5" />} label="Add Germplasm" />
          </CardContent>
        </Card>
      </div>

      {/* Fun Facts */}
      <FunFacts variant="inline" showCategory={true} />

      {/* Recent Programs */}
      {programs.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-lg font-semibold">Active Programs</CardTitle>
            <Link to="/programs" className="text-sm text-prakruti-patta dark:text-prakruti-patta-light hover:text-prakruti-patta-dark dark:hover:text-green-300 flex items-center gap-1">
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {programs.slice(0, 3).map((program: any) => (
                <Link
                  key={program.programDbId}
                  to={`/programs/${program.programDbId}`}
                  className="p-4 border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 rounded-lg hover:border-prakruti-patta/40 hover:shadow-sm transition-all"
                >
                  <h3 className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100 truncate">{program.programName}</h3>
                  {program.abbreviation && (
                    <Badge variant="secondary" className="mt-2 text-xs">{program.abbreviation}</Badge>
                  )}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  )
}

/* ============================================
   SEED COMPANY DASHBOARD
   ============================================ */
interface SeedCompanyDashboardProps {
  totalSeedlots: number
  totalGermplasm: number
  isLoading: boolean
}

function SeedCompanyDashboard({ totalSeedlots, totalGermplasm, isLoading }: SeedCompanyDashboardProps) {
  // Placeholder stats for seed company view
  const pendingTests = 0
  const dispatchReady = 0
  const lowStockAlerts = 0

  return (
    <>
      {/* 4 Key Stats for Seed Company */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Seed Lots" 
          value={totalSeedlots} 
          icon={<Package className="h-5 w-5" />}
          link="/seedlots"
          color="blue"
          isLoading={isLoading}
        />
        <StatCard 
          title="Pending Tests" 
          value={pendingTests} 
          icon={<FlaskConical className="h-5 w-5" />}
          link="/quality"
          color="yellow"
          isLoading={isLoading}
        />
        <StatCard 
          title="Dispatch Ready" 
          value={dispatchReady} 
          icon={<FileText className="h-5 w-5" />}
          link="/traceability"
          color="green"
          isLoading={isLoading}
        />
        <StatCard 
          title="Low Stock" 
          value={lowStockAlerts} 
          icon={<AlertCircle className="h-5 w-5" />}
          link="/seedlots"
          color="red"
          isLoading={isLoading}
        />
      </div>

      {/* Main Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Operations Overview */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold">Operations Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Link to="/seed-operations/quality-gate" className="p-4 border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 rounded-lg hover:bg-prakruti-dhool-50 dark:hover:bg-prakruti-dhool-800 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-prakruti-patta-pale flex items-center justify-center text-prakruti-patta">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100">Quality Gate</p>
                    <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">Scan & verify lots</p>
                  </div>
                </div>
              </Link>
              <Link to="/seed-operations/batches" className="p-4 border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 rounded-lg hover:bg-prakruti-dhool-50 dark:hover:bg-prakruti-dhool-800 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-prakruti-neela-pale flex items-center justify-center text-prakruti-neela">
                    <Cog className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100">Processing</p>
                    <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">Batch management</p>
                  </div>
                </div>
              </Link>
              <Link to="/seed-operations/lots" className="p-4 border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 rounded-lg hover:bg-prakruti-dhool-50 dark:hover:bg-prakruti-dhool-800 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-prakruti-sona-pale flex items-center justify-center text-prakruti-sona-dark">
                    <Package className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100">Inventory</p>
                    <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">Seed lot tracking</p>
                  </div>
                </div>
              </Link>
              <Link to="/seed-operations/dispatch" className="p-4 border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 rounded-lg hover:bg-prakruti-dhool-50 dark:hover:bg-prakruti-dhool-800 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                    <Truck className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100">Dispatch</p>
                    <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">Create shipments</p>
                  </div>
                </div>
              </Link>
            </div>
            <div className="mt-4 pt-4 border-t">
              <Link to="/seed-operations">
                <Button variant="outline" className="w-full">
                  Open Seed Operations Dashboard →
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions for Seed Company */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuickAction to="/seedlots/new" icon={<Package className="h-5 w-5" />} label="New Seed Lot" primary />
            <QuickAction to="/quality" icon={<FlaskConical className="h-5 w-5" />} label="Lab Testing" />
            <QuickAction to="/traceability" icon={<QrCode className="h-5 w-5" />} label="Traceability" />
            <QuickAction to="/inventory" icon={<Warehouse className="h-5 w-5" />} label="Inventory" />
          </CardContent>
        </Card>
      </div>

      {/* Workflow Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <WorkflowCard 
          title="Sample Registration"
          description="Register new samples for testing"
          icon={<FlaskConical className="h-6 w-6" />}
          link="/seed-operations/samples"
          status="available"
        />
        <WorkflowCard 
          title="Lab Testing"
          description="Germination, purity, moisture"
          icon={<Beaker className="h-6 w-6" />}
          link="/seed-operations/testing"
          status="available"
        />
        <WorkflowCard 
          title="Seed Processing"
          description="Cleaning, grading, treatment"
          icon={<Package className="h-6 w-6" />}
          link="/seed-operations/stages"
          status="available"
        />
        <WorkflowCard 
          title="Dispatch"
          description="Packaging and shipping"
          icon={<MapPin className="h-6 w-6" />}
          link="/seed-operations/dispatch"
          status="available"
        />
      </div>
    </>
  )
}

/* ============================================
   HELPER COMPONENTS
   ============================================ */

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  link: string
  color: 'green' | 'blue' | 'emerald' | 'purple' | 'yellow' | 'red'
  isLoading: boolean
}

function StatCard({ title, value, icon, link, color, isLoading }: StatCardProps) {
  const colorClasses = {
    green: 'bg-prakruti-patta-pale dark:bg-green-900/20 text-prakruti-patta dark:text-green-400 border-prakruti-patta/20 dark:border-green-800/30',
    blue: 'bg-prakruti-neela-pale dark:bg-blue-900/20 text-prakruti-neela dark:text-blue-400 border-prakruti-neela/20 dark:border-blue-800/30',
    emerald: 'bg-prakruti-patta-pale dark:bg-emerald-900/20 text-prakruti-patta-light dark:text-emerald-400 border-prakruti-patta/20 dark:border-emerald-800/30',
    purple: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 border-purple-100 dark:border-purple-800/30',
    yellow: 'bg-prakruti-sona-pale dark:bg-yellow-900/20 text-prakruti-sona-dark dark:text-yellow-400 border-prakruti-sona/20 dark:border-yellow-800/30',
    red: 'bg-prakruti-laal-pale dark:bg-red-900/20 text-prakruti-laal dark:text-red-400 border-prakruti-laal/20 dark:border-red-800/30',
  }

  if (isLoading) {
    return (
      <Card className="border border-prakruti-dhool-200 dark:border-prakruti-dhool-700">
        <CardContent className="p-5">
          <Skeleton className="h-10 w-10 rounded-lg mb-3" />
          <Skeleton className="h-8 w-16 mb-1" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Link to={link}>
      <Card className="border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 hover:shadow-md hover:border-prakruti-patta/30 transition-all cursor-pointer">
        <CardContent className="p-5">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${colorClasses[color]}`}>
            {icon}
          </div>
          <p className="text-2xl font-bold text-prakruti-dhool-800 dark:text-prakruti-dhool-100">{value.toLocaleString()}</p>
          <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300">{title}</p>
        </CardContent>
      </Card>
    </Link>
  )
}

interface QuickActionProps {
  to: string
  icon: React.ReactNode
  label: string
  primary?: boolean
}

function QuickAction({ to, icon, label, primary }: QuickActionProps) {
  return (
    <Link to={to} className="block">
      <Button 
        variant={primary ? 'default' : 'outline'} 
        className={`w-full justify-start gap-3 h-11 ${primary ? 'bg-prakruti-patta hover:bg-prakruti-patta-dark' : 'border-prakruti-dhool-200 dark:border-prakruti-dhool-700 hover:bg-prakruti-dhool-100 dark:hover:bg-prakruti-dhool-800'}`}
      >
        {icon}
        <span>{label}</span>
      </Button>
    </Link>
  )
}

interface WorkflowCardProps {
  title: string
  description: string
  icon: React.ReactNode
  link: string
  status: 'available' | 'coming'
}

function WorkflowCard({ title, description, icon, link, status }: WorkflowCardProps) {
  const content = (
    <Card className={`border border-prakruti-dhool-200 dark:border-prakruti-dhool-700 h-full ${status === 'available' ? 'hover:shadow-md hover:border-prakruti-patta/40 cursor-pointer' : 'opacity-60'} transition-all`}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="w-12 h-12 rounded-lg bg-prakruti-dhool-100 dark:bg-prakruti-dhool-800 flex items-center justify-center text-prakruti-dhool-600 dark:text-prakruti-dhool-300">
            {icon}
          </div>
          {status === 'coming' && (
            <Badge variant="secondary" className="text-xs">Coming Soon</Badge>
          )}
        </div>
        <h3 className="font-semibold text-prakruti-dhool-800 dark:text-prakruti-dhool-100">{title}</h3>
        <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300 mt-1">{description}</p>
      </CardContent>
    </Card>
  )

  if (status === 'available') {
    return <Link to={link}>{content}</Link>
  }
  return content
}

function ActivitySkeleton() {
  return (
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
  )
}

interface ActivityFeedProps {
  observations: any[]
  trials: any[]
  germplasm: any[]
}

function ActivityFeed({ observations, trials, germplasm }: ActivityFeedProps) {
  const activities: { icon: React.ReactNode; iconBg: string; title: string; subtitle: string; time: string; link: string }[] = []

  observations.slice(0, 3).forEach((obs: any) => {
    activities.push({
      icon: <ClipboardList className="h-4 w-4" />,
      iconBg: 'bg-purple-100 text-purple-600',
      title: 'Observation recorded',
      subtitle: obs.observationVariableName || 'Unknown trait',
      time: formatRelativeTime(obs.observationTimeStamp),
      link: '/observations',
    })
  })

  trials.slice(0, 2).forEach((trial: any) => {
    activities.push({
      icon: <FlaskConical className="h-4 w-4" />,
      iconBg: 'bg-blue-100 text-blue-600',
      title: trial.trialName || 'Trial',
      subtitle: trial.programName || 'Unknown program',
      time: formatRelativeTime(trial.startDate),
      link: trial.trialDbId ? `/trials/${trial.trialDbId}` : '/trials',
    })
  })

  germplasm.slice(0, 2).forEach((germ: any) => {
    activities.push({
      icon: <Sprout className="h-4 w-4" />,
      iconBg: 'bg-green-100 text-green-600',
      title: germ.germplasmName || 'Germplasm',
      subtitle: germ.commonCropName || germ.genus || 'Unknown',
      time: formatRelativeTime(germ.acquisitionDate),
      link: germ.germplasmDbId ? `/germplasm/${germ.germplasmDbId}` : '/germplasm',
    })
  })

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="w-12 h-12 rounded-full bg-prakruti-dhool-100 dark:bg-prakruti-dhool-800 flex items-center justify-center mx-auto mb-3">
          <BarChart3 className="h-6 w-6 text-prakruti-dhool-400 dark:text-prakruti-dhool-300" />
        </div>
        <p className="text-prakruti-dhool-600 dark:text-prakruti-dhool-300">No recent activity</p>
        <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300 mt-1">Start by creating programs and collecting data</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {activities.slice(0, 5).map((activity, i) => (
        <Link
          key={i}
          to={activity.link}
          className="flex items-center gap-3 p-3 rounded-lg hover:bg-prakruti-dhool-50 dark:hover:bg-prakruti-dhool-800 transition-colors"
        >
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${activity.iconBg}`}>
            {activity.icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-prakruti-dhool-800 dark:text-prakruti-dhool-100 truncate">{activity.title}</p>
            <p className="text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-300 truncate">{activity.subtitle}</p>
          </div>
          <div className="flex items-center gap-1 text-xs text-prakruti-dhool-400 dark:text-prakruti-dhool-300 whitespace-nowrap">
            <Clock className="h-3 w-3" />
            {activity.time}
          </div>
        </Link>
      ))}
    </div>
  )
}
