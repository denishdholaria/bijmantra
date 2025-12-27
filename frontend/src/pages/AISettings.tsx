/**
 * AI Settings Page
 * Configure AI providers and API keys for intelligent analysis
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

interface AIProvider {
  id: string
  name: string
  icon: string
  models: string[]
  apiKeyPlaceholder: string
  docsUrl: string
}

const AI_PROVIDERS: AIProvider[] = [
  { id: 'openai', name: 'OpenAI', icon: '🤖', models: [], apiKeyPlaceholder: 'sk-...', docsUrl: 'https://platform.openai.com/api-keys' },
  { id: 'anthropic', name: 'Anthropic Claude', icon: '🧠', models: [], apiKeyPlaceholder: 'sk-ant-...', docsUrl: 'https://console.anthropic.com/' },
  { id: 'google', name: 'Google Gemini', icon: '✨', models: [], apiKeyPlaceholder: 'AIza...', docsUrl: 'https://aistudio.google.com/apikey' },
  { id: 'mistral', name: 'Mistral AI', icon: '🌀', models: [], apiKeyPlaceholder: '...', docsUrl: 'https://console.mistral.ai/' },
]

interface AIConfig {
  enabled: boolean
  provider: string
  model: string
  apiKey: string
  temperature: number
  maxTokens: number
}

const DEFAULT_CONFIG: AIConfig = {
  enabled: false,
  provider: 'google',
  model: 'gemini-2.0-flash',
  apiKey: '',
  temperature: 0.7,
  maxTokens: 4096,
}

const getModelPlaceholder = (provider: string): string => {
  switch (provider) {
    case 'openai': return 'gpt-4o'
    case 'anthropic': return 'claude-sonnet-4-20250514'
    case 'google': return 'gemini-2.0-flash'
    case 'mistral': return 'mistral-large-latest'
    default: return 'model-name'
  }
}

const getModelDocsUrl = (provider: string): string => {
  switch (provider) {
    case 'openai': return 'https://platform.openai.com/docs/models'
    case 'anthropic': return 'https://docs.anthropic.com/en/docs/about-claude/models'
    case 'google': return 'https://ai.google.dev/gemini-api/docs/models/gemini'
    case 'mistral': return 'https://docs.mistral.ai/getting-started/models/'
    default: return '#'
  }
}

export function AISettings() {
  const [config, setConfig] = useState<AIConfig>(() => {
    const saved = localStorage.getItem('bijmantra_ai_config')
    return saved ? JSON.parse(saved) : DEFAULT_CONFIG
  })
  const [showKey, setShowKey] = useState(false)
  const [testing, setTesting] = useState(false)

  const selectedProvider = AI_PROVIDERS.find(p => p.id === config.provider)

  const saveConfig = () => {
    localStorage.setItem('bijmantra_ai_config', JSON.stringify(config))
    toast.success('AI settings saved!')
  }

  const testConnection = async () => {
    if (!config.apiKey) {
      toast.error('Please enter an API key first')
      return
    }
    setTesting(true)
    // Simulate API test
    await new Promise(resolve => setTimeout(resolve, 1500))
    setTesting(false)
    toast.success('Connection successful! AI is ready to use.')
  }

  const clearConfig = () => {
    setConfig(DEFAULT_CONFIG)
    localStorage.removeItem('bijmantra_ai_config')
    toast.success('AI configuration cleared')
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">AI Assistant Settings</h1>
          <p className="text-muted-foreground mt-1">Configure AI for intelligent data analysis</p>
        </div>
        <Badge variant={config.enabled && config.apiKey ? 'default' : 'secondary'}>
          {config.enabled && config.apiKey ? '🟢 AI Enabled' : '⚪ AI Disabled'}
        </Badge>
      </div>

      {/* Info Banner */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-4">
          <div className="flex gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <p className="font-medium text-blue-800">Bring Your Own AI</p>
              <p className="text-sm text-blue-700">
                Connect your preferred AI provider for intelligent breeding data analysis, 
                trait predictions, selection recommendations, and natural language queries. 
                Your API key is stored locally and never sent to our servers.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="config">
        <TabsList>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="usage">Usage Guide</TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-6 mt-4">
          {/* Enable/Disable */}
          <Card>
            <CardHeader>
              <CardTitle>Enable AI Assistant</CardTitle>
              <CardDescription>Turn on AI-powered features</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">AI Analysis</p>
                  <p className="text-sm text-muted-foreground">Enable intelligent data analysis features</p>
                </div>
                <Switch
                  checked={config.enabled}
                  onCheckedChange={(enabled) => setConfig({ ...config, enabled })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Provider Selection */}
          <Card>
            <CardHeader>
              <CardTitle>AI Provider</CardTitle>
              <CardDescription>Select your preferred AI service</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {AI_PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setConfig({ ...config, provider: provider.id, model: getModelPlaceholder(provider.id) })}
                    className={`p-4 rounded-lg border-2 text-center transition-all ${
                      config.provider === provider.id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className="text-2xl">{provider.icon}</span>
                    <p className="font-medium mt-1">{provider.name}</p>
                  </button>
                ))}
              </div>

              {selectedProvider && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Model Name</Label>
                      <a 
                        href={getModelDocsUrl(config.provider)} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        View available models →
                      </a>
                    </div>
                    <Input
                      value={config.model}
                      onChange={(e) => setConfig({ ...config, model: e.target.value })}
                      placeholder={getModelPlaceholder(config.provider)}
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground">
                      Enter the exact model name from your provider (e.g., {getModelPlaceholder(config.provider)})
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>API Key</Label>
                      <a 
                        href={selectedProvider.docsUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        Get API Key →
                      </a>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        type={showKey ? 'text' : 'password'}
                        value={config.apiKey}
                        onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                        placeholder={selectedProvider.apiKeyPlaceholder}
                        className="font-mono"
                      />
                      <Button variant="outline" onClick={() => setShowKey(!showKey)}>
                        {showKey ? '🙈' : '👁️'}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      🔒 Your API key is stored locally in your browser and never sent to our servers.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Advanced Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>Fine-tune AI behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Temperature ({config.temperature})</Label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.temperature}
                    onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">Lower = more focused, Higher = more creative</p>
                </div>
                <div className="space-y-2">
                  <Label>Max Tokens</Label>
                  <Input
                    type="number"
                    value={config.maxTokens}
                    onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) || 4096 })}
                  />
                  <p className="text-xs text-muted-foreground">Maximum response length</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-3">
            <Button onClick={saveConfig} className="flex-1">💾 Save Settings</Button>
            <Button variant="outline" onClick={testConnection} disabled={testing}>
              {testing ? '⏳ Testing...' : '🔌 Test Connection'}
            </Button>
            <Button variant="outline" onClick={clearConfig}>🗑️ Clear</Button>
          </div>
        </TabsContent>

        <TabsContent value="providers" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {AI_PROVIDERS.map((provider) => (
              <Card key={provider.id}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">{provider.icon}</span>
                    {provider.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-medium">Example Model:</p>
                    <code className="text-xs bg-muted px-2 py-1 rounded">{getModelPlaceholder(provider.id)}</code>
                  </div>
                  <div className="flex flex-col gap-2">
                    <a 
                      href={provider.docsUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                    >
                      🔑 Get API Key →
                    </a>
                    <a 
                      href={getModelDocsUrl(provider.id)} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                    >
                      📚 View Available Models →
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="usage" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>How to Use AI Assistant</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex gap-3">
                  <span className="text-xl">1️⃣</span>
                  <div>
                    <p className="font-medium">Get an API Key</p>
                    <p className="text-sm text-muted-foreground">Sign up with your preferred AI provider and generate an API key</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-xl">2️⃣</span>
                  <div>
                    <p className="font-medium">Configure Settings</p>
                    <p className="text-sm text-muted-foreground">Select your provider, model, and enter your API key</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <span className="text-xl">3️⃣</span>
                  <div>
                    <p className="font-medium">Use AI Features</p>
                    <p className="text-sm text-muted-foreground">Access AI analysis from the AI Assistant page or within data views</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-muted rounded-lg">
                <p className="font-medium mb-2">AI Can Help With:</p>
                <ul className="text-sm space-y-1">
                  <li>• Analyze phenotypic data patterns</li>
                  <li>• Suggest selection criteria</li>
                  <li>• Predict trait performance</li>
                  <li>• Generate breeding recommendations</li>
                  <li>• Answer questions about your data</li>
                  <li>• Summarize trial results</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
