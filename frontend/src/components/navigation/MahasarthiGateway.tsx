
import { cn } from '@/lib/utils';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import { 
  GATEWAYS, 
  GatewayId, 
  GatewayConfig 
} from '@/config/MahasarthiConfig';
import { 
  Globe, 
  Sprout, 
  Package, 
  BarChart3,
  LucideIcon
} from 'lucide-react';

// Icon map since we store icon strings in config
const iconMap: Record<string, LucideIcon> = {
  Globe,
  Sprout,
  Package,
  BarChart3
};

interface MahasarthiGatewayProps {
  activeGateway: GatewayId;
  onSelectGateway: (id: GatewayId) => void;
  collapsed?: boolean;
}

export function MahasarthiGateway({ 
  activeGateway, 
  onSelectGateway, 
  collapsed = false 
}: MahasarthiGatewayProps) {
  
  return (
    <div className={cn(
      "flex flex-col gap-2 p-2 border-b border-white/10",
      collapsed ? "items-center" : ""
    )}>
      {/* Label only visible when expanded */}
      {!collapsed && (
        <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-2 mb-1">
          Gateways
        </div>
      )}

      <div className={cn(
        "grid gap-2",
        collapsed ? "grid-cols-1" : "grid-cols-4"
      )}>
        {(Object.values(GATEWAYS) as GatewayConfig[]).map((gateway) => {
          const Icon = iconMap[gateway.iconName] || Globe;
          const isActive = activeGateway === gateway.id;

          return (
            <TooltipProvider key={gateway.id} delayDuration={0}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onSelectGateway(gateway.id)}
                    className={cn(
                      "group relative flex items-center justify-center rounded-lg transition-all duration-200",
                      // Size changes based on sidebar state
                      collapsed ? "w-10 h-10" : "h-10 w-full",
                      // Active state styling
                      isActive 
                        ? cn("bg-white/10 text-white shadow-lg shadow-black/20", gateway.color.replace('bg-', 'text-'))
                        : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                    )}
                  >
                    <Icon className={cn(
                      "transition-transform duration-200",
                      isActive ? "scale-110" : "group-hover:scale-105",
                      // Adjust icon size
                      collapsed ? "w-5 h-5" : "w-5 h-5" 
                    )} />
                    
                    {/* Active Indicator Dot (Collapsed only) */}
                    {isActive && collapsed && (
                      <div className={cn(
                        "absolute right-1 top-1 w-1.5 h-1.5 rounded-full ring-2 ring-[#0f172a]",
                        gateway.color
                      )} />
                    )}
                    
                    {/* Active Bar (Expanded only) */}
                    {isActive && !collapsed && (
                      <div className={cn(
                        "absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-t-full",
                        gateway.color
                      )} />
                    )}
                  </button>
                </TooltipTrigger>
                <TooltipContent side={collapsed ? "right" : "bottom"} className="bg-slate-800 text-slate-100 border-slate-700">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-semibold">{gateway.label}</span>
                    <span className="text-xs text-slate-400">{gateway.description}</span>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
      </div>
    </div>
  );
}
