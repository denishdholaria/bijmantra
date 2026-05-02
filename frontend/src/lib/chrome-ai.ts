/**
 * Chrome Built-in AI Service
 * Leverages Chrome 138+ Gemini Nano APIs for local, private AI processing
 * 
 * Stable APIs (Chrome 138+):
 * - Summarizer API: Condense long content
 * - Translator API: Translate between languages
 * - Language Detector API: Detect input language
 * 
 * Origin Trial APIs:
 * - Writer API: Generate new content
 * - Rewriter API: Revise and restructure text
 * - Proofreader API: Grammar and spelling corrections
 * - Prompt API: General natural language prompts
 * 
 * @see https://developer.chrome.com/docs/ai/built-in
 */

// Type definitions for Chrome Built-in AI APIs
declare global {
  interface Window {
    ai?: {
      languageModel?: AILanguageModel
      summarizer?: AISummarizer
      writer?: AIWriter
      rewriter?: AIRewriter
      translator?: AITranslator
      languageDetector?: AILanguageDetector
      proofreader?: AIProofreader
    }
    translation?: {
      createTranslator?: (options: TranslatorOptions) => Promise<Translator>
      canTranslate?: (options: TranslatorOptions) => Promise<AICapabilityAvailability>
    }
  }
}

type AICapabilityAvailability = 'readily' | 'after-download' | 'no'

interface AILanguageModel {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: (options?: LanguageModelOptions) => Promise<LanguageModelSession>
}

interface LanguageModelOptions {
  systemPrompt?: string
  temperature?: number
  topK?: number
}

interface LanguageModelSession {
  prompt: (input: string) => Promise<string>
  promptStreaming: (input: string) => ReadableStream<string>
  destroy: () => void
}

interface AISummarizer {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: (options?: SummarizerOptions) => Promise<SummarizerSession>
}

interface SummarizerOptions {
  type?: 'key-points' | 'tl;dr' | 'teaser' | 'headline'
  format?: 'plain-text' | 'markdown'
  length?: 'short' | 'medium' | 'long'
  sharedContext?: string
}

interface SummarizerSession {
  summarize: (text: string, options?: { context?: string }) => Promise<string>
  summarizeStreaming: (text: string) => ReadableStream<string>
  destroy: () => void
}

interface AIWriter {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: (options?: WriterOptions) => Promise<WriterSession>
}

interface WriterOptions {
  tone?: 'formal' | 'neutral' | 'casual'
  format?: 'plain-text' | 'markdown'
  length?: 'short' | 'medium' | 'long'
  sharedContext?: string
}

interface WriterSession {
  write: (task: string, options?: { context?: string }) => Promise<string>
  writeStreaming: (task: string) => ReadableStream<string>
  destroy: () => void
}

interface AIRewriter {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: (options?: RewriterOptions) => Promise<RewriterSession>
}

interface RewriterOptions {
  tone?: 'as-is' | 'more-formal' | 'more-casual'
  format?: 'as-is' | 'plain-text' | 'markdown'
  length?: 'as-is' | 'shorter' | 'longer'
  sharedContext?: string
}

interface RewriterSession {
  rewrite: (text: string, options?: { context?: string }) => Promise<string>
  rewriteStreaming: (text: string) => ReadableStream<string>
  destroy: () => void
}

interface AITranslator {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: (options: TranslatorOptions) => Promise<TranslatorSession>
}

interface TranslatorOptions {
  sourceLanguage: string
  targetLanguage: string
}

interface Translator {
  translate: (text: string) => Promise<string>
}

interface TranslatorSession {
  translate: (text: string) => Promise<string>
  destroy: () => void
}

interface AILanguageDetector {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: () => Promise<LanguageDetectorSession>
}

interface LanguageDetectorSession {
  detect: (text: string) => Promise<LanguageDetectionResult[]>
  destroy: () => void
}

interface LanguageDetectionResult {
  detectedLanguage: string
  confidence: number
}

interface AIProofreader {
  capabilities: () => Promise<{ available: AICapabilityAvailability }>
  create: () => Promise<ProofreaderSession>
}

interface ProofreaderSession {
  proofread: (text: string) => Promise<ProofreadResult>
  destroy: () => void
}

