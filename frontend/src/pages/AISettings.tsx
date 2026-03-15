import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Bot,
  Cpu,
  KeyRound,
  Plus,
  RefreshCw,
  Trash2,
  ShieldCheck,
  WandSparkles,
} from "lucide-react";
import {
  type AIProvider,
  type AIProviderCreatePayload,
  type AIProviderModel,
  type CapabilityManifestCategory,
  type ProviderModelCatalogEntry,
  type AIProviderModelCreatePayload,
  type ReevuAgentSetting,
  type ReevuAgentSettingCreatePayload,
  type ReevuRoutingPolicy,
  type ReevuRoutingPolicyUpsertPayload,
} from "@/lib/api/system/ai-configuration";
import {
  type ChatDiagnosticsProviderLatencySummary,
  type ChatDiagnosticsRoutingDecisionSummary,
  type ChatDiagnosticsRoutingState,
  type ChatDiagnosticsSafeFailureSummary,
  type ChatDiagnosticsStatusSummary,
  type ChatMetricsPolicyFlagSummary,
} from "@/lib/api/system/chat-health";
import { apiClient } from "@/lib/api-client";
import {
  getModelPresets,
  getProviderPreset,
  PROVIDER_PRESETS,
  type ModelLifecycleStrategy,
  type ModelPreset,
  type ProviderPreset,
} from "@/lib/ai-model-catalog";
import { useHydratedSuperuserQueryAccess } from "@/store/auth";

type JsonRecord = Record<string, unknown> | null;

interface ProviderFormState {
  provider_key: string;
  display_name: string;
  base_url: string;
  auth_mode: string;
  encrypted_api_key: string;
  priority: string;
  is_enabled: boolean;
  is_byok_allowed: boolean;
  settings: string;
}

interface ModelFormState {
  provider_id: string;
  model_name: string;
  display_name: string;
  capability_tags: string;
  max_tokens: string;
  temperature: string;
  is_default: boolean;
  is_streaming_supported: boolean;
  is_active: boolean;
  settings: string;
}

interface AgentFormState {
  agent_key: string;
  display_name: string;
  provider_id: string;
  provider_model_id: string;
  system_prompt_override: string;
  tool_policy: string;
  default_task_context: string;
  sampling_temperature: string;
  max_tokens: string;
  capability_overrides: string;
  is_active: boolean;
}

interface RoutingPolicyFormState {
  agent_key: string;
  display_name: string;
  preferred_provider_id: string;
  preferred_provider_model_id: string;
  fallback_to_priority_order: boolean;
  is_active: boolean;
}

const providerDefaults = (): ProviderFormState => ({
  provider_key: "",
  display_name: "",
  base_url: "",
  auth_mode: "api_key",
  encrypted_api_key: "",
  priority: "100",
  is_enabled: true,
  is_byok_allowed: true,
  settings: "",
});

const modelDefaults = (): ModelFormState => ({
  provider_id: "",
  model_name: "",
  display_name: "",
  capability_tags: "",
  max_tokens: "",
  temperature: "",
  is_default: false,
  is_streaming_supported: true,
  is_active: true,
  settings: "",
});

const agentDefaults = (): AgentFormState => ({
  agent_key: "",
  display_name: "",
  provider_id: "",
  provider_model_id: "",
  system_prompt_override: "",
  tool_policy: "",
  default_task_context: "",
  sampling_temperature: "",
  max_tokens: "",
  capability_overrides: "",
  is_active: true,
});

const routingPolicyDefaults = (): RoutingPolicyFormState => ({
  agent_key: "reevu",
  display_name: "REEVU Routing Policy",
  preferred_provider_id: "",
  preferred_provider_model_id: "",
  fallback_to_priority_order: true,
  is_active: true,
});

function applyProviderPreset(form: ProviderFormState, preset: ProviderPreset): ProviderFormState {
  return {
    ...form,
    provider_key: preset.provider_key,
    display_name: preset.display_name,
    base_url: preset.base_url,
    auth_mode: preset.provider_key === "ollama" ? "none" : "api_key",
    priority: preset.priority,
  };
}

function applyModelPreset(form: ModelFormState, preset: ModelPreset): ModelFormState {
  return {
    ...form,
    model_name: preset.model_name,
    display_name: preset.display_name,
    capability_tags: preset.capability_tags,
    max_tokens: preset.max_tokens,
    temperature: preset.temperature,
  };
}

const modelLifecycleStrategies = new Set<ModelLifecycleStrategy>([
  "provider_alias_latest",
  "provider_named_family",
  "managed_named_model",
  "builtin_template",
]);

const modelLifecycleLabels: Record<ModelLifecycleStrategy, string> = {
  provider_alias_latest: "Provider latest alias",
  provider_named_family: "Provider family default",
  managed_named_model: "Named managed default",
  builtin_template: "Built-in template fallback",
};

function normalizeModelLifecycleStrategy(value: string): ModelLifecycleStrategy {
  return modelLifecycleStrategies.has(value as ModelLifecycleStrategy)
    ? value as ModelLifecycleStrategy
    : "managed_named_model";
}

function normalizeModelLifecycleLabel(strategy: ModelLifecycleStrategy, label: string): string {
  const trimmed = label.trim();
  return trimmed || modelLifecycleLabels[strategy];
}

function toProviderPreset(entry: ProviderModelCatalogEntry): ProviderPreset {
  const modelLifecycle = normalizeModelLifecycleStrategy(entry.model_lifecycle);
  return {
    label: entry.provider_preset_label,
    provider_key: entry.provider_key,
    display_name: entry.provider_display_name,
    base_url: entry.base_url,
    priority: String(entry.default_priority),
    recommended_model: entry.recommended_model,
    model_lifecycle: modelLifecycle,
    model_lifecycle_label: normalizeModelLifecycleLabel(modelLifecycle, entry.model_lifecycle_label),
  };
}

function toModelPresets(entry: ProviderModelCatalogEntry): ModelPreset[] {
  return entry.model_presets.map(preset => {
    const lifecycle = normalizeModelLifecycleStrategy(preset.lifecycle);

    return {
      label: preset.label,
      model_name: preset.model_name,
      display_name: preset.display_name,
      capability_tags: preset.capability_tags.join(", "),
      max_tokens: String(preset.max_tokens),
      temperature: String(preset.temperature),
      lifecycle,
      lifecycle_label: normalizeModelLifecycleLabel(lifecycle, preset.lifecycle_label),
    };
  });
}

function parseJsonObject(raw: string, label: string): JsonRecord {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error(`${label} must be a JSON object`);
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`${label}: ${error.message}`);
    }
    throw new Error(`${label} is not valid JSON`);
  }
}

function parseTagList(raw: string) {
  const tags = raw
    .split(",")
    .map(tag => tag.trim())
    .filter(Boolean);
  return tags.length > 0 ? tags : null;
}

function toNumberOrNull(raw: string) {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  const parsed = Number(trimmed);
  if (Number.isNaN(parsed)) {
    throw new Error(`Invalid number: ${raw}`);
  }
  return parsed;
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString();
}

