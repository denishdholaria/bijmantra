/**
 * Shared Navigation Icon Map
 *
 * Single source of truth for all navigation icon mappings.
 * Used by both ShellSidebar and DivisionNavigation.
 */
import {
  Sprout,
  Wheat,
  Leaf,
  Warehouse,
  Globe,
  Sun,
  Radio,
  Building2,
  Factory,
  Rocket,
  Plug,
  BookOpen,
  Wrench,
  Settings,
  Home,
  LayoutDashboard,
  Dna,
  FlaskConical,
  Beaker,
  TestTube2,
  Microscope,
  Target,
  BarChart3,
  LineChart,
  Map,
  MapPin,
  CalendarDays,
  GitMerge,
  GitBranch,
  TreeDeciduous,
  Flower2,
  Package,
  Truck,
  QrCode,
  Shield,
  ShieldCheck,
  BadgeCheck,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Calculator,
  Activity,
  Eye,
  Grid3X3,
  Cpu,
  Bell,
  Wifi,
  HelpCircle,
  GraduationCap,
  MessageSquare,
  Library,
  Brain,
  Lightbulb,
  Users,
  Cog,
  HardDrive,
  Layers,
  Droplets,
  Thermometer,
  CloudSun,
  Atom,
  Orbit,
  Scan,
  Tag,
  Archive,
  RefreshCw,
  SlidersHorizontal,
  Crosshair,
  TrendingUp,
  Folder,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export const navigationIcons: Record<string, LucideIcon> = {
  // Division Icons
  Seedling: Sprout,
  Sprout: Sprout,
  Wheat: Wheat,
  Leaf: Leaf,
  Warehouse: Warehouse,
  Globe: Globe,
  Sun: Sun,
  Radio: Radio,
  Building2: Building2,
  Factory: Factory,
  Rocket: Rocket,
  Plug: Plug,
  BookOpen: BookOpen,
  Wrench: Wrench,
  Settings: Settings,
  Home: Home,
  LayoutDashboard: LayoutDashboard,

  // Science & Lab
  Dna: Dna,
  FlaskConical: FlaskConical,
  Beaker: Beaker,
  TestTube2: TestTube2,
  Microscope: Microscope,
  Atom: Atom,

  // Analytics & Data
  Target: Target,
  Crosshair: Crosshair,
  BarChart3: BarChart3,
  LineChart: LineChart,
  TrendingUp: TrendingUp,
  Activity: Activity,
  Calculator: Calculator,

  // Field & Location
  Map: Map,
  MapPin: MapPin,
  Grid3X3: Grid3X3,
  CalendarDays: CalendarDays,
  Calendar: CalendarDays,

  // Breeding & Genetics
  GitMerge: GitMerge,
  GitBranch: GitBranch,
  TreeDeciduous: TreeDeciduous,
  Flower2: Flower2,

  // Operations
  Package: Package,
  Truck: Truck,
  QrCode: QrCode,
  Scan: Scan,
  Tag: Tag,
  Archive: Archive,
  Cog: Cog,

  // Quality & Compliance
  Shield: Shield,
  ShieldCheck: ShieldCheck,
  BadgeCheck: BadgeCheck,
  ClipboardCheck: ClipboardCheck,
  ClipboardList: ClipboardList,
  FileText: FileText,
  FileCheck: BadgeCheck,

  // Environment
  Layers: Layers,
  Droplets: Droplets,
  Thermometer: Thermometer,
  CloudSun: CloudSun,

  // Technology
  Cpu: Cpu,
  Bell: Bell,
  Wifi: Wifi,
  HardDrive: HardDrive,
  Orbit: Orbit,

  // Knowledge & Help
  HelpCircle: HelpCircle,
  GraduationCap: GraduationCap,
  MessageSquare: MessageSquare,
  Library: Library,
  Book: BookOpen,

  // AI & Smart
  Brain: Brain,
  Lightbulb: Lightbulb,

  // Users
  Users: Users,

  // Misc
  Eye: Eye,
  RefreshCw: RefreshCw,
  SlidersHorizontal: SlidersHorizontal,
  Folder: Folder,
  ArrowLeftRight: GitMerge,
  Clock: CalendarDays,
  Sparkles: Sparkles,
};

/**
 * Get an icon component by name, falling back to Sparkles
 */
export function getNavIcon(name: string): LucideIcon {
  return navigationIcons[name] || Sparkles;
}
