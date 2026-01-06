/**
 * AI Settings Page - Step-by-Step Setup Wizard
 * 
 * REDESIGNED (Dec 31, 2025):
 * - Guided wizard flow for first-time setup
 * - Clear step indicators with progress
 * - Platform-specific installation instructions
 * - Troubleshooting help at each step
 * 
 * Three AI Backend Modes:
 * 1. Local AI (Ollama) - Free, private, offline
 * 2. Cloud AI (API Key) - Google, OpenAI, Anthropic, Groq
 * 3. Auto - Uses best available
 */
import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

// ============================================
// TYPES
// ============================================

type AIMode = 'auto' | 'local' | 'cloud'
type SetupPath = 'local' | 'cloud' | null
type WizardStep = 'choose' | 'install' | 'model' | 'test' | 'complete'

interface CloudProvider {
  id: string
  name: string
  icon: string
  placeholder: string
  docsUrl: string
  description: string
  freeInfo: string
}

interface AIConfig {
  mode: AIMode
  local: {
    host: string
    model: string
    tested: boolean
    lastTestResult?: 'success' | 'error'
  }
  cloud: {
    provider: string
    apiKey: string
    model: string
    tested: boolean
    lastTestResult?: 'success' | 'error'
  }
}

// ============================================
// CONSTANTS
// ============================================

const CLOUD_PROVIDERS: CloudProvider[] = [
  { 
    id: 'google', 
    name: 'Google Gemini', 
    icon: '✨', 
    placeholder: 'AIza...', 
    docsUrl: 'https://aistudio.google.com/apikey',
    description: 'Best for beginners',
    freeInfo: '✅ Free: 60 requests/min'
  },
  { 
    id: 'groq', 
    name: 'Groq', 
    icon: '⚡', 
    placeholder: 'gsk_...', 
    docsUrl: 'https://console.groq.com/',
    description: 'Fastest responses',
    freeInfo: '✅ Free: 30 requests/min'
  },
  { 
    id: 'openai', 
    name: 'OpenAI', 
    icon: '🤖', 
    placeholder: 'sk-...', 
    docsUrl: 'https://platform.openai.com/api-keys',
    description: 'GPT-4o models',
    freeInfo: '💳 Paid only'
  },
  { 
    id: 'anthropic', 
    name: 'Anthropic', 
    icon: '🧠', 
    placeholder: 'sk-ant-...', 
    docsUrl: 'https://console.anthropic.com/',
    description: 'Claude models',
    freeInfo: '💳 Paid only'
  },
]

const OLLAMA_MODELS = [
  { id: 'llama3.2:3b', name: 'Llama 3.2 (3B)', size: '2GB', desc: 'Fast, good for most tasks' },
  { id: 'llama3.2:1b', name: 'Llama 3.2 (1B)', size: '1.3GB', desc: 'Fastest, lighter tasks' },
  { id: 'mistral', name: 'Mistral 7B', size: '4GB', desc: 'Balanced performance' },
  { id: 'gemma2:2b', name: 'Gemma 2 (2B)', size: '1.6GB', desc: 'Google\'s efficient model' },
  { id: 'phi3', name: 'Phi-3 Mini', size: '2.3GB', desc: 'Microsoft\'s compact model' },
]

const DEFAULT_CONFIG: AIConfig = {
  mode: 'auto',
  local: { host: 'http://localhost:11434', model: '', tested: false },
  cloud: { provider: 'google', apiKey: '', model: '', tested: false }
}

const STORAGE_KEY = 'bijmantra_ai_config_v2'

// Detect OS for installation instructions
const getOS = (): 'mac' | 'windows' | 'linux' => {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('mac')) return 'mac'
  if (ua.includes('win')) return 'windows'
  return 'linux'
}

// ============================================
// MAIN COMPONENT
// ============================================

