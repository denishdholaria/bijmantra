import type { ReevuSafeFailure } from '@/lib/reevu-safe-failure'

interface ReevuSafeFailureCardProps {
  safeFailure: ReevuSafeFailure
}

const SECTION_COPY: Record<'searched' | 'missing' | 'next_steps', string> = {
  searched: 'What REEVU checked',
  missing: 'What is still missing',
  next_steps: 'Suggested next steps',
}

function formatMissingContextEntry(entry: Record<string, unknown>): string {
  const reason = typeof entry.reason === 'string' ? entry.reason : null
  const domain = typeof entry.domain === 'string' ? entry.domain : null
  const details = Object.entries(entry)
    .filter(([key, value]) => key !== 'reason' && key !== 'domain' && value !== undefined)
    .map(([key, value]) => `${key.replace(/_/g, ' ')}=${String(value)}`)

  const lead = [domain, reason].filter(Boolean).join(': ')
  return [lead, details.join(', ')].filter(Boolean).join(' · ')
}

export function ReevuSafeFailureCard({ safeFailure }: ReevuSafeFailureCardProps) {
  return (
    <div className="mt-3 rounded-xl border border-amber-300/60 bg-amber-50/80 p-4 text-amber-950 shadow-sm dark:border-amber-800/70 dark:bg-amber-950/30 dark:text-amber-100">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 text-lg leading-none" aria-hidden="true">⚠️</div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold">Structured safe failure</h3>
            <span className="rounded-full border border-amber-400/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide dark:border-amber-700/80">
              {safeFailure.error_category.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="mt-1 text-xs text-amber-900/80 dark:text-amber-100/80">
            REEVU stopped here instead of guessing from incomplete or ambiguous system state.
          </p>

          <div className="mt-3 grid gap-3 md:grid-cols-3">
            {(['searched', 'missing', 'next_steps'] as const).map(section => (
              <section key={section} className="rounded-lg border border-amber-200/70 bg-white/60 p-3 dark:border-amber-900/60 dark:bg-slate-950/20">
                <h4 className="text-[11px] font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300">
                  {SECTION_COPY[section]}
                </h4>
                <ul className="mt-2 space-y-1 text-xs">
                  {safeFailure[section].map((item, index) => (
                    <li key={`${section}-${index}`} className="flex gap-2">
                      <span aria-hidden="true">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>

          {safeFailure.missing_context && safeFailure.missing_context.length > 0 && (
            <section className="mt-3 rounded-lg border border-amber-200/70 bg-white/60 p-3 dark:border-amber-900/60 dark:bg-slate-950/20">
              <h4 className="text-[11px] font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-300">
                Missing context details
              </h4>
              <ul className="mt-2 space-y-1 text-xs">
                {safeFailure.missing_context.map((entry, index) => (
                  <li key={`missing-context-${index}`} className="flex gap-2">
                    <span aria-hidden="true">•</span>
                    <span>{formatMissingContextEntry(entry)}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

export default ReevuSafeFailureCard
