/**
 * AI Service
 * Handles communication with various AI providers
 */

export interface AIConfig {
  enabled: boolean
  provider: 'openai' | 'anthropic' | 'google' | 'mistral'
  model: string
  apiKey: string
  temperature: number
  maxTokens: number
}

export interface AIMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface AIResponse {
  content: string
  usage?: {
    promptTokens: number
    completionTokens: number
    totalTokens: number
  }
}

const PROVIDER_ENDPOINTS = {
  openai: 'https://api.openai.com/v1/chat/completions',
  anthropic: 'https://api.anthropic.com/v1/messages',
  google: 'https://generativelanguage.googleapis.com/v1beta/models',
  mistral: 'https://api.mistral.ai/v1/chat/completions',
}

const BREEDING_SYSTEM_PROMPT = `You are an expert plant breeding assistant integrated into Bijmantra, a BrAPI-compliant breeding management system. You help breeders with:

1. Data Analysis: Analyze phenotypic and genotypic data, identify patterns, and provide statistical insights
2. Selection Decisions: Recommend germplasm for advancement based on breeding objectives
3. Trial Design: Suggest optimal experimental designs (RCBD, Alpha-lattice, etc.)
4. Genetic Gain: Calculate and interpret genetic gain, heritability, and selection indices
5. Breeding Strategy: Provide recommendations for crossing schemes and population improvement

When analyzing data:
- Be specific with numbers and statistics
- Use proper breeding terminology
- Provide actionable recommendations
- Consider both short-term and long-term breeding goals
- Account for GxE interactions when relevant

Format responses clearly with headers, bullet points, and tables when appropriate.`

class AIService {
  private config: AIConfig | null = null

  constructor() {
    this.loadConfig()
  }

  loadConfig() {
    const saved = localStorage.getItem('bijmantra_ai_config')
    this.config = saved ? JSON.parse(saved) : null
  }

  isConfigured(): boolean {
    return !!(this.config?.enabled && this.config?.apiKey)
  }

  getConfig(): AIConfig | null {
    return this.config
  }

  async chat(messages: AIMessage[], systemPrompt?: string): Promise<AIResponse> {
    if (!this.isConfigured() || !this.config) {
      throw new Error('AI is not configured. Please add your API key in AI Settings.')
    }

    const fullMessages: AIMessage[] = [
      { role: 'system', content: systemPrompt || BREEDING_SYSTEM_PROMPT },
      ...messages,
    ]

    switch (this.config.provider) {
      case 'openai':
        return this.callOpenAI(fullMessages)
      case 'anthropic':
        return this.callAnthropic(fullMessages)
      case 'google':
        return this.callGoogle(fullMessages)
      case 'mistral':
        return this.callMistral(fullMessages)
      default:
        throw new Error(`Unknown provider: ${this.config.provider}`)
    }
  }

  private async callOpenAI(messages: AIMessage[]): Promise<AIResponse> {
    const response = await fetch(PROVIDER_ENDPOINTS.openai, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config!.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config!.model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        temperature: this.config!.temperature,
        max_tokens: this.config!.maxTokens,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || 'OpenAI API error')
    }

    const data = await response.json()
    return {
      content: data.choices[0].message.content,
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    }
  }

  private async callAnthropic(messages: AIMessage[]): Promise<AIResponse> {
    const systemMessage = messages.find(m => m.role === 'system')
    const chatMessages = messages.filter(m => m.role !== 'system')

    const response = await fetch(PROVIDER_ENDPOINTS.anthropic, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.config!.apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: this.config!.model,
        max_tokens: this.config!.maxTokens,
        system: systemMessage?.content || BREEDING_SYSTEM_PROMPT,
        messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || 'Anthropic API error')
    }

    const data = await response.json()
    return {
      content: data.content[0].text,
      usage: {
        promptTokens: data.usage?.input_tokens || 0,
        completionTokens: data.usage?.output_tokens || 0,
        totalTokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0),
      },
    }
  }

  private async callGoogle(messages: AIMessage[]): Promise<AIResponse> {
    const url = `${PROVIDER_ENDPOINTS.google}/${this.config!.model}:generateContent?key=${this.config!.apiKey}`
    
    const contents = messages
      .filter(m => m.role !== 'system')
      .map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }],
      }))

    const systemInstruction = messages.find(m => m.role === 'system')

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents,
        systemInstruction: systemInstruction ? { parts: [{ text: systemInstruction.content }] } : undefined,
        generationConfig: {
          temperature: this.config!.temperature,
          maxOutputTokens: this.config!.maxTokens,
        },
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error?.message || 'Google AI API error')
    }

    const data = await response.json()
    return {
      content: data.candidates[0].content.parts[0].text,
      usage: {
        promptTokens: data.usageMetadata?.promptTokenCount || 0,
        completionTokens: data.usageMetadata?.candidatesTokenCount || 0,
        totalTokens: data.usageMetadata?.totalTokenCount || 0,
      },
    }
  }

  private async callMistral(messages: AIMessage[]): Promise<AIResponse> {
    const response = await fetch(PROVIDER_ENDPOINTS.mistral, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config!.apiKey}`,
      },
      body: JSON.stringify({
        model: this.config!.model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        temperature: this.config!.temperature,
        max_tokens: this.config!.maxTokens,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || 'Mistral API error')
    }

    const data = await response.json()
    return {
      content: data.choices[0].message.content,
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    }
  }

  // Convenience methods for common breeding tasks
  async analyzeData(data: any, question: string): Promise<string> {
    const messages: AIMessage[] = [
      {
        role: 'user',
        content: `Here is my breeding data:\n\n${JSON.stringify(data, null, 2)}\n\nQuestion: ${question}`,
      },
    ]
    const response = await this.chat(messages)
    return response.content
  }

  async getSelectionRecommendations(traitData: any, objectives: string): Promise<string> {
    const messages: AIMessage[] = [
      {
        role: 'user',
        content: `Based on the following trait data and breeding objectives, provide selection recommendations:\n\nTrait Data:\n${JSON.stringify(traitData, null, 2)}\n\nBreeding Objectives: ${objectives}`,
      },
    ]
    const response = await this.chat(messages)
    return response.content
  }

  async summarizeTrial(trialData: any): Promise<string> {
    const messages: AIMessage[] = [
      {
        role: 'user',
        content: `Please summarize the following trial results in a clear, professional format:\n\n${JSON.stringify(trialData, null, 2)}`,
      },
    ]
    const response = await this.chat(messages)
    return response.content
  }
}

export const aiService = new AIService()
