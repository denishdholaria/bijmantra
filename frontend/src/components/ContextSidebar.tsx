/**
 * Context-Aware Sidebar Component
 * Shows related items and quick actions based on current page context
 */

import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface ContextItem {
  path: string
  label: string
  icon: string
  count?: number
}

interface QuickAction {
  label: string
  icon: string
  path: string
}

// Define context relationships between pages
const PAGE_CONTEXTS: Record<string, {
  title: string
  related: ContextItem[]
  quickActions: QuickAction[]
}> = {
  '/germplasm': {
    title: 'Germplasm',
    related: [
      { path: '/seedlots', label: 'Seed Lots', icon: '📦' },
      { path: '/crosses', label: 'Crosses', icon: '🧬' },
      { path: '/pedigree', label: 'Pedigree', icon: '🌳' },
      { path: '/attributevalues', label: 'Attributes', icon: '📝' },
    ],
    quickActions: [
      { label: 'Add Germplasm', icon: '➕', path: '/germplasm/new' },
      { label: 'Import Data', icon: '📥', path: '/import-export' },
      { label: 'Search', icon: '🔍', path: '/germplasm-search' },
    ],
  },
  '/trials': {
    title: 'Trials',
    related: [
      { path: '/studies', label: 'Studies', icon: '📈' },
      { path: '/locations', label: 'Locations', icon: '📍' },
      { path: '/observations', label: 'Observations', icon: '📋' },
      { path: '/trialdesign', label: 'Trial Design', icon: '🎲' },
    ],
    quickActions: [
      { label: 'New Trial', icon: '➕', path: '/trials/new' },
      { label: 'Compare Trials', icon: '⚖️', path: '/trial-comparison' },
      { label: 'Trial Network', icon: '🌐', path: '/trial-network' },
    ],
  },
  '/observations': {
    title: 'Observations',
    related: [
      { path: '/traits', label: 'Traits', icon: '🔬' },
      { path: '/observationunits', label: 'Units', icon: '🌿' },
      { path: '/images', label: 'Images', icon: '📷' },
      { path: '/events', label: 'Events', icon: '📆' },
    ],
    quickActions: [
      { label: 'Collect Data', icon: '📋', path: '/observations/collect' },
      { label: 'Field Scanner', icon: '📱', path: '/field-scanner' },
      { label: 'Quick Entry', icon: '⚡', path: '/quick-entry' },
    ],
  },
  '/genomic-selection': {
    title: 'Genomic Selection',
    related: [
      { path: '/breeding-values', label: 'Breeding Values', icon: '📊' },
      { path: '/wasm-gblup', label: 'WASM GBLUP', icon: '⚡' },
      { path: '/parent-selection', label: 'Parent Selection', icon: '👨‍👩‍👧' },
      { path: '/cross-prediction', label: 'Cross Prediction', icon: '🔮' },
    ],
    quickActions: [
      { label: 'Run GBLUP', icon: '🧮', path: '/wasm-gblup' },
      { label: 'Select Parents', icon: '👨‍👩‍👧', path: '/parent-selection' },
      { label: 'Predict Cross', icon: '🔮', path: '/cross-prediction' },
    ],
  },
  '/analytics': {
    title: 'Analytics',
    related: [
      { path: '/visualization', label: 'Visualization', icon: '📈' },
      { path: '/advanced-reports', label: 'Reports', icon: '📑' },
      { path: '/trial-comparison', label: 'Compare', icon: '⚖️' },
      { path: '/activity', label: 'Activity', icon: '📜' },
    ],
    quickActions: [
      { label: 'Create Report', icon: '📑', path: '/advanced-reports' },
      { label: 'Export Data', icon: '📤', path: '/export-templates' },
      { label: 'Visualize', icon: '📊', path: '/visualization' },
    ],
  },
  '/crosses': {
    title: 'Crosses',
    related: [
      { path: '/germplasm', label: 'Germplasm', icon: '🌱' },
      { path: '/crossingprojects', label: 'Projects', icon: '🔀' },
      { path: '/plannedcrosses', label: 'Planned', icon: '📋' },
      { path: '/progeny', label: 'Progeny', icon: '🌿' },
    ],
    quickActions: [
      { label: 'New Cross', icon: '➕', path: '/crosses/new' },
      { label: 'Crossing Planner', icon: '💑', path: '/crossingplanner' },
      { label: 'Parent Selection', icon: '👨‍👩‍👧', path: '/parent-selection' },
    ],
  },
}

interface ContextSidebarProps {
  collapsed?: boolean
}

export function ContextSidebar({ collapsed = false }: ContextSidebarProps) {
  const location = useLocation()

  // Find matching context for current path
  const context = useMemo(() => {
    // Try exact match first
    if (PAGE_CONTEXTS[location.pathname]) {
      return PAGE_CONTEXTS[location.pathname]
    }
    // Try prefix match
    const matchingKey = Object.keys(PAGE_CONTEXTS).find(key => 
      location.pathname.startsWith(key)
    )
    return matchingKey ? PAGE_CONTEXTS[matchingKey] : null
  }, [location.pathname])

  if (!context || collapsed) return null

  return (
    <div className="border-t border-gray-100 pt-3 mt-3">
      {/* Context Title */}
      <div className="px-2 py-1.5 text-xs font-medium text-gray-400 uppercase tracking-wider flex items-center gap-1">
        <span>📍</span> {context.title} Context
      </div>

      {/* Quick Actions */}
      <div className="space-y-0.5 mb-3">
        {context.quickActions.map((action) => (
          <Link
            key={action.path}
            to={action.path}
            className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-green-700 hover:bg-green-50 transition-colors"
          >
            <span>{action.icon}</span>
            <span>{action.label}</span>
          </Link>
        ))}
      </div>

      {/* Related Items */}
      <div className="px-2 py-1 text-xs text-gray-400 uppercase tracking-wider">
        Related
      </div>
      <div className="space-y-0.5">
        {context.related.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <span>{item.icon}</span>
            <span className="flex-1">{item.label}</span>
            {item.count !== undefined && (
              <span className="text-xs text-gray-400">{item.count}</span>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