interface ProofreadResult {
  corrections: Array<{
    start: number
    end: number
    original: string
    replacement: string
    type: 'spelling' | 'grammar' | 'punctuation'
  }>
}

// API Availability Status
export interface ChromeAIStatus {
  isChrome: boolean
  version: number
  apis: {
    languageModel: AICapabilityAvailability | 'unavailable'
    summarizer: AICapabilityAvailability | 'unavailable'
    writer: AICapabilityAvailability | 'unavailable'
    rewriter: AICapabilityAvailability | 'unavailable'
    translator: AICapabilityAvailability | 'unavailable'
    languageDetector: AICapabilityAvailability | 'unavailable'
    proofreader: AICapabilityAvailability | 'unavailable'
  }
}

class ChromeAIService {
  private sessions: {
    languageModel?: LanguageModelSession
    summarizer?: SummarizerSession
    writer?: WriterSession
    rewriter?: RewriterSession
    translator?: Map<string, TranslatorSession>
    languageDetector?: LanguageDetectorSession
    proofreader?: ProofreaderSession
  } = { translator: new Map() }

  /**
   * Check Chrome version and API availability
   */
  async getStatus(): Promise<ChromeAIStatus> {
    const isChrome = /Chrome\/(\d+)/.test(navigator.userAgent)
    const versionMatch = navigator.userAgent.match(/Chrome\/(\d+)/)
    const version = versionMatch ? parseInt(versionMatch[1]) : 0

    const status: ChromeAIStatus = {
      isChrome,
      version,
      apis: {
        languageModel: 'unavailable',
        summarizer: 'unavailable',
        writer: 'unavailable',
        rewriter: 'unavailable',
        translator: 'unavailable',
        languageDetector: 'unavailable',
        proofreader: 'unavailable',
      }
    }

    if (!isChrome || version < 138) {
      return status
    }

    // Check each API
    try {
      if (window.ai?.languageModel) {
        const caps = await window.ai.languageModel.capabilities()
        status.apis.languageModel = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.summarizer) {
        const caps = await window.ai.summarizer.capabilities()
        status.apis.summarizer = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.writer) {
        const caps = await window.ai.writer.capabilities()
        status.apis.writer = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.rewriter) {
        const caps = await window.ai.rewriter.capabilities()
        status.apis.rewriter = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.translator) {
        const caps = await window.ai.translator.capabilities()
        status.apis.translator = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.languageDetector) {
        const caps = await window.ai.languageDetector.capabilities()
        status.apis.languageDetector = caps.available
      }
    } catch { /* API not available */ }

    try {
      if (window.ai?.proofreader) {
        const caps = await window.ai.proofreader.capabilities()
        status.apis.proofreader = caps.available
      }
    } catch { /* API not available */ }

    return status
  }

  /**
   * Check if any Chrome AI API is available
   */
  async isAvailable(): Promise<boolean> {
    const status = await this.getStatus()
    return Object.values(status.apis).some(v => v === 'readily' || v === 'after-download')
  }

  // ============================================
  // SUMMARIZER API (Chrome 138 Stable)
  // ============================================

  /**
   * Summarize text using Chrome's built-in Summarizer
   * Perfect for: trial results, germplasm descriptions, observation data
   */
  async summarize(
    text: string,
    options?: {
      type?: 'key-points' | 'tl;dr' | 'teaser' | 'headline'
      length?: 'short' | 'medium' | 'long'
      context?: string
    }
  ): Promise<string> {
    if (!window.ai?.summarizer) {
      throw new Error('Summarizer API not available. Requires Chrome 138+')
    }

    if (!this.sessions.summarizer) {
      this.sessions.summarizer = await window.ai.summarizer.create({
        type: options?.type || 'key-points',
        format: 'markdown',
        length: options?.length || 'medium',
        sharedContext: 'Plant breeding and agricultural research data'
      })
    }

    return this.sessions.summarizer.summarize(text, { context: options?.context })
  }

