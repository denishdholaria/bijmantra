/**
 * AI Settings Page - Cloud AI Setup Wizard
 *
 * REDESIGNED (Jan 2026):
 * - Simplified to Cloud AI only for reliability and agentic capabilities
 * - Guided wizard flow for first-time setup
 * - Clear step indicators with progress
 * - Platform-agnostic (no local installation needed)
 *
 * Supported Cloud AI Providers:
 * - Google Gemini (Free tier available)
 * - Groq (Free tier available, fastest)
 * - OpenAI (Paid only)
 * - Anthropic (Paid only)
 */
import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";

// ============================================
// TYPES
// ============================================

type AIMode = "cloud"; // Simplified to cloud-only
type SetupPath = "cloud" | null;
type WizardStep = "choose" | "provider" | "test" | "complete";

interface CloudProvider {
  id: string;
  name: string;
  icon: string;
  placeholder: string;
  docsUrl: string;
  modelsDocsUrl: string; // Link to official model docs - always up to date
  description: string;
  freeInfo: string;
  defaultModel: string;
  exampleModel: string; // Just an example for the user
}

// ============================================
// CONSTANTS
// ============================================

const CLOUD_PROVIDERS: CloudProvider[] = [
  {
    id: "google",
    name: "Google Gemini",
    icon: "✨",
    placeholder: "AIza...",
    docsUrl: "https://aistudio.google.com/apikey",
    modelsDocsUrl: "https://ai.google.dev/gemini-api/docs/models/gemini",
    description: "Best for beginners",
    freeInfo: "✅ Free: 60 requests/min",
    defaultModel: "gemini-2.5-flash",
    exampleModel: "gemini-3-flash",
  },
  {
    id: "groq",
    name: "Groq",
    icon: "⚡",
    placeholder: "gsk_...",
    docsUrl: "https://console.groq.com/",
    modelsDocsUrl: "https://console.groq.com/docs/models",
    description: "Fastest responses",
    freeInfo: "✅ Free: 30 requests/min",
    defaultModel: "llama-3.3-70b-versatile",
    exampleModel: "llama-4-scout-17b",
  },
  {
    id: "openai",
    name: "OpenAI",
    icon: "🤖",
    placeholder: "sk-...",
    docsUrl: "https://platform.openai.com/api-keys",
    modelsDocsUrl: "https://platform.openai.com/docs/models",
    description: "GPT-5 models",
    freeInfo: "💳 Paid only",
    defaultModel: "gpt-4.1-mini",
    exampleModel: "gpt-5.1-mini",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    icon: "🧠",
    placeholder: "sk-ant-...",
    docsUrl: "https://console.anthropic.com/",
    modelsDocsUrl: "https://docs.anthropic.com/en/docs/about-claude/models",
    description: "Claude 4.5 models",
    freeInfo: "💳 Paid only",
    defaultModel: "claude-sonnet-4-5",
    exampleModel: "claude-opus-4-5",
  },
];

// OLLAMA_MODELS removed - Cloud-only architecture

interface AIConfig {
  mode: AIMode;
  cloud: {
    provider: string;
    apiKey: string;
    model: string;
    tested: boolean;
    lastTestResult?: "success" | "error";
  };
}

const DEFAULT_CONFIG: AIConfig = {
  mode: "cloud",
  cloud: {
    provider: "google",
    apiKey: "",
    model: "gemini-2.5-flash",
    tested: false,
  },
};

const STORAGE_KEY = "bijmantra_ai_config_v2";

// ============================================
// MAIN COMPONENT
// ============================================

