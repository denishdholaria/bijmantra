import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Settings, Upload } from 'lucide-react'

type Wallpaper = {
  id: string
  name: string
  description: string
  previewClassName?: string
  previewImageUrl?: string
}

type SystemSettingsMenuProps = {
  wallpapers: Wallpaper[]
  activeWallpaperId: string
  onChange: (id: string) => void
  onUpload: (file: File) => void
}

export function SystemSettingsMenu({
  wallpapers,
  activeWallpaperId,
  onChange,
  onUpload,
}: SystemSettingsMenuProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-full border border-slate-200/70 bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-600 transition hover:border-emerald-200 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-400 dark:border-slate-800/70 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:border-emerald-700/60 dark:hover:text-emerald-200"
        >
          <Settings className="h-3.5 w-3.5" />
          Settings
        </button>
      </PopoverTrigger>
      <PopoverContent className="mr-6 w-80 p-0" align="end">
        <div className="border-b border-slate-200 p-4 dark:border-slate-800">
          <h4 className="font-semibold leading-none text-slate-900 dark:text-slate-100">
            Appearance
          </h4>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Customize your workspace wallpaper.
          </p>
        </div>
        <div className="p-4">
          <div className="mb-4 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Wallpaper
            </span>
            <label className="flex cursor-pointer items-center gap-1.5 rounded-md px-2 py-1 text-[10px] uppercase tracking-wider text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/30">
              <Upload className="h-3 w-3" />
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
          <div className="grid grid-cols-2 gap-2">
            {wallpapers.map((wallpaper) => (
              <button
                key={wallpaper.id}
                type="button"
                onClick={() => onChange(wallpaper.id)}
                className={`relative flex aspect-video items-center justify-center overflow-hidden rounded-lg border transition ${
                  activeWallpaperId === wallpaper.id
                    ? 'border-emerald-500 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 hover:border-emerald-200 dark:border-slate-800'
                }`}
              >
                <div
                  className={`absolute inset-0 ${wallpaper.previewClassName ?? ''}`}
                  style={
                    wallpaper.previewImageUrl
                      ? {
                          backgroundImage: `url(${wallpaper.previewImageUrl})`,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                        }
                      : undefined
                  }
                />
                <span className="sr-only">{wallpaper.name}</span>
                {activeWallpaperId === wallpaper.id && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/10">
                    <div className="h-2 w-2 rounded-full bg-white shadow-sm" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