  /**
   * Summarize breeding trial results
   */
  async summarizeTrialResults(trialData: any): Promise<string> {
    const text = `Trial: ${trialData.trialName || 'Unknown'}
Program: ${trialData.programName || 'N/A'}
Entries: ${trialData.entries?.length || 0}
Locations: ${trialData.locations?.length || 0}
Observations: ${JSON.stringify(trialData.observations || [], null, 2)}`

    return this.summarize(text, {
      type: 'key-points',
      length: 'medium',
      context: 'Summarize key findings from this breeding trial'
    })
  }

  /**
   * Generate headline for germplasm
   */
  async generateGermplasmHeadline(germplasm: any): Promise<string> {
    const text = `Germplasm: ${germplasm.germplasmName}
Species: ${germplasm.genus} ${germplasm.species}
Origin: ${germplasm.countryOfOriginCode || 'Unknown'}
Attributes: ${JSON.stringify(germplasm.attributes || [])}`

    return this.summarize(text, { type: 'headline', length: 'short' })
  }

  // ============================================
  // TRANSLATOR API (Chrome 138 Stable)
  // ============================================

  /**
   * Translate text between languages
   */
  async translate(
    text: string,
    sourceLanguage: string,
    targetLanguage: string
  ): Promise<string> {
    if (!window.ai?.translator) {
      throw new Error('Translator API not available. Requires Chrome 138+')
    }

    const key = `${sourceLanguage}-${targetLanguage}`
    
    if (!this.sessions.translator?.has(key)) {
      const session = await window.ai.translator.create({
        sourceLanguage,
        targetLanguage
      })
      this.sessions.translator?.set(key, session)
    }

    return this.sessions.translator!.get(key)!.translate(text)
  }

  /**
   * Auto-translate with language detection
   */
  async autoTranslate(text: string, targetLanguage: string = 'en'): Promise<string> {
    const detected = await this.detectLanguage(text)
    if (detected.language === targetLanguage) {
      return text // Already in target language
    }
    return this.translate(text, detected.language, targetLanguage)
  }

  // ============================================
  // LANGUAGE DETECTOR API (Chrome 138 Stable)
  // ============================================

  /**
   * Detect the language of input text
   */
  async detectLanguage(text: string): Promise<{ language: string; confidence: number }> {
    if (!window.ai?.languageDetector) {
      throw new Error('Language Detector API not available. Requires Chrome 138+')
    }

    if (!this.sessions.languageDetector) {
      this.sessions.languageDetector = await window.ai.languageDetector.create()
    }

    const results = await this.sessions.languageDetector.detect(text)
    const top = results[0] || { detectedLanguage: 'en', confidence: 0 }
    
    return {
      language: top.detectedLanguage,
      confidence: top.confidence
    }
  }

  // ============================================
  // WRITER API (Origin Trial)
  // ============================================

  /**
   * Generate new content based on a task description
   */
  async write(
    task: string,
    options?: {
      tone?: 'formal' | 'neutral' | 'casual'
      length?: 'short' | 'medium' | 'long'
      context?: string
    }
  ): Promise<string> {
    if (!window.ai?.writer) {
      throw new Error('Writer API not available. Requires Chrome origin trial enrollment')
    }

    if (!this.sessions.writer) {
      this.sessions.writer = await window.ai.writer.create({
        tone: options?.tone || 'formal',
        format: 'markdown',
        length: options?.length || 'medium',
        sharedContext: 'Plant breeding and agricultural research'
      })
    }

    return this.sessions.writer.write(task, { context: options?.context })
  }

  /**
   * Generate a breeding report
   */
  async generateBreedingReport(data: {
    program: string
    season: string
    trials: number
    topPerformers: string[]
    recommendations: string[]
  }): Promise<string> {
    const task = `Write a professional breeding program report for ${data.program} covering the ${data.season} season. 
Include ${data.trials} trials conducted.
Top performers: ${data.topPerformers.join(', ')}.
Key recommendations: ${data.recommendations.join('; ')}.`

    return this.write(task, { tone: 'formal', length: 'long' })
  }

  // ============================================
  // REWRITER API (Origin Trial)
  // ============================================

