import { launcherModules } from '../registry/moduleRegistry'

type LauncherGridProps = {
  shortcutIds: string[]
  onCreateShortcut: (id: string) => void
}

export function LauncherGrid({ shortcutIds, onCreateShortcut }: LauncherGridProps) {
  return (
    <section className="w-full">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
            System Launcher
          </p>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Applications
          </h2>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Launch modules or pin them to your desktop.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {launcherModules.map((module) => {
          const Icon = module.icon
          const isPinned = shortcutIds.includes(module.id)
          return (
            <div
              key={module.id}
              className="group flex h-full flex-col justify-between rounded-2xl border border-slate-200/70 bg-white/80 p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-200 hover:bg-white hover:shadow-md dark:border-slate-800/70 dark:bg-slate-900/60 dark:hover:border-emerald-600/40"
            >
              <div className="flex items-start gap-4">
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100/70 text-emerald-700 transition group-hover:bg-emerald-200/70 dark:bg-emerald-900/40 dark:text-emerald-200">
                  <Icon className="h-5 w-5" />
                </span>
                <div className="flex flex-col gap-2">
                  <span className="text-base font-semibold text-slate-900 dark:text-slate-100">
                    {module.title}
                  </span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {module.subtitle}
                  </span>
                </div>
              </div>
              <div className="mt-5 flex items-center gap-2">
                <button
                  type="button"
                  className="flex-1 rounded-full border border-emerald-200/80 bg-emerald-50/80 px-4 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:border-emerald-700/60 dark:bg-emerald-900/30 dark:text-emerald-200 dark:hover:bg-emerald-900/50"
                >
                  Open module
                </button>
                <button
                  type="button"
                  onClick={() => onCreateShortcut(module.id)}
                  className="rounded-full border border-slate-200/80 px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-emerald-200 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-800 dark:text-slate-300 dark:hover:border-emerald-700/60 dark:hover:text-emerald-200"
                  disabled={isPinned}
                >
                  {isPinned ? 'Pinned' : 'Pin shortcut'}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
