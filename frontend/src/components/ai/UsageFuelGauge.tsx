import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface UsageStats {
  used: number;
  limit: number;
  remaining: number;
}

export function UsageFuelGauge({ className }: { className?: string }) {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUsage = async () => {
    try {
      const token = apiClient.getToken();
      if (!token) return;
      
      const response = await fetch("/api/v2/chat/usage", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (e) {
      console.error("Failed to fetch usage:", e);
    } finally {
      setLoading(false);
    }
  };

  // Poll usage occasionally or on mount
  useEffect(() => {
    fetchUsage();
    // Refresh every 30s to stay relatively current if chatting
    const timer = setInterval(fetchUsage, 30000);
    return () => clearInterval(timer);
  }, []);

  if (loading || !stats) return null;

  // Don't show gauge if limit is huge (unlimited/BYOK mostly)
  // Assuming default limit is 50. If > 1000, probably unlimited.
  if (stats.limit > 1000) return null;

  const percentage = Math.min((stats.used / stats.limit) * 100, 100);
  
  // Color Logic
  let colorClass = "bg-emerald-500";
  if (percentage > 70) colorClass = "bg-amber-500";
  if (percentage > 90) colorClass = "bg-red-500";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn("flex items-center gap-2 px-2 py-1 bg-white/10 rounded-md cursor-help transition-opacity hover:opacity-80", className)}>
            <span className="text-[10px] font-medium opacity-80 uppercase tracking-wider">Fuel</span>
            
            {/* The Gauge */}
            <div className="w-16 h-2 bg-black/20 rounded-full overflow-hidden relative border border-white/10">
              <div 
                className={cn("h-full transition-all duration-500 ease-out", colorClass)} 
                style={{ width: `${percentage}%` }}
              />
            </div>
            
            <span className={cn("text-xs font-mono font-bold", percentage > 90 ? "text-red-200" : "")}>
              {stats.used}/{stats.limit}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent className="bg-slate-900 border-slate-700 text-white p-3">
          <div className="space-y-1">
            <p className="font-semibold">Daily AI Quota</p>
            <p className="text-xs text-slate-300">
              You have used {stats.used} of {stats.limit} requests today.
            </p>
            {percentage >= 100 && (
              <p className="text-xs text-red-400 font-bold mt-1">
                Limit reached! Switch to Pro mode to continue.
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
