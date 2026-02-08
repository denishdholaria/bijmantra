import {
  Sprout,
  ClipboardList,
  Dna,
  BarChart3,
  CloudSun,
  BookOpen,
  Settings,
} from 'lucide-react'
import type { DockApp, ShellModule } from '../shell/types'

export const launcherModules: ShellModule[] = [
  {
    id: 'breeding',
    title: 'Breeding',
    subtitle: 'Trait strategy & cultivar planning',
    icon: Sprout,
    defaultRoute: '/programs',
  },
  {
    id: 'field-trials',
    title: 'Field Trials',
    subtitle: 'Multi-location performance studies',
    icon: ClipboardList,
    defaultRoute: '/trials',
  },
  {
    id: 'genomics',
    title: 'Genomics',
    subtitle: 'Marker data & genomic pipelines',
    icon: Dna,
    defaultRoute: '/genomics', // Assuming this route exists, otherwise maybe /markers
  },
  {
    id: 'analytics',
    title: 'Analytics',
    subtitle: 'Insights, forecasts, and dashboards',
    icon: BarChart3,
    defaultRoute: '/analytics',
  },
  {
    id: 'environment',
    title: 'Environment',
    subtitle: 'G×E models & weather signals',
    icon: CloudSun,
    defaultRoute: '/environment',
  },
  {
    id: 'knowledge',
    title: 'Knowledge',
    subtitle: 'Research library & playbooks',
    icon: BookOpen,
    defaultRoute: '/knowledge',
  },
]

export const defaultShortcutIds = ['breeding', 'genomics', 'analytics', 'knowledge']

export const dockApps: DockApp[] = [
  {
    id: 'breeding',
    title: 'Breeding',
    icon: Sprout,
    route: '/programs',
  },
  {
    id: 'genomics',
    title: 'Genomics',
    icon: Dna,
    route: '/genomics',
  },
  {
    id: 'analytics',
    title: 'Analytics',
    icon: BarChart3,
    route: '/analytics',
  },
  {
    id: 'knowledge',
    title: 'Knowledge',
    icon: BookOpen,
    route: '/knowledge',
  },
  {
    id: 'settings',
    title: 'Settings',
    icon: Settings,
    route: '/settings',
  },
]