export function AISettings() {
  // Config state
  const [config, setConfig] = useState<AIConfig>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) return JSON.parse(saved)
    } catch { /* ignore */ }
    return DEFAULT_CONFIG
  })

  // Wizard state
  const [showWizard, setShowWizard] = useState(false)
  const [setupPath, setSetupPath] = useState<SetupPath>(null)
  const [wizardStep, setWizardStep] = useState<WizardStep>('choose')
  const [selectedModel, setSelectedModel] = useState('llama3.2:3b')
  
  // Testing state
  const [testing, setTesting] = useState<'local' | 'cloud' | null>(null)
  const [ollamaModels, setOllamaModels] = useState<string[]>([])
  const [showApiKey, setShowApiKey] = useState(false)
  const [serverOllamaAvailable, setServerOllamaAvailable] = useState(false)

  const os = getOS()
  const selectedCloudProvider = CLOUD_PROVIDERS.find(p => p.id === config.cloud.provider)

  // Check if already configured
  const isConfigured = config.local.lastTestResult === 'success' || 
                       config.cloud.lastTestResult === 'success' ||
                       serverOllamaAvailable

  // Check server status on mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const token = apiClient.getToken()
        const response = await fetch('/api/v2/chat/status', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        })
        if (response.ok) {
          const data = await response.json()
          setServerOllamaAvailable(data.providers?.ollama?.available || false)
        }
      } catch { /* ignore */ }
    }
    checkServer()
  }, [])

  // Auto-show wizard if not configured
  useEffect(() => {
    if (!isConfigured && !showWizard) {
      // Small delay to let page render first
      const timer = setTimeout(() => setShowWizard(true), 500)
      return () => clearTimeout(timer)
    }
  }, [isConfigured, showWizard])

  // Save config
  const saveConfig = useCallback((newConfig: AIConfig) => {
    setConfig(newConfig)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newConfig))
    // Backward compatibility
    localStorage.setItem('bijmantra_ai_config', JSON.stringify({
      enabled: newConfig.mode !== 'auto' || newConfig.cloud.apiKey,
      provider: newConfig.cloud.provider,
      apiKey: newConfig.cloud.apiKey,
      model: newConfig.cloud.model
    }))
  }, [])

  // Test Ollama connection
  const testOllama = async () => {
    setTesting('local')
    try {
      const response = await fetch(`${config.local.host}/api/tags`)
      if (response.ok) {
        const data = await response.json()
        const models = data.models?.map((m: any) => m.name) || []
        setOllamaModels(models)
        
        if (models.length > 0) {
          const newConfig = {
            ...config,
            mode: 'local' as AIMode,
            local: { ...config.local, model: models[0], tested: true, lastTestResult: 'success' as const }
          }
          saveConfig(newConfig)
          toast.success(`Connected! Found ${models.length} model(s)`)
          return true
        } else {
          toast.warning('Ollama running but no models. Continue to download one.')
          return false
        }
      }
      throw new Error('Not responding')
    } catch {
      const newConfig = {
        ...config,
        local: { ...config.local, tested: true, lastTestResult: 'error' as const }
      }
      saveConfig(newConfig)
      toast.error('Cannot connect to Ollama')
      return false
    } finally {
      setTesting(null)
    }
  }

  // Test cloud connection
  const testCloud = async () => {
    if (!config.cloud.apiKey) {
      toast.error('Enter an API key first')
      return false
    }
    setTesting('cloud')
    try {
      const token = apiClient.getToken()
      const response = await fetch('/api/v2/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          message: 'Say "OK" to confirm.',
          include_context: false,
          preferred_provider: config.cloud.provider,
          user_api_key: config.cloud.apiKey,
          user_model: config.cloud.model || undefined
        })
      })
      if (response.ok) {
        const data = await response.json()
        const newConfig = {
          ...config,
          mode: 'cloud' as AIMode,
          cloud: { ...config.cloud, tested: true, lastTestResult: 'success' as const, model: data.model || config.cloud.model }
        }
        saveConfig(newConfig)
        toast.success(`Connected to ${data.provider}!`)
        return true
      }
      throw new Error('API error')
    } catch {
      const newConfig = {
        ...config,
        cloud: { ...config.cloud, tested: true, lastTestResult: 'error' as const }
      }
      saveConfig(newConfig)
      toast.error('Connection failed. Check your API key.')
      return false
    } finally {
      setTesting(null)
    }
  }

  // Get effective backend status
  const getEffectiveBackend = () => {
    if (config.mode === 'local' && config.local.lastTestResult === 'success') {
      return { name: 'Ollama', model: config.local.model, status: 'ready' as const }
    }
    if (config.mode === 'cloud' && config.cloud.lastTestResult === 'success') {
      return { name: selectedCloudProvider?.name || config.cloud.provider, model: config.cloud.model, status: 'ready' as const }
    }
    if (serverOllamaAvailable) {
      return { name: 'Ollama (Server)', model: '', status: 'ready' as const }
    }
    return { name: 'Not configured', model: '', status: 'none' as const }
  }

  const effective = getEffectiveBackend()

  // Reset wizard
  const resetWizard = () => {
    setSetupPath(null)
    setWizardStep('choose')
    setShowWizard(true)
  }

  // Wizard step navigation
  const getWizardSteps = (): { id: WizardStep; label: string }[] => {
    if (setupPath === 'local') {
      return [
        { id: 'choose', label: 'Choose' },
        { id: 'install', label: 'Install' },
        { id: 'model', label: 'Model' },
        { id: 'test', label: 'Test' },
        { id: 'complete', label: 'Done' }
      ]
    }
    return [
      { id: 'choose', label: 'Choose' },
      { id: 'install', label: 'Provider' },
      { id: 'test', label: 'API Key' },
      { id: 'complete', label: 'Done' }
    ]
  }

  const wizardSteps = getWizardSteps()
  const currentStepIndex = wizardSteps.findIndex(s => s.id === wizardStep)

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">AI Assistant Setup</h1>
          <p className="text-muted-foreground mt-1">Connect Veena to an AI model</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={effective.status === 'ready' ? 'default' : 'secondary'} className="text-sm px-3 py-1">
            {effective.status === 'ready' ? `✅ ${effective.name}` : '⚠️ Not Connected'}
          </Badge>
          {isConfigured && (
            <Button variant="outline" size="sm" onClick={resetWizard}>
              🔄 Reconfigure
            </Button>
          )}
        </div>
      </div>

      {/* Experimental Notice */}
      <Card className="border-purple-200 bg-purple-50 dark:bg-purple-900/20">
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            <Badge className="bg-purple-600 text-white shrink-0">🧪 Experimental</Badge>
            <div className="space-y-1">
              <p className="text-sm text-purple-800 dark:text-purple-200">
                <strong>AI integration is experimental.</strong> Features may change, and responses should be verified independently.
              </p>
              <p className="text-xs text-purple-700 dark:text-purple-300">
                We're actively improving Veena's agricultural knowledge. Your feedback helps us make it better.
              </p>
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
                <Button variant="ghost" size="sm" onClick={() => setShowWizard(false)}>✕</Button>
              )}
            </div>
            {/* Progress Steps */}
            <div className="flex items-center gap-1 mt-4">
              {wizardSteps.map((step, i) => (
                <div key={step.id} className="flex items-center">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors',
                    i < currentStepIndex ? 'bg-green-500 text-white' :
                    i === currentStepIndex ? 'bg-primary text-white' :
                    'bg-gray-200 text-gray-500'
                  )}>
                    {i < currentStepIndex ? '✓' : i + 1}
                  </div>
                  {i < wizardSteps.length - 1 && (
                    <div className={cn(
                      'w-8 h-1 mx-1',
                      i < currentStepIndex ? 'bg-green-500' : 'bg-gray-200'
                    )} />
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-1 mt-1">
              {wizardSteps.map((step, i) => (
                <span key={step.id} className={cn(
                  'text-[10px] w-8 text-center',
                  i === currentStepIndex ? 'text-primary font-medium' : 'text-muted-foreground'
                )}>
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

      {/* Quick Reference */}
      {isConfigured && !showWizard && (
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">🏠 Local AI (Ollama)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                Free, private, works offline
              </p>
              <Badge variant={config.local.lastTestResult === 'success' ? 'default' : 'secondary'}>
                {config.local.lastTestResult === 'success' ? `✓ ${config.local.model}` : 'Not configured'}
              </Badge>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">☁️ Cloud AI</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                {selectedCloudProvider?.name || 'API key required'}
              </p>
              <Badge variant={config.cloud.lastTestResult === 'success' ? 'default' : 'secondary'}>
                {config.cloud.lastTestResult === 'success' ? `✓ Connected` : 'Not configured'}
              </Badge>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )

  // ============================================
  // WIZARD STEP RENDERER
  // ============================================

  function renderWizardStep() {
    // Step 1: Choose Path
    if (wizardStep === 'choose') {
      return (
        <div className="space-y-4">
          <p className="text-center text-muted-foreground">
            How would you like to connect Veena to AI?
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {/* Local Option */}
            <button
              onClick={() => { setSetupPath('local'); setWizardStep('install') }}
              className="p-6 rounded-xl border-2 border-gray-200 hover:border-primary hover:bg-primary/5 transition-all text-left group"
            >
              <div className="text-4xl mb-3">🏠</div>
              <h3 className="font-semibold text-lg mb-1">Local AI (Ollama)</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Run AI on your own computer. Free, private, works offline.
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="text-green-600 border-green-300">✅ Free forever</Badge>
                <Badge variant="outline" className="text-blue-600 border-blue-300">🔒 Private</Badge>
                <Badge variant="outline" className="text-purple-600 border-purple-300">📴 Offline</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                Requires: 8GB RAM, 2GB disk space
              </p>
            </button>

            {/* Cloud Option */}
            <button
              onClick={() => { setSetupPath('cloud'); setWizardStep('install') }}
              className="p-6 rounded-xl border-2 border-gray-200 hover:border-primary hover:bg-primary/5 transition-all text-left group"
            >
              <div className="text-4xl mb-3">☁️</div>
              <h3 className="font-semibold text-lg mb-1">Cloud AI (API Key)</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Use Google, OpenAI, or other cloud providers. Quick setup.
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="text-amber-600 border-amber-300">⚡ Instant</Badge>
                <Badge variant="outline" className="text-green-600 border-green-300">✅ Free tiers</Badge>
                <Badge variant="outline" className="text-blue-600 border-blue-300">🌐 Any device</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                Requires: Internet connection, API key
              </p>
            </button>
          </div>
        </div>
      )
    }

    // ============================================
    // LOCAL PATH: Step 2 - Install Ollama
    // ============================================
    if (setupPath === 'local' && wizardStep === 'install') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Step 1: Install Ollama</h3>
            <p className="text-muted-foreground">
              Ollama lets you run AI models locally on your computer
            </p>
          </div>

          {/* OS-specific instructions */}
          <div className="p-4 bg-muted rounded-lg space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span>Detected OS:</span>
              <Badge variant="outline">
                {os === 'mac' ? '🍎 macOS' : os === 'windows' ? '🪟 Windows' : '🐧 Linux'}
              </Badge>
            </div>

            {os === 'mac' && (
              <div className="space-y-3">
                <p className="text-sm"><strong>Option 1:</strong> Download installer</p>
                <a 
                  href="https://ollama.ai/download/mac" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                >
                  ⬇️ Download for macOS
                </a>
                <p className="text-sm mt-4"><strong>Option 2:</strong> Using Homebrew</p>
                <code className="block bg-black text-green-400 px-3 py-2 rounded text-sm font-mono">
                  brew install ollama
                </code>
              </div>
            )}

            {os === 'windows' && (
              <div className="space-y-3">
                <p className="text-sm">Download and run the installer:</p>
                <a 
                  href="https://ollama.ai/download/windows" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                >
                  ⬇️ Download for Windows
                </a>
                <p className="text-xs text-muted-foreground mt-2">
                  After installation, Ollama runs in the system tray
                </p>
              </div>
            )}

            {os === 'linux' && (
              <div className="space-y-3">
                <p className="text-sm">Run this command in terminal:</p>
                <code className="block bg-black text-green-400 px-3 py-2 rounded text-sm font-mono">
                  curl -fsSL https://ollama.ai/install.sh | sh
                </code>
                <p className="text-xs text-muted-foreground mt-2">
                  Then start with: <code className="bg-gray-200 px-1 rounded">ollama serve</code>
                </p>
              </div>
            )}
          </div>

          {/* Verification */}
          <div className="p-4 border rounded-lg space-y-3">
            <p className="text-sm font-medium">✅ After installing, verify it's running:</p>
            <div className="flex gap-2">
              <Input
                value={config.local.host}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  local: { ...prev.local, host: e.target.value }
                }))}
                placeholder="http://localhost:11434"
                className="font-mono"
              />
              <Button onClick={testOllama} disabled={testing === 'local'}>
                {testing === 'local' ? '⏳' : '🔌'} Check
              </Button>
            </div>
            {config.local.lastTestResult === 'error' && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800 font-medium">❌ Cannot connect to Ollama</p>
                <p className="text-xs text-red-700 mt-1">
                  Make sure Ollama is installed and running. On macOS/Windows, check the menu bar icon.
                </p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={() => setWizardStep('choose')}>
              ← Back
            </Button>
            <Button onClick={() => setWizardStep('model')}>
              Next: Download Model →
            </Button>
          </div>
        </div>
      )
    }

    // ============================================
    // LOCAL PATH: Step 3 - Download Model
    // ============================================
    if (setupPath === 'local' && wizardStep === 'model') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Step 2: Download an AI Model</h3>
            <p className="text-muted-foreground">
              Choose a model to download. Smaller = faster, larger = smarter.
            </p>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            {OLLAMA_MODELS.map((model) => (
              <label
                key={model.id}
                className={cn(
                  'flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all',
                  selectedModel === model.id 
                    ? 'border-primary bg-primary/5' 
                    : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <input
                  type="radio"
                  name="model"
                  checked={selectedModel === model.id}
                  onChange={() => setSelectedModel(model.id)}
                  className="sr-only"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{model.name}</span>
                    <Badge variant="outline" className="text-xs">{model.size}</Badge>
                    {model.id === 'llama3.2:3b' && (
                      <Badge className="text-xs bg-green-500">Recommended</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{model.desc}</p>
                </div>
                <div className={cn(
                  'w-5 h-5 rounded-full border-2 flex items-center justify-center',
                  selectedModel === model.id ? 'border-primary bg-primary' : 'border-gray-300'
                )}>
                  {selectedModel === model.id && <span className="text-white text-xs">✓</span>}
                </div>
              </label>
            ))}
          </div>

          {/* Download Command */}
          <div className="p-4 bg-muted rounded-lg space-y-3">
            <p className="text-sm font-medium">Run this command in terminal:</p>
            <div className="flex gap-2">
              <code className="flex-1 bg-black text-green-400 px-3 py-2 rounded text-sm font-mono">
                ollama pull {selectedModel}
              </code>
              <Button
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(`ollama pull ${selectedModel}`)
                  toast.success('Command copied!')
                }}
              >
                📋 Copy
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              This will download ~{OLLAMA_MODELS.find(m => m.id === selectedModel)?.size}. 
              Wait for it to complete before continuing.
            </p>
          </div>

          {/* Already have models? */}
          {ollamaModels.length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800 font-medium">
                ✅ Found {ollamaModels.length} model(s) already installed:
              </p>
              <p className="text-sm text-green-700 mt-1">
                {ollamaModels.slice(0, 5).join(', ')}
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={() => setWizardStep('install')}>
              ← Back
            </Button>
            <Button onClick={() => setWizardStep('test')}>
              Next: Test Connection →
            </Button>
          </div>
        </div>
      )
    }

    // ============================================
    // LOCAL PATH: Step 4 - Test Connection
    // ============================================
    if (setupPath === 'local' && wizardStep === 'test') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Step 3: Test Connection</h3>
            <p className="text-muted-foreground">
              Let's make sure everything is working
            </p>
          </div>

          {/* Test Button */}
          <div className="p-6 border-2 border-dashed rounded-lg text-center space-y-4">
            <div className="text-5xl">
              {config.local.lastTestResult === 'success' ? '✅' : 
               config.local.lastTestResult === 'error' ? '❌' : '🔌'}
            </div>
            <Button 
              size="lg" 
              onClick={async () => {
                const success = await testOllama()
                if (success) {
                  setTimeout(() => setWizardStep('complete'), 500)
                }
              }}
              disabled={testing === 'local'}
              className="px-8"
            >
              {testing === 'local' ? '⏳ Testing...' : 'Test Connection'}
            </Button>
          </div>

          {/* Status */}
          {config.local.lastTestResult === 'success' && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">✅ Connected successfully!</p>
              <p className="text-sm text-green-700 mt-1">
                Model: {config.local.model}
              </p>
            </div>
          )}

          {config.local.lastTestResult === 'error' && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg space-y-2">
              <p className="text-red-800 font-medium">❌ Connection failed</p>
              <div className="text-sm text-red-700 space-y-1">
                <p><strong>Troubleshooting:</strong></p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Is Ollama running? Check menu bar (macOS) or system tray (Windows)</li>
                  <li>Try running <code className="bg-red-100 px-1 rounded">ollama serve</code> in terminal</li>
                  <li>Did you download a model? Run <code className="bg-red-100 px-1 rounded">ollama pull {selectedModel}</code></li>
                  <li>Check if port 11434 is blocked by firewall</li>
                </ul>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={() => setWizardStep('model')}>
              ← Back
            </Button>
            <Button 
              onClick={() => setWizardStep('complete')}
              disabled={config.local.lastTestResult !== 'success'}
            >
              Complete Setup →
            </Button>
          </div>
        </div>
      )
    }

    // ============================================
    // CLOUD PATH: Step 2 - Select Provider
    // ============================================
    if (setupPath === 'cloud' && wizardStep === 'install') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Step 1: Choose a Provider</h3>
            <p className="text-muted-foreground">
              Select which AI service you want to use
            </p>
          </div>

          {/* Provider Grid */}
          <div className="grid grid-cols-2 gap-3">
            {CLOUD_PROVIDERS.map((provider) => (
              <button
                key={provider.id}
                onClick={() => setConfig(prev => ({
                  ...prev,
                  cloud: { ...prev.cloud, provider: provider.id, tested: false, lastTestResult: undefined }
                }))}
                className={cn(
                  'p-4 rounded-lg border-2 text-left transition-all',
                  config.cloud.provider === provider.id 
                    ? 'border-primary bg-primary/5' 
                    : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{provider.icon}</span>
                  <span className="font-medium">{provider.name}</span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">{provider.description}</p>
                <Badge 
                  variant="outline" 
                  className={cn(
                    'text-xs',
                    provider.freeInfo.includes('Free') ? 'text-green-600 border-green-300' : 'text-gray-600'
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
                {selectedCloudProvider.description}. {selectedCloudProvider.freeInfo}
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
            <Button variant="outline" onClick={() => setWizardStep('choose')}>
              ← Back
            </Button>
            <Button onClick={() => setWizardStep('test')}>
              Next: Enter API Key →
            </Button>
          </div>
        </div>
      )
    }

    // ============================================
    // CLOUD PATH: Step 3 - Enter API Key & Test
    // ============================================
    if (setupPath === 'cloud' && wizardStep === 'test') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Step 2: Enter Your API Key</h3>
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
            {selectedCloudProvider?.id === 'google' && (
              <p className="text-xs text-blue-700 mt-2">
                Tip: Sign in with Google, click "Create API Key", copy it.
              </p>
            )}
            {selectedCloudProvider?.id === 'groq' && (
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
                type={showApiKey ? 'text' : 'password'}
                value={config.cloud.apiKey}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  cloud: { ...prev.cloud, apiKey: e.target.value, tested: false, lastTestResult: undefined }
                }))}
                placeholder={selectedCloudProvider?.placeholder}
                className="font-mono"
              />
              <Button variant="outline" onClick={() => setShowApiKey(!showApiKey)}>
                {showApiKey ? '🙈' : '👁️'}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              🔒 Your API key is stored locally in your browser and sent directly to {selectedCloudProvider?.name}.
            </p>
          </div>

          {/* Test Button */}
          <div className="p-4 border rounded-lg space-y-3">
            <Button 
              onClick={async () => {
                const success = await testCloud()
                if (success) {
                  setTimeout(() => setWizardStep('complete'), 500)
                }
              }}
              disabled={testing === 'cloud' || !config.cloud.apiKey}
              className="w-full"
            >
              {testing === 'cloud' ? '⏳ Testing...' : '🔌 Test Connection'}
            </Button>

            {/* Status */}
            {config.cloud.lastTestResult === 'success' && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 font-medium">✅ Connected to {selectedCloudProvider?.name}!</p>
                {config.cloud.model && (
                  <p className="text-sm text-green-700">Model: {config.cloud.model}</p>
                )}
              </div>
            )}

            {config.cloud.lastTestResult === 'error' && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg space-y-2">
                <p className="text-red-800 font-medium">❌ Connection failed</p>
                <div className="text-sm text-red-700">
                  <p><strong>Check:</strong></p>
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
            <Button variant="outline" onClick={() => setWizardStep('install')}>
              ← Back
            </Button>
            <Button 
              onClick={() => setWizardStep('complete')}
              disabled={config.cloud.lastTestResult !== 'success'}
            >
              Complete Setup →
            </Button>
          </div>
        </div>
      )
    }

    // ============================================
    // COMPLETE: Both Paths
    // ============================================
    if (wizardStep === 'complete') {
      const isLocal = setupPath === 'local'
      return (
        <div className="space-y-6 text-center">
          <div className="text-6xl">🎉</div>
          <div>
            <h3 className="text-xl font-semibold mb-2">Setup Complete!</h3>
            <p className="text-muted-foreground">
              Veena is now connected to {isLocal ? 'Ollama' : selectedCloudProvider?.name}
            </p>
          </div>

          {/* Summary */}
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-left">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{isLocal ? '🏠' : '☁️'}</span>
              <div>
                <p className="font-medium text-green-800">
                  {isLocal ? `Local AI: ${config.local.model}` : `Cloud AI: ${selectedCloudProvider?.name}`}
                </p>
                <p className="text-sm text-green-700">
                  {isLocal 
                    ? 'Free, private, works offline' 
                    : `Using your API key • ${selectedCloudProvider?.freeInfo}`
                  }
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
            <Button onClick={() => {
              setShowWizard(false)
              // Could navigate to Veena chat here
            }}>
              Start Chatting with Veena →
            </Button>
          </div>
        </div>
      )
    }

    return null
  }
}
