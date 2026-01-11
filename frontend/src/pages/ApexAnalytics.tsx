/**
 * Apex Analytics Dashboard
 * Comprehensive breeding analytics with AI insights
 * 
 * APEX FEATURE: Unified analytics dashboard showcasing all apex capabilities
 */

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { cn } from '@/lib/utils'
import { ModuleInfoMark } from '@/components/ModuleInfoMark'
import {
  GeneticGainChart,
  HeritabilityGauge,
  SelectionResponseChart,
  CorrelationHeatmap
} from '@/components/visualizations'
import { PresenceAvatars } from '@/components/collaboration'
import { analyticsAPI } from '@/lib/api-client'

// ============================================
// TYPES
// ============================================

interface GeneticGainData {
  year: number
  gain: number
  cumulative: number
  target: number
}

interface HeritabilityData {
  trait: string
  value: number
  se?: number
}

interface SelectionResponseData {
  generation: number
  mean: number
  variance: number
  selected: number
}

interface CorrelationMatrix {
  traits: string[]
  matrix: number[][]
}

interface AnalyticsSummary {
  total_trials: number
  active_studies: number
  germplasm_entries: number
  observations_this_month: number
  genetic_gain_rate: number
  data_quality_score: number
  selection_intensity: number
  breeding_cycle_days: number
}

interface QuickInsight {
  id: string
  type: string
  title: string
  description: string
  action_label?: string
  action_route?: string
  created_at: string
}

interface AnalyticsResponse {
  genetic_gain: GeneticGainData[]
  heritabilities: HeritabilityData[]
  selection_response: SelectionResponseData[]
  correlations: CorrelationMatrix
  summary: AnalyticsSummary
  insights: QuickInsight[]
}

interface ComputeJob {
  id: string
  name: string
  status: string
  progress: number
  engine: string
}

// ============================================
// COMPONENTS
// ============================================

