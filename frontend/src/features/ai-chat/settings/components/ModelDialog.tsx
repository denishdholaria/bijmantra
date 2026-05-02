import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { RefreshCw, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AIProvider } from "@/lib/api/system/ai-configuration";
import type { ModelPreset } from "@/lib/ai-model-catalog";
import type { OllamaQueryState } from "../ollama-utils";
import type { ModelFormState } from "../types";

interface ModelDialogProps {
  title: string;
  description: string;
  form: ModelFormState;
  setForm: React.Dispatch<React.SetStateAction<ModelFormState>>;
  onSubmit: () => void;
  submitLabel: string;
  pending: boolean;
  trigger?: React.ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  providers: AIProvider[];
  modelPresets: Record<string, ModelPreset[]> | null;
  ollamaModels: string[];
  ollamaQueryState: OllamaQueryState;
  onRefreshOllamaModels: () => Promise<void>;
}

export function ModelDialog({
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
  providers,
  modelPresets,
  ollamaModels,
  ollamaQueryState,
  onRefreshOllamaModels,
}: ModelDialogProps) {
  const selectedProvider = providers.find((provider) => String(provider.id) === form.provider_id);
  const providerKey = selectedProvider?.provider_key;
  const presets = providerKey ? modelPresets?.[providerKey] ?? [] : [];
  const isOllama = providerKey === "ollama";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger ? <DialogTrigger asChild>{trigger}</DialogTrigger> : null}
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <Label>Provider</Label>
            <Select
              value={form.provider_id}
              onValueChange={(value) =>
                setForm((current) => ({ ...current, provider_id: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {providers.map((provider) => (
                  <SelectItem key={provider.id} value={String(provider.id)}>
                    {provider.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Model Name</Label>
            <Input
              value={form.model_name}
              onChange={(event) =>
                setForm((current) => ({ ...current, model_name: event.target.value }))
              }
              placeholder="llama3.2:3b"
            />
          </div>

          <div className="space-y-2">
            <Label>Display Name</Label>
            <Input
              value={form.display_name}
              onChange={(event) =>
                setForm((current) => ({ ...current, display_name: event.target.value }))
              }
              placeholder="Llama 3.2 3B"
            />
          </div>

          <div className="space-y-2">
            <Label>Capability Tags</Label>
            <Input
              value={form.capability_tags}
              onChange={(event) =>
                setForm((current) => ({ ...current, capability_tags: event.target.value }))
              }
              placeholder="chat, reasoning, streaming"
            />
          </div>

          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input
              type="number"
              value={form.max_tokens}
              onChange={(event) =>
                setForm((current) => ({ ...current, max_tokens: event.target.value }))
              }
              placeholder="8192"
            />
          </div>

          <div className="space-y-2">
            <Label>Temperature</Label>
            <Input
              type="number"
              value={form.temperature}
              onChange={(event) =>
                setForm((current) => ({ ...current, temperature: event.target.value }))
              }
              placeholder="0.7"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <Label>Model Settings</Label>
            <Textarea
              value={form.settings}
              onChange={(event) =>
                setForm((current) => ({ ...current, settings: event.target.value }))
              }
              placeholder='{"temperature": 0.7}'
              rows={4}
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <Label>Default Model</Label>
              <p className="text-sm text-muted-foreground">Use this model as the default choice for the provider.</p>
            </div>
            <Switch
              checked={form.is_default}
              onCheckedChange={(checked) =>
                setForm((current) => ({ ...current, is_default: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <Label>Streaming Supported</Label>
              <p className="text-sm text-muted-foreground">
                Enable if this model supports streaming responses.
              </p>
            </div>
            <Switch
              checked={form.is_streaming_supported}
              onCheckedChange={(checked) =>
                setForm((current) => ({ ...current, is_streaming_supported: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3 md:col-span-2">
            <div>
              <Label>Active</Label>
              <p className="text-sm text-muted-foreground">Inactive models are ignored by routing and selection.</p>
            </div>
            <Switch
              checked={form.is_active}
              onCheckedChange={(checked) =>
                setForm((current) => ({ ...current, is_active: checked }))
              }
            />
          </div>

          <div className="md:col-span-2 space-y-4">
            <Card className="border">
              <CardHeader>
                <CardTitle>Provider Presets</CardTitle>
                <CardDescription>
                  Select a preset to populate the model name and metadata after choosing a provider.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedProvider ? (
                  presets.length > 0 ? (
                    <div className="grid gap-2 md:grid-cols-2">
                      {presets.map((preset) => (
                        <Button
                          key={preset.model_name}
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            setForm((current) => ({
                              ...current,
                              model_name: preset.model_name,
                              display_name: preset.display_name,
                              capability_tags: preset.capability_tags,
                              max_tokens: preset.max_tokens,
                              temperature: preset.temperature,
                            }))
                          }
                        >
                          <div className="flex items-center gap-2">
                            <Sparkles className="h-4 w-4" />
                            <span>{preset.display_name}</span>
                          </div>
                        </Button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No presets until a provider is selected.</p>
                  )
                ) : (
                  <p className="text-sm text-muted-foreground">Select a provider to see model presets.</p>
                )}
              </CardContent>
            </Card>

            {isOllama ? (
              <div className="space-y-4">
                {/* Primary section: dynamic models when available, presets when not */}
                <div className="rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium">
                      {ollamaModels.length > 0 ? 'Local Ollama Models' : 'Ollama Model Presets'}
                    </h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void onRefreshOllamaModels()}
                      disabled={ollamaQueryState.isFetching}
                      title="Refresh Ollama models"
                    >
                      <RefreshCw className={cn("h-3.5 w-3.5", ollamaQueryState.isFetching && "animate-spin")} />
                    </Button>
                  </div>

                  {ollamaModels.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {ollamaModels.map((model) => (
                        <Button
                          key={model}
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setForm((prev) => ({
                              ...prev,
                              model_name: model,
                              display_name: prev.display_name || model,
                            }));
                          }}
                          className={cn(
                            form.model_name === model && "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30"
                          )}
                        >
                          {model}
                        </Button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      No models detected. These are fallback defaults — verify your Ollama host is running and has models pulled.
                    </p>
                  )}
                </div>

                {/* Secondary section: fallback presets when dynamic models are primary, or primary presets when no dynamic models */}
                {ollamaModels.length > 0 && presets && presets.length > 0 ? (
                  <div className="rounded-lg border border-dashed p-4">
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Fallback Presets</h4>
                    <div className="flex flex-wrap gap-2">
                      {presets.map((preset) => (
                        <Button
                          key={preset.model_name}
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setForm((prev) => ({
                              ...prev,
                              model_name: preset.model_name,
                              display_name: prev.display_name || preset.display_name,
                              max_tokens: preset.max_tokens,
                              temperature: preset.temperature,
                            }));
                          }}
                          className="text-xs"
                        >
                          {preset.display_name}
                        </Button>
                      ))}
                    </div>
                  </div>
                ) : ollamaModels.length === 0 && presets && presets.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {presets.map((preset) => (
                      <Button
                        key={preset.model_name}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setForm((prev) => ({
                            ...prev,
                            model_name: preset.model_name,
                            display_name: prev.display_name || preset.display_name,
                            max_tokens: preset.max_tokens,
                            temperature: preset.temperature,
                          }));
                        }}
                      >
                        {preset.display_name}
                      </Button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
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
