type Wallpaper = {
  id: string
  name: string
  description: string
  previewClassName?: string
  previewImageUrl?: string
}

type WallpaperSelectorProps = {
  wallpapers: Wallpaper[]
  activeWallpaperId: string
  onChange: (id: string) => void
  onUpload: (file: File) => void
}

export function WallpaperSelector({
  wallpapers,
  activeWallpaperId,
  onChange,
  onUpload,
}: WallpaperSelectorProps) {
  return (
    <section className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
            Desktop
          </p>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Wallpaper
          </h2>
        </div>
        <label className="rounded-full border border-slate-200/70 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600 transition hover:border-emerald-200 hover:text-emerald-700 focus-within:outline focus-within:outline-2 focus-within:outline-emerald-400 dark:border-slate-800/70 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:border-emerald-700/60 dark:hover:text-emerald-200">
          Upload
          <input
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) {
                onUpload(file)
              }
              event.target.value = ''
            }}
          />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {wallpapers.map((wallpaper) => (
          <button
            key={wallpaper.id}
            type="button"
            onClick={() => onChange(wallpaper.id)}
            className="flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/70 p-3 text-left transition hover:border-emerald-200 hover:shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:border-slate-800/70 dark:bg-slate-900/60 dark:hover:border-emerald-700/60"
          >
            <span
              className={`h-12 w-12 rounded-xl border border-white/60 shadow-inner ${
                wallpaper.previewClassName ?? ''
              }`}
              style={
                wallpaper.previewImageUrl
                  ? {
                      backgroundImage: `url(${wallpaper.previewImageUrl})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                    }
                  : undefined
              }
              aria-hidden="true"
            />
            <span className="flex flex-col">
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                {wallpaper.name}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {wallpaper.description}
              </span>
              {activeWallpaperId === wallpaper.id ? (
                <span className="mt-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-300">
                  Active
                </span>
              ) : null}
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