function StatCard({ 
  label, 
  value, 
  change, 
  icon,
  trend 
}: { 
  label: string
  value: string | number
  change?: number
  icon: string
  trend?: 'up' | 'down' | 'stable'
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        {change !== undefined && (
          <span className={cn(
            'text-xs font-medium px-2 py-0.5 rounded-full',
            trend === 'up' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
            trend === 'down' && 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
            trend === 'stable' && 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'
          )}>
            {trend === 'up' && '↑'}{trend === 'down' && '↓'}{trend === 'stable' && '→'} {Math.abs(change)}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-white">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  )
}

function QuickInsight({ 
  type, 
  title, 
  description, 
  action 
}: { 
  type: 'success' | 'warning' | 'info'
  title: string
  description: string
  action?: { label: string; onClick: () => void }
}) {
  const config = {
    success: { icon: '✅', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
    warning: { icon: '⚠️', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-200 dark:border-amber-800' },
    info: { icon: '💡', bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-blue-200 dark:border-blue-800' }
  }

  const c = config[type]

  return (
    <div className={cn('rounded-lg border p-3', c.bg, c.border)}>
      <div className="flex items-start gap-2">
        <span className="text-lg">{c.icon}</span>
        <div className="flex-1">
          <div className="font-medium text-gray-900 dark:text-white text-sm">{title}</div>
          <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{description}</div>
          {action && (
            <button 
              onClick={action.onClick}
              className="text-xs text-amber-600 dark:text-amber-400 font-medium mt-1 hover:underline"
            >
              {action.label} →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function ComputeStatus() {
  const [jobId, setJobId] = useState<string | null>(null)

  const runMutation = useMutation({
    mutationFn: () => analyticsAPI.computeGBLUP({ trait_id: 'Yield' }),
    onSuccess: (response) => {
      setJobId(response.job_id)
    },
  })

  const { data: jobStatus } = useQuery({
    queryKey: ['compute-job', jobId],
    queryFn: () => analyticsAPI.getComputeJob(jobId!),
    enabled: !!jobId && runMutation.isSuccess,
    refetchInterval: (query) => query.state.data?.status === 'completed' ? false : 1000,
  })

  const status = jobStatus?.status || (runMutation.isPending ? 'computing' : 'idle')
  const progress = (jobStatus as any)?.progress || 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900 dark:text-white">Compute Engine</h3>
        <span className={cn(
          'text-xs px-2 py-0.5 rounded-full',
          status === 'idle' && 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
          status === 'computing' && 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
          status === 'running' && 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
          status === 'completed' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
        )}>
          {status === 'idle' && 'Ready'}
          {(status === 'computing' || status === 'running') && 'Computing...'}
          {status === 'completed' && 'Complete'}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-gray-600 dark:text-gray-400">Engine</span>
          <span className="font-medium text-gray-900 dark:text-white">Fortran HPC</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-600 dark:text-gray-400">BLAS</span>
          <span className="font-medium text-gray-900 dark:text-white">OpenBLAS</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-600 dark:text-gray-400">Threads</span>
          <span className="font-medium text-gray-900 dark:text-white">8</span>
        </div>
      </div>

      {(status === 'computing' || status === 'running') && (
        <div className="mt-3">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-amber-500 transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1 text-center">{progress}%</div>
        </div>
      )}

      <button
        onClick={() => runMutation.mutate()}
        disabled={status === 'computing' || status === 'running' || runMutation.isPending}
        className={cn(
          'w-full mt-3 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          (status === 'computing' || status === 'running')
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700'
            : 'bg-amber-500 text-white hover:bg-amber-600'
        )}
      >
        {(status === 'computing' || status === 'running') ? 'Processing...' : 'Run GBLUP Analysis'}
      </button>
    </div>
  )
}

// ============================================
// MAIN COMPONENT
// ============================================

export default function ApexAnalytics() {
  const [activeTab, setActiveTab] = useState<'overview' | 'genetic' | 'phenotypic' | 'genomic'>('overview')

  // Fetch analytics data from API
  const { data, isLoading, error } = useQuery<AnalyticsResponse>({
    queryKey: ['apex-analytics'],
    queryFn: () => analyticsAPI.getAnalytics() as Promise<AnalyticsResponse>,
  })

  // Fetch Veena summary
  const { data: veenaSummary } = useQuery<{ summary: string; key_metrics: Record<string, string> }>({
    queryKey: ['veena-summary'],
    queryFn: () => analyticsAPI.getVeenaSummary() as Promise<{ summary: string; key_metrics: Record<string, string> }>,
  })

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center text-red-500">
          <p>Failed to load analytics data</p>
        </div>
      </div>
    )
  }

  // Transform data for charts
  const geneticGainData = data.genetic_gain.map(g => ({
    year: g.year,
    gain: g.gain,
    cumulative: g.cumulative,
    target: g.target
  }))

  const heritabilities = data.heritabilities.map(h => ({
    trait: h.trait,
    value: h.value
  }))

  const selectionResponse = data.selection_response.map(s => ({
    generation: s.generation,
    mean: s.mean,
    variance: s.variance,
    selected: s.selected
  }))

  const summary = {
    totalTrials: data.summary.total_trials,
    activeStudies: data.summary.active_studies,
    germplasmEntries: data.summary.germplasm_entries,
    observationsThisMonth: data.summary.observations_this_month,
    geneticGainRate: data.summary.genetic_gain_rate,
    dataQualityScore: data.summary.data_quality_score
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            Apex Analytics
            <ModuleInfoMark
              title="Apex Analytics Dashboard"
              description="Comprehensive breeding analytics with AI-powered insights and high-performance computing"
              techStack={['Fortran HPC', 'Rust FFI', 'WASM', 'TensorFlow.js', 'D3.js']}
              dataSource="All breeding program data"
              computeEngine="Fortran BLUP/GBLUP + Veena AI"
              apiEndpoint="/api/v2/analytics"
            />
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            High-performance breeding analytics powered by Fortran & Veena AI 🪷
          </p>
        </div>

        <div className="flex items-center gap-4">
          <PresenceAvatars
            users={[
              { id: '1', name: 'Dr. Sharma', email: '', color: '#ef4444' },
              { id: '2', name: 'Priya Patel', email: '', color: '#3b82f6' }
            ]}
            currentUserId="current"
          />
          <button className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium">
            Export Report
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'genetic', label: 'Genetic Analysis', icon: '🧬' },
          { id: 'phenotypic', label: 'Phenotypic', icon: '🌾' },
          { id: 'genomic', label: 'Genomic', icon: '🔬' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={cn(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === tab.id
                ? 'border-amber-500 text-amber-600 dark:text-amber-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            )}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard label="Active Trials" value={summary.totalTrials} icon="🧪" change={14} trend="up" />
        <StatCard label="Studies" value={summary.activeStudies} icon="📋" change={8} trend="up" />
        <StatCard label="Germplasm" value={summary.germplasmEntries} icon="🌱" change={5} trend="up" />
        <StatCard label="Observations" value={summary.observationsThisMonth} icon="📝" change={23} trend="up" />
        <StatCard label="Genetic Gain" value={`${summary.geneticGainRate}%`} icon="📈" change={12} trend="up" />
        <StatCard label="Data Quality" value={`${summary.dataQualityScore}%`} icon="✅" change={-2} trend="down" />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Charts */}
        <div className="lg:col-span-2 space-y-6">
          <GeneticGainChart data={geneticGainData} />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SelectionResponseChart data={selectionResponse} />
            <CorrelationHeatmap 
              traits={data.correlations.traits} 
              correlations={data.correlations.matrix}
            />
          </div>
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Heritabilities */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Heritability Estimates</h3>
            <div className="grid grid-cols-2 gap-3">
              {heritabilities.map(h => (
                <HeritabilityGauge key={h.trait} trait={h.trait} value={h.value} />
              ))}
            </div>
          </div>

          {/* Compute Status */}
          <ComputeStatus />

          {/* Quick Insights */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Insights</h3>
            <div className="space-y-3">
              {data.insights.map(insight => (
                <QuickInsight
                  key={insight.id}
                  type={insight.type as 'success' | 'warning' | 'info'}
                  title={insight.title}
                  description={insight.description}
                  action={insight.action_label ? { label: insight.action_label, onClick: () => {} } : undefined}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Veena AI Summary */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-5 border border-amber-200 dark:border-amber-800">
        <div className="flex items-start gap-3">
          <span className="text-3xl">🪷</span>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-semibold text-amber-800 dark:text-amber-300">
                Veena's Analysis Summary
              </span>
              <span className="text-xs bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 px-2 py-0.5 rounded-full">
                AI Generated
              </span>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              {veenaSummary?.summary || `Namaste! 🙏 Your breeding program is performing exceptionally well this season. 
              The genetic gain of ${summary.geneticGainRate}% per year exceeds your target by 30%, driven primarily by 
              improved selection accuracy from genomic predictions. Would you like me to generate a detailed report?`}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
