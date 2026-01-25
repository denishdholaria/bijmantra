/**
 * Role Switcher Component
 * Allows users to switch between different role views
 * Useful for demos and users with multiple responsibilities
 */

import { useRoleStore, UserRole } from '@/hooks/useRoleBasedNav'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const ROLE_INFO: Record<UserRole, { label: string; icon: string; description: string }> = {
  all: {
    label: 'All Access',
    icon: '🌐',
    description: 'Full access to all features',
  },
  breeder: {
    label: 'Breeder',
    icon: '🌱',
    description: 'Germplasm, crosses, selection tools',
  },
  field_tech: {
    label: 'Field Technician',
    icon: '📱',
    description: 'Data collection, scanning, sync',
  },
  analyst: {
    label: 'Data Analyst',
    icon: '📊',
    description: 'Analytics, WASM tools, reports',
  },
  admin: {
    label: 'Administrator',
    icon: '⚙️',
    description: 'Users, system, backups',
  },
  researcher: {
    label: 'Researcher',
    icon: '🔬',
    description: 'Genomics, publications, analysis',
  },
}

interface RoleSwitcherProps {
  compact?: boolean
}

export function RoleSwitcher({ compact = false }: RoleSwitcherProps) {
  const { overrideRole, setOverrideRole } = useRoleStore()
  const currentRole = overrideRole || 'all'
  const roleInfo = ROLE_INFO[currentRole]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors ${
            compact ? 'text-sm' : ''
          }`}
        >
          <span>{roleInfo.icon}</span>
          {!compact && (
            <>
              <span className="font-medium text-gray-700">{roleInfo.label}</span>
              <span className="text-gray-400">▼</span>
            </>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="text-xs text-gray-500 uppercase">
          Switch View Mode
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {(Object.keys(ROLE_INFO) as UserRole[]).map((role) => {
          const info = ROLE_INFO[role]
          const isActive = currentRole === role

          return (
            <DropdownMenuItem
              key={role}
              onClick={() => setOverrideRole(role === 'all' ? null : role)}
              className={`cursor-pointer ${isActive ? 'bg-green-50' : ''}`}
            >
              <div className="flex items-start gap-3 py-1">
                <span className="text-lg">{info.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`font-medium ${isActive ? 'text-green-700' : 'text-gray-700'}`}>
                      {info.label}
                    </span>
                    {isActive && (
                      <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{info.description}</p>
                </div>
              </div>
            </DropdownMenuItem>
          )
        })}

        <DropdownMenuSeparator />
        <div className="px-2 py-2 text-xs text-gray-400">
          💡 Role views filter navigation to show relevant tools
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/**
 * Compact role indicator for header
 */
export function RoleIndicator() {
  const { overrideRole } = useRoleStore()
  const currentRole = overrideRole || 'all'
  const roleInfo = ROLE_INFO[currentRole]

  if (currentRole === 'all') return null

  return (
    <div className="flex items-center gap-1.5 px-2 py-1 bg-green-50 rounded-full text-xs">
      <span>{roleInfo.icon}</span>
      <span className="text-green-700 font-medium">{roleInfo.label} View</span>
    </div>
  )
}
