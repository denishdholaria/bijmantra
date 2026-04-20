/**
 * useAISettings Hook
 * 
 * State management and data fetching for AI configuration.
 * Extracted from pages/AISettings.tsx as part of Titanium Path hot-file reduction.
 */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useHydratedSuperuserQueryAccess } from "@/store/auth";
import { aiSettingsService } from "../services/aiSettingsService";
import {
  providerDefaults,
  modelDefaults,
  agentDefaults,
  routingPolicyDefaults,
  buildProviderPayload,
  buildModelPayload,
  buildAgentPayload,
  buildRoutingPolicyPayload,
  extractErrorMessage,
} from "./helpers";
import type { ReevuAgentSetting } from "@/lib/api/system/ai-configuration";
import type { AIProvider, AIProviderModel } from "@/lib/api/system/ai-configuration";
import { PROVIDER_PRESETS, type ProviderPreset, type ModelPreset } from "@/lib/ai-model-catalog";
import {
  normalizeModelLifecycleStrategy,
  normalizeModelLifecycleLabel,
} from "./helpers";
import type { ProviderModelCatalogEntry } from "@/lib/api/system/ai-configuration";
import type { OllamaQueryState } from "./ollama-utils";

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
  return entry.model_presets.map((preset) => {
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

export function useAISettings() {
  const canQueryAISettings = useHydratedSuperuserQueryAccess();
  const queryClient = useQueryClient();

  // Form state
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
  const [isTesting, setIsTesting] = useState(false);

  // Queries
  const providersQuery = useQuery({
    queryKey: ["ai-configuration", "providers"],
    queryFn: () => aiSettingsService.listProviders(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const modelsQuery = useQuery({
    queryKey: ["ai-configuration", "models"],
    queryFn: () => aiSettingsService.listModels(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const agentSettingsQuery = useQuery({
    queryKey: ["ai-configuration", "agent-settings"],
    queryFn: () => aiSettingsService.listAgentSettings(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const routingPoliciesQuery = useQuery({
    queryKey: ["ai-configuration", "routing-policies"],
    queryFn: () => aiSettingsService.listRoutingPolicies(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const capabilitiesQuery = useQuery({
    queryKey: ["ai-configuration", "capabilities"],
    queryFn: () => aiSettingsService.listCapabilities(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const modelCatalogQuery = useQuery({
    queryKey: ["ai-configuration", "model-catalog"],
    queryFn: () => aiSettingsService.listModelCatalog(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const ollamaModelsQuery = useQuery({
    queryKey: ["ai-configuration", "ollama-models"],
    queryFn: () => aiSettingsService.listOllamaModels(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const chatHealthQuery = useQuery({
    queryKey: ["chat-health"],
    queryFn: () => aiSettingsService.getChatHealth(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const chatMetricsQuery = useQuery({
    queryKey: ["chat-metrics"],
    queryFn: () => aiSettingsService.getChatMetrics(),
    enabled: canQueryAISettings,
    retry: false,
  });

  const chatDiagnosticsQuery = useQuery({
    queryKey: ["chat-diagnostics"],
    queryFn: () => aiSettingsService.getChatDiagnostics(),
    enabled: canQueryAISettings,
    retry: false,
  });

  // Data
  const providers = providersQuery.data || [];
  const models = modelsQuery.data || [];
  const agentSettings = agentSettingsQuery.data || [];
  const routingPolicies = routingPoliciesQuery.data || [];
  const capabilityCategories = capabilitiesQuery.data || [];
  const modelCatalog = modelCatalogQuery.data || [];
  const ollamaModels = ollamaModelsQuery.data?.models || [];

  const ollamaQueryState: OllamaQueryState = {
    data: ollamaModelsQuery.data,
    isError: ollamaModelsQuery.isError,
    isLoading: ollamaModelsQuery.isLoading,
    isFetching: ollamaModelsQuery.isFetching,
  };

  const chatHealth = chatHealthQuery.data;
  const chatMetrics = chatMetricsQuery.data;
  const chatDiagnostics = chatDiagnosticsQuery.data;

  const providerPresets = modelCatalog.length ? modelCatalog.map(toProviderPreset) : PROVIDER_PRESETS;
  const modelPresetMap = modelCatalog.length
    ? Object.fromEntries(modelCatalog.map((entry) => [entry.provider_key, toModelPresets(entry)]))
    : null;

  // Computed values
  const modelsByProvider = useMemo(() => {
    return models.reduce<Record<number, AIProviderModel[]>>((acc, model) => {
      acc[model.provider_id] = acc[model.provider_id] || [];
      acc[model.provider_id].push(model);
      return acc;
    }, {});
  }, [models]);

  const providerLookup = useMemo(() => {
    return Object.fromEntries(providers.map((provider) => [provider.id, provider]));
  }, [providers]);

  const modelLookup = useMemo(() => {
    return Object.fromEntries(models.map((model) => [model.id, model]));
  }, [models]);

  const routingPolicy = useMemo(() => {
    return routingPolicies.find((policy) => policy.agent_key === "reevu") || null;
  }, [routingPolicies]);

  const routingPolicyModels = useMemo(() => {
    return routingPolicyForm.preferred_provider_id
      ? models.filter((model) => model.provider_id === Number(routingPolicyForm.preferred_provider_id))
      : models;
  }, [models, routingPolicyForm.preferred_provider_id]);

  // Effects
  useEffect(() => {
    if (providers.length === 0 && activeTab === "routing") {
      setActiveTab("providers");
    }
  }, [activeTab, providers.length]);

  useEffect(() => {
    if (routingPolicy) {
      setRoutingPolicyForm({
        agent_key: routingPolicy.agent_key,
        display_name: routingPolicy.display_name || "",
        preferred_provider_id: routingPolicy.preferred_provider_id
          ? String(routingPolicy.preferred_provider_id)
          : "",
        preferred_provider_model_id: routingPolicy.preferred_provider_model_id
          ? String(routingPolicy.preferred_provider_model_id)
          : "",
        fallback_to_priority_order: routingPolicy.fallback_to_priority_order,
        is_active: routingPolicy.is_active,
      });
      return;
    }

    setRoutingPolicyForm(routingPolicyDefaults());
  }, [routingPolicy]);

  // Refresh all queries
  const refreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "providers"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "models"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "agent-settings"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "routing-policies"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "model-catalog"] }),
      queryClient.invalidateQueries({ queryKey: ["ai-configuration", "ollama-models"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-health"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-metrics"] }),
      queryClient.invalidateQueries({ queryKey: ["chat-diagnostics"] }),
    ]);
  };

  // Targeted Ollama refresh — invalidates only the Ollama models query
  const refreshOllamaModels = async () => {
    await queryClient.invalidateQueries({ queryKey: ["ai-configuration", "ollama-models"] });
  };

  // Mutations
  const providerMutation = useMutation({
    mutationFn: async () => {
      const payload = buildProviderPayload(providerForm);
      if (editingProvider) {
        return aiSettingsService.updateProvider(editingProvider.id, payload);
      }
      return aiSettingsService.createProvider(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setProviderDialogOpen(false);
      setEditingProvider(null);
      setProviderForm(providerDefaults());
      toast.success(editingProvider ? "Provider updated" : "Provider created");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });

  const modelMutation = useMutation({
    mutationFn: async () => {
      const payload = buildModelPayload(modelForm);
      if (editingModel) {
        return aiSettingsService.updateModel(editingModel.id, payload);
      }
      return aiSettingsService.createModel(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setModelDialogOpen(false);
      setEditingModel(null);
      setModelForm(modelDefaults());
      toast.success(editingModel ? "Model updated" : "Model created");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });

  const agentMutation = useMutation({
    mutationFn: async () => {
      const payload = buildAgentPayload(agentForm);
      if (editingAgent) {
        return aiSettingsService.updateAgentSetting(editingAgent.id, payload);
      }
      return aiSettingsService.createAgentSetting(payload);
    },
    onSuccess: async () => {
      await refreshAll();
      setAgentDialogOpen(false);
      setEditingAgent(null);
      setAgentForm(agentDefaults());
      toast.success(editingAgent ? "Agent setting updated" : "Agent setting created");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });

  const deleteProviderMutation = useMutation({
    mutationFn: (providerId: number) => aiSettingsService.deleteProvider(providerId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Provider deleted");
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  const deleteModelMutation = useMutation({
    mutationFn: (modelId: number) => aiSettingsService.deleteModel(modelId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Model deleted");
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  const deleteAgentMutation = useMutation({
    mutationFn: (settingId: number) => aiSettingsService.deleteAgentSetting(settingId),
    onSuccess: async () => {
      await refreshAll();
      toast.success("Agent setting deleted");
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  const routingPolicyMutation = useMutation({
    mutationFn: () => {
      const payload = buildRoutingPolicyPayload(routingPolicyForm);
      return aiSettingsService.upsertRoutingPolicy(payload.agent_key, payload);
    },
    onSuccess: async () => {
      await refreshAll();
      toast.success(routingPolicy ? "Routing policy updated" : "Routing policy saved");
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error));
    },
  });

  const deleteRoutingPolicyMutation = useMutation({
    mutationFn: (agentKey: string) => aiSettingsService.deleteRoutingPolicy(agentKey),
    onSuccess: async () => {
      await refreshAll();
      setRoutingPolicyForm(routingPolicyDefaults());
      toast.success("Routing policy cleared");
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  });

  // Test connection
  const testConnection = async () => {
    setIsTesting(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const { apiClient } = await import("@/lib/api-client");
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

  // Dialog handlers
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
      default_task_context: agent.default_task_context
        ? JSON.stringify(agent.default_task_context, null, 2)
        : "",
      sampling_temperature: agent.sampling_temperature !== null ? String(agent.sampling_temperature) : "",
      max_tokens: agent.max_tokens !== null ? String(agent.max_tokens) : "",
      capability_overrides: agent.capability_overrides?.join(", ") || "",
      is_active: agent.is_active,
    });
    setAgentDialogOpen(true);
  };

  const loading =
    providersQuery.isLoading ||
    modelsQuery.isLoading ||
    agentSettingsQuery.isLoading ||
    routingPoliciesQuery.isLoading ||
    modelCatalogQuery.isLoading ||
    ollamaModelsQuery.isLoading;

  return {
    // State
    providerForm,
    setProviderForm,
    editingProvider,
    providerDialogOpen,
    setProviderDialogOpen,
    modelForm,
    setModelForm,
    editingModel,
    modelDialogOpen,
    setModelDialogOpen,
    agentForm,
    setAgentForm,
    editingAgent,
    agentDialogOpen,
    setAgentDialogOpen,
    routingPolicyForm,
    setRoutingPolicyForm,
    activeTab,
    setActiveTab,
    isTesting,

    // Data
    providers,
    models,
    agentSettings,
    routingPolicies,
    capabilityCategories,
    modelCatalog,
    chatHealth,
    chatMetrics,
    chatDiagnostics,
    providerPresets,
    modelPresetMap,
    modelsByProvider,
    providerLookup,
    modelLookup,
    routingPolicy,
    routingPolicyModels,
    ollamaModels,
    ollamaQueryState,
    loading,

    // Actions
    refreshAll,
    refreshOllamaModels,
    testConnection,
    openCreateProvider,
    openEditProvider,
    openCreateModel,
    openEditModel,
    openCreateAgent,
    openEditAgent,

    // Mutations
    providerMutation,
    modelMutation,
    agentMutation,
    deleteProviderMutation,
    deleteModelMutation,
    deleteAgentMutation,
    routingPolicyMutation,
    deleteRoutingPolicyMutation,
  };
}
