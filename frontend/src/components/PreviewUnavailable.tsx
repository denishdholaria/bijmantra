/**
 * PreviewUnavailable
 *
 * Shown when a page requires the full BijMantra backend which is not
 * running in this preview environment.
 *
 * Tone: professional and forward-looking — not an error, just a scope note.
 */

import { Sprout, ArrowUpRight } from 'lucide-react'

interface PreviewUnavailableProps {
  /** Optional feature name, e.g. "Programs" or "IoT Sensors" */
  feature?: string
  /** Optional className for the wrapper */
  className?: string
}

export function PreviewUnavailable({ feature, className = '' }: PreviewUnavailableProps) {
  return (
    <div className={`flex min-h-[320px] flex-col items-center justify-center px-6 py-16 text-center ${className}`}>
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300">
        <Sprout className="h-6 w-6" />
      </div>

      <h3 className="mt-5 text-lg font-semibold text-slate-900 dark:text-white">
        {feature ? `${feature} — Not Available in Preview` : 'Not Available in Preview'}
      </h3>

      <p className="mt-3 max-w-md text-sm leading-6 text-slate-600 dark:text-slate-300">
        BijMantra is under active development. This is a UI preview only — this section requires the full backend infrastructure which is not running in this environment.
      </p>

      <p className="mt-2 max-w-md text-xs leading-5 text-slate-500 dark:text-slate-400">
        Contact us for a full demonstration or early access.
      </p>

      <a
        href="https://bijmantra.org"
        target="_blank"
        rel="noopener noreferrer"
        className="mt-6 inline-flex items-center gap-1.5 rounded-full border border-emerald-300/70 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800 transition-colors hover:bg-emerald-100 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200 dark:hover:bg-emerald-500/20"
      >
        Learn about the full platform
        <ArrowUpRight className="h-3.5 w-3.5" />
      </a>
    </div>
  )
}

export default PreviewUnavailable
