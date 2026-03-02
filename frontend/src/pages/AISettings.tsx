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
import { useState, useMemo } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";

interface ReevuSimpleConfig {
  mode: "managed" | "byok";
  byok: {
    provider: string;
    apiKey: string;
    model: string;
  };
}

const REEVU_STORAGE_KEY = "bijmantra_reevu_config_v1";
const REEVU_LEGACY_KEY = "bijmantra_ai_config_v2";

const REEVU_PROVIDERS = [
  { id: "google", label: "Google Gemini" },
  { id: "groq", label: "Groq" },
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Anthropic" },
];

const REEVU_DEFAULT_CONFIG: ReevuSimpleConfig = {
  mode: "managed",
  byok: {
    provider: "google",
    apiKey: "",
    model: "gemini-2.5-flash",
  },
};

function loadReevuConfig(): ReevuSimpleConfig {
  try {
    const saved = localStorage.getItem(REEVU_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed?.mode === "managed" || parsed?.mode === "byok") {
        return {
          mode: "managed",
          byok: {
            provider: parsed.byok?.provider || "google",
            apiKey: "",
            model: parsed.byok?.model || "gemini-2.5-flash",
          },
        };
      }
    }

    const legacy = localStorage.getItem(REEVU_LEGACY_KEY);
    if (legacy) {
      const parsed = JSON.parse(legacy);
      if (parsed?.cloud) {
        return {
          mode: "managed",
          byok: {
            provider: parsed.cloud.provider || "google",
            apiKey: "",
            model: parsed.cloud.model || "gemini-2.5-flash",
          },
        };
      }
    }
  } catch {
    // Ignore parse errors and use defaults.
  }

  return REEVU_DEFAULT_CONFIG;
}

export function AISettings() {
  const [config, setConfig] = useState<ReevuSimpleConfig>(() => loadReevuConfig());
  const [isTesting, setIsTesting] = useState(false);

  const providerLabel = useMemo(
    () =>
      REEVU_PROVIDERS.find((provider) => provider.id === config.byok.provider)
        ?.label || config.byok.provider,
    [config.byok.provider]
  );

  const saveConfig = (next: ReevuSimpleConfig) => {
    const normalized: ReevuSimpleConfig = {
      ...next,
      mode: "managed",
      byok: {
        ...next.byok,
        apiKey: "",
      },
    };

    setConfig(normalized);
    localStorage.setItem(REEVU_STORAGE_KEY, JSON.stringify(normalized));

    // Compatibility mirror for older code paths that still read this key.
    localStorage.setItem(
      REEVU_LEGACY_KEY,
      JSON.stringify({
        mode: "cloud",
        cloud: {
          provider: next.byok.provider,
          apiKey: "",
          model: next.byok.model,
          tested: true,
          lastTestResult: "success",
        },
      })
    );
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
        toast.error("Backend is reachable, but no AI provider is configured. Add server key or use BYOK.");
        return;
      }

      toast.success(`REEVU connected via ${data.provider || "backend"}`);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        toast.error("Connection timed out");
      } else {
        toast.error("Connection failed. Check backend and credentials.");
      }
    } finally {
      clearTimeout(timeoutId);
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold">REEVU Agent Settings</h1>
        <p className="text-muted-foreground mt-1">
          One clean configuration path. REEVU runs in Managed backend mode only.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Runtime Mode</CardTitle>
          <CardDescription>
            Managed mode uses server-side provider routing. BYOK is disabled to avoid config clashes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button variant="default" onClick={() => saveConfig({ ...config, mode: "managed" })}>
              Managed Backend (Only Mode)
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="default">Managed</Badge>
            <span className="text-sm text-muted-foreground">
              No API key stored in browser. Provider routing is server-managed.
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Connectivity Check</CardTitle>
          <CardDescription>
            Sends a minimal request through the same runtime chat path used in REEVU.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={testConnection} disabled={isTesting}>
            {isTesting ? "Testing…" : "Test REEVU Connection"}
          </Button>
        </CardContent>
      </Card>

      <Card className="border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800">
        <CardContent className="pt-4 text-sm text-amber-800 dark:text-amber-300">
          AI output can be incorrect. Verify recommendations with scientific review before field execution.
        </CardContent>
      </Card>
    </div>
  );
}

export default AISettings;
