/**
 * Slashed Sidebar Prototype — WCAG 2.1 AA Compliant
 * 
 * Design concept: Diagonal edge sidebar with slash-prefixed navigation
 * This is a standalone preview component, not integrated into the app.
 * 
 * Refinements v2:
 * - More visible diagonal edge with glowing stroke
 * - Child items no longer show slash prefix (only top-level)
 * - Active state simplified to right indicator bar only (no border box)
 * - Better collapsed state proportions
 * - Improved spacing
 * 
 * @see docs/design/slashed-sidebar.backup.tsx for original version
 */

import { useState, useCallback, type ReactNode } from "react";
import { 
  Home, 
  LayoutDashboard, 
  Sprout, 
  Archive, 
  Cpu, 
  Zap, 
  Settings, 
  ChevronDown,
  Sparkles,
  PanelLeftClose,
  PanelLeft,
  type LucideIcon,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  children?: NavItem[];
}

interface NavNodeProps {
  item: NavItem;
  level: number;
  open: boolean;
  active: string;
  expanded: string | null;
  setActive: (id: string) => void;
  setExpanded: (id: string | null) => void;
}

// ============================================================================
// Navigation Data
// ============================================================================

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Home", icon: Home },
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  {
    id: "breeding",
    label: "Breeding",
    icon: Sprout,
    children: [
      { id: "trials", label: "Field Trials", icon: Zap },
      { id: "genomics", label: "Genomics", icon: Zap },
      { id: "phenotyping", label: "Phenotyping", icon: Zap },
    ],
  },
  { id: "seedbank", label: "Seed Bank", icon: Archive },
  { id: "iot", label: "IoT & Sensors", icon: Cpu },
  { id: "ai", label: "AI Insights", icon: Zap },
  { id: "settings", label: "Settings", icon: Settings },
];

// ============================================================================
// Constants
// ============================================================================

const SIDEBAR_WIDTH_OPEN = 260;
const SIDEBAR_WIDTH_COLLAPSED = 64;
const SLASH_OFFSET = 50; // How much the diagonal cuts in

// ============================================================================
// Main Component
// ============================================================================