function formatUptime(seconds: number | undefined) {
  if (!seconds) {
    return "-";
  }

  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }

  if (seconds < 3600) {
    return `${Math.round(seconds / 60)}m`;
  }

  if (seconds < 86400) {
    return `${Math.round(seconds / 3600)}h`;
  }

  return `${Math.round(seconds / 86400)}d`;
}

function formatRoutingLabel(value: string) {
  return value.replace(/_/g, " ");
}

function extractErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

function buildProviderPayload(form: ProviderFormState): AIProviderCreatePayload {
  return {
    provider_key: form.provider_key.trim(),
    display_name: form.display_name.trim(),
    base_url: form.base_url.trim() || null,
    auth_mode: form.auth_mode.trim() || "api_key",
    encrypted_api_key: form.encrypted_api_key.trim() || null,
    priority: Number(form.priority || "100"),
    is_enabled: form.is_enabled,
    is_byok_allowed: form.is_byok_allowed,
    settings: parseJsonObject(form.settings, "Provider settings"),
  };
}

function buildModelPayload(form: ModelFormState): AIProviderModelCreatePayload {
  const providerId = Number(form.provider_id);
  if (!providerId) {
    throw new Error("Provider is required");
  }

  return {
    provider_id: providerId,
    model_name: form.model_name.trim(),
    display_name: form.display_name.trim() || null,
    capability_tags: parseTagList(form.capability_tags),
    max_tokens: toNumberOrNull(form.max_tokens),
    temperature: toNumberOrNull(form.temperature),
    is_default: form.is_default,
    is_streaming_supported: form.is_streaming_supported,
    is_active: form.is_active,
    settings: parseJsonObject(form.settings, "Model settings"),
  };
}

function buildAgentPayload(form: AgentFormState): ReevuAgentSettingCreatePayload {
  return {
    agent_key: form.agent_key.trim(),
    display_name: form.display_name.trim() || null,
    provider_id: form.provider_id ? Number(form.provider_id) : null,
    provider_model_id: form.provider_model_id ? Number(form.provider_model_id) : null,
    system_prompt_override: form.system_prompt_override.trim() || null,
    tool_policy: parseJsonObject(form.tool_policy, "Tool policy"),
    default_task_context: parseJsonObject(form.default_task_context, "Default task context"),
    sampling_temperature: toNumberOrNull(form.sampling_temperature),
    max_tokens: toNumberOrNull(form.max_tokens),
    capability_overrides: parseTagList(form.capability_overrides),
    is_active: form.is_active,
  };
}

function buildRoutingPolicyPayload(form: RoutingPolicyFormState): ReevuRoutingPolicyUpsertPayload {
  return {
    agent_key: form.agent_key.trim(),
    display_name: form.display_name.trim() || null,
    preferred_provider_id: form.preferred_provider_id ? Number(form.preferred_provider_id) : null,
    preferred_provider_model_id: form.preferred_provider_model_id ? Number(form.preferred_provider_model_id) : null,
    fallback_to_priority_order: form.fallback_to_priority_order,
    is_active: form.is_active,
  };
}

