/**
 * Provider Dialog Component
 * 
 * Dialog for creating and editing AI providers.
 * Extracted from pages/AISettings.tsx as part of Titanium Path hot-file reduction.
 */

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { WandSparkles } from "lucide-react";
import type { ProviderFormState } from "../types";
import type { ProviderPreset } from "@/lib/ai-model-catalog";
import { applyProviderPreset } from "../helpers";

interface ProviderDialogProps {
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
  providerPresets?: ProviderPreset[];
}

export function ProviderDialog({
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
}: ProviderDialogProps) {
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
              Choose a preset first. If REEVU already shows{" "}
              <span className="font-medium text-foreground">Server env key</span>, you do not need to paste
              the same key here again.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {providerPresets.map((preset) => (
                <Button
                  key={preset.provider_key}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setForm((current) => applyProviderPreset(current, preset))}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Cloud providers remain the default and recommended path. Ollama is available as an advanced
              local option and uses a host URL instead of a cloud API key.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Provider Key</Label>
            <Input
              value={form.provider_key}
              onChange={(event) =>
                setForm((current) => ({ ...current, provider_key: event.target.value }))
              }
              placeholder="openai"
            />
          </div>
          <div className="space-y-2">
            <Label>Display Name</Label>
            <Input
              value={form.display_name}
              onChange={(event) =>
                setForm((current) => ({ ...current, display_name: event.target.value }))
              }
              placeholder="OpenAI"
            />
          </div>
          <div className="space-y-2">
            <Label>Auth Mode</Label>
            <Input
              value={form.auth_mode}
              onChange={(event) => setForm((current) => ({ ...current, auth_mode: event.target.value }))}
              placeholder="api_key"
            />
          </div>
          <div className="space-y-2">
            <Label>Priority</Label>
            <Input
              type="number"
              value={form.priority}
              onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Base URL</Label>
            <Input
              value={form.base_url}
              onChange={(event) => setForm((current) => ({ ...current, base_url: event.target.value }))}
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>{isLocalProvider ? "Local Provider Key" : "Server API Key"}</Label>
            <Input
              type="password"
              value={form.encrypted_api_key}
              onChange={(event) =>
                setForm((current) => ({ ...current, encrypted_api_key: event.target.value }))
              }
              placeholder={
                isLocalProvider
                  ? "Leave blank for local Ollama routing"
                  : "Paste only if you want organization-managed routing to use this key"
              }
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
              onChange={(event) => setForm((current) => ({ ...current, settings: event.target.value }))}
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
              onCheckedChange={(checked) => setForm((current) => ({ ...current, is_enabled: checked }))}
            />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>BYOK Allowed</Label>
              <p className="text-sm text-muted-foreground">
                Expose this provider to browser-side bring-your-own-key flows.
              </p>
            </div>
            <Switch
              checked={form.is_byok_allowed}
              onCheckedChange={(checked) =>
                setForm((current) => ({ ...current, is_byok_allowed: checked }))
              }
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={pending}>
            {pending ? "Saving..." : submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
