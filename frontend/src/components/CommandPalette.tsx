/**
 * Command Palette Component
 * Global search and navigation with ⌘K / Ctrl+K
 */

import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Command } from "cmdk";

import {
  MessageSquare,
  Eye,
  ScanLine,
  Microscope,
  Leaf,
  Target,
  Cpu,
  Settings,
  BarChart3,
  Search,
  Wheat,
  FlaskConical,
  LineChart,
  MapPin,
  Users,
  Calendar,
  Sprout,
  Package,
  GitMerge,
  GitBranch,
  ClipboardList,
  FileText,
  Camera,
  Book,
  TestTube2,
  Dna,
  Grid3X3,
  Map as MapIcon,
  Sparkles,
  Layers,
  SlidersHorizontal,
  RefreshCw,
  Globe,
  Zap,
  Calculator,
  CheckCircle2,
  Award,
  Activity,
  Database,
  TreeDeciduous,
  Sun,
  Upload,
  User,
  Bell,
  WifiOff,
  Archive,
  Rocket,
  HelpCircle,
  Plus,
  History,
  NotebookPen,
  Info,
  Keyboard,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  section: string;
  keywords?: string[];
}

// Flattened navigation items for search
const allNavItems: NavItem[] = [
  // AI
  {
    path: "/ai-assistant",
    label: "AI Assistant",
    icon: MessageSquare,
    section: "AI",
    keywords: ["chat", "help", "question"],
  },
  {
    path: "/plant-vision",
    label: "Plant Vision",
    icon: Eye,
    section: "AI",
    keywords: ["camera", "detect", "disease"],
  },
  {
    path: "/field-scanner",
    label: "Field Scanner",
    icon: ScanLine,
    section: "AI",
    keywords: ["scan", "qr", "barcode"],
  },
  {
    path: "/disease-atlas",
    label: "Disease Atlas",
    icon: Microscope,
    section: "AI",
    keywords: ["pest", "pathogen"],
  },
  {
    path: "/crop-health",
    label: "Crop Health Dashboard",
    icon: Leaf,
    section: "AI",
  },
  {
    path: "/yield-predictor",
    label: "Yield Predictor",
    icon: Target,
    section: "AI",
    keywords: ["forecast", "estimate"],
  },
  {
    path: "/chrome-ai",
    label: "Chrome AI",
    icon: Cpu,
    section: "AI",
    keywords: ["gemini", "local"],
  },
  { path: "/ai-settings", label: "AI Settings", icon: Settings, section: "AI" },

  // Core
  {
    path: "/dashboard",
    label: "Dashboard",
    icon: BarChart3,
    section: "Core",
    keywords: ["home", "overview"],
  },
  {
    path: "/search",
    label: "Search",
    icon: Search,
    section: "Core",
    keywords: ["find", "lookup"],
  },
  {
    path: "/programs",
    label: "Programs",
    icon: Wheat,
    section: "Core",
    keywords: ["breeding program"],
  },
  {
    path: "/trials",
    label: "Trials",
    icon: FlaskConical,
    section: "Core",
    keywords: ["experiment", "test"],
  },
  { path: "/studies", label: "Studies", icon: LineChart, section: "Core" },
  {
    path: "/locations",
    label: "Locations",
    icon: MapPin,
    section: "Core",
    keywords: ["site", "field", "place"],
  },
  {
    path: "/people",
    label: "People",
    icon: Users,
    section: "Core",
    keywords: ["team", "staff", "contact"],
  },
  {
    path: "/seasons",
    label: "Seasons",
    icon: Calendar,
    section: "Core",
    keywords: ["year", "cycle"],
  },

  // Germplasm
  {
    path: "/germplasm",
    label: "Germplasm",
    icon: Sprout,
    section: "Germplasm",
    keywords: ["accession", "variety", "line"],
  },
  {
    path: "/seedlots",
    label: "Seed Lots",
    icon: Package,
    section: "Germplasm",
    keywords: ["inventory", "stock"],
  },
  {
    path: "/crosses",
    label: "Crosses",
    icon: GitMerge,
    section: "Germplasm",
    keywords: ["hybridization", "mating"],
  },
  {
    path: "/crossingprojects",
    label: "Crossing Projects",
    icon: GitBranch,
    section: "Germplasm",
  },
  {
    path: "/plannedcrosses",
    label: "Planned Crosses",
    icon: ClipboardList,
    section: "Germplasm",
  },
  {
    path: "/progeny",
    label: "Progeny",
    icon: Leaf,
    section: "Germplasm",
    keywords: ["offspring", "descendants"],
  },
  {
    path: "/attributevalues",
    label: "Germplasm Attributes",
    icon: FileText,
    section: "Germplasm",
  },

  // Phenotyping
  {
    path: "/traits",
    label: "Traits",
    icon: Microscope,
    section: "Phenotyping",
    keywords: ["variable", "characteristic"],
  },
  {
    path: "/observations",
    label: "Observations",
    icon: Eye,
    section: "Phenotyping",
    keywords: ["data", "measurement"],
  },
  {
    path: "/observationunits",
    label: "Observation Units",
    icon: Leaf,
    section: "Phenotyping",
    keywords: ["plot", "plant"],
  },
  {
    path: "/events",
    label: "Events",
    icon: Calendar,
    section: "Phenotyping",
    keywords: ["activity", "treatment"],
  },
  {
    path: "/images",
    label: "Images",
    icon: Camera,
    section: "Phenotyping",
    keywords: ["photo", "picture"],
  },
  {
    path: "/ontologies",
    label: "Ontologies",
    icon: Book,
    section: "Phenotyping",
  },

  // Genotyping
  {
    path: "/samples",
    label: "Samples",
    icon: TestTube2,
    section: "Genotyping",
    keywords: ["dna", "tissue"],
  },
  {
    path: "/variants",
    label: "Variants",
    icon: Dna,
    section: "Genotyping",
    keywords: ["snp", "marker"],
  },
  {
    path: "/allelematrix",
    label: "Allele Matrix",
    icon: Grid3X3,
    section: "Genotyping",
  },
  {
    path: "/plates",
    label: "Plates",
    icon: FlaskConical,
    section: "Genotyping",
  },
  {
    path: "/references",
    label: "References",
    icon: Book,
    section: "Genotyping",
    keywords: ["genome"],
  },
  {
    path: "/genomemaps",
    label: "Genome Maps",
    icon: MapIcon,
    section: "Genotyping",
  },

  // Genomics
  {
    path: "/genetic-diversity",
    label: "Genetic Diversity",
    icon: Sparkles,
    section: "Genomics",
    keywords: ["diversity", "heterozygosity"],
  },
  {
    path: "/breeding-values",
    label: "Breeding Values",
    icon: BarChart3,
    section: "Genomics",
    keywords: ["blup", "ebv"],
  },
  {
    path: "/qtl-mapping",
    label: "QTL Mapping",
    icon: Target,
    section: "Genomics",
    keywords: ["gwas", "association"],
  },
  {
    path: "/genomic-selection",
    label: "Genomic Selection",
    icon: Dna,
    section: "Genomics",
    keywords: ["gs", "gebv"],
  },
  {
    path: "/marker-assisted-selection",
    label: "Marker Assisted Selection",
    icon: Layers,
    section: "Genomics",
    keywords: ["mas", "mabc"],
  },
  {
    path: "/haplotype-analysis",
    label: "Haplotype Analysis",
    icon: Layers,
    section: "Genomics",
  },
  {
    path: "/linkage-disequilibrium",
    label: "Linkage Disequilibrium",
    icon: GitBranch,
    section: "Genomics",
    keywords: ["ld"],
  },
  {
    path: "/population-genetics",
    label: "Population Genetics",
    icon: Users,
    section: "Genomics",
    keywords: ["structure", "pca"],
  },
  {
    path: "/parentage-analysis",
    label: "Parentage Analysis",
    icon: Users,
    section: "Genomics",
    keywords: ["pedigree", "verification"],
  },
  {
    path: "/genetic-correlation",
    label: "Genetic Correlation",
    icon: RefreshCw,
    section: "Genomics",
  },
  {
    path: "/gxe-interaction",
    label: "G×E Interaction",
    icon: Globe,
    section: "Genomics",
    keywords: ["ammi", "gge"],
  },
  {
    path: "/stability-analysis",
    label: "Stability Analysis",
    icon: SlidersHorizontal,
    section: "Genomics",
  },

  // Advanced Breeding
  {
    path: "/molecular-breeding",
    label: "Molecular Breeding",
    icon: FlaskConical,
    section: "Advanced",
  },
  {
    path: "/phenomic-selection",
    label: "Phenomic Selection",
    icon: Camera,
    section: "Advanced",
  },
  {
    path: "/speed-breeding",
    label: "Speed Breeding",
    icon: Zap,
    section: "Advanced",
  },
  {
    path: "/doubled-haploid",
    label: "Doubled Haploid",
    icon: Microscope,
    section: "Advanced",
    keywords: ["dh"],
  },
  {
    path: "/breeding-simulator",
    label: "Breeding Simulator",
    icon: Cpu,
    section: "Advanced",
  },
  {
    path: "/genetic-gain-calculator",
    label: "Genetic Gain Calculator",
    icon: Calculator,
    section: "Advanced",
  },
  {
    path: "/cross-prediction",
    label: "Cross Prediction",
    icon: Sparkles,
    section: "Advanced",
  },
  {
    path: "/parent-selection",
    label: "Parent Selection",
    icon: Users,
    section: "Advanced",
  },
  {
    path: "/selection-decision",
    label: "Selection Decision",
    icon: CheckCircle2,
    section: "Advanced",
  },
  {
    path: "/performance-ranking",
    label: "Performance Ranking",
    icon: Award,
    section: "Advanced",
  },

  // Analytics
  {
    path: "/analytics",
    label: "Analytics Dashboard",
    icon: BarChart3,
    section: "Analytics",
  },
  {
    path: "/trial-summary",
    label: "Trial Summary",
    icon: FileText,
    section: "Analytics",
  },
  {
    path: "/trial-comparison",
    label: "Trial Comparison",
    icon: SlidersHorizontal,
    section: "Analytics",
  },
  {
    path: "/trial-network",
    label: "Trial Network",
    icon: Globe,
    section: "Analytics",
  },
  {
    path: "/visualization",
    label: "Data Visualization",
    icon: LineChart,
    section: "Analytics",
  },
  {
    path: "/advanced-reports",
    label: "Advanced Reports",
    icon: FileText,
    section: "Analytics",
  },
  {
    path: "/activity",
    label: "Activity Timeline",
    icon: Activity,
    section: "Analytics",
  },

  // Planning
  {
    path: "/season-planning",
    label: "Season Planning",
    icon: Calendar,
    section: "Planning",
  },
  {
    path: "/field-planning",
    label: "Field Planning",
    icon: ClipboardList,
    section: "Planning",
  },
  {
    path: "/resource-allocation",
    label: "Resource Allocation",
    icon: Database,
    section: "Planning",
  },
  {
    path: "/breeding-history",
    label: "Breeding History",
    icon: Book,
    section: "Planning",
  },
  {
    path: "/breeding-goals",
    label: "Breeding Goals",
    icon: Target,
    section: "Planning",
  },
  {
    path: "/resource-calendar",
    label: "Resource Calendar",
    icon: Calendar,
    section: "Planning",
  },

  // Tools
  {
    path: "/fieldlayout",
    label: "Field Layout",
    icon: MapIcon,
    section: "Tools",
  },
  {
    path: "/trialdesign",
    label: "Trial Design",
    icon: Grid3X3,
    section: "Tools",
    keywords: ["rcbd", "alpha"],
  },
  {
    path: "/selectionindex",
    label: "Selection Index",
    icon: Target,
    section: "Tools",
  },
  {
    path: "/geneticgain",
    label: "Genetic Gain",
    icon: LineChart,
    section: "Tools",
  },
  {
    path: "/pedigree",
    label: "Pedigree Viewer",
    icon: TreeDeciduous,
    section: "Tools",
  },
  {
    path: "/pipeline",
    label: "Breeding Pipeline",
    icon: Layers,
    section: "Tools",
  },
  { path: "/harvest", label: "Harvest Planner", icon: Wheat, section: "Tools" },
  {
    path: "/inventory",
    label: "Seed Inventory",
    icon: Package,
    section: "Tools",
  },
  {
    path: "/crossingplanner",
    label: "Crossing Planner",
    icon: GitMerge,
    section: "Tools",
  },
  {
    path: "/scanner",
    label: "Barcode Scanner",
    icon: ScanLine,
    section: "Tools",
  },
  { path: "/weather", label: "Weather", icon: Sun, section: "Tools" },
  {
    path: "/import-export",
    label: "Import/Export",
    icon: Upload,
    section: "Tools",
  },
  { path: "/reports", label: "Reports", icon: FileText, section: "Tools" },

  // WASM
  {
    path: "/wasm-genomics",
    label: "WASM Genomics",
    icon: Zap,
    section: "WASM Engine",
    keywords: ["rust", "performance"],
  },
  {
    path: "/wasm-gblup",
    label: "WASM GBLUP",
    icon: BarChart3,
    section: "WASM Engine",
  },
  {
    path: "/wasm-popgen",
    label: "WASM Population Genetics",
    icon: Users,
    section: "WASM Engine",
  },
  {
    path: "/wasm-ld",
    label: "WASM LD Analysis",
    icon: Layers,
    section: "WASM Engine",
  },
  {
    path: "/wasm-selection",
    label: "WASM Selection Index",
    icon: Target,
    section: "WASM Engine",
  },

  // System
  { path: "/settings", label: "Settings", icon: Settings, section: "System" },
  { path: "/profile", label: "Profile", icon: User, section: "System" },
  {
    path: "/notifications",
    label: "Notifications",
    icon: Bell,
    section: "System",
  },
  {
    path: "/system-health",
    label: "System Health",
    icon: Activity,
    section: "System",
  },
  { path: "/offline", label: "Offline Mode", icon: WifiOff, section: "System" },
  {
    path: "/backup",
    label: "Backup & Restore",
    icon: Archive,
    section: "System",
  },
  { path: "/users", label: "User Management", icon: Users, section: "System" },
  { path: "/auditlog", label: "Audit Log", icon: FileText, section: "System" },
  {
    path: "/api-explorer",
    label: "API Explorer",
    icon: Database,
    section: "System",
  },

  // Help
  { path: "/help", label: "Help Center", icon: Book, section: "Help" },
  {
    path: "/quick-guide",
    label: "Quick Start Guide",
    icon: Rocket,
    section: "Help",
  },
  { path: "/glossary", label: "Glossary", icon: Book, section: "Help" },
  { path: "/faq", label: "FAQ", icon: HelpCircle, section: "Help" },
  {
    path: "/keyboard-shortcuts",
    label: "Keyboard Shortcuts",
    icon: Keyboard,
    section: "Help",
  },
  { path: "/about", label: "About", icon: Info, section: "Help" },
];

