/**
 * Icon System for Bijmantra
 * Using Lucide React for consistent, professional icons
 * 
 * Benefits over emojis:
 * - Consistent across all platforms
 * - Customizable size and color
 * - Better accessibility
 * - Professional appearance
 */

import {
  // Navigation & UI
  Home,
  Search,
  Settings,
  Bell,
  Menu,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Star,
  StarOff,
  Clock,
  X,
  Plus,
  Minus,
  Check,
  AlertCircle,
  Info,
  HelpCircle,
  ExternalLink,
  
  // Breeding & Agriculture
  Sprout,
  Leaf,
  TreeDeciduous,
  Flower2,
  Apple,
  Wheat,
  
  // Science & Data
  FlaskConical,
  Microscope,
  TestTube2,
  Dna,
  Activity,
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  TrendingDown,
  
  // Location & Field
  MapPin,
  Map,
  Navigation,
  Compass,
  Globe,
  Sun,
  Cloud,
  CloudRain,
  Thermometer,
  
  // Documents & Data
  FileText,
  Files,
  FolderOpen,
  Database,
  Table2,
  Grid3X3,
  List,
  ClipboardList,
  BookOpen,
  
  // People & Collaboration
  Users,
  User,
  UserPlus,
  MessageSquare,
  Share2,
  GitBranch,
  GitMerge,
  
  // Tools & Actions
  Wrench,
  Calculator,
  Calendar,
  CalendarDays,
  Package,
  Box,
  Archive,
  Download,
  Upload,
  RefreshCw,
  Zap,
  
  // AI & Tech
  Brain,
  Sparkles,
  Bot,
  Cpu,
  Server,
  Wifi,
  WifiOff,
  
  // Media
  Camera,
  Image,
  ScanLine,
  QrCode,
  Printer,
  
  // Status
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  
  // Misc
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Key,
  Shield,
  Award,
  Target,
  Crosshair,
  Layers,
  Filter,
  SlidersHorizontal,
  MoreHorizontal,
  MoreVertical,
  
} from 'lucide-react'

import { cn } from '@/lib/utils'

// ============================================
// ICON MAPPING
// ============================================

export const icons = {
  // Navigation
  home: Home,
  search: Search,
  settings: Settings,
  bell: Bell,
  menu: Menu,
  chevronDown: ChevronDown,
  chevronRight: ChevronRight,
  chevronLeft: ChevronLeft,
  star: Star,
  starOff: StarOff,
  clock: Clock,
  close: X,
  plus: Plus,
  minus: Minus,
  check: Check,
  
  // Breeding
  sprout: Sprout,
  leaf: Leaf,
  tree: TreeDeciduous,
  flower: Flower2,
  apple: Apple,
  wheat: Wheat,
  germplasm: Sprout,
  seedlot: Package,
  cross: GitMerge,
  pedigree: GitBranch,
  
  // Science
  flask: FlaskConical,
  microscope: Microscope,
  testTube: TestTube2,
  dna: Dna,
  genomics: Dna,
  
  // Data & Analytics
  activity: Activity,
  barChart: BarChart3,
  lineChart: LineChart,
  pieChart: PieChart,
  trendUp: TrendingUp,
  trendDown: TrendingDown,
  analytics: BarChart3,
  insights: Sparkles,
  
  // Location
  mapPin: MapPin,
  map: Map,
  navigation: Navigation,
  compass: Compass,
  globe: Globe,
  location: MapPin,
  field: Map,
  
  // Weather
  sun: Sun,
  cloud: Cloud,
  rain: CloudRain,
  temperature: Thermometer,
  weather: Cloud,
  
  // Documents
  file: FileText,
  files: Files,
  folder: FolderOpen,
  database: Database,
  table: Table2,
  grid: Grid3X3,
  list: List,
  clipboard: ClipboardList,
  book: BookOpen,
  report: FileText,
  
  // People
  users: Users,
  user: User,
  userPlus: UserPlus,
  team: Users,
  collaboration: Users,
  
  // Communication
  message: MessageSquare,
  share: Share2,
  chat: MessageSquare,
  
  // Tools
  wrench: Wrench,
  calculator: Calculator,
  calendar: Calendar,
  calendarDays: CalendarDays,
  package: Package,
  box: Box,
  archive: Archive,
  download: Download,
  upload: Upload,
  refresh: RefreshCw,
  zap: Zap,
  tools: Wrench,
  
  // AI
  brain: Brain,
  sparkles: Sparkles,
  bot: Bot,
  ai: Brain,
  veena: Sparkles,
  
  // Tech
  cpu: Cpu,
  server: Server,
  wifi: Wifi,
  wifiOff: WifiOff,
  wasm: Cpu,
  
  // Media
  camera: Camera,
  image: Image,
  scan: ScanLine,
  qrCode: QrCode,
  printer: Printer,
  
  // Status
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  help: HelpCircle,
  loading: Loader2,
  alert: AlertCircle,
  
  // Security
  eye: Eye,
  eyeOff: EyeOff,
  lock: Lock,
  unlock: Unlock,
  key: Key,
  shield: Shield,
  
  // Misc
  award: Award,
  target: Target,
  crosshair: Crosshair,
  layers: Layers,
  filter: Filter,
  sliders: SlidersHorizontal,
  moreH: MoreHorizontal,
  moreV: MoreVertical,
  external: ExternalLink,
  
  // Breeding-specific aliases
  program: Wheat,
  trial: FlaskConical,
  study: ClipboardList,
  trait: Microscope,
  observation: Eye,
  sample: TestTube2,
  variant: Dna,
  harvest: Wheat,
  nursery: Sprout,
  inventory: Package,
  pipeline: Layers,
  selection: Target,
  ranking: Award,
  simulator: Cpu,
  
} as const