export default function SlashSidebar() {
  const [open, setOpen] = useState(true);
  const [active, setActive] = useState("settings");
  const [expanded, setExpanded] = useState<string | null>("breeding");

  const toggleSidebar = useCallback(() => setOpen(prev => !prev), []);

  const width = open ? SIDEBAR_WIDTH_OPEN : SIDEBAR_WIDTH_COLLAPSED;
  const slashOffset = open ? SLASH_OFFSET : 12;

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Static ambient background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute top-1/4 right-1/4 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-3xl" />
      </div>

      {/* Sidebar */}
      <aside
        role="navigation"
        aria-label="Main navigation"
        className="relative overflow-visible transition-all duration-300 ease-out z-20 flex-shrink-0 motion-reduce:transition-none"
        style={{ width }}
      >
        {/* Slashed gradient background with visible edge */}
        <svg
          viewBox={`0 0 ${width} 800`}
          preserveAspectRatio="none"
          className="absolute inset-0 h-full transition-all duration-300 motion-reduce:transition-none"
          style={{ width: width + 2 }}
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="sidebarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0f172a" />
              <stop offset="40%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            <linearGradient id="edgeGlow" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.1" />
              <stop offset="30%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#06b6d4" stopOpacity="1" />
              <stop offset="70%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.1" />
            </linearGradient>
            <filter id="edgeBlur" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceGraphic" stdDeviation="2" />
            </filter>
          </defs>
          
          {/* Main shape */}
          <path 
            d={`M0 0 L${width} 0 L${width - slashOffset} 800 L0 800 Z`}
            fill="url(#sidebarGradient)"
            className="transition-all duration-300 motion-reduce:transition-none"
          />
          
          {/* Glowing diagonal edge - blurred background */}
          <path 
            d={`M${width} 0 L${width - slashOffset} 800`}
            stroke="url(#edgeGlow)"
            strokeWidth="6"
            fill="none"
            filter="url(#edgeBlur)"
            className="transition-all duration-300 motion-reduce:transition-none"
          />
          
          {/* Glowing diagonal edge - sharp line */}
          <path 
            d={`M${width} 0 L${width - slashOffset} 800`}
            stroke="url(#edgeGlow)"
            strokeWidth="2"
            fill="none"
            className="transition-all duration-300 motion-reduce:transition-none"
          />
        </svg>

        {/* Content */}
        <div className="relative z-10 h-full flex flex-col text-slate-200">
          {/* Header */}
          <div className={`flex items-center ${open ? 'justify-between' : 'justify-center'} p-3 border-b border-white/10`}>
            {open && (
              <div className="flex items-center gap-2 pl-1">
                <span className="text-emerald-400 font-mono text-xl font-bold">/</span>
                <span className="font-semibold text-white tracking-tight">Bijmantra</span>
              </div>
            )}
            <button
              onClick={toggleSidebar}
              aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
              aria-expanded={open}
              className="p-2 rounded-lg hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-colors"
            >
              {open ? (
                <PanelLeftClose className="w-5 h-5" />
              ) : (
                <PanelLeft className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Navigation */}
          <nav 
            className="flex-1 overflow-y-auto p-2 space-y-0.5" 
            aria-label="Sidebar navigation"
            style={{ scrollbarWidth: 'thin', scrollbarColor: '#10b981 transparent' }}
          >
            {NAV_ITEMS.map((item) => (
              <NavNode
                key={item.id}
                item={item}
                level={0}
                open={open}
                active={active}
                expanded={expanded}
                setActive={setActive}
                setExpanded={setExpanded}
              />
            ))}
          </nav>

          {/* Footer */}
          <div className="p-3 border-t border-white/10">
            {open ? (
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">WCAG 2.1 AA</span>
            ) : (
              <span className="sr-only">WCAG 2.1 AA Compliant</span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 relative z-10 overflow-auto">
        <div className="max-w-4xl mx-auto space-y-5">
          {/* Header */}
          <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-5 shadow-lg border border-slate-200/50 dark:border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl shadow-lg shadow-emerald-500/20">
                <Sparkles className="w-5 h-5 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800 dark:text-white capitalize">
                  {active}
                </h1>
                <p className="text-slate-500 dark:text-slate-400 text-sm">
                  Slashed sidebar prototype v2
                </p>
              </div>
            </div>
          </header>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Active Projects" value="24" color="emerald" icon={LayoutDashboard} />
            <StatCard label="Data Points" value="12.5K" color="cyan" icon={Cpu} />
            <StatCard label="Success Rate" value="94%" color="violet" icon={Zap} />
          </div>

          {/* Info Panel */}
          <div className="bg-slate-800 dark:bg-slate-900 rounded-2xl p-5 shadow-lg border border-slate-700">
            <h2 className="text-lg font-bold text-white mb-3">Refinements v2</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">✓</span>
                <span>More visible diagonal edge with glowing stroke</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">✓</span>
                <span>Child items no longer show slash prefix</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">✓</span>
                <span>Active state: right indicator bar only (no border box)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">✓</span>
                <span>Better collapsed state proportions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">✓</span>
                <span>Tighter spacing and smaller toggle button</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

// ============================================================================
// NavNode Component
// ============================================================================

function NavNode({ item, level, open, active, expanded, setActive, setExpanded }: NavNodeProps) {
  const isActive = active === item.id;
  const isExpanded = expanded === item.id;
  const hasChildren = Boolean(item.children?.length);
  const Icon = item.icon;
  const isTopLevel = level === 0;

  const handleClick = () => {
    setActive(item.id);
    if (hasChildren) {
      setExpanded(isExpanded ? null : item.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div className="flex flex-col">
      <button
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        aria-current={isActive ? "page" : undefined}
        aria-expanded={hasChildren ? isExpanded : undefined}
        aria-haspopup={hasChildren ? "true" : undefined}
        className={`
          group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2
          transition-all duration-150 motion-reduce:transition-none
          focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:ring-inset
          ${isActive 
            ? "bg-emerald-500/10 text-emerald-300" 
            : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
          }
          ${!open ? 'justify-center' : ''}
        `}
        style={{ marginLeft: open && !isTopLevel ? 12 : 0 }}
      >
        {/* Slash prefix - only for top-level items when expanded */}
        {open && isTopLevel && (
          <span 
            className={`text-xs font-mono w-3 flex-shrink-0 transition-colors duration-150 ${
              isActive ? 'text-emerald-400' : 'text-slate-600'
            }`}
            aria-hidden="true"
          >
            /
          </span>
        )}
        
        {/* Indent space for child items */}
        {open && !isTopLevel && (
          <span className="w-3 flex-shrink-0" aria-hidden="true" />
        )}

        {/* Icon */}
        <Icon 
          className={`w-[18px] h-[18px] flex-shrink-0 transition-transform duration-150 motion-reduce:transition-none ${
            isActive ? 'text-emerald-400' : ''
          }`}
          aria-hidden="true"
        />

        {/* Label */}
        {open && (
          <span className={`flex-1 text-left text-sm truncate ${isActive ? 'font-medium' : ''}`}>
            {item.label}
          </span>
        )}

        {/* Expand indicator */}
        {hasChildren && open && (
          <ChevronDown 
            className={`w-4 h-4 text-slate-500 transition-transform duration-150 motion-reduce:transition-none ${
              isExpanded ? 'rotate-180' : ''
            }`}
            aria-hidden="true"
          />
        )}

        {/* Active indicator bar - right side */}
        {isActive && (
          <div 
            className={`absolute right-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-gradient-to-b from-emerald-400 to-cyan-400 rounded-full shadow-lg shadow-emerald-500/50 ${
              open ? '' : 'right-1'
            }`}
            aria-hidden="true"
          />
        )}

        {/* Tooltip for collapsed state */}
        {!open && (
          <span className="sr-only">{item.label}</span>
        )}
      </button>

      {/* Children */}
      {hasChildren && isExpanded && open && (
        <div 
          className="mt-0.5 space-y-0.5"
          role="group"
          aria-label={`${item.label} submenu`}
        >
          {item.children!.map((child) => (
            <NavNode
              key={child.id}
              item={child}
              level={level + 1}
              open={open}
              active={active}
              expanded={expanded}
              setActive={setActive}
              setExpanded={setExpanded}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// StatCard Component
// ============================================================================

interface StatCardProps {
  label: string;
  value: string;
  color: 'emerald' | 'cyan' | 'violet';
  icon: LucideIcon;
}

function StatCard({ label, value, color, icon: Icon }: StatCardProps) {
  const colorClasses = {
    emerald: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    cyan: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
    violet: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  };

  return (
    <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-xl p-4 shadow-md border border-slate-200/50 dark:border-slate-700/50">
      <div className={`inline-flex p-2 rounded-lg mb-2 ${colorClasses[color]}`}>
        <Icon className="w-4 h-4" aria-hidden="true" />
      </div>
      <div className="text-2xl font-bold text-slate-800 dark:text-white">{value}</div>
      <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
    </div>
  );
}
