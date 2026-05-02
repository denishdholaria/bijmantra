import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import type { ChatUsageResponse, ChatUsageSoftAlertState } from "@/lib/api/ai/chat";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function gaugeClassName(state: ChatUsageSoftAlertState) {
  if (state === "exhausted" || state === "critical") {
    return "bg-red-500";
  }

  if (state === "warning" || state === "watch") {
    return "bg-amber-500";
  }

  return "bg-emerald-500";
}

function textTone(state: ChatUsageSoftAlertState) {
  if (state === "exhausted" || state === "critical") {
    return "text-red-200";
  }

  if (state === "warning") {
    return "text-amber-100";
  }

  return "text-white";
}

function triggerTone(state: ChatUsageSoftAlertState) {
  if (state === "exhausted" || state === "critical") {
    return "border-red-300/20 bg-red-500/10";
  }

  if (state === "warning" || state === "watch") {
    return "border-amber-300/20 bg-amber-500/10";
  }

  return "border-white/10 bg-white/10";
}

const GAUGE_WIDTH_CLASSES = [
  "w-0",
  "w-[5%]",
  "w-[10%]",
  "w-[15%]",
  "w-[20%]",
  "w-[25%]",
  "w-[30%]",
  "w-[35%]",
  "w-[40%]",
  "w-[45%]",
  "w-1/2",
  "w-[55%]",
  "w-[60%]",
  "w-[65%]",
  "w-[70%]",
  "w-[75%]",
  "w-[80%]",
  "w-[85%]",
  "w-[90%]",
  "w-[95%]",
  "w-full",
];

function gaugeWidthClass(percentage: number) {
  const clamped = Math.max(0, Math.min(100, percentage));
  const bucket = Math.round(clamped / 5);

  return GAUGE_WIDTH_CLASSES[bucket] ?? "w-full";
}

function formatSoftAlertLabel(state: ChatUsageSoftAlertState) {
  if (state === "exhausted") {
    return "Exhausted";
  }

  if (state === "critical") {
    return "Critical";
  }

  if (state === "warning") {
    return "Warning";
  }

  if (state === "watch") {
    return "Watch";
  }

  return "Healthy";
}

export function UsageFuelGauge({ className }: { className?: string }) {
  const [stats, setStats] = useState<ChatUsageResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUsage = async () => {
    try {
      const token = apiClient.getToken();
      if (!token) {
        setStats(null);
        return;
      }

      const data = await apiClient.chatService.getUsage();
      setStats(data);
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

  const percentage = Math.min(stats.request_percentage_used, 100);
  const providerLabel = stats.provider.active_provider ?? "Unavailable";
  const modelLabel = stats.provider.active_model ?? "Unavailable";
  const laneReason = stats.attribution.lane.reason ?? "Lane attribution is unavailable.";
  const missionReason = stats.attribution.mission.reason ?? "Mission attribution is unavailable.";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "flex items-center gap-2 rounded-md border px-2 py-1 cursor-help transition-opacity hover:opacity-80",
              triggerTone(stats.soft_alert.state),
              className
            )}
          >
            <span className="text-[10px] font-medium opacity-80 uppercase tracking-wider">Fuel</span>

            <div className="w-16 h-2 bg-black/20 rounded-full overflow-hidden relative border border-white/10">
              <div
                className={cn(
                  "h-full transition-all duration-500 ease-out",
                  gaugeClassName(stats.soft_alert.state),
                  gaugeWidthClass(percentage)
                )}
              />
            </div>

            <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" aria-hidden="true" />

            <span className={cn("text-xs font-mono font-bold", textTone(stats.soft_alert.state))}>
              {stats.used}/{stats.limit}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent className="bg-slate-900 border-slate-700 text-white p-3">
          <div className="space-y-2 max-w-xs">
            <p className="font-semibold">Daily AI Quota</p>
            <p className="text-xs text-slate-300">
              You have used {stats.used} of {stats.limit} managed requests today. {stats.remaining} remain.
            </p>
            <p className="text-xs text-slate-300">
              Soft alert: <span className="font-semibold text-white">{formatSoftAlertLabel(stats.soft_alert.state)}</span> ({stats.soft_alert.percent_used.toFixed(1)}%)
            </p>
            <p className="text-xs text-slate-300">{stats.soft_alert.message}</p>
            <div className="space-y-1 border-t border-slate-700/70 pt-2 text-xs text-slate-300">
              <p>
                Provider: <span className="text-white">{providerLabel}</span>
              </p>
              <p>
                Model: <span className="text-white">{modelLabel}</span>
              </p>
              <p>
                Tokens today: <span className="text-white">{stats.token_telemetry.total_tokens.toLocaleString()}</span>
                {" "}
                ({stats.token_telemetry.input_tokens.toLocaleString()} in / {stats.token_telemetry.output_tokens.toLocaleString()} out)
              </p>
              <p>{stats.token_telemetry.coverage_message}</p>
              <p>{laneReason}</p>
              <p>{missionReason}</p>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
