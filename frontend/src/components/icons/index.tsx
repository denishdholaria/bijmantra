/**
 * BijMantra Icon System
 * 
 * Centralized icon management using Lucide React.
 * Provides semantic naming for consistent usage across the app.
 */

import {
  // Navigation & Layout
  Home,
  LayoutDashboard,
  Menu,
  X,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  ExternalLink,
  MoreHorizontal,
  MoreVertical,
  Grip,
  PanelLeft,
  PanelRight,
  Maximize2,
  Minimize2,
  Code,
  
  // Plant Sciences & Breeding
  Sprout,
  Wheat,
  Leaf,
  TreeDeciduous,
  Flower2,
  Apple,
  Cherry,
  
  // Genomics & Science
  Dna,
  Atom,
  Microscope,
  FlaskConical,
  TestTube2,
  Beaker,
  Pipette,
  
  // Data & Analytics
  BarChart3,
  LineChart,
  PieChart,
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Crosshair,
  Calculator,
  Hash,
  Percent,
  
  // Operations & Logistics
  Package,
  Warehouse,
  Factory,
  Truck,
  Building2,
  Store,
  ShoppingCart,
  
  // Quality & Compliance
  Shield,
  ShieldCheck,
  ShieldAlert,
  BadgeCheck,
  Award,
  Medal,
  Trophy,
  Star,
  
  // Environment & Weather
  Sun,
  Moon,
  Cloud,
  CloudSun,
  CloudRain,
  Thermometer,
  Droplets,
  Wind,
  Snowflake,
  
  // Earth & Space
  Globe,
  Globe2,
  Map,
  MapPin,
  Navigation,
  Compass,
  Rocket,
  Orbit,
  Satellite,
  
  // Technology & Sensors
  Radio,
  Wifi,
  WifiOff,
  Signal,
  Bluetooth,
  Cpu,
  HardDrive,
  Server,
  Database,
  
  // Actions
  Plus,
  Minus,
  Pencil,
  Trash2,
  Save,
  Download,
  Upload,
  RefreshCw,
  RotateCcw,
  Copy,
  Clipboard,
  ClipboardCheck,
  ClipboardList,
  
  // Status & Feedback
  Check,
  CheckCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  HelpCircle,
  Loader2,
  Clock,
  Timer,
  Calendar,
  CalendarDays,
  
  // Communication
  Bell,
  BellRing,
  BellOff,
  Mail,
  MessageSquare,
  MessageCircle,
  Send,
  
  // Users & Teams
  User,
  Users,
  UserPlus,
  UserMinus,
  UserCheck,
  UserX,
  Contact,
  
  // Files & Documents
  File,
  FileText,
  FileSpreadsheet,
  FileImage,
  FileCode,
  Folder,
  FolderOpen,
  FolderPlus,
  Archive,
  
  // Search & Filter
  Search,
  Filter,
  SlidersHorizontal,
  ArrowUpDown,
  ListFilter,
  
  // View & Display
  Eye,
  EyeOff,
  Maximize,
  Minimize,
  ZoomIn,
  ZoomOut,
  Grid3X3,
  List,
  LayoutGrid,
  Table2,
  
  // Tools & Settings
  Settings,
  Settings2,
  Wrench,
  Cog,
  SlidersVertical,
  Plug,
  Zap,
  
  // Git & Version Control
  GitMerge,
  GitBranch,
  GitCommit,
  GitPullRequest,
  
  // Media
  Image,
  Camera,
  Video,
  Play,
  Pause,
  Square,
  Volume2,
  VolumeX,
  
  // Misc
  QrCode,
  Barcode,
  Scan,
  ScanLine,
  Fingerprint,
  Key,
  Lock,
  Unlock,
  Link,
  Unlink,
  Share2,
  Bookmark,
  Heart,
  ThumbsUp,
  ThumbsDown,
  Flag,
  Tag,
  Tags,
  Layers,
  Box,
  Boxes,
  Sparkles,
  Lightbulb,
  Brain,
  GraduationCap,
  BookOpen,
  Library,
  Newspaper,
  Smartphone,
  Monitor,
  Laptop,
  Printer,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Semantic icon mapping for BijMantra
 * Maps domain-specific names to Lucide icons
 */
export const Icons = {
  // ═══════════════════════════════════════════════════════════════════════════
  // MODULES & DIVISIONS
  // ═══════════════════════════════════════════════════════════════════════════
  
  // Home & Dashboard
  home: Home,
  dashboard: LayoutDashboard,
  
  // Plant Sciences
  plantSciences: Sprout,
  breeding: Wheat,
  germplasm: Wheat,
  crosses: GitMerge,
  pedigree: TreeDeciduous,
  progeny: Flower2,
  
  // Genomics
  genomics: Dna,
  molecular: Atom,
  variants: Dna,
  alleleMatrix: Grid3X3,
  gwas: Activity,
  
  // Trials & Studies
  trials: FlaskConical,
  studies: Beaker,
  experiments: TestTube2,
  
  // Field Operations
  fieldOps: Map,
  fieldBook: ClipboardList,
  fieldLayout: Grid3X3,
  locations: MapPin,
  seasons: CalendarDays,
  
  // Phenotyping
  phenotyping: Microscope,
  traits: SlidersHorizontal,
  observations: Eye,
  
  // Selection & Analytics
  selection: Target,
  selectionIndex: Crosshair,
  geneticGain: TrendingUp,
  statistics: BarChart3,
  analytics: LineChart,
  
  // Seed Bank
  seedBank: Warehouse,
  vault: Archive,
  accessions: Sprout,
  conservation: Shield,
  viability: Activity,
  regeneration: RefreshCw,
  
  // Earth Systems
  earthSystems: Globe,
  weather: CloudSun,
  climate: Thermometer,
  soil: Layers,
  irrigation: Droplets,
  drought: Sun,
  
  // Sun-Earth Systems
  sunEarth: Sun,
  solar: Sun,
  photoperiod: Clock,
  uvIndex: Shield,
  
  // Sensor Networks
  sensors: Radio,
  devices: Cpu,
  liveData: Activity,
  alerts: Bell,
  iot: Wifi,
  
  // Seed Operations
  seedOps: Factory,
  qualityGate: ShieldCheck,
  labTesting: FlaskConical,
  samples: TestTube2,
  certificates: BadgeCheck,
  processing: Cog,
  inventory: Package,
  warehouse: Warehouse,
  dispatch: Truck,
  traceability: QrCode,
  lineage: GitBranch,
  
  // Commercial
  commercial: Building2,
  dus: ClipboardCheck,
  licensing: FileText,
  
  // Space Research
  spaceResearch: Rocket,
  spaceCrops: Leaf,
  radiation: Atom,
  lifeSupport: Users,
  
  // Integrations
  integrations: Plug,
  api: Code,
  dataSync: RefreshCw,
  
  // Tools
  tools: Wrench,
  calculator: Calculator,
  scanner: Scan,
  labels: Tag,
  
  // Settings & Admin
  settings: Settings,
  users: Users,
  team: Users,
  audit: Shield,
  backup: HardDrive,
  
  // Knowledge
  knowledge: BookOpen,
  helpCenter: HelpCircle,
  training: GraduationCap,
  forums: MessageSquare,
  glossary: Library,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════════════════
  
  add: Plus,
  create: Plus,
  edit: Pencil,
  delete: Trash2,
  remove: Minus,
  save: Save,
  cancel: X,
  close: X,
  confirm: Check,
  
  import: Download,
  export: Upload,
  download: Download,
  upload: Upload,
  
  refresh: RefreshCw,
  reload: RotateCcw,
  
  copy: Copy,
  paste: Clipboard,
  duplicate: Copy,
  
  search: Search,
  filter: Filter,
  sort: ArrowUpDown,
  
  expand: ChevronDown,
  collapse: ChevronUp,
  expandAll: Maximize2,
  collapseAll: Minimize2,
  
  view: Eye,
  hide: EyeOff,
  preview: Eye,
  
  share: Share2,
  link: Link,
  unlink: Unlink,
  
  bookmark: Bookmark,
  favorite: Star,
  like: Heart,
  
  print: Printer,
  scanAction: ScanLine,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // STATUS & FEEDBACK
  // ═══════════════════════════════════════════════════════════════════════════
  
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
  help: HelpCircle,
  
  loading: Loader2,
  pending: Clock,
  inProgress: Timer,
  completed: CheckCircle2,
  
  online: Wifi,
  offline: WifiOff,
  synced: CheckCircle,
  unsynced: RefreshCw,
  conflict: AlertCircle,
  
  active: CheckCircle,
  inactive: XCircle,
  enabled: Check,
  disabled: X,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // NAVIGATION
  // ═══════════════════════════════════════════════════════════════════════════
  
  menu: Menu,
  back: ArrowLeft,
  forward: ArrowRight,
  up: ArrowUp,
  down: ArrowDown,
  
  chevronDown: ChevronDown,
  chevronUp: ChevronUp,
  chevronLeft: ChevronLeft,
  chevronRight: ChevronRight,
  
  more: MoreHorizontal,
  moreVertical: MoreVertical,
  
  external: ExternalLink,
  
  panelLeft: PanelLeft,
  panelRight: PanelRight,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // DATA TYPES
  // ═══════════════════════════════════════════════════════════════════════════
  
  number: Hash,
  percentage: Percent,
  date: Calendar,
  time: Clock,
  text: FileText,
  image: Image,
  file: File,
  folder: Folder,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // VIEWS
  // ═══════════════════════════════════════════════════════════════════════════
  
  gridView: LayoutGrid,
  listView: List,
  tableView: Table2,
  cardView: Grid3X3,
  
  zoomIn: ZoomIn,
  zoomOut: ZoomOut,
  fullscreen: Maximize,
  exitFullscreen: Minimize,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // COMMUNICATION
  // ═══════════════════════════════════════════════════════════════════════════
  
  notification: Bell,
  notificationActive: BellRing,
  notificationOff: BellOff,
  
  message: MessageSquare,
  chat: MessageCircle,
  email: Mail,
  send: Send,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // USERS
  // ═══════════════════════════════════════════════════════════════════════════
  
  user: User,
  userAdd: UserPlus,
  userRemove: UserMinus,
  userCheck: UserCheck,
  userX: UserX,
  profile: Contact,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // SECURITY
  // ═══════════════════════════════════════════════════════════════════════════
  
  lock: Lock,
  unlock: Unlock,
  key: Key,
  fingerprint: Fingerprint,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // AI & SMART FEATURES
  // ═══════════════════════════════════════════════════════════════════════════
  
  ai: Brain,
  smart: Sparkles,
  insights: Lightbulb,
  prediction: TrendingUp,
  
  // ═══════════════════════════════════════════════════════════════════════════
  // DEVICES
  // ═══════════════════════════════════════════════════════════════════════════
  
  mobile: Smartphone,
  desktop: Monitor,
  laptop: Laptop,
  camera: Camera,
  
} as const;

/**
 * Type for all available icon names
 */
export type IconName = keyof typeof Icons;

/**
 * Icon size presets
 */
export const iconSizes = {
  xs: 'h-3 w-3',
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
  xl: 'h-8 w-8',
  '2xl': 'h-10 w-10',
  '3xl': 'h-12 w-12',
} as const;

export type IconSize = keyof typeof iconSizes;

/**
 * Icon component props
 */
interface IconProps {
  /** Icon name from the Icons map */
  name: IconName;
  /** Size preset or custom class */
  size?: IconSize;
  /** Additional CSS classes */
  className?: string;
  /** Stroke width (default: 2) */
  strokeWidth?: number;
  /** Accessible label */
  'aria-label'?: string;
}

/**
 * Icon component with consistent sizing and styling
 * 
 * @example
 * <Icon name="plantSciences" size="lg" />
 * <Icon name="success" className="text-green-500" />
 */
export function Icon({ 
  name, 
  size = 'md', 
  className,
  strokeWidth = 2,
  'aria-label': ariaLabel,
}: IconProps) {
  const IconComponent = Icons[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }
  
  return (
    <IconComponent 
      className={cn(iconSizes[size], className)}
      strokeWidth={strokeWidth}
      aria-label={ariaLabel}
      aria-hidden={!ariaLabel}
    />
  );
}

/**
 * Get icon component by name (for dynamic usage)
 */
export function getIcon(name: IconName): LucideIcon | null {
  return Icons[name] as LucideIcon || null;
}

/**
 * Check if an icon name exists
 */
export function hasIcon(name: string): name is IconName {
  return name in Icons;
}

// Re-export commonly used icons for direct import
export {
  // Most used
  Sprout,
  Wheat,
  Dna,
  FlaskConical,
  BarChart3,
  Target,
  Package,
  Warehouse,
  Factory,
  Globe,
  Sun,
  Radio,
  Rocket,
  Settings,
  BookOpen,
  
  // Actions
  Plus,
  Pencil,
  Trash2,
  Save,
  Search,
  Filter,
  RefreshCw,
  
  // Status
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Loader2,
  
  // Navigation
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Menu,
  X,
};

export default Icons;
