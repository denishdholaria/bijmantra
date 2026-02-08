import type { LucideIcon } from 'lucide-react'

export type ShellModule = {
  id: string
  title: string
  subtitle: string
  icon: LucideIcon
  defaultRoute?: string
}

export type DockApp = {
  id: string
  title: string
  icon: LucideIcon
  /** Route to navigate to when clicked (replaces window-based opening) */
  route?: string
}
