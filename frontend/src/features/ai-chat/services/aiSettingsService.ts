/**
 * AI Settings Service
 * 
 * Provides API client methods for AI configuration management.
 * Extracted from pages/AISettings.tsx as part of Titanium Path hot-file reduction.
 */

import { apiClient } from "@/lib/api-client";

export const aiSettingsService = {
  // Provider operations
  listProviders: () => apiClient.aiConfigurationService.listProviders(),
  createProvider: (payload: any) => apiClient.aiConfigurationService.createProvider(payload),
  updateProvider: (id: number, payload: any) => apiClient.aiConfigurationService.updateProvider(id, payload),
  deleteProvider: (id: number) => apiClient.aiConfigurationService.deleteProvider(id),

  // Model operations
  listModels: () => apiClient.aiConfigurationService.listModels(),
  createModel: (payload: any) => apiClient.aiConfigurationService.createModel(payload),
  updateModel: (id: number, payload: any) => apiClient.aiConfigurationService.updateModel(id, payload),
  deleteModel: (id: number) => apiClient.aiConfigurationService.deleteModel(id),

  // Agent operations
  listAgentSettings: () => apiClient.aiConfigurationService.listAgentSettings(),
  createAgentSetting: (payload: any) => apiClient.aiConfigurationService.createAgentSetting(payload),
  updateAgentSetting: (id: number, payload: any) => apiClient.aiConfigurationService.updateAgentSetting(id, payload),
  deleteAgentSetting: (id: number) => apiClient.aiConfigurationService.deleteAgentSetting(id),

  // Routing policy operations
  listRoutingPolicies: () => apiClient.aiConfigurationService.listRoutingPolicies(),
  upsertRoutingPolicy: (agentKey: string, payload: any) => apiClient.aiConfigurationService.upsertRoutingPolicy(agentKey, payload),
  deleteRoutingPolicy: (agentKey: string) => apiClient.aiConfigurationService.deleteRoutingPolicy(agentKey),

  // Capabilities and catalog
  listCapabilities: () => apiClient.aiConfigurationService.listCapabilities(),
  listModelCatalog: () => apiClient.aiConfigurationService.listModelCatalog(),
  listOllamaModels: () => apiClient.aiConfigurationService.listOllamaModels(),

  // Health and diagnostics
  getChatHealth: () => apiClient.chatHealthService.getChatHealth(),
  getChatMetrics: () => apiClient.chatHealthService.getChatMetrics(),
  getChatDiagnostics: () => apiClient.chatHealthService.getChatDiagnostics(),
};
