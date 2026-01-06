/**
 * AI Assistant Page
 * Interactive AI chat for breeding data analysis with automatic data context
 * Supports hybrid mode: Chrome AI (local) + Cloud AI (API)
 */
import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { Link } from 'react-router-dom'
import { aiDataContext, DataContext } from '@/lib/ai-data-context'
import { chromeAI, ChromeAIStatus } from '@/lib/chrome-ai'
import { ApiKeyNotice, MultiServiceNotice } from '@/components/ApiKeyNotice'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface AIConfig {
  enabled: boolean
  provider: string
  model: string
  apiKey: string
  temperature: number
  maxTokens: number
}

const QUICK_PROMPTS = [
  { icon: '📊', label: 'Analyze yield data', prompt: 'Analyze the yield data from my latest trial and identify top performers' },
  { icon: '🧬', label: 'Selection advice', prompt: 'Based on the phenotypic data, which germplasm should I select for advancement?' },
  { icon: '📈', label: 'Trend analysis', prompt: 'What trends do you see in my breeding program over the last 3 years?' },
  { icon: '🌾', label: 'Trait correlation', prompt: 'Analyze the correlation between yield and disease resistance in my data' },
  { icon: '🔬', label: 'Heritability estimate', prompt: 'Help me estimate heritability for the traits in my trial' },
  { icon: '📋', label: 'Trial summary', prompt: 'Summarize the results of my current trial in a report format' },
]

