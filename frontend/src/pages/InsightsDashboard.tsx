/**
 * AI-Powered Insights Dashboard
 * Predictive analytics and intelligent recommendations
 * 
 * APEX FEATURE: No competitor has AI-powered breeding insights
 */

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { ModuleInfoMark } from '@/components/ModuleInfoMark'

interface Insight {
  id: string
  type: 'prediction' | 'recommendation' | 'alert' | 'opportunity'
  title: string
  description: string
  confidence: number
  impact: 'high' | 'medium' | 'low'
  category: string
  actionable: boolean
  actions?: { label: string; action: string }[]
  data?: Record<string, any>
  createdAt: Date
}

interface TrendData {
  label: string
  current: number
  previous: number
  change: number
  trend: 'up' | 'down' | 'stable'
}

// Insight Card Component
function InsightCard({ insight, onAction }: { insight: Insight; onAction?: (action: string) => void }) {
  const typeConfig = {
    prediction: { icon: '🔮', color: 'purple', label: 'Prediction' },
    recommendation: { icon: '💡', color: 'amber', label: 'Recommendation' },
    alert: { icon: '⚠️', color: 'red', label: 'Alert' },
    opportunity: { icon: '🎯', color: 'green', label: 'Opportunity' }
  }

  const impactConfig = {
    high: { color: 'red', label: 'High Impact' },
    medium: { color: 'amber', label: 'Medium Impact' },
    low: { color: 'blue', label: 'Low Impact' }
  }

  const config = typeConfig[insight.type]
  const impact = impactConfig[insight.impact]

  return (
    <div className={cn(
      'bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 transition-all hover:shadow-lg',
      insight.impact === 'high' && 'ring-2 ring-red-200 dark:ring-red-900'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <span className={cn(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              `bg-${config.color}-100 text-${config.color}-700 dark:bg-${config.color}-900/30 dark:text-${config.color}-400`
            )}>
              {config.label}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <span className={cn(
            'text-xs px-2 py-0.5 rounded-full',
            `bg-${impact.color}-100 text-${impact.color}-700 dark:bg-${impact.color}-900/30 dark:text-${impact.color}-400`
          )}>
            {impact.label}
          </span>
          <span className="text-xs text-gray-500">
            {insight.confidence}% confidence
          </span>
        </div>
      </div>

      {/* Content */}
      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
        {insight.title}
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        {insight.description}
      </p>

      {/* Category */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-1 rounded">
          {insight.category}
        </span>
      </div>

      {/* Actions */}
      {insight.actionable && insight.actions && (
        <div className="flex gap-2 pt-3 border-t border-gray-100 dark:border-gray-700">
          {insight.actions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => onAction?.(action.action)}
              className={cn(
                'px-3 py-1.5 text-sm rounded-lg transition-colors',
                idx === 0
                  ? 'bg-amber-500 text-white hover:bg-amber-600'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              )}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Trend Indicator
function TrendIndicator({ data }: { data: TrendData }) {
  const trendConfig = {
    up: { icon: '↑', color: 'text-green-500' },
    down: { icon: '↓', color: 'text-red-500' },
    stable: { icon: '→', color: 'text-gray-500' }
  }

  const config = trendConfig[data.trend]

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">
        {data.label}
      </div>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {data.current.toLocaleString()}
        </span>
        <span className={cn('text-sm font-medium flex items-center', config.color)}>
          {config.icon} {Math.abs(data.change)}%
        </span>
      </div>
      <div className="text-xs text-gray-400 mt-1">
        vs. previous period: {data.previous.toLocaleString()}
      </div>
    </div>
  )
}

// AI Summary Component
function AISummary({ summary }: { summary: string }) {
  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-5 border border-amber-200 dark:border-amber-800">
      <div className="flex items-start gap-3">
        <span className="text-3xl">🪷</span>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-amber-800 dark:text-amber-300">
              Veena's Analysis
            </span>
            <span className="text-xs bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200 px-2 py-0.5 rounded-full">
              AI Generated
            </span>
          </div>
          <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
            {summary}
          </p>
        </div>
      </div>
    </div>
  )
}

export default function InsightsDashboard() {
  const [insights, setInsights] = useState<Insight[]>([])
  const [trends, setTrends] = useState<TrendData[]>([])
  const [aiSummary, setAiSummary] = useState('')
  const [filter, setFilter] = useState<'all' | 'prediction' | 'recommendation' | 'alert' | 'opportunity'>('all')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading insights
    setTimeout(() => {
      setInsights([
        {
          id: '1',
          type: 'prediction',
          title: 'Yield Increase Predicted for Trial T-2024-15',
          description: 'Based on current growth patterns and weather forecasts, we predict a 12% yield increase for wheat varieties in Trial T-2024-15. The favorable moisture conditions and optimal temperature range are contributing factors.',
          confidence: 87,
          impact: 'high',
          category: 'Yield Prediction',
          actionable: true,
          actions: [
            { label: 'View Trial Details', action: 'view-trial' },
            { label: 'Adjust Resources', action: 'adjust-resources' }
          ],
          createdAt: new Date()
        },
        {
          id: '2',
          type: 'recommendation',
          title: 'Optimal Crossing Parents Identified',
          description: 'Analysis of genomic data suggests crossing Line A-2847 with Line B-1923 could produce progeny with 15% higher disease resistance while maintaining yield potential.',
          confidence: 92,
          impact: 'high',
          category: 'Crossing Strategy',
          actionable: true,
          actions: [
            { label: 'Plan Cross', action: 'plan-cross' },
            { label: 'View Analysis', action: 'view-analysis' }
          ],
          createdAt: new Date()
        },
        {
          id: '3',
          type: 'alert',
          title: 'Data Quality Issue Detected',
          description: 'Missing phenotype observations detected in 3 plots of Study S-2024-08. This may affect statistical analysis accuracy. Recommend field verification.',
          confidence: 95,
          impact: 'medium',
          category: 'Data Quality',
          actionable: true,
          actions: [
            { label: 'Review Data', action: 'review-data' },
            { label: 'Dismiss', action: 'dismiss' }
          ],
          createdAt: new Date()
        },
        {
          id: '4',
          type: 'opportunity',
          title: 'Genetic Gain Acceleration Possible',
          description: 'Current selection intensity could be increased by 20% without compromising genetic diversity. This would accelerate genetic gain by approximately 0.5% per cycle.',
          confidence: 78,
          impact: 'medium',
          category: 'Selection Strategy',
          actionable: true,
          actions: [
            { label: 'Simulate Impact', action: 'simulate' },
            { label: 'Learn More', action: 'learn-more' }
          ],
          createdAt: new Date()
        },
        {
          id: '5',
          type: 'prediction',
          title: 'Flowering Date Forecast',
          description: 'Based on accumulated growing degree days and current weather patterns, flowering is predicted to occur 5 days earlier than historical average for Location L-001.',
          confidence: 84,
          impact: 'low',
          category: 'Phenology',
          actionable: false,
          createdAt: new Date()
        }
      ])

      setTrends([
        { label: 'Active Trials', current: 24, previous: 21, change: 14.3, trend: 'up' },
        { label: 'Observations This Week', current: 1847, previous: 1623, change: 13.8, trend: 'up' },
        { label: 'Genetic Gain (% per year)', current: 2.3, previous: 2.1, change: 9.5, trend: 'up' },
        { label: 'Data Quality Score', current: 94, previous: 96, change: -2.1, trend: 'down' }
      ])

      setAiSummary(
        "Namaste! 🙏 Your breeding program is showing strong momentum this season. " +
        "I've identified 2 high-impact opportunities that could significantly improve your genetic gain. " +
        "The predicted yield increase in Trial T-2024-15 is particularly exciting - the combination of favorable weather and your improved germplasm is paying off. " +
        "However, I noticed some data quality issues that need attention before your next analysis cycle. " +
        "Would you like me to prioritize the crossing recommendations or focus on data cleanup first?"
      )

      setIsLoading(false)
    }, 1000)
  }, [])

  const filteredInsights = filter === 'all' 
    ? insights 
    : insights.filter(i => i.type === filter)

  const handleAction = (action: string) => {
    console.log('Action triggered:', action)
    // Handle navigation or modal opening
  }

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">Veena is analyzing your data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            AI Insights Dashboard
            <ModuleInfoMark
              title="AI-Powered Insights"
              description="Predictive analytics and intelligent recommendations powered by Veena AI"
              techStack={['TensorFlow.js', 'ONNX Runtime', 'Custom ML Models']}
              dataSource="All breeding program data"
              computeEngine="Veena AI + Fortran Analytics"
              apiEndpoint="/api/v2/insights"
            />
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Intelligent recommendations powered by Veena 🪷
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Last updated: Just now</span>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      {/* AI Summary */}
      <AISummary summary={aiSummary} />

      {/* Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {trends.map((trend, idx) => (
          <TrendIndicator key={idx} data={trend} />
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700 pb-2">
        {[
          { value: 'all', label: 'All Insights', count: insights.length },
          { value: 'prediction', label: '🔮 Predictions', count: insights.filter(i => i.type === 'prediction').length },
          { value: 'recommendation', label: '💡 Recommendations', count: insights.filter(i => i.type === 'recommendation').length },
          { value: 'alert', label: '⚠️ Alerts', count: insights.filter(i => i.type === 'alert').length },
          { value: 'opportunity', label: '🎯 Opportunities', count: insights.filter(i => i.type === 'opportunity').length }
        ].map(tab => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value as any)}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              filter === tab.value
                ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            )}
          >
            {tab.label}
            <span className="ml-1.5 text-xs bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded-full">
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredInsights.map(insight => (
          <InsightCard
            key={insight.id}
            insight={insight}
            onAction={handleAction}
          />
        ))}
      </div>

      {filteredInsights.length === 0 && (
        <div className="text-center py-12">
          <span className="text-4xl mb-4 block">🔍</span>
          <p className="text-gray-500 dark:text-gray-400">
            No insights found for this filter
          </p>
        </div>
      )}
    </div>
  )
}