  /**
   * Rewrite text with different tone or length
   */
  async rewrite(
    text: string,
    options?: {
      tone?: 'as-is' | 'more-formal' | 'more-casual'
      length?: 'as-is' | 'shorter' | 'longer'
      context?: string
    }
  ): Promise<string> {
    if (!window.ai?.rewriter) {
      throw new Error('Rewriter API not available. Requires Chrome origin trial enrollment')
    }

    if (!this.sessions.rewriter) {
      this.sessions.rewriter = await window.ai.rewriter.create({
        tone: options?.tone || 'as-is',
        format: 'markdown',
        length: options?.length || 'as-is',
        sharedContext: 'Plant breeding and agricultural research'
      })
    }

    return this.sessions.rewriter.rewrite(text, { context: options?.context })
  }

  /**
   * Simplify technical breeding description for non-experts
   */
  async simplifyForNonExperts(technicalText: string): Promise<string> {
    return this.rewrite(technicalText, {
      tone: 'more-casual',
      length: 'shorter',
      context: 'Simplify this technical breeding description for farmers and non-scientists'
    })
  }

  // ============================================
  // PROOFREADER API (Origin Trial)
  // ============================================

  /**
   * Proofread text for grammar and spelling
   */
  async proofread(text: string): Promise<{
    correctedText: string
    corrections: Array<{
      original: string
      replacement: string
      type: string
    }>
  }> {
    if (!window.ai?.proofreader) {
      throw new Error('Proofreader API not available. Requires Chrome origin trial enrollment')
    }

    if (!this.sessions.proofreader) {
      this.sessions.proofreader = await window.ai.proofreader.create()
    }

    const result = await this.sessions.proofreader.proofread(text)
    
    // Apply corrections to get corrected text
    let correctedText = text
    const sortedCorrections = [...result.corrections].sort((a, b) => b.start - a.start)
    
    for (const correction of sortedCorrections) {
      correctedText = 
        correctedText.slice(0, correction.start) + 
        correction.replacement + 
        correctedText.slice(correction.end)
    }

    return {
      correctedText,
      corrections: result.corrections.map(c => ({
        original: c.original,
        replacement: c.replacement,
        type: c.type
      }))
    }
  }

  // ============================================
  // PROMPT API (Origin Trial for Web, Stable for Extensions)
  // ============================================

  /**
   * Send a natural language prompt to Gemini Nano
   */
  async prompt(
    input: string,
    options?: {
      systemPrompt?: string
      temperature?: number
    }
  ): Promise<string> {
    if (!window.ai?.languageModel) {
      throw new Error('Prompt API not available. Requires Chrome origin trial enrollment')
    }

    if (!this.sessions.languageModel) {
      this.sessions.languageModel = await window.ai.languageModel.create({
        systemPrompt: options?.systemPrompt || 
          'You are a helpful plant breeding assistant. Provide concise, accurate information about breeding, genetics, and agricultural research.',
        temperature: options?.temperature || 0.7
      })
    }

    return this.sessions.languageModel.prompt(input)
  }

  /**
   * Ask a breeding-related question
   */
  async askBreedingQuestion(question: string): Promise<string> {
    return this.prompt(question, {
      systemPrompt: `You are an expert plant breeding assistant. Answer questions about:
- Breeding methods and strategies
- Genetic concepts and inheritance
- Trial design and analysis
- Selection criteria and indices
- Germplasm management
Provide practical, actionable advice.`
    })
  }

  // ============================================
  // UTILITY METHODS
  // ============================================

  /**
   * Destroy all active sessions to free resources
   */
  destroyAllSessions(): void {
    this.sessions.languageModel?.destroy()
    this.sessions.summarizer?.destroy()
    this.sessions.writer?.destroy()
    this.sessions.rewriter?.destroy()
    this.sessions.languageDetector?.destroy()
    this.sessions.proofreader?.destroy()
    this.sessions.translator?.forEach(t => t.destroy())
    
    this.sessions = { translator: new Map() }
  }

  /**
   * Get human-readable API status
   */
  getStatusDescription(status: AICapabilityAvailability | 'unavailable'): string {
    switch (status) {
      case 'readily': return '✅ Ready to use'
      case 'after-download': return '⏳ Available after model download'
      case 'no': return '❌ Not supported on this device'
      case 'unavailable': return '⚪ API not available'
      default: return '❓ Unknown'
    }
  }
}

export const chromeAI = new ChromeAIService()
