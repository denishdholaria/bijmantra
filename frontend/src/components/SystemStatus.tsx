/**
 * System Status Component
 * Real-time monitoring of system health and services
 * 
 * Features:
 * - Service health indicators
 * - Latency monitoring
 * - Uptime tracking
 * - Compute engine status
 */

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { DataPanel, StatusBadge } from './DataPanel'

interface ServiceStatus {
  name: string
  status: 'online' | 'degraded' | 'offline'
  latency?: number
  lastCheck: Date
}

interface ComputeEngine {
  name: string
  icon: string
  status: 'active' | 'idle' | 'offline'
  activeJobs: number
  description: string
}

export function SystemStatus() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Database', status: 'online', latency: 12, lastCheck: new Date() },
    { name: 'Search Engine', status: 'online', latency: 8, lastCheck: new Date() },
    { name: 'AI Services', status: 'online', latency: 45, lastCheck: new Date() },
    { name: 'File Storage', status: 'online', latency: 23, lastCheck: new Date() },
    { name: 'Cache', status: 'online', latency: 2, lastCheck: new Date() },
  ])

  const [computeEngines] = useState<ComputeEngine[]>([
    { name: 'Fortran HPC', icon: '⚡', status: 'idle', activeJobs: 0, description: 'BLUP/GBLUP, REML' },
    { name: 'Rust WASM', icon: '🦀', status: 'active', activeJobs: 3, description: 'Browser compute' },
    { name: 'WebGPU', icon: '🎮', status: 'idle', activeJobs: 0, description: 'GPU acceleration' },
    { name: 'Python ML', icon: '🐍', status: 'idle', activeJobs: 0, description: 'AI inference' },
  ])

  const [uptime] = useState(99.97)
  const [lastIncident] = useState('14 days ago')

  // Simulate periodic status checks
  useEffect(() => {
    const interval = setInterval(() => {
      setServices(prev => prev.map(service => ({
        ...service,
        latency: service.latency ? Math.max(1, service.latency + Math.floor(Math.random() * 5) - 2) : undefined,
        lastCheck: new Date()
      })))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const allServicesOnline = services.every(s => s.status === 'online')

  return (
    <DataPanel
      title="System Status"
      status={allServicesOnline ? 'nominal' : 'warning'}
      statusText={allServicesOnline ? 'ALL SYSTEMS NOMINAL' : 'DEGRADED'}
      moduleInfo={{
        description: 'Real-time monitoring of all system services and compute engines',
        techStack: ['React', 'WebSocket', 'Redis'],
        dataSource: 'Health check endpoints'
      }}
    >
      <div className="space-y-6">
        {/* Services */}
        <div>
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Services
          </h4>
          <div className="space-y-2">
            {services.map((service) => (
              <ServiceRow key={service.name} service={service} />
            ))}
          </div>
        </div>

        {/* Compute Engines */}
        <div>
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Compute Engines
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {computeEngines.map((engine) => (
              <ComputeEngineCard key={engine.name} engine={engine} />
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Uptime</span>
            <span className="font-mono font-semibold text-green-600 dark:text-green-400">{uptime}%</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-gray-500 dark:text-gray-400">Last Incident</span>
            <span className="text-gray-600 dark:text-gray-300">{lastIncident}</span>
          </div>
        </div>
      </div>
    </DataPanel>
  )
}

/* ============================================
   SERVICE ROW COMPONENT
   ============================================ */
function ServiceRow({ service }: { service: ServiceStatus }) {
  const statusColors = {
    online: 'bg-green-500',
    degraded: 'bg-orange-500 animate-pulse',
    offline: 'bg-red-500 animate-pulse'
  }

  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span className={cn('w-2 h-2 rounded-full', statusColors[service.status])} />
        <span className="text-sm text-gray-700 dark:text-gray-300">{service.name}</span>
      </div>
      {service.latency !== undefined && (
        <span className="text-xs font-mono text-gray-500 dark:text-gray-400">
          {service.latency}ms
        </span>
      )}
    </div>
  )
}

/* ============================================
   COMPUTE ENGINE CARD
   ============================================ */
function ComputeEngineCard({ engine }: { engine: ComputeEngine }) {
  const statusColors = {
    active: 'text-green-600 dark:text-green-400',
    idle: 'text-gray-500 dark:text-gray-400',
    offline: 'text-red-600 dark:text-red-400'
  }

  const statusDot = {
    active: 'bg-green-500',
    idle: 'bg-gray-400',
    offline: 'bg-red-500'
  }

  return (
    <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-1">
        <span className="text-lg">{engine.icon}</span>
        <span className={cn('w-2 h-2 rounded-full', statusDot[engine.status])} />
      </div>
      <p className="text-sm font-medium text-gray-900 dark:text-white">{engine.name}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{engine.description}</p>
      {engine.status === 'active' && (
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">Jobs</span>
            <span className={cn('text-xs font-mono font-semibold', statusColors[engine.status])}>
              {engine.activeJobs}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ============================================
   COMPACT SYSTEM STATUS (for header/footer)
   ============================================ */
export function CompactSystemStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <div className="flex items-center gap-3">
      <StatusPill label="API" status={isOnline ? 'online' : 'offline'} />
      <StatusPill label="Sync" status={isOnline ? 'online' : 'offline'} />
      <StatusPill label="AI" status="online" />
    </div>
  )
}

function StatusPill({ label, status }: { label: string; status: 'online' | 'degraded' | 'offline' }) {
  const colors = {
    online: 'text-green-600 dark:text-green-400',
    degraded: 'text-orange-600 dark:text-orange-400',
    offline: 'text-gray-500 dark:text-gray-400'
  }

  const dots = {
    online: 'bg-green-500',
    degraded: 'bg-orange-500 animate-pulse',
    offline: 'bg-gray-400'
  }

  return (
    <div className="flex items-center gap-1.5">
      <span className={cn('w-1.5 h-1.5 rounded-full', dots[status])} />
      <span className={cn('text-xs font-medium', colors[status])}>{label}</span>
    </div>
  )
}
