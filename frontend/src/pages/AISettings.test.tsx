import { fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AISettings } from './AISettings';
import { apiClient } from '@/lib/api-client';
import { useHydratedSuperuserQueryAccess } from '@/store/auth';

vi.mock('@/store/auth', () => ({
  useHydratedSuperuserQueryAccess: vi.fn(),
}));

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    aiConfigurationService: {
      listProviders: vi.fn(),
      listModels: vi.fn(),
      listAgentSettings: vi.fn(),
      listRoutingPolicies: vi.fn(),
      listCapabilities: vi.fn(),
      listModelCatalog: vi.fn(),
      listOllamaModels: vi.fn(),
      createProvider: vi.fn(),
      updateProvider: vi.fn(),
      deleteProvider: vi.fn(),
      createModel: vi.fn(),
      updateModel: vi.fn(),
      deleteModel: vi.fn(),
      createAgentSetting: vi.fn(),
      updateAgentSetting: vi.fn(),
      deleteAgentSetting: vi.fn(),
      upsertRoutingPolicy: vi.fn(),
      deleteRoutingPolicy: vi.fn(),
    },
    chatHealthService: {
      getChatHealth: vi.fn(),
      getChatMetrics: vi.fn(),
      getChatDiagnostics: vi.fn(),
    },
  },
}));

