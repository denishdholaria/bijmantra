import { useEffect, useState } from 'react'
import { Command } from 'cmdk'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Monitor, Sun, Moon, RefreshCw, LayoutGrid } from 'lucide-react'
import { useWindowStore } from '@/store/windowStore'
import { useNotificationStore } from '@/store/notificationStore'
import { launcherModules } from '../registry/moduleRegistry'
import { cn } from '@/lib/utils'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const { openWindow } = useWindowStore()
  const { addNotification } = useNotificationStore()

  // Toggle with Cmd+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = (command: () => void) => {
    setOpen(false)
    command()
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[1000] flex items-start justify-center pt-[20vh] bg-black/40 backdrop-blur-sm"
          onClick={(e) => {
             if (e.target === e.currentTarget) setOpen(false)
          }}
        >
          <motion.div
             initial={{ scale: 0.95, opacity: 0, y: 10 }}
             animate={{ scale: 1, opacity: 1, y: 0 }}
             exit={{ scale: 0.95, opacity: 0, y: 10 }}
             transition={{ type: "spring", stiffness: 300, damping: 30 }}
             className="w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white/95 shadow-2xl backdrop-blur dark:border-slate-800 dark:bg-slate-900/95"
          >
            <Command className="w-full">
              <div className="flex items-center border-b border-slate-100 px-3 dark:border-slate-800" cmdk-input-wrapper="">
                <Search className="mr-2 h-5 w-5 shrink-0 opacity-50" />
                <Command.Input 
                  placeholder="Type a command or search..."
                  className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-slate-500 disabled:cursor-not-allowed disabled:opacity-50 dark:text-slate-100"
                />
              </div>
              
              <Command.List className="max-h-[300px] overflow-y-auto overflow-x-hidden p-2">
                <Command.Empty className="py-6 text-center text-sm text-slate-500">
                  No results found.
                </Command.Empty>

                <Command.Group heading="Applications" className="px-2 pb-2 text-xs font-medium text-slate-500">
                  {launcherModules.map((app) => (
                    <Command.Item
                      key={app.id}
                      onSelect={() => runCommand(() => openWindow({ ...app }))}
                      className="group relative flex cursor-pointer select-none items-center rounded-lg px-2 py-2 text-sm outline-none aria-selected:bg-emerald-100 aria-selected:text-emerald-900 dark:aria-selected:bg-emerald-900/30 dark:aria-selected:text-emerald-100"
                    >
                      <LayoutGrid className="mr-2 h-4 w-4 opacity-70" />
                      <span>{app.title}</span>
                      <span className="ml-auto text-xs opacity-50">{app.subtitle}</span>
                    </Command.Item>
                  ))}
                </Command.Group>

                <Command.Group heading="System" className="px-2 pt-2 pb-2 text-xs font-medium text-slate-500">
                  <Command.Item
                    onSelect={() => runCommand(() => window.location.reload())}
                    className="group relative flex cursor-pointer select-none items-center rounded-lg px-2 py-2 text-sm outline-none aria-selected:bg-slate-100 aria-selected:text-slate-900 dark:aria-selected:bg-slate-800 dark:aria-selected:text-slate-100"
                  >
                    <RefreshCw className="mr-2 h-4 w-4 opacity-70" />
                    <span>Reload System</span>
                    <span className="ml-auto text-xs opacity-50">⌘R</span>
                  </Command.Item>

                  <Command.Item
                    onSelect={() => runCommand(() => 
                      addNotification({
                         title: "Theme Changed",
                         message: "Dark mode toggled (simulation)",
                         type: "info"
                      })
                    )}
                    value="toggle dark mode theme"
                    className="group relative flex cursor-pointer select-none items-center rounded-lg px-2 py-2 text-sm outline-none aria-selected:bg-slate-100 aria-selected:text-slate-900 dark:aria-selected:bg-slate-800 dark:aria-selected:text-slate-100"
                  >
                    <Moon className="mr-2 h-4 w-4 opacity-70" />
                    <span>Toggle Dark Mode</span>
                  </Command.Item>
                </Command.Group>

              </Command.List>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
