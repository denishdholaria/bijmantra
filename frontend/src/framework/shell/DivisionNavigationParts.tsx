import type { CSSProperties } from 'react'
import type { CustomWorkspace, WorkspaceColor } from '@/types/customWorkspace'
import type { Workspace } from '@/types/workspace'

type GradientStop = {
  from: string
  to: string
}

const customWorkspaceStops: Record<WorkspaceColor, GradientStop> = {
  green: { from: '#22c55e', to: '#059669' },
  blue: { from: '#3b82f6', to: '#4f46e5' },
  purple: { from: '#a855f7', to: '#7c3aed' },
  amber: { from: '#f59e0b', to: '#ea580c' },
  slate: { from: '#64748b', to: '#475569' },
}

function resolveSystemWorkspaceStops(color: string): GradientStop {
  if (color.includes('green')) {
    return { from: '#22c55e', to: '#059669' }
  }

  if (color.includes('blue')) {
    return { from: '#3b82f6', to: '#4f46e5' }
  }

  if (color.includes('purple')) {
    return { from: '#a855f7', to: '#7c3aed' }
  }

  if (color.includes('amber')) {
    return { from: '#f59e0b', to: '#ea580c' }
  }

  return { from: '#64748b', to: '#475569' }
}

function buildWorkspaceIndicatorStyle(stops: GradientStop): CSSProperties {
  return {
    background: 'linear-gradient(to right, var(--tw-gradient-stops))',
    ['--tw-gradient-from' as string]: stops.from,
    ['--tw-gradient-to' as string]: stops.to,
  }
}

export function CustomWorkspaceIndicator({
  workspace,
}: {
  workspace: CustomWorkspace
}) {
  return (
    <div
      className="px-3 py-2 mb-2 rounded-lg text-white text-xs font-medium"
      style={buildWorkspaceIndicatorStyle(customWorkspaceStops[workspace.color])}
    >
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider opacity-80">Custom</span>
        <span>•</span>
        <span>{workspace.name}</span>
      </div>
    </div>
  )
}

export function SystemWorkspaceIndicator({
  workspace,
}: {
  workspace: Workspace
}) {
  return (
    <div
      className="px-3 py-2 mb-2 rounded-lg bg-gradient-to-r opacity-90 text-white text-xs font-medium"
      style={buildWorkspaceIndicatorStyle(resolveSystemWorkspaceStops(workspace.color))}
    >
      {workspace.name}
    </div>
  )
}

export function DivisionNavigationLabel({
  isCustomWorkspaceActive,
  hasActiveWorkspace,
}: {
  isCustomWorkspaceActive: boolean
  hasActiveWorkspace: boolean
}) {
  return (
    <div className="px-3 py-2 text-xs font-semibold text-prakruti-dhool-500 dark:text-prakruti-dhool-400 uppercase tracking-wider">
      {isCustomWorkspaceActive ? 'Selected Pages' : hasActiveWorkspace ? 'Modules' : 'All Modules'}
    </div>
  )
}

export function DivisionNavigationEmptyState({
  isCustomWorkspaceActive,
  customWorkspaceName,
  activeWorkspaceName,
}: {
  isCustomWorkspaceActive: boolean
  customWorkspaceName?: string
  activeWorkspaceName?: string
}) {
  return (
    <div className="px-3 py-4 text-sm text-prakruti-dhool-500 dark:text-prakruti-dhool-400 text-center">
      {isCustomWorkspaceActive
        ? `No pages in ${customWorkspaceName || 'custom workspace'}`
        : `No modules available for ${activeWorkspaceName}`}
    </div>
  )
}