describe('AISettings', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    vi.clearAllMocks();
    vi.mocked(useHydratedSuperuserQueryAccess).mockReturnValue(true);

    class MockResizeObserver {
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    }

    global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

    Element.prototype.setPointerCapture = vi.fn();
    Element.prototype.releasePointerCapture = vi.fn();
    Element.prototype.hasPointerCapture = vi.fn();
    Element.prototype.scrollIntoView = vi.fn();

    if (!global.PointerEvent) {
      class MockPointerEvent extends MouseEvent {
        constructor(type: string, props: PointerEventInit = {}) {
          super(type, props);
        }
      }
      global.PointerEvent = MockPointerEvent as unknown as typeof PointerEvent;
    }

    vi.mocked(apiClient.aiConfigurationService.listProviders).mockResolvedValue([]);
    vi.mocked(apiClient.aiConfigurationService.listModels).mockResolvedValue([]);
    vi.mocked(apiClient.aiConfigurationService.listAgentSettings).mockResolvedValue([]);
    vi.mocked(apiClient.aiConfigurationService.listRoutingPolicies).mockResolvedValue([]);
    vi.mocked(apiClient.aiConfigurationService.listCapabilities).mockResolvedValue([]);
    vi.mocked(apiClient.aiConfigurationService.listOllamaModels).mockResolvedValue({ models: [] });
    vi.mocked(apiClient.aiConfigurationService.listModelCatalog).mockResolvedValue([
      {
        provider_key: 'google',
        provider_label: 'Google Gemini',
        provider_display_name: 'Google Gemini Managed',
        base_url: 'https://example.invalid/gemini',
        default_priority: 21,
        recommended_model: 'gemini-flash-latest',
        model_lifecycle: 'provider_alias_latest',
        model_lifecycle_label: 'Provider latest alias',
        provider_preset_label: 'Google Gemini Managed',
        model_presets: [
          {
            label: 'Gemini Flash Managed',
            model_name: 'gemini-flash-latest',
            display_name: 'Gemini Flash Managed',
            capability_tags: ['chat', 'reasoning', 'streaming'],
            max_tokens: 8192,
            temperature: 0.7,
            lifecycle: 'provider_alias_latest',
            lifecycle_label: 'Provider latest alias',
          },
        ],
      },
    ]);
    vi.mocked(apiClient.chatHealthService.getChatHealth).mockResolvedValue({
      status: 'healthy',
      assistant: 'REEVU',
      active_provider: 'google',
      active_model: 'gemini-flash-latest',
      active_provider_source: 'server_env',
      active_provider_source_label: 'Server env key',
      capabilities: ['chat'],
      rag_enabled: false,
      llm_enabled: true,
      free_tier_available: true,
    });
    vi.mocked(apiClient.chatHealthService.getChatMetrics).mockResolvedValue({
      uptime_seconds: 60,
      total_requests: 1,
      requests: [],
      policy_flags: [],
      latency: {
        total: {
          count: 1,
          min: 0.1,
          max: 0.2,
          mean: 0.15,
          p50: 0.1,
          p95: 0.2,
          p99: 0.2,
        },
      },
    });
    vi.mocked(apiClient.chatHealthService.getChatDiagnostics).mockResolvedValue({
      assistant: 'REEVU',
      active_provider: 'google',
      active_model: 'gemini-flash-latest',
      active_provider_source: 'server_env',
      active_provider_source_label: 'Server env key',
      uptime_seconds: 60,
      total_requests: 1,
      providers: [],
      request_statuses: [],
      provider_latencies: [],
      safe_failures: [],
      routing_decisions: [],
      policy_flags: [],
      routing_state: {
        selection_mode: 'priority_order',
        preferred_provider: null,
        preferred_provider_only: false,
      },
    });
  });

  it('prefers backend model catalog presets in the provider quick-start dialog', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AISettings />
      </QueryClientProvider>,
    );

    const addProviderButtons = await screen.findAllByRole('button', { name: /add provider/i });
    fireEvent.click(addProviderButtons[0]);

    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Google Gemini Managed')).toBeInTheDocument();
    expect(within(dialog).queryByText(/^Google Gemini$/)).not.toBeInTheDocument();
  });

  it('falls back to built-in model presets when the backend model catalog is empty', async () => {
    vi.mocked(apiClient.aiConfigurationService.listProviders).mockResolvedValue([
      {
        id: 1,
        organization_id: 1,
        provider_key: 'openai',
        display_name: 'OpenAI',
        base_url: 'https://api.openai.com/v1',
        auth_mode: 'api_key',
        priority: 40,
        is_enabled: true,
        is_byok_allowed: true,
        settings: null,
        has_api_key: false,
        created_at: '2026-03-12T00:00:00.000Z',
        updated_at: '2026-03-12T00:00:00.000Z',
      },
    ]);
    vi.mocked(apiClient.aiConfigurationService.listModelCatalog).mockResolvedValue([]);

    render(
      <QueryClientProvider client={queryClient}>
        <AISettings />
      </QueryClientProvider>,
    );

    const addProviderButtons = await screen.findAllByRole('button', { name: /add provider/i });
    fireEvent.click(addProviderButtons[0]);

    expect(await screen.findByText('FunctionGemma')).toBeInTheDocument();
    expect(screen.getByText('HuggingFace')).toBeInTheDocument();
    expect(screen.getByText('Ollama (Local, Advanced)')).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });

    const modelsTab = await screen.findByRole('tab', { name: /models/i });
    fireEvent.mouseDown(modelsTab);
    fireEvent.click(modelsTab);

    await screen.findByText('Per-provider model catalog, defaults, and streaming capability flags.');

    const addModelButton = await screen.findByRole('button', { name: /add model/i });
    fireEvent.click(addModelButton);

    const providerTrigger = await screen.findByRole('combobox');
    fireEvent.mouseDown(providerTrigger);
    fireEvent.pointerDown(providerTrigger);
    fireEvent.click(providerTrigger);
    fireEvent.click(await screen.findByRole('option', { name: 'OpenAI' }));

    expect(await screen.findByText('GPT-4.1 Mini')).toBeInTheDocument();
    expect(screen.queryByText('No presets until a provider is selected.')).not.toBeInTheDocument();
  });

  it('surfaces ollama as a local advanced preset when the backend catalog includes it', async () => {
    vi.mocked(apiClient.aiConfigurationService.listModelCatalog).mockResolvedValue([
      {
        provider_key: 'ollama',
        provider_label: 'Ollama (Local)',
        provider_display_name: 'Ollama (Local)',
        base_url: 'http://localhost:11434',
        default_priority: 70,
        recommended_model: 'llama3.2:3b',
        model_lifecycle: 'managed_named_model',
        model_lifecycle_label: 'Local named model',
        provider_preset_label: 'Ollama (Local, Advanced)',
        model_presets: [
          {
            label: 'Llama 3.2 3B',
            model_name: 'llama3.2:3b',
            display_name: 'Llama 3.2 3B',
            capability_tags: ['chat', 'reasoning', 'streaming'],
            max_tokens: 8192,
            temperature: 0.7,
            lifecycle: 'managed_named_model',
            lifecycle_label: 'Local named model',
          },
        ],
      },
    ]);

    render(
      <QueryClientProvider client={queryClient}>
        <AISettings />
      </QueryClientProvider>,
    );

    const addProviderButtons = await screen.findAllByRole('button', { name: /add provider/i });
    fireEvent.click(addProviderButtons[0]);

    expect(await screen.findByText('Ollama (Local, Advanced)')).toBeInTheDocument();
    expect(screen.getByText('Cloud providers remain the default and recommended path. Ollama is available as an advanced local option and uses a host URL instead of a cloud API key.')).toBeInTheDocument();
  });

  it('uses the human-readable runtime provider label instead of the raw provider slug', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AISettings />
      </QueryClientProvider>,
    );

    const providerLabels = await screen.findAllByText('Google Gemini');
    expect(providerLabels.length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText(/^google$/)).not.toBeInTheDocument();
  });

  it('falls back per provider when the backend catalog only covers a subset of providers', async () => {
    vi.mocked(apiClient.aiConfigurationService.listProviders).mockResolvedValue([
      {
        id: 1,
        organization_id: 1,
        provider_key: 'openai',
        display_name: 'OpenAI',
        base_url: 'https://api.openai.com/v1',
        auth_mode: 'api_key',
        priority: 40,
        is_enabled: true,
        is_byok_allowed: true,
        settings: null,
        has_api_key: false,
        created_at: '2026-03-12T00:00:00.000Z',
        updated_at: '2026-03-12T00:00:00.000Z',
      },
    ]);
    vi.mocked(apiClient.aiConfigurationService.listModelCatalog).mockResolvedValue([
      {
        provider_key: 'google',
        provider_label: 'Google Gemini',
        provider_display_name: 'Google Gemini Managed',
        base_url: 'https://example.invalid/gemini',
        default_priority: 21,
        recommended_model: 'gemini-flash-latest',
        model_lifecycle: 'provider_alias_latest',
        model_lifecycle_label: 'Provider latest alias',
        provider_preset_label: 'Google Gemini Managed',
        model_presets: [
          {
            label: 'Gemini Flash Managed',
            model_name: 'gemini-flash-latest',
            display_name: 'Gemini Flash Managed',
            capability_tags: ['chat', 'reasoning', 'streaming'],
            max_tokens: 8192,
            temperature: 0.7,
            lifecycle: 'provider_alias_latest',
            lifecycle_label: 'Provider latest alias',
          },
        ],
      },
    ]);

    render(
      <QueryClientProvider client={queryClient}>
        <AISettings />
      </QueryClientProvider>,
    );

    const modelsTab = await screen.findByRole('tab', { name: /models/i });
    fireEvent.mouseDown(modelsTab);
    fireEvent.click(modelsTab);

    await screen.findByText('Per-provider model catalog, defaults, and streaming capability flags.');

    const addModelButton = await screen.findByRole('button', { name: /add model/i });
    fireEvent.click(addModelButton);

    const providerTrigger = await screen.findByRole('combobox');
    fireEvent.mouseDown(providerTrigger);
    fireEvent.pointerDown(providerTrigger);
    fireEvent.click(providerTrigger);
    fireEvent.click(await screen.findByRole('option', { name: 'OpenAI' }));

    expect(await screen.findByText('GPT-4.1 Mini')).toBeInTheDocument();
    expect(screen.queryByText('Gemini Flash Managed')).not.toBeInTheDocument();
  });
});