export function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [includeData, setIncludeData] = useState(true)
  const [dataContext, setDataContext] = useState<DataContext | null>(null)
  const [loadingData, setLoadingData] = useState(false)
  const [chromeAIStatus, setChromeAIStatus] = useState<ChromeAIStatus | null>(null)
  const [useHybridMode, setUseHybridMode] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const config: AIConfig | null = (() => {
    const saved = localStorage.getItem('bijmantra_ai_config')
    return saved ? JSON.parse(saved) : null
  })()

  // Check Chrome AI availability
  useEffect(() => {
    chromeAI.getStatus().then(setChromeAIStatus)
  }, [])

  // Load data context on mount
  useEffect(() => {
    if (includeData) {
      loadDataContext()
    }
  }, [includeData])

  const loadDataContext = async () => {
    setLoadingData(true)
    try {
      const context = await aiDataContext.getFullContext()
      setDataContext(context)
    } catch (error) {
      console.error('Failed to load data context:', error)
    } finally {
      setLoadingData(false)
    }
  }

  const isConfigured = config?.enabled && config?.apiKey

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (content: string) => {
    if (!content.trim()) return
    if (!isConfigured) {
      toast.error('Please configure AI settings first')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      // Build conversation history for context
      const conversationHistory = [...messages, userMessage].map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }))

      // Add data context to the first message if enabled
      let messagesWithContext = conversationHistory
      if (includeData && dataContext) {
        const dataPrompt = aiDataContext.formatForPrompt(dataContext)
        // Prepend data context to the user's message
        messagesWithContext = conversationHistory.map((m, i) => {
          if (i === conversationHistory.length - 1 && m.role === 'user') {
            return {
              ...m,
              content: `${dataPrompt}\n\n---\n\n**User Question:** ${m.content}`
            }
          }
          return m
        })
      }

      let response: string

      // Try Chrome AI first if hybrid mode is enabled and available
      const chromeAIAvailable = chromeAIStatus?.apis.languageModel === 'readily'
      
      if (useHybridMode && chromeAIAvailable && isSimpleQuery(content)) {
        // Use Chrome AI for simple queries (local, fast, private)
        try {
          response = await chromeAI.askBreedingQuestion(content)
          toast.success('Answered by Chrome AI (local)', { duration: 2000 })
        } catch (chromeError) {
          // Fallback to cloud AI
          console.log('Chrome AI failed, falling back to cloud:', chromeError)
          response = await callAI(messagesWithContext, config!)
        }
      } else {
        // Use cloud AI for complex queries or when Chrome AI unavailable
        response = await callAI(messagesWithContext, config!)
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('AI Error:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to get AI response')
    } finally {
      setLoading(false)
    }
  }

  // Real AI API call function
  const callAI = async (messages: { role: string; content: string }[], config: AIConfig): Promise<string> => {
    const systemPrompt = `You are an expert plant breeding assistant integrated into Bijmantra, a BrAPI-compliant breeding management system. You help breeders with:

1. Data Analysis: Analyze phenotypic and genotypic data, identify patterns, and provide statistical insights
2. Selection Decisions: Recommend germplasm for advancement based on breeding objectives
3. Trial Design: Suggest optimal experimental designs (RCBD, Alpha-lattice, etc.)
4. Genetic Gain: Calculate and interpret genetic gain, heritability, and selection indices
5. Breeding Strategy: Provide recommendations for crossing schemes and population improvement

When analyzing data:
- Be specific with numbers and statistics when provided
- Use proper breeding terminology
- Provide actionable recommendations
- Consider both short-term and long-term breeding goals
- Format responses clearly with headers, bullet points, and tables when appropriate.`

    switch (config.provider) {
      case 'openai':
        return callOpenAI(messages, config, systemPrompt)
      case 'anthropic':
        return callAnthropic(messages, config, systemPrompt)
      case 'google':
        return callGoogle(messages, config, systemPrompt)
      case 'mistral':
        return callMistral(messages, config, systemPrompt)
      default:
        throw new Error(`Unknown provider: ${config.provider}`)
    }
  }

  const callOpenAI = async (messages: { role: string; content: string }[], config: AIConfig, systemPrompt: string): Promise<string> => {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`,
      },
      body: JSON.stringify({
        model: config.model,
        messages: [{ role: 'system', content: systemPrompt }, ...messages],
        temperature: config.temperature,
        max_tokens: config.maxTokens,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || `OpenAI API error: ${response.status}`)
    }

    const data = await response.json()
    return data.choices[0].message.content
  }

  const callAnthropic = async (messages: { role: string; content: string }[], config: AIConfig, systemPrompt: string): Promise<string> => {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': config.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: config.model,
        max_tokens: config.maxTokens,
        system: systemPrompt,
        messages: messages.map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content })),
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || `Anthropic API error: ${response.status}`)
    }

    const data = await response.json()
    return data.content[0].text
  }

  const callGoogle = async (messages: { role: string; content: string }[], config: AIConfig, systemPrompt: string): Promise<string> => {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${config.apiKey}`
    
    const contents = messages.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }],
    }))

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents,
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: {
          temperature: config.temperature,
          maxOutputTokens: config.maxTokens,
        },
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || `Google AI API error: ${response.status}`)
    }

    const data = await response.json()
    return data.candidates[0].content.parts[0].text
  }

  const callMistral = async (messages: { role: string; content: string }[], config: AIConfig, systemPrompt: string): Promise<string> => {
    const response = await fetch('https://api.mistral.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`,
      },
      body: JSON.stringify({
        model: config.model,
        messages: [{ role: 'system', content: systemPrompt }, ...messages],
        temperature: config.temperature,
        max_tokens: config.maxTokens,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || `Mistral API error: ${response.status}`)
    }

    const data = await response.json()
    return data.choices[0].message.content
  }

  // Detect if a query is simple enough for Chrome AI
  const isSimpleQuery = (query: string): boolean => {
    const simplePatterns = [
      /what is/i,
      /define/i,
      /explain/i,
      /how do/i,
      /what are/i,
      /tell me about/i,
      /describe/i,
      /difference between/i,
      /meaning of/i,
    ]
    // Simple queries are short and match common patterns
    return query.length < 200 && simplePatterns.some(p => p.test(query))
  }

  const clearChat = () => {
    setMessages([])
    toast.success('Chat cleared')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">AI Assistant</h1>
          <p className="text-muted-foreground mt-1">Intelligent breeding data analysis</p>
        </div>
        <div className="flex items-center gap-2">
          {isConfigured ? (
            <Badge className="bg-green-100 text-green-700">
              🟢 {config?.provider} / {config?.model}
            </Badge>
          ) : (
            <Badge variant="secondary">⚪ Not Configured</Badge>
          )}
          <Link to="/ai-settings">
            <Button variant="outline" size="sm">⚙️ Settings</Button>
          </Link>
        </div>
      </div>

      {!isConfigured ? (
        <MultiServiceNotice 
          serviceIds={['google_ai', 'groq', 'ollama', 'openai', 'anthropic']} 
          title="AI Provider Configuration Required"
          className="border-yellow-200 bg-yellow-50"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Quick Prompts & Data Context */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-sm">Quick Prompts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {QUICK_PROMPTS.map((prompt, i) => (
                <Button
                  key={i}
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-left h-auto py-2"
                  onClick={() => sendMessage(prompt.prompt)}
                >
                  <span className="mr-2">{prompt.icon}</span>
                  <span className="truncate">{prompt.label}</span>
                </Button>
              ))}

              {/* Data Context Toggle */}
              <div className="mt-4 pt-4 border-t space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="include-data" className="text-sm font-medium">Include App Data</Label>
                  <Switch
                    id="include-data"
                    checked={includeData}
                    onCheckedChange={setIncludeData}
                  />
                </div>
                {includeData && (
                  <div className="text-xs space-y-1">
                    {loadingData ? (
                      <p className="text-muted-foreground">⏳ Loading data...</p>
                    ) : dataContext ? (
                      <>
                        <p className="text-green-600">✓ Data context loaded</p>
                        <p className="text-muted-foreground">
                          {dataContext.germplasm.length} germplasm, {dataContext.observations.length} observations
                        </p>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-6 text-xs p-0"
                          onClick={loadDataContext}
                        >
                          🔄 Refresh
                        </Button>
                      </>
                    ) : (
                      <p className="text-yellow-600">⚠️ No data available (backend may be offline)</p>
                    )}
                  </div>
                )}
              </div>

              {/* Hybrid Mode Toggle */}
              <div className="mt-4 pt-4 border-t space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="hybrid-mode" className="text-sm font-medium">Hybrid AI Mode</Label>
                  <Switch
                    id="hybrid-mode"
                    checked={useHybridMode}
                    onCheckedChange={setUseHybridMode}
                  />
                </div>
                <div className="text-xs space-y-1">
                  {chromeAIStatus?.apis.languageModel === 'readily' ? (
                    <p className="text-green-600">✓ Chrome AI available</p>
                  ) : chromeAIStatus?.apis.languageModel === 'after-download' ? (
                    <p className="text-yellow-600">⏳ Chrome AI needs download</p>
                  ) : (
                    <p className="text-muted-foreground">⚪ Chrome AI unavailable</p>
                  )}
                  <p className="text-muted-foreground">
                    {useHybridMode ? 'Simple queries use local AI' : 'All queries use cloud AI'}
                  </p>
                  <Link to="/chrome-ai" className="text-primary hover:underline text-xs">
                    Explore Chrome AI →
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Chat Area */}
          <Card className="lg:col-span-3 flex flex-col" style={{ height: '600px' }}>
            <CardHeader className="pb-2 flex-shrink-0">
              <div className="flex items-center justify-between">
                <CardTitle>Chat</CardTitle>
                <Button variant="ghost" size="sm" onClick={clearChat}>🗑️ Clear</Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col overflow-hidden">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {messages.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <span className="text-4xl">💬</span>
                    <p className="mt-2">Start a conversation with your AI assistant</p>
                    <p className="text-sm">Ask about your breeding data, get recommendations, or analyze results</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                        <div className={`text-xs mt-1 ${msg.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                          {msg.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <div className="animate-bounce">🤖</div>
                        <span className="text-sm text-muted-foreground">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="flex gap-2 flex-shrink-0">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about your breeding data..."
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
                  disabled={loading}
                />
                <Button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
                  {loading ? '⏳' : '📤'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