// Quick actions
const quickActions = [
  {
    id: "new-observation",
    label: "Add Observation",
    icon: Plus,
    action: "navigate",
    path: "/observations/collect",
  },
  {
    id: "new-germplasm",
    label: "Add Germplasm",
    icon: Sprout,
    action: "navigate",
    path: "/germplasm/new",
  },
  {
    id: "new-cross",
    label: "Create Cross",
    icon: GitMerge,
    action: "navigate",
    path: "/crosses/new",
  },
  {
    id: "scan",
    label: "Scan Barcode",
    icon: ScanLine,
    action: "navigate",
    path: "/scanner",
  },
  {
    id: "ai-chat",
    label: "Ask AI Assistant",
    icon: MessageSquare,
    action: "navigate",
    path: "/ai-assistant",
  },
];

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [recentItems, setRecentItems] = useState<string[]>([]);

  // Load recent items from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("bijmantra-recent-nav");
    if (stored) {
      setRecentItems(JSON.parse(stored));
    }
  }, [open]);

  const handleSelect = useCallback(
    (path: string) => {
      // Update recent items
      const updated = [path, ...recentItems.filter((p) => p !== path)].slice(
        0,
        5
      );
      localStorage.setItem("bijmantra-recent-nav", JSON.stringify(updated));
      setRecentItems(updated);

      onOpenChange(false);
      setSearch("");
      navigate(path);
    },
    [navigate, onOpenChange, recentItems]
  );

  // Get recent nav items
  const recentNavItems = recentItems
    .map((path) => allNavItems.find((item) => item.path === path))
    .filter(Boolean) as NavItem[];

  // Group items by section
  const groupedItems = allNavItems.reduce(
    (acc, item) => {
      if (!acc[item.section]) acc[item.section] = [];
      acc[item.section].push(item);
      return acc;
    },
    {} as Record<string, NavItem[]>
  );

  return (
    <Command.Dialog
      open={open}
      onOpenChange={onOpenChange}
      label="Global Command Menu"
      className="fixed inset-0 z-[100]"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-2xl">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-gray-200 dark:border-slate-700 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <Search
              className="w-5 h-5 text-gray-400 dark:text-gray-500"
              strokeWidth={1.5}
            />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search pages, tools, or type a command..."
              className="flex-1 bg-transparent outline-none text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500"
              autoFocus
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-700 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <Command.List className="max-h-[60vh] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-gray-500">
              No results found. Try a different search term.
            </Command.Empty>

            {/* Quick Actions */}
            {!search && (
              <Command.Group heading="Quick Actions" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Quick Actions
                </div>
                {quickActions.map((action) => (
                  <Command.Item
                    key={action.id}
                    value={action.label}
                    onSelect={() => handleSelect(action.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-green-50 dark:hover:bg-green-900/30 hover:text-green-700 dark:hover:text-green-400 data-[selected=true]:bg-green-50 dark:data-[selected=true]:bg-green-900/30 data-[selected=true]:text-green-700 dark:data-[selected=true]:text-green-400"
                  >
                    <action.icon className="w-5 h-5" strokeWidth={1.75} />
                    <span className="font-medium">{action.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Recent */}
            {!search && recentNavItems.length > 0 && (
              <Command.Group heading="Recent" className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Recent
                </div>
                {recentNavItems.map((item) => (
                  <Command.Item
                    key={`recent-${item.path}`}
                    value={`recent ${item.label}`}
                    onSelect={() => handleSelect(item.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                  >
                    <item.icon
                      className="w-5 h-5 text-gray-400"
                      strokeWidth={1.75}
                    />
                    <span>{item.label}</span>
                    <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">
                      {item.section}
                    </span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* All Sections */}
            {Object.entries(groupedItems).map(([section, items]) => (
              <Command.Group key={section} heading={section} className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {section}
                </div>
                {items.map((item) => (
                  <Command.Item
                    key={item.path}
                    value={`${item.label} ${item.section} ${item.keywords?.join(" ") || ""}`}
                    onSelect={() => handleSelect(item.path)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 data-[selected=true]:bg-gray-100 dark:data-[selected=true]:bg-slate-700"
                  >
                    <item.icon
                      className="w-5 h-5 text-gray-400"
                      strokeWidth={1.75}
                    />
                    <span>{item.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ↑↓
                </kbd>{" "}
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ↵
                </kbd>{" "}
                Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-700 rounded border dark:border-slate-600">
                  ESC
                </kbd>{" "}
                Close
              </span>
            </div>
            <span>
              <Sprout className="inline w-3 h-3 mr-1" strokeWidth={2.5} />{" "}
              Bijmantra
            </span>
          </div>
        </div>
      </div>
    </Command.Dialog>
  );
}
