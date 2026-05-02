/**
 * Data Panel Component
 * Reusable panel for displaying metrics and data
 * 
 * Features:
 * - Status indicators
 * - Collapsible sections
 * - Module info integration
 * - Dark mode support
 */

import { useState, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { ModuleInfoMark } from './ModuleInfoMark'

interface DataPanelProps {
  title: string
  children: ReactNode
  className?: string
  status?: 'nominal' | 'warning' | 'critical' | 'info' | 'offline'
  statusText?: string
  collapsible?: boolean
  defaultCollapsed?: boolean
  actions?: ReactNode
  footer?: ReactNode
  moduleInfo?: {
    description: string
    techStack: string[]
    dataSource?: string
    computeEngine?: string
  }
}

const statusConfig = {
  nominal: {
    dot: 'bg-green-500',
    text: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    label: 'NOMINAL'
  },
  warning: {
    dot: 'bg-orange-500 animate-pulse',
    text: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-200 dark:border-orange-800',
    label: 'WARNING'
  },
  critical: {
    dot: 'bg-red-500 animate-pulse',
    text: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    label: 'CRITICAL'
  },
  info: {
    dot: 'bg-blue-500',
    text: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    label: 'INFO'
  },
  offline: {
    dot: 'bg-gray-400',
    text: 'text-gray-500 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-700',
    label: 'OFFLINE'
  }
}

export function DataPanel({
  title,
  children,
  className,
  status,
  statusText,
  collapsible = false,
  defaultCollapsed = false,
  actions,
  footer,
  moduleInfo
}: DataPanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed)
  const statusStyle = status ? statusConfig[status] : null

  return (
    <div className={cn(
      'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        <div className="flex items-center gap-3">
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            >
              <svg
                className={cn('w-4 h-4 transition-transform', collapsed ? '' : 'rotate-90')}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
          
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>

          {moduleInfo && (
            <ModuleInfoMark
              title={title}
              description={moduleInfo.description}
              techStack={moduleInfo.techStack}
              dataSource={moduleInfo.dataSource}
              computeEngine={moduleInfo.computeEngine}
            />
          )}
        </div>

        <div className="flex items-center gap-3">
          {actions}
          
          {/* Status indicator */}
          {statusStyle && (
            <div className={cn(
              'flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono font-semibold tracking-wide',
              statusStyle.bg,
              statusStyle.border,
              'border'
            )}>
              <span className={cn('w-1.5 h-1.5 rounded-full', statusStyle.dot)} />
              <span className={statusStyle.text}>
                {statusText || statusStyle.label}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Body */}
      {!collapsed && (
        <div className="p-4">
          {children}
        </div>
      )}

      {/* Footer */}
      {footer && !collapsed && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          {footer}
        </div>
      )}
    </div>
  )
}

/* ============================================
   METRIC DISPLAY COMPONENT
   ============================================ */
interface MetricProps {
  label: string
  value: string | number
  unit?: string
  delta?: number
  deltaLabel?: string
  color?: 'default' | 'green' | 'blue' | 'orange' | 'red'
  size?: 'sm' | 'md' | 'lg'
}

const colorMap = {
  default: 'text-gray-900 dark:text-white',
  green: 'text-green-600 dark:text-green-400',
  blue: 'text-blue-600 dark:text-blue-400',
  orange: 'text-orange-600 dark:text-orange-400',
  red: 'text-red-600 dark:text-red-400'
}

const sizeMap = {
  sm: 'text-lg',
  md: 'text-2xl',
  lg: 'text-4xl'
}

export function Metric({
  label,
  value,
  unit,
  delta,
  deltaLabel,
  color = 'default',
  size = 'md'
}: MetricProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-medium tracking-wider uppercase text-gray-500 dark:text-gray-400">
        {label}
      </span>
      <div className="flex items-baseline gap-1">
        <span className={cn('font-bold leading-none', colorMap[color], sizeMap[size])}>
          {value}
        </span>
        {unit && (
          <span className="text-xs text-gray-500 dark:text-gray-400">{unit}</span>
        )}
      </div>
      {delta !== undefined && (
        <div className={cn(
          'flex items-center gap-1 text-xs',
          delta >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          <span>{delta >= 0 ? '↑' : '↓'}</span>
          <span>{Math.abs(delta)}%</span>
          {deltaLabel && <span className="text-gray-500 dark:text-gray-400">{deltaLabel}</span>}
        </div>
      )}
    </div>
  )
}

/* ============================================
   STATUS BADGE COMPONENT
   ============================================ */
interface StatusBadgeProps {
  children: ReactNode
  variant?: 'green' | 'blue' | 'orange' | 'red' | 'gray'
  pulse?: boolean
}

const badgeVariants = {
  green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  gray: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

export function StatusBadge({ children, variant = 'gray', pulse = false }: StatusBadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium',
      badgeVariants[variant],
      pulse && 'animate-pulse'
    )}>
      {children}
    </span>
  )
}

/* ============================================
   PROGRESS BAR COMPONENT
   ============================================ */
interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showValue?: boolean
  color?: 'green' | 'blue' | 'orange' | 'red'
  size?: 'sm' | 'md'
  animated?: boolean
}

const progressColors = {
  green: 'bg-green-500',
  blue: 'bg-blue-500',
  orange: 'bg-orange-500',
  red: 'bg-red-500'
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = true,
  color = 'green',
  size = 'md',
  animated = false
}: ProgressBarProps) {
  const percentage = Math.min((value / max) * 100, 100)

  return (
    <div className="space-y-1.5">
      {(label || showValue) && (
        <div className="flex items-center justify-between">
          {label && (
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {value}/{max}
            </span>
          )}
        </div>
      )}
      <div className={cn(
        'relative overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700',
        size === 'sm' ? 'h-1' : 'h-2'
      )}>
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            progressColors[color],
            animated && 'relative overflow-hidden'
          )}
          style={{ width: `${percentage}%` }}
        >
          {animated && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-[shimmer_2s_infinite]" />
          )}
        </div>
      </div>
    </div>
  )
}