function RoutingTelemetryContent({
  variant,
  routingState,
  activeProvider,
  activeModel,
  activeProviderSourceLabel,
  requestStatuses,
  providerLatencies,
  safeFailures,
  routingDecisions,
  policyFlags,
}: {
  variant: "compact" | "full";
  routingState: ChatDiagnosticsRoutingState | undefined;
  activeProvider: string | undefined;
  activeModel: string | undefined;
  activeProviderSourceLabel: string | undefined;
  requestStatuses: ChatDiagnosticsStatusSummary[];
  providerLatencies: ChatDiagnosticsProviderLatencySummary[];
  safeFailures: ChatDiagnosticsSafeFailureSummary[];
  routingDecisions: ChatDiagnosticsRoutingDecisionSummary[];
  policyFlags: ChatMetricsPolicyFlagSummary[];
}) {
  const safeFailureCount = safeFailures.reduce((sum, item) => sum + item.count, 0);

  if (variant === "compact") {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Runtime State</div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="outline">
              {formatRoutingLabel(routingState?.selection_mode || "priority_order")}
            </Badge>
            {routingState?.preferred_provider ? (
              <Badge variant="outline">preferred {routingState.preferred_provider}</Badge>
            ) : null}
            {routingState?.preferred_provider_only ? (
              <Badge className="bg-amber-100 text-amber-800">preferred only</Badge>
            ) : null}
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Active Provider</span>
              <span className="font-medium capitalize">{activeProvider || "unknown"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Active Model</span>
              <span className="font-medium">{activeModel || "-"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Power Source</span>
              <span className="font-medium">{activeProviderSourceLabel || "Unavailable"}</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Recent Decisions</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {routingDecisions.slice(0, 4).length ? routingDecisions.slice(0, 4).map(item => (
              <Badge key={item.decision} variant="outline">
                {formatRoutingLabel(item.decision)}: {item.count}
              </Badge>
            )) : <span className="text-sm text-muted-foreground">No routing telemetry recorded yet</span>}
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Safe failures observed: <span className="font-medium text-foreground">{safeFailureCount}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Request Statuses</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {requestStatuses.length ? requestStatuses.map(item => (
              <Badge key={item.status} variant="outline">{item.status}: {item.count}</Badge>
            )) : <span className="text-sm text-muted-foreground">No request telemetry yet</span>}
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Provider Latency</div>
          <div className="mt-3 space-y-2">
            {providerLatencies.length ? providerLatencies.map(item => (
              <div key={item.provider} className="flex items-center justify-between text-sm">
                <span className="font-medium capitalize">{item.provider}</span>
                <span className="text-muted-foreground">P50 {Math.round(item.p50 * 1000)}ms</span>
              </div>
            )) : <div className="text-sm text-muted-foreground">No provider latency samples yet</div>}
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Safe Failures</div>
          <div className="mt-3 space-y-2">
            {safeFailures.length ? safeFailures.map(item => (
              <div key={item.reason} className="flex items-center justify-between text-sm">
                <span className="font-medium">{formatRoutingLabel(item.reason)}</span>
                <span className="text-muted-foreground">{item.count}</span>
              </div>
            )) : <div className="text-sm text-muted-foreground">No safe failures recorded</div>}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Routing State</div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="outline">
              {formatRoutingLabel(routingState?.selection_mode || "priority_order")}
            </Badge>
            {routingState?.preferred_provider ? (
              <Badge variant="outline">preferred {routingState.preferred_provider}</Badge>
            ) : null}
            {routingState?.preferred_provider_only ? (
              <Badge className="bg-amber-100 text-amber-800">preferred only</Badge>
            ) : null}
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Active provider: <span className="font-medium text-foreground capitalize">{activeProvider || "unknown"}</span>
          </div>
          <div className="mt-2 text-sm text-muted-foreground">
            Power source: <span className="font-medium text-foreground">{activeProviderSourceLabel || "Unavailable"}</span>
          </div>
        </div>

        <div className="rounded-lg border p-4">
          <div className="text-sm font-medium text-muted-foreground">Routing Decisions</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {routingDecisions.length ? routingDecisions.map(item => (
              <Badge key={item.decision} variant="outline">
                {formatRoutingLabel(item.decision)}: {item.count}
              </Badge>
            )) : <span className="text-sm text-muted-foreground">No routing telemetry recorded yet</span>}
          </div>
        </div>
      </div>

      <div className="rounded-lg border p-4">
        <div className="text-sm font-medium text-muted-foreground">Policy Flags</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {policyFlags.length ? policyFlags.map(item => (
            <Badge key={item.flag} className="bg-amber-100 text-amber-800">
              {item.flag}: {item.count}
            </Badge>
          )) : <span className="text-sm text-muted-foreground">No policy validation flags recorded</span>}
        </div>
      </div>
    </div>
  );
}

function ProviderDialog({
  title,
  description,
  form,
  setForm,
  onSubmit,
  submitLabel,
  pending,
  trigger,
  open,
  onOpenChange,
  providerPresets = [],
}: {
  title: string;
  description: string;
  form: ProviderFormState;
  setForm: React.Dispatch<React.SetStateAction<ProviderFormState>>;
  onSubmit: () => void;
  submitLabel: string;
  pending: boolean;
  trigger: React.ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  providerPresets: ProviderPreset[];
}) {
  const isLocalProvider = form.provider_key === "ollama";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 md:grid-cols-2">
          <div className="rounded-lg border bg-muted/30 p-4 text-sm md:col-span-2">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <WandSparkles className="h-4 w-4" /> Quick Start
            </div>
            <p className="mt-2 text-muted-foreground">
              Choose a preset first. If REEVU already shows <span className="font-medium text-foreground">Server env key</span>, you do not need to paste the same key here again.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {providerPresets.map(preset => (
                <Button
                  key={preset.provider_key}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setForm(current => applyProviderPreset(current, preset))}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Cloud providers remain the default and recommended path. Ollama is available as an advanced local option and uses a host URL instead of a cloud API key.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Provider Key</Label>
            <Input
              value={form.provider_key}
              onChange={event => setForm(current => ({ ...current, provider_key: event.target.value }))}
              placeholder="openai"
            />
          </div>
          <div className="space-y-2">
            <Label>Display Name</Label>
            <Input
              value={form.display_name}
              onChange={event => setForm(current => ({ ...current, display_name: event.target.value }))}
              placeholder="OpenAI"
            />
          </div>
          <div className="space-y-2">
            <Label>Auth Mode</Label>
            <Input
              value={form.auth_mode}
              onChange={event => setForm(current => ({ ...current, auth_mode: event.target.value }))}
              placeholder="api_key"
            />
          </div>
          <div className="space-y-2">
            <Label>Priority</Label>
            <Input
              type="number"
              value={form.priority}
              onChange={event => setForm(current => ({ ...current, priority: event.target.value }))}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Base URL</Label>
            <Input
              value={form.base_url}
              onChange={event => setForm(current => ({ ...current, base_url: event.target.value }))}
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>{isLocalProvider ? "Local Provider Key" : "Server API Key"}</Label>
            <Input
              type="password"
              value={form.encrypted_api_key}
              onChange={event => setForm(current => ({ ...current, encrypted_api_key: event.target.value }))}
              placeholder={isLocalProvider ? "Leave blank for local Ollama routing" : "Paste only if you want organization-managed routing to use this key"}
            />
            <p className="text-xs text-muted-foreground">
              {isLocalProvider
                ? "Ollama does not require a cloud API key. Leave this blank unless your local gateway adds its own auth layer."
                : "Leave blank if runtime already uses a server env key or if you are editing metadata only."}
            </p>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Settings JSON</Label>
            <Textarea
              value={form.settings}
              onChange={event => setForm(current => ({ ...current, settings: event.target.value }))}
              placeholder='{"timeout": 30}'
              rows={4}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Provider Enabled</Label>
              <p className="text-sm text-muted-foreground">Eligible for managed routing.</p>
            </div>
            <Switch
              checked={form.is_enabled}
              onCheckedChange={checked => setForm(current => ({ ...current, is_enabled: checked }))}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>BYOK Allowed</Label>
              <p className="text-sm text-muted-foreground">Expose this provider to browser-side bring-your-own-key flows.</p>
            </div>
            <Switch
              checked={form.is_byok_allowed}
              onCheckedChange={checked => setForm(current => ({ ...current, is_byok_allowed: checked }))}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSubmit} disabled={pending}>{pending ? "Saving..." : submitLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ModelDialog({
  title,
  description,
  form,
  setForm,
  providers,
  onSubmit,
  submitLabel,
  pending,
  trigger,
  open,
  onOpenChange,
  providerPresets = [],
  modelPresetMap = null,
}: {
  title: string;
  description: string;
  form: ModelFormState;
  setForm: React.Dispatch<React.SetStateAction<ModelFormState>>;
  providers: AIProvider[];
  onSubmit: () => void;
  submitLabel: string;
  pending: boolean;
  trigger: React.ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  providerPresets?: ProviderPreset[];
  modelPresetMap?: Record<string, ModelPreset[]> | null;
}) {
  const selectedProvider = providers.find(provider => String(provider.id) === form.provider_id);
  const modelPresets = selectedProvider
    ? modelPresetMap?.[selectedProvider.provider_key] || getModelPresets(selectedProvider.provider_key)
    : [];
  const selectedProviderPreset = selectedProvider
    ? providerPresets.find(preset => preset.provider_key === selectedProvider.provider_key) || getProviderPreset(selectedProvider.provider_key)
    : undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 md:grid-cols-2">
          <div className="rounded-lg border bg-muted/30 p-4 text-sm md:col-span-2">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <WandSparkles className="h-4 w-4" /> Recommended Model Presets
            </div>
            <p className="mt-2 text-muted-foreground">
              Select a provider, then apply a preset instead of filling model metadata from scratch.
            </p>
            {selectedProviderPreset ? (
              <p className="mt-2 text-xs text-muted-foreground">
                {selectedProviderPreset.label} recommends <span className="font-medium text-foreground">{selectedProviderPreset.recommended_model}</span> using the <span className="font-medium text-foreground">{selectedProviderPreset.model_lifecycle_label}</span> policy.
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2">
              {modelPresets.length ? modelPresets.map(preset => (
                <Button
                  key={preset.model_name}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setForm(current => applyModelPreset(current, preset))}
                >
                  {preset.label}
                </Button>
              )) : <span className="text-xs text-muted-foreground">No presets until a provider is selected.</span>}
            </div>
          </div>
          <div className="space-y-2">
            <Label>Provider</Label>
            <Select value={form.provider_id} onValueChange={value => setForm(current => ({ ...current, provider_id: value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {providers.map(provider => (
                  <SelectItem key={provider.id} value={String(provider.id)}>{provider.display_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Model Name</Label>
            <Input
              value={form.model_name}
              onChange={event => setForm(current => ({ ...current, model_name: event.target.value }))}
              placeholder="gpt-4.1-mini"
            />
          </div>
          <div className="space-y-2">
            <Label>Display Name</Label>
            <Input
              value={form.display_name}
              onChange={event => setForm(current => ({ ...current, display_name: event.target.value }))}
              placeholder="GPT-4.1 Mini"
            />
          </div>
          <div className="space-y-2">
            <Label>Capability Tags</Label>
            <Input
              value={form.capability_tags}
              onChange={event => setForm(current => ({ ...current, capability_tags: event.target.value }))}
              placeholder="chat, reasoning, streaming"
            />
          </div>
          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input
              type="number"
              value={form.max_tokens}
              onChange={event => setForm(current => ({ ...current, max_tokens: event.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Temperature</Label>
            <Input
              type="number"
              step="0.1"
              value={form.temperature}
              onChange={event => setForm(current => ({ ...current, temperature: event.target.value }))}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Settings JSON</Label>
            <Textarea
              value={form.settings}
              onChange={event => setForm(current => ({ ...current, settings: event.target.value }))}
              placeholder='{"context_window": 128000}'
              rows={4}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Default Model</Label>
              <p className="text-sm text-muted-foreground">Preferred default for this provider.</p>
            </div>
            <Switch
              checked={form.is_default}
              onCheckedChange={checked => setForm(current => ({ ...current, is_default: checked }))}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Streaming Supported</Label>
              <p className="text-sm text-muted-foreground">Expose SSE streaming for this model.</p>
            </div>
            <Switch
              checked={form.is_streaming_supported}
              onCheckedChange={checked => setForm(current => ({ ...current, is_streaming_supported: checked }))}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Model Active</Label>
              <p className="text-sm text-muted-foreground">Available for runtime selection.</p>
            </div>
            <Switch
              checked={form.is_active}
              onCheckedChange={checked => setForm(current => ({ ...current, is_active: checked }))}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSubmit} disabled={pending}>{pending ? "Saving..." : submitLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AgentDialog({
  title,
  description,
  form,
  setForm,
  capabilityCategories,
  providers,
  models,
  onSubmit,
  submitLabel,
  pending,
  trigger,
  open,
  onOpenChange,
}: {
  title: string;
  description: string;
  form: AgentFormState;
  setForm: React.Dispatch<React.SetStateAction<AgentFormState>>;
  capabilityCategories: CapabilityManifestCategory[];
  providers: AIProvider[];
  models: AIProviderModel[];
  onSubmit: () => void;
  submitLabel: string;
  pending: boolean;
  trigger: React.ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const filteredModels = form.provider_id
    ? models.filter(model => model.provider_id === Number(form.provider_id))
    : models;
  const selectedCapabilities = useMemo(
    () => parseTagList(form.capability_overrides) || [],
    [form.capability_overrides],
  );

  const toggleCapability = (capabilityName: string, checked: boolean | string) => {
    const nextCapabilities = checked
      ? [...selectedCapabilities, capabilityName]
      : selectedCapabilities.filter(capability => capability !== capabilityName);
    const uniqueCapabilities = Array.from(new Set(nextCapabilities));

    setForm(current => ({
      ...current,
      capability_overrides: uniqueCapabilities.join(", "),
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Agent Key</Label>
            <Input
              value={form.agent_key}
              onChange={event => setForm(current => ({ ...current, agent_key: event.target.value }))}
              placeholder="reevu-default"
            />
          </div>
          <div className="space-y-2">
            <Label>Display Name</Label>
            <Input
              value={form.display_name}
              onChange={event => setForm(current => ({ ...current, display_name: event.target.value }))}
              placeholder="REEVU Default"
            />
          </div>
          <div className="space-y-2">
            <Label>Provider Override</Label>
            <Select value={form.provider_id || "none"} onValueChange={value => setForm(current => ({ ...current, provider_id: value === "none" ? "" : value, provider_model_id: value === "none" ? "" : current.provider_model_id }))}>
              <SelectTrigger>
                <SelectValue placeholder="Follow routing policy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Follow routing policy</SelectItem>
                {providers.map(provider => (
                  <SelectItem key={provider.id} value={String(provider.id)}>{provider.display_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Model Override</Label>
            <Select value={form.provider_model_id || "none"} onValueChange={value => setForm(current => ({ ...current, provider_model_id: value === "none" ? "" : value }))}>
              <SelectTrigger>
                <SelectValue placeholder="Provider default" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Provider default</SelectItem>
                {filteredModels.map(model => (
                  <SelectItem key={model.id} value={String(model.id)}>{model.display_name || model.model_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Sampling Temperature</Label>
            <Input
              type="number"
              step="0.1"
              value={form.sampling_temperature}
              onChange={event => setForm(current => ({ ...current, sampling_temperature: event.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input
              type="number"
              value={form.max_tokens}
              onChange={event => setForm(current => ({ ...current, max_tokens: event.target.value }))}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Capability Overrides</Label>
            <div className="rounded-lg border p-3">
              <p className="mb-3 text-sm text-muted-foreground">
                Select which REEVU tools this agent can use. Leaving everything unchecked keeps the agent on its standard unrestricted tool set.
              </p>
              <ScrollArea className="h-64 pr-3">
                <div className="space-y-4">
                  {capabilityCategories.map(category => (
                    <div key={category.id} className="space-y-2">
                      <div>
                        <p className="text-sm font-medium">{category.label}</p>
                        <p className="text-xs text-muted-foreground">{category.description}</p>
                      </div>
                      <div className="space-y-2">
                        {category.tools.map(tool => {
                          const checked = selectedCapabilities.includes(tool.name);
                          return (
                            <label key={tool.name} className="flex items-start gap-3 rounded-md border p-3">
                              <Checkbox
                                checked={checked}
                                onCheckedChange={value => toggleCapability(tool.name, value)}
                                className="mt-0.5"
                              />
                              <div className="space-y-1">
                                <div className="text-sm font-medium">{tool.label}</div>
                                <div className="text-xs text-muted-foreground">{tool.description}</div>
                                <div className="text-xs text-muted-foreground">{tool.name}</div>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>System Prompt Override</Label>
            <Textarea
              value={form.system_prompt_override}
              onChange={event => setForm(current => ({ ...current, system_prompt_override: event.target.value }))}
              rows={5}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Tool Policy JSON</Label>
            <Textarea
              value={form.tool_policy}
              onChange={event => setForm(current => ({ ...current, tool_policy: event.target.value }))}
              placeholder='{"search": "required"}'
              rows={4}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Default Task Context JSON</Label>
            <Textarea
              value={form.default_task_context}
              onChange={event => setForm(current => ({ ...current, default_task_context: event.target.value }))}
              placeholder='{"workspace": "breeding"}'
              rows={4}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Active</Label>
              <p className="text-sm text-muted-foreground">Allow this agent profile to be selected at runtime.</p>
            </div>
            <Switch
              checked={form.is_active}
              onCheckedChange={checked => setForm(current => ({ ...current, is_active: checked }))}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={onSubmit} disabled={pending}>{pending ? "Saving..." : submitLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function AISettings() {
  const canQueryAISettings = useHydratedSuperuserQueryAccess();

  const queryClient = useQueryClient();
  const [isTesting, setIsTesting] = useState(false);
  const [providerForm, setProviderForm] = useState(providerDefaults);
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [modelForm, setModelForm] = useState(modelDefaults);
  const [editingModel, setEditingModel] = useState<AIProviderModel | null>(null);
  const [modelDialogOpen, setModelDialogOpen] = useState(false);
  const [agentForm, setAgentForm] = useState(agentDefaults);
  const [editingAgent, setEditingAgent] = useState<ReevuAgentSetting | null>(null);
  const [agentDialogOpen, setAgentDialogOpen] = useState(false);
  const [routingPolicyForm, setRoutingPolicyForm] = useState(routingPolicyDefaults);
  const [activeTab, setActiveTab] = useState("routing");

  const providersQuery = useQuery({
    queryKey: ["ai-configuration", "providers"],
    queryFn: () => apiClient.aiConfigurationService.listProviders(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const modelsQuery = useQuery({
    queryKey: ["ai-configuration", "models"],
    queryFn: () => apiClient.aiConfigurationService.listModels(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const agentSettingsQuery = useQuery({
    queryKey: ["ai-configuration", "agent-settings"],
    queryFn: () => apiClient.aiConfigurationService.listAgentSettings(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const routingPoliciesQuery = useQuery({
    queryKey: ["ai-configuration", "routing-policies"],
    queryFn: () => apiClient.aiConfigurationService.listRoutingPolicies(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const capabilitiesQuery = useQuery({
    queryKey: ["ai-configuration", "capabilities"],
    queryFn: () => apiClient.aiConfigurationService.listCapabilities(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const modelCatalogQuery = useQuery({
    queryKey: ["ai-configuration", "model-catalog"],
    queryFn: () => apiClient.aiConfigurationService.listModelCatalog(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const chatHealthQuery = useQuery({
    queryKey: ["chat-health"],
    queryFn: () => apiClient.chatHealthService.getChatHealth(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const chatMetricsQuery = useQuery({
    queryKey: ["chat-metrics"],
    queryFn: () => apiClient.chatHealthService.getChatMetrics(),
    enabled: canQueryAISettings,
    retry: false,
  });
  const chatDiagnosticsQuery = useQuery({
    queryKey: ["chat-diagnostics"],
    queryFn: () => apiClient.chatHealthService.getChatDiagnostics(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const providers = providersQuery.data || [];
  const models = modelsQuery.data || [];
  const agentSettings = agentSettingsQuery.data || [];
  const routingPolicies = routingPoliciesQuery.data || [];
  const capabilityCategories = capabilitiesQuery.data || [];
  const modelCatalog = modelCatalogQuery.data || [];
  const chatHealth = chatHealthQuery.data;
  const chatMetrics = chatMetricsQuery.data;
  const chatDiagnostics = chatDiagnosticsQuery.data;
  const providerPresets = modelCatalog.length
    ? modelCatalog.map(toProviderPreset)
    : PROVIDER_PRESETS;
  const modelPresetMap = modelCatalog.length
    ? Object.fromEntries(modelCatalog.map(entry => [entry.provider_key, toModelPresets(entry)]))
    : null;

  useEffect(() => {
    if (providers.length === 0 && activeTab === "routing") {
      setActiveTab("providers");
    }
  }, [activeTab, providers.length]);

  const modelsByProvider = useMemo(() => {
    return models.reduce<Record<number, AIProviderModel[]>>((acc, model) => {
      acc[model.provider_id] = acc[model.provider_id] || [];
      acc[model.provider_id].push(model);
      return acc;
    }, {});
  }, [models]);

  const providerLookup = useMemo(() => {
    return Object.fromEntries(providers.map(provider => [provider.id, provider]));
  }, [providers]);

  const modelLookup = useMemo(() => {
    return Object.fromEntries(models.map(model => [model.id, model]));
  }, [models]);

  const routingPolicy = useMemo(() => {
    return routingPolicies.find(policy => policy.agent_key === "reevu") || null;
  }, [routingPolicies]);

  const routingPolicyModels = useMemo(() => {
    return routingPolicyForm.preferred_provider_id
      ? models.filter(model => model.provider_id === Number(routingPolicyForm.preferred_provider_id))
      : models;
  }, [models, routingPolicyForm.preferred_provider_id]);

  useEffect(() => {
    if (routingPolicy) {
      setRoutingPolicyForm({
        agent_key: routingPolicy.agent_key,
        display_name: routingPolicy.display_name || "",
        preferred_provider_id: routingPolicy.preferred_provider_id ? String(routingPolicy.preferred_provider_id) : "",
        preferred_provider_model_id: routingPolicy.preferred_provider_model_id ? String(routingPolicy.preferred_provider_model_id) : "",
        fallback_to_priority_order: routingPolicy.fallback_to_priority_order,
        is_active: routingPolicy.is_active,
      });
      return;
    }

    setRoutingPolicyForm(routingPolicyDefaults());
  }, [routingPolicy]);

  const refreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "providers"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "models"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "agent-settings"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "routing-policies"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "model-catalog"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-health"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-metrics"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-diagnostics"] }),
    ]);
  };

  const providerMutation = useMutation({
    mutationFn: async () => {
      const payload = buildProviderPayload(providerForm);
      if (editingProvider) {
        return apiClient.aiConfigurationService.updateProvider(editingProvider.id, payload);
      }
      return apiClient.aiConfigurationService.createProvider(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setProviderDialogOpen(false);
      setEditingProvider(null);
      setProviderForm(providerDefaults());
      toast.success(editingProvider ? "Provider updated" : "Provider created");
    },
    onError: error => {
      toast.error(extractErrorMessage(error));
    },
  });

  const modelMutation = useMutation({
    mutationFn: async () => {
      const payload = buildModelPayload(modelForm);
      if (editingModel) {
        return apiClient.aiConfigurationService.updateModel(editingModel.id, payload);
      }
      return apiClient.aiConfigurationService.createModel(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setModelDialogOpen(false);
      setEditingModel(null);
      setModelForm(modelDefaults());
      toast.success(editingModel ? "Model updated" : "Model created");
    },
    onError: error => {
      toast.error(extractErrorMessage(error));
    },
  });

  const agentMutation = useMutation({
    mutationFn: async () => {
      const payload = buildAgentPayload(agentForm);
      if (editingAgent) {
        return apiClient.aiConfigurationService.updateAgentSetting(editingAgent.id, payload);
      }
      return apiClient.aiConfigurationService.createAgentSetting(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setAgentDialogOpen(false);
      setEditingAgent(null);
      setAgentForm(agentDefaults());
      toast.success(editingAgent ? "Agent setting updated" : "Agent setting created");
    },
    onError: error => {
      toast.error(extractErrorMessage(error));
    },
  });

  const deleteProviderMutation = useMutation({
    mutationFn: (providerId: number) => apiClient.aiConfigurationService.deleteProvider(providerId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Provider deleted");
    },
    onError: error => toast.error(extractErrorMessage(error)),
  });

  const deleteModelMutation = useMutation({
    mutationFn: (modelId: number) => apiClient.aiConfigurationService.deleteModel(modelId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Model deleted");
    },
    onError: error => toast.error(extractErrorMessage(error)),
  });

  const deleteAgentMutation = useMutation({
    mutationFn: (settingId: number) => apiClient.aiConfigurationService.deleteAgentSetting(settingId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Agent setting deleted");
    },
    onError: error => toast.error(extractErrorMessage(error)),
  });

  const routingPolicyMutation = useMutation({
    mutationFn: () => {
      const payload = buildRoutingPolicyPayload(routingPolicyForm);
      return apiClient.aiConfigurationService.upsertRoutingPolicy(payload.agent_key, payload);
    },
    onSuccess: async () => {
      await refreshAll();
      toast.success(routingPolicy ? "Routing policy updated" : "Routing policy saved");
    },
    onError: error => {
      toast.error(extractErrorMessage(error));
    },
  });

  const deleteRoutingPolicyMutation = useMutation({
    mutationFn: (agentKey: string) => apiClient.aiConfigurationService.deleteRoutingPolicy(agentKey),
    onSuccess: async () => {
      await refreshAll();
      setRoutingPolicyForm(routingPolicyDefaults());
      toast.success("Routing policy cleared");
    },
    onError: error => toast.error(extractErrorMessage(error)),
  });

  const loading = providersQuery.isLoading || modelsQuery.isLoading || agentSettingsQuery.isLoading || routingPoliciesQuery.isLoading || modelCatalogQuery.isLoading;

  const activeProviders = providers.filter(provider => provider.is_enabled).length;
  const activeModels = models.filter(model => model.is_active).length;
  const activeAgents = agentSettings.filter(agent => agent.is_active).length;
  const runtimeP50Ms = chatMetrics?.latency?.total?.p50 ? Math.round(chatMetrics.latency.total.p50 * 1000) : null;
  const runtimeP95Ms = chatMetrics?.latency?.total?.p95 ? Math.round(chatMetrics.latency.total.p95 * 1000) : null;
  const routingState = chatDiagnostics?.routing_state;
  const requestStatuses = chatDiagnostics?.request_statuses || [];
  const providerLatencies = chatDiagnostics?.provider_latencies || [];
  const safeFailures = chatDiagnostics?.safe_failures || [];
  const routingDecisions = chatDiagnostics?.routing_decisions || [];
  const policyFlags = chatDiagnostics?.policy_flags || [];
  const telemetryActiveProvider = chatDiagnostics?.active_provider || chatHealth?.active_provider;
  const telemetryActiveModel = chatDiagnostics?.active_model || chatHealth?.active_model;

  const openCreateProvider = () => {
    setEditingProvider(null);
    setProviderForm(providerDefaults());
    setProviderDialogOpen(true);
  };

  const openEditProvider = (provider: AIProvider) => {
    setEditingProvider(provider);
    setProviderForm({
      provider_key: provider.provider_key,
      display_name: provider.display_name,
      base_url: provider.base_url || "",
      auth_mode: provider.auth_mode,
      encrypted_api_key: "",
      priority: String(provider.priority),
      is_enabled: provider.is_enabled,
      is_byok_allowed: provider.is_byok_allowed,
      settings: provider.settings ? JSON.stringify(provider.settings, null, 2) : "",
    });
    setProviderDialogOpen(true);
  };

  const openCreateModel = () => {
    setEditingModel(null);
    setModelForm(modelDefaults());
    setModelDialogOpen(true);
  };

  const openEditModel = (model: AIProviderModel) => {
    setEditingModel(model);
    setModelForm({
      provider_id: String(model.provider_id),
      model_name: model.model_name,
      display_name: model.display_name || "",
      capability_tags: model.capability_tags?.join(", ") || "",
      max_tokens: model.max_tokens ? String(model.max_tokens) : "",
      temperature: model.temperature !== null ? String(model.temperature) : "",
      is_default: model.is_default,
      is_streaming_supported: model.is_streaming_supported,
      is_active: model.is_active,
      settings: model.settings ? JSON.stringify(model.settings, null, 2) : "",
    });
    setModelDialogOpen(true);
  };

  const openCreateAgent = () => {
    setEditingAgent(null);
    setAgentForm(agentDefaults());
    setAgentDialogOpen(true);
  };

  const openEditAgent = (agent: ReevuAgentSetting) => {
    setEditingAgent(agent);
    setAgentForm({
      agent_key: agent.agent_key,
      display_name: agent.display_name || "",
      provider_id: agent.provider_id ? String(agent.provider_id) : "",
      provider_model_id: agent.provider_model_id ? String(agent.provider_model_id) : "",
      system_prompt_override: agent.system_prompt_override || "",
      tool_policy: agent.tool_policy ? JSON.stringify(agent.tool_policy, null, 2) : "",
      default_task_context: agent.default_task_context ? JSON.stringify(agent.default_task_context, null, 2) : "",
      sampling_temperature: agent.sampling_temperature !== null ? String(agent.sampling_temperature) : "",
      max_tokens: agent.max_tokens !== null ? String(agent.max_tokens) : "",
      capability_overrides: agent.capability_overrides?.join(", ") || "",
      is_active: agent.is_active,
    });
    setAgentDialogOpen(true);
  };

  const testConnection = async () => {
    setIsTesting(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const token = apiClient.getToken();
      const response = await fetch("/api/v2/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: "Reply only with: READY",
          include_context: false,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      if (data?.provider === "template") {
        toast.error("Backend is reachable, but managed provider routing still resolves to template fallback.");
        return;
      }

      toast.success(`REEVU connected via ${data.provider || "managed backend"}`);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        toast.error("Connection timed out");
      } else {
        toast.error("Connection failed. Check backend health and provider credentials.");
      }
    } finally {
      clearTimeout(timeoutId);
      setIsTesting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-1">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold lg:text-3xl">AI Configuration</h1>
          <p className="mt-1 text-muted-foreground">
            Configure managed providers, model defaults, and REEVU agent routing for this organization.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => void refreshAll()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={testConnection} disabled={isTesting}>
            <WandSparkles className="mr-2 h-4 w-4" />
            {isTesting ? "Testing..." : "Test REEVU Runtime"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium"><KeyRound className="h-4 w-4" /> Active Providers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeProviders}</div>
            <p className="text-sm text-muted-foreground">{providers.length} total provider records</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium"><Cpu className="h-4 w-4" /> Active Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeModels}</div>
            <p className="text-sm text-muted-foreground">{models.length} model configurations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium"><Bot className="h-4 w-4" /> Active Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAgents}</div>
            <p className="text-sm text-muted-foreground">{agentSettings.length} REEVU agent profiles</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium"><ShieldCheck className="h-4 w-4" /> Runtime Provider</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{chatHealth?.active_provider || 'unknown'}</div>
            <p className="text-sm text-muted-foreground">{chatHealth?.active_model || 'No active model'}</p>
            <p className="mt-1 text-xs text-muted-foreground">{chatHealth?.active_provider_source_label || 'Unavailable'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium"><Cpu className="h-4 w-4" /> Runtime Load</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{chatMetrics?.total_requests ?? 0}</div>
            <p className="text-sm text-muted-foreground">
              {runtimeP50Ms !== null ? `P50 ${runtimeP50Ms}ms` : 'No latency samples yet'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Managed Mode</CardTitle>
          <CardDescription>
            REEVU now runs through the backend-managed routing path. Browser-side keys are not stored here.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <Badge variant="default">Managed Backend</Badge>
          {chatHealth?.active_provider_source_label ? <Badge variant="outline">{chatHealth.active_provider_source_label}</Badge> : null}
          <span>Provider selection, model defaults, and agent overrides are enforced server-side per organization.</span>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Runtime Health</CardTitle>
          <CardDescription>
            Live status from the canonical REEVU chat runtime, using the same request-scoped provider path as production chat.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2">
              <Badge className={chatHealth?.llm_enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}>
                {chatHealth?.llm_enabled ? 'LLM Enabled' : 'Template Fallback'}
              </Badge>
              {chatHealth?.free_tier_available ? <Badge variant="outline">Free Tier Available</Badge> : null}
              {chatHealth?.rag_enabled ? <Badge variant="outline">RAG Enabled</Badge> : null}
            </div>
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Assistant</span>
                <span className="font-medium">{chatHealth?.assistant || 'REEVU'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Active Provider</span>
                <span className="font-medium capitalize">{chatHealth?.active_provider || 'unknown'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Active Model</span>
                <span className="font-medium">{chatHealth?.active_model || '-'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Power Source</span>
                <span className="font-medium">{chatHealth?.active_provider_source_label || 'Unavailable'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Capabilities</span>
                <span className="font-medium">{chatHealth?.capabilities?.length || 0}</span>
              </div>
            </div>
          </div>

          <div className="rounded-lg border p-4">
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Uptime</span>
                <span className="font-medium">{formatUptime(chatMetrics?.uptime_seconds)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Requests</span>
                <span className="font-medium">{chatMetrics?.total_requests ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">P50 Latency</span>
                <span className="font-medium">{runtimeP50Ms !== null ? `${runtimeP50Ms}ms` : '-'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">P95 Latency</span>
                <span className="font-medium">{runtimeP95Ms !== null ? `${runtimeP95Ms}ms` : '-'}</span>
              </div>
              <div className="flex items-start justify-between gap-4">
                <span className="text-muted-foreground">Policy Flags</span>
                <span className="font-medium">{chatMetrics?.policy_flags?.length ?? 0}</span>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(chatHealth?.capabilities || []).slice(0, 4).map(capability => (
                <Badge key={capability} variant="outline">{capability}</Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="routing">Routing</TabsTrigger>
          <TabsTrigger value="diagnostics">Diagnostics</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="agents">REEVU Agents</TabsTrigger>
        </TabsList>

        {providers.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col gap-3 p-4 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
              <div>
                <div className="font-medium text-foreground">Start with a provider</div>
                <p>Add your provider and API key first. After that, add a model and then decide how REEVU should route to it.</p>
              </div>
              <Button onClick={openCreateProvider}>
                <Plus className="mr-2 h-4 w-4" />Add Provider
              </Button>
            </CardContent>
          </Card>
        ) : null}

        <TabsContent value="routing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Routing Policy</CardTitle>
              <CardDescription>
                Set the organization default REEVU provider and model, then choose whether managed routing may fall back to priority order.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Policy Name</Label>
                  <Input
                    value={routingPolicyForm.display_name}
                    onChange={event => setRoutingPolicyForm(current => ({ ...current, display_name: event.target.value }))}
                    placeholder="REEVU Routing Policy"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Agent Key</Label>
                  <Input value={routingPolicyForm.agent_key} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Preferred Provider</Label>
                  <Select
                    value={routingPolicyForm.preferred_provider_id || "none"}
                    onValueChange={value => setRoutingPolicyForm(current => ({
                      ...current,
                      preferred_provider_id: value === "none" ? "" : value,
                      preferred_provider_model_id: value === "none" ? "" : current.preferred_provider_model_id,
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Priority routing only" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Priority routing only</SelectItem>
                      {providers.map(provider => (
                        <SelectItem key={provider.id} value={String(provider.id)}>{provider.display_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Preferred Model</Label>
                  <Select
                    value={routingPolicyForm.preferred_provider_model_id || "none"}
                    onValueChange={value => setRoutingPolicyForm(current => ({ ...current, preferred_provider_model_id: value === "none" ? "" : value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Provider default" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Provider default</SelectItem>
                      {routingPolicyModels.map(model => (
                        <SelectItem key={model.id} value={String(model.id)}>{model.display_name || model.model_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <Label>Fallback to Priority Order</Label>
                    <p className="text-sm text-muted-foreground">
                      When the preferred provider is unavailable, continue through the existing managed priority order.
                    </p>
                  </div>
                  <Switch
                    checked={routingPolicyForm.fallback_to_priority_order}
                    onCheckedChange={checked => setRoutingPolicyForm(current => ({ ...current, fallback_to_priority_order: checked }))}
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <Label>Policy Active</Label>
                    <p className="text-sm text-muted-foreground">
                      Disable this to return REEVU to plain provider priority routing for the organization.
                    </p>
                  </div>
                  <Switch
                    checked={routingPolicyForm.is_active}
                    onCheckedChange={checked => setRoutingPolicyForm(current => ({ ...current, is_active: checked }))}
                  />
                </div>
              </div>

              <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                {routingPolicyForm.preferred_provider_id
                  ? `Current target: ${providerLookup[Number(routingPolicyForm.preferred_provider_id)]?.display_name || "Unknown provider"}${routingPolicyForm.preferred_provider_model_id ? ` / ${modelLookup[Number(routingPolicyForm.preferred_provider_model_id)]?.display_name || modelLookup[Number(routingPolicyForm.preferred_provider_model_id)]?.model_name || "Provider default"}` : " / Provider default"}.`
                  : "Current target: provider priority order only."}
              </div>

              <div className="flex flex-wrap gap-3">
                <Button onClick={() => routingPolicyMutation.mutate()} disabled={routingPolicyMutation.isPending}>
                  {routingPolicyMutation.isPending ? "Saving..." : "Save Routing Policy"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setRoutingPolicyForm(routingPolicyDefaults())}
                  disabled={routingPolicyMutation.isPending}
                >
                  Reset Form
                </Button>
                <Button
                  variant="outline"
                  onClick={() => deleteRoutingPolicyMutation.mutate(routingPolicyForm.agent_key)}
                  disabled={!routingPolicy || deleteRoutingPolicyMutation.isPending}
                >
                  Clear Persisted Policy
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Live Routing Summary</CardTitle>
              <CardDescription>
                Compare the persisted routing policy with the current runtime selection path before leaving this tab.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <RoutingTelemetryContent
                variant="compact"
                routingState={routingState}
                activeProvider={telemetryActiveProvider}
                activeModel={telemetryActiveModel}
                activeProviderSourceLabel={chatDiagnostics?.active_provider_source_label || chatHealth?.active_provider_source_label}
                requestStatuses={requestStatuses}
                providerLatencies={providerLatencies}
                safeFailures={safeFailures}
                routingDecisions={routingDecisions}
                policyFlags={policyFlags}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="diagnostics" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>Runtime Diagnostics</CardTitle>
                <CardDescription>
                  Live REEVU routing behavior and safe-failure telemetry from the production chat runtime.
                </CardDescription>
              </div>
              <Button variant="outline" onClick={refreshAll}>
                <RefreshCw className="mr-2 h-4 w-4" />Refresh Telemetry
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <RoutingTelemetryContent
                variant="full"
                routingState={routingState}
                activeProvider={telemetryActiveProvider}
                activeModel={telemetryActiveModel}
                activeProviderSourceLabel={chatDiagnostics?.active_provider_source_label || chatHealth?.active_provider_source_label}
                requestStatuses={requestStatuses}
                providerLatencies={providerLatencies}
                safeFailures={safeFailures}
                routingDecisions={routingDecisions}
                policyFlags={policyFlags}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>Providers</CardTitle>
                <CardDescription>Organization-scoped provider credentials, priority, and enablement.</CardDescription>
              </div>
              <ProviderDialog
                title={editingProvider ? "Edit Provider" : "Add Provider"}
                description="Persist a managed provider configuration for REEVU runtime routing."
                form={providerForm}
                setForm={setProviderForm}
                providerPresets={providerPresets}
                onSubmit={() => providerMutation.mutate()}
                submitLabel={editingProvider ? "Save Provider" : "Create Provider"}
                pending={providerMutation.isPending}
                trigger={<Button onClick={openCreateProvider}><Plus className="mr-2 h-4 w-4" />Add Provider</Button>}
                open={providerDialogOpen}
                onOpenChange={open => {
                  setProviderDialogOpen(open);
                  if (!open) {
                    setEditingProvider(null);
                    setProviderForm(providerDefaults());
                  }
                }}
              />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : providers.length === 0 ? (
                <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                  No providers configured yet.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Key</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Flags</TableHead>
                      <TableHead>Updated</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {providers.map(provider => (
                      <TableRow key={provider.id}>
                        <TableCell>
                          <div className="font-medium">{provider.display_name}</div>
                          <div className="text-xs text-muted-foreground">{provider.base_url || "Default endpoint"}</div>
                        </TableCell>
                        <TableCell>{provider.provider_key}</TableCell>
                        <TableCell>{provider.priority}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant={provider.is_enabled ? "default" : "secondary"}>{provider.is_enabled ? "Enabled" : "Disabled"}</Badge>
                            <Badge variant="outline">{provider.auth_mode}</Badge>
                            {provider.has_api_key ? <Badge variant="outline">Key Loaded</Badge> : null}
                            {provider.is_byok_allowed ? <Badge variant="outline">BYOK</Badge> : null}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">{formatTimestamp(provider.updated_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button variant="outline" size="sm" onClick={() => openEditProvider(provider)}>Edit</Button>
                            <Button variant="outline" size="sm" onClick={() => deleteProviderMutation.mutate(provider.id)} disabled={deleteProviderMutation.isPending}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>Models</CardTitle>
                <CardDescription>Per-provider model catalog, defaults, and streaming capability flags.</CardDescription>
              </div>
              <ModelDialog
                title={editingModel ? "Edit Model" : "Add Model"}
                description="Attach model metadata to a provider for org-scoped routing."
                form={modelForm}
                setForm={setModelForm}
                providers={providers}
                providerPresets={providerPresets}
                modelPresetMap={modelPresetMap}
                onSubmit={() => modelMutation.mutate()}
                submitLabel={editingModel ? "Save Model" : "Create Model"}
                pending={modelMutation.isPending}
                trigger={<Button onClick={openCreateModel} disabled={providers.length === 0}><Plus className="mr-2 h-4 w-4" />Add Model</Button>}
                open={modelDialogOpen}
                onOpenChange={open => {
                  setModelDialogOpen(open);
                  if (!open) {
                    setEditingModel(null);
                    setModelForm(modelDefaults());
                  }
                }}
              />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : models.length === 0 ? (
                <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                  No models configured yet.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Provider</TableHead>
                      <TableHead>Capabilities</TableHead>
                      <TableHead>Limits</TableHead>
                      <TableHead>Flags</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {models.map(model => (
                      <TableRow key={model.id}>
                        <TableCell>
                          <div className="font-medium">{model.display_name || model.model_name}</div>
                          <div className="text-xs text-muted-foreground">{model.model_name}</div>
                        </TableCell>
                        <TableCell>{providerLookup[model.provider_id]?.display_name || model.provider_id}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            {(model.capability_tags || []).slice(0, 3).map(tag => (
                              <Badge key={tag} variant="outline">{tag}</Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <div>Tokens: {model.max_tokens ?? "-"}</div>
                            <div className="text-muted-foreground">Temp: {model.temperature ?? "-"}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-2">
                            {model.is_default ? <Badge variant="default">Default</Badge> : null}
                            {model.is_streaming_supported ? <Badge variant="outline">Streaming</Badge> : null}
                            <Badge variant={model.is_active ? "default" : "secondary"}>{model.is_active ? "Active" : "Inactive"}</Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button variant="outline" size="sm" onClick={() => openEditModel(model)}>Edit</Button>
                            <Button variant="outline" size="sm" onClick={() => deleteModelMutation.mutate(model.id)} disabled={deleteModelMutation.isPending}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>REEVU Agents</CardTitle>
                <CardDescription>Agent-level provider/model overrides, prompt customization, and task context defaults.</CardDescription>
              </div>
              <AgentDialog
                title={editingAgent ? "Edit Agent Setting" : "Add Agent Setting"}
                description="Define agent-specific routing and prompt behavior."
                form={agentForm}
                setForm={setAgentForm}
                capabilityCategories={capabilityCategories}
                providers={providers}
                models={models}
                onSubmit={() => agentMutation.mutate()}
                submitLabel={editingAgent ? "Save Agent" : "Create Agent"}
                pending={agentMutation.isPending}
                trigger={<Button onClick={openCreateAgent}><Plus className="mr-2 h-4 w-4" />Add Agent</Button>}
                open={agentDialogOpen}
                onOpenChange={open => {
                  setAgentDialogOpen(open);
                  if (!open) {
                    setEditingAgent(null);
                    setAgentForm(agentDefaults());
                  }
                }}
              />
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : agentSettings.length === 0 ? (
                <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                  No REEVU agent settings configured yet.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Agent</TableHead>
                      <TableHead>Routing</TableHead>
                      <TableHead>Overrides</TableHead>
                      <TableHead>Updated</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agentSettings.map(agent => {
                      const provider = agent.provider_id ? providerLookup[agent.provider_id] : null;
                      const model = agent.provider_model_id ? modelLookup[agent.provider_model_id] : null;
                      return (
                        <TableRow key={agent.id}>
                          <TableCell>
                            <div className="font-medium">{agent.display_name || agent.agent_key}</div>
                            <div className="text-xs text-muted-foreground">{agent.agent_key}</div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              <div>{provider?.display_name || "Routing policy default"}</div>
                              <div className="text-muted-foreground">{model?.display_name || model?.model_name || "Provider default"}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-2">
                              <Badge variant={agent.is_active ? "default" : "secondary"}>{agent.is_active ? "Active" : "Inactive"}</Badge>
                              {agent.capability_overrides?.slice(0, 3).map(capability => (
                                <Badge key={capability} variant="outline">{capability}</Badge>
                              ))}
                              {agent.tool_policy ? <Badge variant="outline">Tool Policy</Badge> : null}
                              {agent.default_task_context ? <Badge variant="outline">Task Context</Badge> : null}
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">{formatTimestamp(agent.updated_at)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button variant="outline" size="sm" onClick={() => openEditAgent(agent)}>Edit</Button>
                              <Button variant="outline" size="sm" onClick={() => deleteAgentMutation.mutate(agent.id)} disabled={deleteAgentMutation.isPending}>
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card className="border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20">
        <CardContent className="pt-4 text-sm text-amber-800 dark:text-amber-300">
          AI output can be incorrect. Treat these settings as operational routing controls, not scientific validation.
        </CardContent>
      </Card>
    </div>
  );
}

export default AISettings;
