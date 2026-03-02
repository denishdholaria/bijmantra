/**
 * Module Info Mark (i-mark) Component
 * Shows technical information about each module/page
 * 
 * Purpose: Transparency about tech stack and architectural decisions
 * As per requirement: "App pages must have I-mark note of that module/page"
 */

import { useState } from 'react'
import { cn } from '@/lib/utils'

interface ModuleInfoMarkProps {
  title: string
  description: string
  techStack: string[]
  dataSource?: string
  computeEngine?: string
  apiEndpoint?: string
  architectureNotes?: string
  className?: string
}

export function ModuleInfoMark({
  title,
  description,
  techStack,
  dataSource,
  computeEngine,
  apiEndpoint,
  architectureNotes,
  className
}: ModuleInfoMarkProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={cn('relative inline-flex', className)}>
      {/* Info Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold transition-all duration-200',
          isOpen
            ? 'bg-green-500 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600 hover:text-green-600'
        )}
        title="Module Information"
      >
        i
      </button>

      {/* Info Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="absolute left-0 top-full mt-2 z-50 w-80 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden">
              {/* Header */}
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center justify-between">
                  <h4 className="font-mono text-[11px] font-semibold tracking-[0.1em] uppercase text-green-600 dark:text-green-400">
                    Module Info
                  </h4>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{title}</p>
              </div>

              {/* Content */}
              <div className="p-4 space-y-4">
                {/* Description */}
                <div>
                  <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-1">
                    Description
                  </label>
                  <p className="text-[13px] text-gray-600 dark:text-gray-300 leading-relaxed">
                    {description}
                  </p>
                </div>

                {/* Tech Stack */}
                <div>
                  <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-2">
                    Tech Stack
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {techStack.map((tech) => (
                      <TechBadge key={tech} tech={tech} />
                    ))}
                  </div>
                </div>

                {/* Data Source */}
                {dataSource && (
                  <div>
                    <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-1">
                      Data Source
                    </label>
                    <p className="text-[12px] text-gray-600 dark:text-gray-300 font-mono">
                      {dataSource}
                    </p>
                  </div>
                )}

                {/* Compute Engine */}
                {computeEngine && (
                  <div>
                    <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-1">
                      Compute Engine
                    </label>
                    <div className="flex items-center gap-2">
                      <ComputeEngineBadge engine={computeEngine} />
                    </div>
                  </div>
                )}

                {/* API Endpoint */}
                {apiEndpoint && (
                  <div>
                    <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-1">
                      API Endpoint
                    </label>
                    <code className="block text-[11px] text-green-600 dark:text-green-400 font-mono bg-gray-100 dark:bg-gray-900 px-2 py-1 rounded">
                      {apiEndpoint}
                    </code>
                  </div>
                )}

                {/* Architecture Notes */}
                {architectureNotes && (
                  <div>
                    <label className="block font-mono text-[9px] font-medium tracking-[0.15em] uppercase text-gray-500 dark:text-gray-400 mb-1">
                      Architecture Decision
                    </label>
                    <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-relaxed italic">
                      "{architectureNotes}"
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <p className="text-[10px] text-gray-500 dark:text-gray-400 font-mono">
                  Bijmantra v0.1.0 • High-Precision Computing
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/* ============================================
   TECH BADGE COMPONENT
   ============================================ */
interface TechBadgeProps {
  tech: string
}

const techColors: Record<string, { bg: string; text: string }> = {
  'TypeScript': { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400' },
  'Rust': { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-400' },
  'Fortran': { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400' },
  'Python': { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-400' },
  'React': { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-600 dark:text-cyan-400' },
  'FastAPI': { bg: 'bg-teal-100 dark:bg-teal-900/30', text: 'text-teal-600 dark:text-teal-400' },
  'WebAssembly': { bg: 'bg-violet-100 dark:bg-violet-900/30', text: 'text-violet-600 dark:text-violet-400' },
  'WASM': { bg: 'bg-violet-100 dark:bg-violet-900/30', text: 'text-violet-600 dark:text-violet-400' },
  'WebGPU': { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-600 dark:text-amber-400' },
  'PostgreSQL': { bg: 'bg-indigo-100 dark:bg-indigo-900/30', text: 'text-indigo-600 dark:text-indigo-400' },
  'Redis': { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-600 dark:text-red-400' },
  'Meilisearch': { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-600 dark:text-pink-400' },
  'IndexedDB': { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-400' },
  'default': { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-300' }
}

function TechBadge({ tech }: TechBadgeProps) {
  const colors = techColors[tech] || techColors['default']
  
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium',
      colors.bg,
      colors.text
    )}>
      {tech}
    </span>
  )
}

/* ============================================
   COMPUTE ENGINE BADGE
   ============================================ */
interface ComputeEngineBadgeProps {
  engine: string
}

const engineConfig: Record<string, { icon: string; color: string; label: string }> = {
  'fortran': { icon: '⚡', color: 'text-purple-600 dark:text-purple-400', label: 'Fortran HPC' },
  'rust-wasm': { icon: '🦀', color: 'text-orange-600 dark:text-orange-400', label: 'Rust WASM' },
  'webgpu': { icon: '🎮', color: 'text-amber-600 dark:text-amber-400', label: 'WebGPU' },
  'python': { icon: '🐍', color: 'text-blue-600 dark:text-blue-400', label: 'Python' },
  'browser': { icon: '🌐', color: 'text-cyan-600 dark:text-cyan-400', label: 'Browser JS' },
  'hybrid': { icon: '🔀', color: 'text-green-600 dark:text-green-400', label: 'Hybrid' }
}

function ComputeEngineBadge({ engine }: ComputeEngineBadgeProps) {
  const config = engineConfig[engine.toLowerCase()] || { icon: '⚙️', color: 'text-gray-600 dark:text-gray-400', label: engine }
  
  return (
    <div className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600',
      config.color
    )}>
      <span>{config.icon}</span>
      <span className="font-mono text-[10px] font-semibold tracking-wide uppercase">
        {config.label}
      </span>
    </div>
  )
}

/* ============================================
   PAGE INFO WRAPPER
   ============================================ */
interface PageInfoWrapperProps {
  children: React.ReactNode
  moduleInfo: {
    title: string
    description: string
    techStack: string[]
    dataSource?: string
    computeEngine?: string
    apiEndpoint?: string
    architectureNotes?: string
  }
}

export function PageInfoWrapper({ children, moduleInfo }: PageInfoWrapperProps) {
  return (
    <div className="relative">
      {/* Floating Info Mark */}
      <div className="absolute top-0 right-0 z-10">
        <ModuleInfoMark {...moduleInfo} />
      </div>
      {children}
    </div>
  )
}