export function AISettings() {
  // Config state
  const [config, setConfig] = useState<AIConfig>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch {
      /* ignore */
    }
    return DEFAULT_CONFIG;
  });

  // Wizard state
  const [showWizard, setShowWizard] = useState(false);
  const [setupPath, setSetupPath] = useState<SetupPath>(null);
  const [wizardStep, setWizardStep] = useState<WizardStep>("choose");

  // Testing state
  const [testing, setTesting] = useState<"cloud" | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  const selectedCloudProvider = CLOUD_PROVIDERS.find(
    (p) => p.id === config.cloud.provider
  );

  // Check if already configured (Cloud-Only)
  const isConfigured = config.cloud.lastTestResult === "success";

  // Auto-show wizard if not configured
  useEffect(() => {
    if (!isConfigured && !showWizard) {
      // Small delay to let page render first
      const timer = setTimeout(() => setShowWizard(true), 500);
      return () => clearTimeout(timer);
    }
  }, [isConfigured, showWizard]);

  // Save config
  // Security Note: API keys are stored in localStorage for PWA offline functionality.
  // This is a known trade-off - keys are accessible to JavaScript but required for
  // client-side AI calls. Users are advised to use keys with limited scope/quotas.
  const saveConfig = useCallback((newConfig: AIConfig) => {
    setConfig(newConfig);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newConfig));
    // Backward compatibility
    localStorage.setItem(
      "bijmantra_ai_config",
      JSON.stringify({
        enabled: newConfig.mode === "cloud" && !!newConfig.cloud.apiKey,
        provider: newConfig.cloud.provider,
        apiKey: newConfig.cloud.apiKey,
        model: newConfig.cloud.model,
      })
    );
  }, []);

  // testOllama removed - Cloud-only architecture

  // Test cloud connection
  const testCloud = async () => {
    if (!config.cloud.apiKey) {
      toast.error("Enter an API key first");
      return false;
    }
    setTesting("cloud");
    try {
      const token = apiClient.getToken();
      const response = await fetch("/api/v2/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: 'Say "OK" to confirm.',
          include_context: false,
          preferred_provider: config.cloud.provider,
          user_api_key: config.cloud.apiKey,
          user_model: config.cloud.model || undefined,
        }),
      });
      if (response.ok) {
        const data = await response.json();
        const newConfig = {
          ...config,
          mode: "cloud" as AIMode,
          cloud: {
            ...config.cloud,
            tested: true,
            lastTestResult: "success" as const,
            model: data.model || config.cloud.model,
          },
        };
        saveConfig(newConfig);
        toast.success(`Connected to ${data.provider}!`);
        return true;
      }
      throw new Error("API error");
    } catch {
      const newConfig = {
        ...config,
        cloud: {
          ...config.cloud,
          tested: true,
          lastTestResult: "error" as const,
        },
      };
      saveConfig(newConfig);
      toast.error("Connection failed. Check your API key.");
      return false;
    } finally {
      setTesting(null);
    }
  };

  // Get effective backend status (Cloud-Only)
  const getEffectiveBackend = () => {
    if (config.cloud.lastTestResult === "success") {
      return {
        name: selectedCloudProvider?.name || config.cloud.provider,
        model: config.cloud.model,
        status: "ready" as const,
      };
    }
    return { name: "Not configured", model: "", status: "none" as const };
  };

  const effective = getEffectiveBackend();

  // Reset wizard
  const resetWizard = () => {
    setSetupPath(null);
    setWizardStep("choose");
    setShowWizard(true);
  };

  // Wizard step navigation (Cloud-Only)
  const getWizardSteps = (): { id: WizardStep; label: string }[] => {
    return [
      { id: "choose", label: "Choose" },
      { id: "provider", label: "Provider" },
      { id: "test", label: "API Key" },
      { id: "complete", label: "Done" },
    ];
  };

  const wizardSteps = getWizardSteps();
  const currentStepIndex = wizardSteps.findIndex((s) => s.id === wizardStep);

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">AI Assistant Setup</h1>
          <p className="text-muted-foreground mt-1">
            Connect Veena to an AI model
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={effective.status === "ready" ? "default" : "secondary"}
            className="text-sm px-3 py-1"
          >
            {effective.status === "ready"
              ? `✅ ${effective.name}`
              : "⚠️ Not Connected"}
          </Badge>
          {isConfigured && (
            <Button variant="outline" size="sm" onClick={resetWizard}>
              🔄 Reconfigure
            </Button>
          )}
        </div>
      </div>

      {/* Scientific Disclaimer & Development Status */}
      <Card className="border-amber-200 bg-amber-50 dark:bg-amber-900/20">
        <CardContent className="pt-4">
          <div className="space-y-4">
            {/* Scientific Disclaimer */}
            <div className="flex items-start gap-3">
              <Badge className="bg-amber-600 text-white shrink-0">
                ⚖️ Scientific Disclaimer
              </Badge>
              <div className="space-y-1">
                <p className="text-sm text-amber-900 dark:text-amber-200 leading-relaxed font-medium">
                  AI responses are for assistance only and not a substitute for
                  expert analysis.
                </p>
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                  Veena is an assistant. All breeding data analysis and
                  recommendations must be **independently verified** by a
                  qualified scientist before implementation.
                </p>
              </div>
            </div>

            {/* Under Development Warning */}
            <div className="flex items-start gap-3 pt-3 border-t border-amber-200/60 dark:border-amber-800/60">
              <Badge
                variant="outline"
                className="border-amber-600 text-amber-700 dark:text-amber-400 shrink-0"
              >
                🚧 Under Development
              </Badge>
              <div className="space-y-1">
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                  Veena is currently <strong>evolving</strong>. It does not yet
                  have full access to your live database for real-time analysis.
                  Please use it primarily for general inquiries and drafted
                  assistance.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Setup Wizard */}
      {showWizard && (
        <Card className="border-2 border-primary/20">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">🧙‍♂️ Setup Wizard</CardTitle>
              {isConfigured && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowWizard(false)}
                >
                  ✕
                </Button>
              )}
            </div>
            {/* Progress Steps */}
            <div className="flex items-center gap-1 mt-4">
              {wizardSteps.map((step, i) => (
                <div key={step.id} className="flex items-center">
                  <div
                    className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
                      i < currentStepIndex
                        ? "bg-green-500 text-white"
                        : i === currentStepIndex
                          ? "bg-primary text-white"
                          : "bg-gray-200 text-gray-500"
                    )}
                  >
                    {i < currentStepIndex ? "✓" : i + 1}
                  </div>
                  {i < wizardSteps.length - 1 && (
                    <div
                      className={cn(
                        "w-8 h-1 mx-1",
                        i < currentStepIndex ? "bg-green-500" : "bg-gray-200"
                      )}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-1 mt-1">
              {wizardSteps.map((step, i) => (
                <span
                  key={step.id}
                  className={cn(
                    "text-[10px] w-8 text-center",
                    i === currentStepIndex
                      ? "text-primary font-medium"
                      : "text-muted-foreground"
                  )}
                >
                  {step.label}
                </span>
              ))}
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {/* Step Content */}
            {renderWizardStep()}
          </CardContent>
        </Card>
      )}

      {/* Current Status (when configured) */}
      {isConfigured && !showWizard && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-900/20">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div className="flex-1">
                <p className="font-medium text-green-800 dark:text-green-200">
                  Veena is connected to: {effective.name}
                </p>
                {effective.model && (
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Model: {effective.model}
                  </p>
                )}
              </div>
              <Button variant="outline" onClick={resetWizard}>
                Change
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Reference - Cloud Only */}
      {isConfigured && !showWizard && (
        <div className="grid md:grid-cols-1 gap-4 max-w-md mx-auto">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">☁️ Cloud AI</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                {selectedCloudProvider?.name || "API key required"}
              </p>
              <Badge
                variant={
                  config.cloud.lastTestResult === "success"
                    ? "default"
                    : "secondary"
                }
              >
                {config.cloud.lastTestResult === "success"
                  ? `✓ Connected`
                  : "Not configured"}
              </Badge>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  // ============================================
  // WIZARD STEP RENDERER
  // ============================================

  function renderWizardStep() {
    // Step 1: Choose Path (Cloud-Only - just a welcome)
    if (wizardStep === "choose") {
      return (
        <div className="space-y-4 text-center">
          <div className="text-6xl mb-4">☁️</div>
          <p className="text-muted-foreground">
            Connect Veena to a Cloud AI provider for powerful, agentic capabilities.
          </p>
          <Button
            onClick={() => {
              setSetupPath("cloud");
              setWizardStep("provider");
            }}
            size="lg"
            className="mt-4"
          >
            Get Started →
          </Button>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            <Badge variant="outline" className="text-amber-600 border-amber-300">
              ⚡ Instant
            </Badge>
            <Badge variant="outline" className="text-green-600 border-green-300">
              ✅ Free tiers available
            </Badge>
            <Badge variant="outline" className="text-blue-600 border-blue-300">
              🌐 Works on any device
            </Badge>
          </div>
        </div>
      );
    }

    // ============================================
    // CLOUD PATH: Step 2 - Select Provider
    // ============================================
    if (setupPath === "cloud" && wizardStep === "provider") {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">
              Step 1: Choose a Provider
            </h3>
            <p className="text-muted-foreground">
              Select which AI service you want to use
            </p>
          </div>

          {/* Provider Grid */}
          <div className="grid grid-cols-2 gap-3">
            {CLOUD_PROVIDERS.map((provider) => (
              <button
                key={provider.id}
                onClick={() =>
                  setConfig((prev) => ({
                    ...prev,
                    cloud: {
                      ...prev.cloud,
                      provider: provider.id,
                      model: provider.defaultModel,
                      tested: false,
                      lastTestResult: undefined,
                    },
                  }))
                }
                className={cn(
                  "p-4 rounded-lg border-2 text-left transition-all",
                  config.cloud.provider === provider.id
                    ? "border-primary bg-primary/5"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{provider.icon}</span>
                  <span className="font-medium">{provider.name}</span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  {provider.description}
                </p>
                <Badge
                  variant="outline"
                  className={cn(
                    "text-xs",
                    provider.freeInfo.includes("Free")
                      ? "text-green-600 border-green-300"
                      : "text-gray-600"
                  )}
                >
                  {provider.freeInfo}
                </Badge>
              </button>
            ))}
          </div>

          {/* Selected Provider Info */}
          {selectedCloudProvider && (
            <div className="p-4 bg-muted rounded-lg space-y-3">
              <p className="text-sm font-medium">
                {selectedCloudProvider.icon} {selectedCloudProvider.name}
              </p>
              <p className="text-sm text-muted-foreground">
                {selectedCloudProvider.description}.{" "}
                {selectedCloudProvider.freeInfo}
              </p>
              <a
                href={selectedCloudProvider.docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-primary hover:underline text-sm"
              >
                Get your API key from {selectedCloudProvider.name} →
              </a>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={() => setWizardStep("choose")}>
              ← Back
            </Button>
            <Button onClick={() => setWizardStep("test")}>
              Next: Enter API Key →
            </Button>
          </div>
        </div>
      );
    }

    // ============================================
    // CLOUD PATH: Step 3 - Enter API Key & Test
    // ============================================
    if (setupPath === "cloud" && wizardStep === "test") {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">
              Step 2: Enter Your API Key
            </h3>
            <p className="text-muted-foreground">
              Paste your {selectedCloudProvider?.name} API key below
            </p>
          </div>

          {/* Get API Key Link */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 mb-2">
              <strong>Don't have an API key?</strong> Get one here:
            </p>
            <a
              href={selectedCloudProvider?.docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              🔑 Get {selectedCloudProvider?.name} API Key
            </a>
            {selectedCloudProvider?.id === "google" && (
              <p className="text-xs text-blue-700 mt-2">
                Tip: Sign in with Google, click "Create API Key", copy it.
              </p>
            )}
            {selectedCloudProvider?.id === "groq" && (
              <p className="text-xs text-blue-700 mt-2">
                Tip: Sign up free, go to API Keys, create new key.
              </p>
            )}
          </div>

          {/* API Key Input */}
          <div className="space-y-3">
            <Label>API Key</Label>
            <div className="flex gap-2">
              <Input
                type={showApiKey ? "text" : "password"}
                value={config.cloud.apiKey}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    cloud: {
                      ...prev.cloud,
                      apiKey: e.target.value,
                      tested: false,
                      lastTestResult: undefined,
                    },
                  }))
                }
                placeholder={selectedCloudProvider?.placeholder}
                className="font-mono"
              />
              <Button
                variant="outline"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? "🙈" : "👁️"}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              🔒 Your API key is stored locally in your browser and sent
              directly to {selectedCloudProvider?.name}.
            </p>
          </div>

          {/* Model Selection - Manual Input with Official Docs Link */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Model Identifier</Label>
              <a
                href={selectedCloudProvider?.modelsDocsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary hover:underline flex items-center gap-1 font-medium"
              >
                🌐 Official Models List →
              </a>
            </div>
            <Input
              value={config.cloud.model}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  cloud: { ...prev.cloud, model: e.target.value },
                }))
              }
              placeholder={`e.g., ${selectedCloudProvider?.exampleModel}`}
              className="font-mono text-sm"
            />
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-xs text-blue-800 dark:text-blue-200 leading-relaxed">
                <strong>Pro Tip:</strong> AI providers release new models
                frequently. To use the latest model (like{" "}
                <code>{selectedCloudProvider?.exampleModel}</code>), check their
                documentation and paste the identifier above.
              </p>
            </div>
          </div>

          {/* Test Button */}
          <div className="p-4 border rounded-lg space-y-3">
            <Button
              onClick={async () => {
                const success = await testCloud();
                if (success) {
                  setTimeout(() => setWizardStep("complete"), 500);
                }
              }}
              disabled={testing === "cloud" || !config.cloud.apiKey}
              className="w-full"
            >
              {testing === "cloud" ? "⏳ Testing..." : "🔌 Test Connection"}
            </Button>

            {/* Status */}
            {config.cloud.lastTestResult === "success" && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 font-medium">
                  ✅ Connected to {selectedCloudProvider?.name}!
                </p>
                {config.cloud.model && (
                  <p className="text-sm text-green-700">
                    Model: {config.cloud.model}
                  </p>
                )}
              </div>
            )}

            {config.cloud.lastTestResult === "error" && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg space-y-2">
                <p className="text-red-800 font-medium">❌ Connection failed</p>
                <div className="text-sm text-red-700">
                  <p>
                    <strong>Check:</strong>
                  </p>
                  <ul className="list-disc list-inside">
                    <li>Is the API key correct? (no extra spaces)</li>
                    <li>Does the key have the right permissions?</li>
                    <li>Have you exceeded the rate limit?</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={() => setWizardStep("install")}>
              ← Back
            </Button>
            <Button
              onClick={() => setWizardStep("complete")}
              disabled={config.cloud.lastTestResult !== "success"}
            >
              Complete Setup →
            </Button>
          </div>
        </div>
      );
    }

    // ============================================
    // COMPLETE
    // ============================================
    if (wizardStep === "complete") {
      return (
        <div className="space-y-6 text-center">
          <div className="text-6xl">🎉</div>
          <div>
            <h3 className="text-xl font-semibold mb-2">Setup Complete!</h3>
            <p className="text-muted-foreground">
              Veena is now connected to {selectedCloudProvider?.name}
            </p>
          </div>

          {/* Summary */}
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-left">
            <div className="flex items-center gap-3">
              <span className="text-3xl">☁️</span>
              <div>
                <p className="font-medium text-green-800">
                  Cloud AI: {selectedCloudProvider?.name}
                </p>
                <p className="text-sm text-green-700">
                  Using your API key • {selectedCloudProvider?.freeInfo}
                </p>
              </div>
            </div>
          </div>

          {/* What's Next */}
          <div className="p-4 bg-muted rounded-lg text-left space-y-2">
            <p className="font-medium">What's next?</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Click the 🪷 button to chat with Veena</li>
              <li>• Ask about your breeding programs, trials, or germplasm</li>
              <li>• Veena can help analyze data and suggest recommendations</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-center pt-4">
            <Button variant="outline" onClick={() => setShowWizard(false)}>
              Close
            </Button>
            <Button
              onClick={() => {
                setShowWizard(false);
              }}
            >
              Start Chatting with Veena →
            </Button>
          </div>
        </div>
      );
    }

    return null;
  }
}