export type IconName = keyof typeof icons

// ============================================
// ICON COMPONENT
// ============================================

interface IconProps {
  name: IconName
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  strokeWidth?: number
}

const sizeMap = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
}

export function Icon({ name, size = 'md', className, strokeWidth = 2 }: IconProps) {
  const IconComponent = icons[name]
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`)
    return null
  }
  
  return (
    <IconComponent 
      className={cn(sizeMap[size], className)} 
      strokeWidth={strokeWidth}
    />
  )
}

// ============================================
// NAV ICON MAPPING (emoji to Lucide)
// ============================================

export const navIconMap: Record<string, IconName> = {
  // Categories
  '🏠': 'home',
  '🌱': 'sprout',
  '📊': 'barChart',
  '🧬': 'dna',
  '🌾': 'wheat',
  '🛠️': 'wrench',
  
  // Common items
  '💬': 'message',
  '🌿': 'leaf',
  '📱': 'scan',
  '🦠': 'microscope',
  '🎯': 'target',
  '🌐': 'globe',
  '⚙️': 'settings',
  '🔍': 'search',
  '🧪': 'flask',
  '📈': 'lineChart',
  '📍': 'mapPin',
  '👥': 'users',
  '📅': 'calendar',
  '📦': 'package',
  '🔀': 'cross',
  '📋': 'clipboard',
  '🔬': 'microscope',
  '📆': 'calendarDays',
  '📷': 'camera',
  '📖': 'book',
  '🧫': 'testTube',
  '📐': 'grid',
  '🗺️': 'map',
  '📚': 'book',
  '🌈': 'sparkles',
  '🔖': 'layers',
  '🔗': 'pedigree',
  '👨‍👩‍👧': 'users',
  '🔄': 'refresh',
  '🌍': 'globe',
  '⚖️': 'sliders',
  '🚀': 'zap',
  '⚡': 'zap',
  '🎮': 'cpu',
  '🧮': 'calculator',
  '✅': 'check',
  '🏆': 'award',
  '🪷': 'sparkles',
  '🧠': 'brain',
  '📑': 'files',
  '📜': 'file',
  '🗓️': 'calendar',
  '💰': 'database',
  '🔔': 'bell',
  '✓': 'check',
  '📤': 'upload',
  '🌳': 'tree',
  '💑': 'users',
  '📉': 'lineChart',
  '🏷️': 'layers',
  '🗃️': 'archive',
  '📓': 'book',
  '📬': 'message',
  '🤝': 'share',
  '📰': 'file',
  '🎓': 'award',
  '💚': 'success',
  '📴': 'wifiOff',
  '💾': 'database',
  '👤': 'user',
  '🔌': 'cpu',
  '❓': 'help',
  '⌨️': 'settings',
  '🎉': 'sparkles',
  '💡': 'sparkles',
  '📝': 'file',
  '📧': 'message',
  '🔒': 'lock',
  'ℹ️': 'info',
  '🚁': 'navigation',
  '📡': 'wifi',
  '⛓️': 'pedigree',
  '🌤️': 'sun',
}

// Helper to get icon from emoji
export function getIconFromEmoji(emoji: string): IconName {
  return navIconMap[emoji] || 'help'
}

// ============================================
// CATEGORY COLORS
// ============================================

export const categoryColors = {
  home: {
    gradient: 'from-blue-500 to-cyan-500',
    bg: 'bg-blue-500',
    text: 'text-blue-600',
    light: 'bg-blue-50 text-blue-700',
  },
  breeding: {
    gradient: 'from-green-500 to-emerald-500',
    bg: 'bg-green-500',
    text: 'text-green-600',
    light: 'bg-green-50 text-green-700',
  },
  data: {
    gradient: 'from-purple-500 to-violet-500',
    bg: 'bg-purple-500',
    text: 'text-purple-600',
    light: 'bg-purple-50 text-purple-700',
  },
  genomics: {
    gradient: 'from-amber-500 to-orange-500',
    bg: 'bg-amber-500',
    text: 'text-amber-600',
    light: 'bg-amber-50 text-amber-700',
  },
  field: {
    gradient: 'from-teal-500 to-green-500',
    bg: 'bg-teal-500',
    text: 'text-teal-600',
    light: 'bg-teal-50 text-teal-700',
  },
  tools: {
    gradient: 'from-gray-500 to-slate-600',
    bg: 'bg-gray-500',
    text: 'text-gray-600',
    light: 'bg-gray-50 text-gray-700',
  },
} as const

export type CategoryId = keyof typeof categoryColors

export default icons
