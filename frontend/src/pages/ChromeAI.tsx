/**
 * Chrome AI Page
 * Showcase Chrome's Built-in AI capabilities (Gemini Nano)
 * 
 * Features:
 * - Summarizer: Condense trial results, germplasm descriptions
 * - Translator: Multi-language support for international programs
 * - Language Detector: Auto-detect input language
 * - Writer: Generate breeding reports
 * - Rewriter: Simplify technical content
 * - Proofreader: Check notes and comments
 */
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'
import { chromeAI, ChromeAIStatus } from '@/lib/chrome-ai'

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'hi', name: 'Hindi' },
  { code: 'ar', name: 'Arabic' },
]

export function ChromeAI() {
  const [status, setStatus] = useState<ChromeAIStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)

  // Summarizer state
  const [summaryInput, setSummaryInput] = useState('')
  const [summaryType, setSummaryType] = useState<'key-points' | 'tl;dr' | 'headline'>('key-points')
  const [summaryOutput, setSummaryOutput] = useState('')

  // Translator state
  const [translateInput, setTranslateInput] = useState('')
  const [sourceLang, setSourceLang] = useState('en')
  const [targetLang, setTargetLang] = useState('es')
  const [translateOutput, setTranslateOutput] = useState('')
  const [detectedLang, setDetectedLang] = useState<{ language: string; confidence: number } | null>(null)

  // Writer state
  const [writeTask, setWriteTask] = useState('')
  const [writeTone, setWriteTone] = useState<'formal' | 'neutral' | 'casual'>('formal')
  const [writeOutput, setWriteOutput] = useState('')

  // Rewriter state
  const [rewriteInput, setRewriteInput] = useState('')
  const [rewriteTone, setRewriteTone] = useState<'as-is' | 'more-formal' | 'more-casual'>('more-casual')
  const [rewriteOutput, setRewriteOutput] = useState('')

  // Proofreader state
  const [proofInput, setProofInput] = useState('')
  const [proofOutput, setProofOutput] = useState<{ correctedText: string; corrections: any[] } | null>(null)

  // Prompt state
  const [promptInput, setPromptInput] = useState('')
  const [promptOutput, setPromptOutput] = useState('')

  useEffect(() => {
    checkStatus()
    return () => chromeAI.destroyAllSessions()
  }, [])

  const checkStatus = async () => {
    setLoading(true)
    try {
      const s = await chromeAI.getStatus()
      setStatus(s)
    } catch (error) {
      console.error('Failed to check Chrome AI status:', error)
    }
    setLoading(false)
  }

  const handleSummarize = async () => {
    if (!summaryInput.trim()) {
      toast.error('Please enter text to summarize')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.summarize(summaryInput, { type: summaryType })
      setSummaryOutput(result)
      toast.success('Summary generated!')
    } catch (error: any) {
      toast.error(error.message || 'Summarization failed')
    }
    setProcessing(false)
  }

  const handleTranslate = async () => {
    if (!translateInput.trim()) {
      toast.error('Please enter text to translate')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.translate(translateInput, sourceLang, targetLang)
      setTranslateOutput(result)
      toast.success('Translation complete!')
    } catch (error: any) {
      toast.error(error.message || 'Translation failed')
    }
    setProcessing(false)
  }

  const handleDetectLanguage = async () => {
    if (!translateInput.trim()) {
      toast.error('Please enter text to detect language')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.detectLanguage(translateInput)
      setDetectedLang(result)
      setSourceLang(result.language)
      toast.success(`Detected: ${result.language} (${(result.confidence * 100).toFixed(0)}% confidence)`)
    } catch (error: any) {
      toast.error(error.message || 'Language detection failed')
    }
    setProcessing(false)
  }

  const handleWrite = async () => {
    if (!writeTask.trim()) {
      toast.error('Please describe what to write')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.write(writeTask, { tone: writeTone })
      setWriteOutput(result)
      toast.success('Content generated!')
    } catch (error: any) {
      toast.error(error.message || 'Writing failed')
    }
    setProcessing(false)
  }

  const handleRewrite = async () => {
    if (!rewriteInput.trim()) {
      toast.error('Please enter text to rewrite')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.rewrite(rewriteInput, { tone: rewriteTone })
      setRewriteOutput(result)
      toast.success('Text rewritten!')
    } catch (error: any) {
      toast.error(error.message || 'Rewriting failed')
    }
    setProcessing(false)
  }

  const handleProofread = async () => {
    if (!proofInput.trim()) {
      toast.error('Please enter text to proofread')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.proofread(proofInput)
      setProofOutput(result)
      toast.success(`Found ${result.corrections.length} corrections`)
    } catch (error: any) {
      toast.error(error.message || 'Proofreading failed')
    }
    setProcessing(false)
  }

  const handlePrompt = async () => {
    if (!promptInput.trim()) {
      toast.error('Please enter a question')
      return
    }
    setProcessing(true)
    try {
      const result = await chromeAI.askBreedingQuestion(promptInput)
      setPromptOutput(result)
      toast.success('Response received!')
    } catch (error: any) {
      toast.error(error.message || 'Prompt failed')
    }
    setProcessing(false)
  }

  const getStatusBadge = (apiStatus: string) => {
    switch (apiStatus) {
      case 'readily':
        return <Badge className="bg-green-100 text-green-700">✅ Ready</Badge>
      case 'after-download':
        return <Badge className="bg-yellow-100 text-yellow-700">⏳ Download Required</Badge>
      case 'no':
        return <Badge className="bg-red-100 text-red-700">❌ Not Supported</Badge>
      default:
        return <Badge variant="secondary">⚪ Unavailable</Badge>
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🔄</div>
          <p>Checking Chrome AI availability...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Chrome Built-in AI</h1>
          <p className="text-muted-foreground mt-1">Local AI powered by Gemini Nano</p>
        </div>
        <div className="flex items-center gap-2">
          {status?.isChrome ? (
            <Badge variant="outline">Chrome {status.version}</Badge>
          ) : (
            <Badge variant="destructive">Not Chrome</Badge>
          )}
          <Button variant="outline" size="sm" onClick={checkStatus}>
            🔄 Refresh Status
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <Card className={status?.isChrome && status.version >= 138 ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'}>
        <CardContent className="pt-4">
          <div className="flex gap-3">
            <span className="text-2xl">{status?.isChrome && status.version >= 138 ? '🚀' : '⚠️'}</span>
            <div className="flex-1">
              <p className="font-medium">
                {status?.isChrome && status.version >= 138 
                  ? 'Chrome Built-in AI Available!' 
                  : 'Chrome 138+ Required'}
              </p>
              <p className="text-sm text-muted-foreground">
                {status?.isChrome && status.version >= 138 
                  ? 'Your browser supports local AI processing with Gemini Nano. No API keys needed!'
                  : 'Please update to Chrome 138 or later to use built-in AI features.'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Setup Instructions - Show if APIs are unavailable */}
      {status?.isChrome && status.version >= 138 && Object.values(status.apis).every(v => v === 'unavailable') && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-blue-800">⚙️ Setup Required</CardTitle>
            <CardDescription className="text-blue-700">
              Chrome Built-in AI needs to be enabled and the model downloaded
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="space-y-2">
              <p className="font-medium text-blue-800">Step 1: Enable Chrome Flags</p>
              <p className="text-blue-700">Go to <code className="bg-blue-100 px-1 rounded">chrome://flags</code> and enable:</p>
              <ul className="list-disc list-inside text-blue-700 space-y-1 ml-2">
                <li><code className="bg-blue-100 px-1 rounded text-xs">#optimization-guide-on-device-model</code> → Enabled BypassPerfRequirement</li>
                <li><code className="bg-blue-100 px-1 rounded text-xs">#prompt-api-for-gemini-nano</code> → Enabled</li>
                <li><code className="bg-blue-100 px-1 rounded text-xs">#summarization-api-for-gemini-nano</code> → Enabled</li>
                <li><code className="bg-blue-100 px-1 rounded text-xs">#translation-api</code> → Enabled</li>
              </ul>
            </div>
            <div className="space-y-2">
              <p className="font-medium text-blue-800">Step 2: Relaunch Chrome</p>
              <p className="text-blue-700">Click the "Relaunch" button at the bottom of the flags page</p>
            </div>
            <div className="space-y-2">
              <p className="font-medium text-blue-800">Step 3: Download Gemini Nano Model</p>
              <p className="text-blue-700">Go to <code className="bg-blue-100 px-1 rounded">chrome://components</code></p>
              <p className="text-blue-700">Find "Optimization Guide On Device Model" and click "Check for update"</p>
              <p className="text-blue-700 text-xs">(Model is ~1.7GB, download may take a few minutes)</p>
            </div>
            <div className="space-y-2">
              <p className="font-medium text-blue-800">Step 4: Refresh this page</p>
              <p className="text-blue-700">After the model downloads, refresh and click "Refresh Status"</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Status Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {status && Object.entries(status.apis).map(([api, apiStatus]) => (
          <Card key={api} className="text-center">
            <CardContent className="pt-4 pb-3">
              <p className="text-xs font-medium capitalize mb-2">{api.replace(/([A-Z])/g, ' $1').trim()}</p>
              {getStatusBadge(apiStatus)}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Feature Tabs */}
      <Tabs defaultValue="summarizer">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="summarizer">📝 Summarizer</TabsTrigger>
          <TabsTrigger value="translator">🌐 Translator</TabsTrigger>
          <TabsTrigger value="writer">✍️ Writer</TabsTrigger>
          <TabsTrigger value="rewriter">🔄 Rewriter</TabsTrigger>
          <TabsTrigger value="proofreader">✅ Proofreader</TabsTrigger>
          <TabsTrigger value="prompt">💬 Prompt</TabsTrigger>
        </TabsList>

        {/* Summarizer Tab */}
        <TabsContent value="summarizer" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                📝 Summarizer API
                {getStatusBadge(status?.apis.summarizer || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Condense trial results, germplasm descriptions, and research notes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select value={summaryType} onValueChange={(v: any) => setSummaryType(v)}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="key-points">Key Points</SelectItem>
                    <SelectItem value="tl;dr">TL;DR</SelectItem>
                    <SelectItem value="headline">Headline</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                placeholder="Paste trial results, germplasm data, or any text to summarize..."
                value={summaryInput}
                onChange={(e) => setSummaryInput(e.target.value)}
                rows={6}
              />
              <Button onClick={handleSummarize} disabled={processing || status?.apis.summarizer === 'unavailable'}>
                {processing ? '⏳ Processing...' : '📝 Summarize'}
              </Button>
              {summaryOutput && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Summary:</p>
                  <p className="whitespace-pre-wrap">{summaryOutput}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Translator Tab */}
        <TabsContent value="translator" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🌐 Translator & Language Detector
                {getStatusBadge(status?.apis.translator || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Multi-language support for international breeding programs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2 items-center">
                <Select value={sourceLang} onValueChange={setSourceLang}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map(l => (
                      <SelectItem key={l.code} value={l.code}>{l.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <span>→</span>
                <Select value={targetLang} onValueChange={setTargetLang}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map(l => (
                      <SelectItem key={l.code} value={l.code}>{l.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" size="sm" onClick={handleDetectLanguage} disabled={processing}>
                  🔍 Detect Language
                </Button>
                {detectedLang && (
                  <Badge variant="outline">
                    Detected: {detectedLang.language} ({(detectedLang.confidence * 100).toFixed(0)}%)
                  </Badge>
                )}
              </div>
              <Textarea
                placeholder="Enter text to translate..."
                value={translateInput}
                onChange={(e) => setTranslateInput(e.target.value)}
                rows={4}
              />
              <Button onClick={handleTranslate} disabled={processing || status?.apis.translator === 'unavailable'}>
                {processing ? '⏳ Translating...' : '🌐 Translate'}
              </Button>
              {translateOutput && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Translation:</p>
                  <p className="whitespace-pre-wrap">{translateOutput}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Writer Tab */}
        <TabsContent value="writer" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                ✍️ Writer API
                {getStatusBadge(status?.apis.writer || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Generate breeding reports, documentation, and content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select value={writeTone} onValueChange={(v: any) => setWriteTone(v)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Formal</SelectItem>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                placeholder="Describe what you want to write... e.g., 'Write a summary report for the 2024 wheat breeding trial with 50 entries tested across 3 locations'"
                value={writeTask}
                onChange={(e) => setWriteTask(e.target.value)}
                rows={4}
              />
              <Button onClick={handleWrite} disabled={processing || status?.apis.writer === 'unavailable'}>
                {processing ? '⏳ Writing...' : '✍️ Generate'}
              </Button>
              {writeOutput && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Generated Content:</p>
                  <p className="whitespace-pre-wrap">{writeOutput}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rewriter Tab */}
        <TabsContent value="rewriter" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🔄 Rewriter API
                {getStatusBadge(status?.apis.rewriter || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Simplify technical content or adjust tone for different audiences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select value={rewriteTone} onValueChange={(v: any) => setRewriteTone(v)}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="as-is">Keep Tone</SelectItem>
                    <SelectItem value="more-formal">More Formal</SelectItem>
                    <SelectItem value="more-casual">More Casual</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                placeholder="Paste technical breeding text to rewrite for a different audience..."
                value={rewriteInput}
                onChange={(e) => setRewriteInput(e.target.value)}
                rows={4}
              />
              <Button onClick={handleRewrite} disabled={processing || status?.apis.rewriter === 'unavailable'}>
                {processing ? '⏳ Rewriting...' : '🔄 Rewrite'}
              </Button>
              {rewriteOutput && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Rewritten:</p>
                  <p className="whitespace-pre-wrap">{rewriteOutput}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Proofreader Tab */}
        <TabsContent value="proofreader" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                ✅ Proofreader API
                {getStatusBadge(status?.apis.proofreader || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Check notes, comments, and documentation for grammar and spelling
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Enter text to proofread..."
                value={proofInput}
                onChange={(e) => setProofInput(e.target.value)}
                rows={4}
              />
              <Button onClick={handleProofread} disabled={processing || status?.apis.proofreader === 'unavailable'}>
                {processing ? '⏳ Checking...' : '✅ Proofread'}
              </Button>
              {proofOutput && (
                <div className="space-y-3">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium mb-2 text-green-700">Corrected Text:</p>
                    <p className="whitespace-pre-wrap">{proofOutput.correctedText}</p>
                  </div>
                  {proofOutput.corrections.length > 0 && (
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm font-medium mb-2">Corrections ({proofOutput.corrections.length}):</p>
                      <ul className="text-sm space-y-1">
                        {proofOutput.corrections.map((c, i) => (
                          <li key={i}>
                            <span className="line-through text-red-500">{c.original}</span>
                            {' → '}
                            <span className="text-green-600">{c.replacement}</span>
                            <Badge variant="outline" className="ml-2 text-xs">{c.type}</Badge>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Prompt Tab */}
        <TabsContent value="prompt" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                💬 Prompt API
                {getStatusBadge(status?.apis.languageModel || 'unavailable')}
              </CardTitle>
              <CardDescription>
                Ask breeding questions directly to Gemini Nano
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Ask a breeding question... e.g., 'What is the best crossing scheme for improving disease resistance while maintaining yield?'"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                rows={3}
              />
              <Button onClick={handlePrompt} disabled={processing || status?.apis.languageModel === 'unavailable'}>
                {processing ? '⏳ Thinking...' : '💬 Ask'}
              </Button>
              {promptOutput && (
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">Response:</p>
                  <p className="whitespace-pre-wrap">{promptOutput}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Use Cases */}
      <Card>
        <CardHeader>
          <CardTitle>🌱 Breeding Use Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="font-medium text-blue-800">📝 Trial Summaries</p>
              <p className="text-sm text-blue-600">Quickly summarize trial results for reports and presentations</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="font-medium text-green-800">🌐 Multi-Language</p>
              <p className="text-sm text-green-600">Translate breeding data for international collaborations</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="font-medium text-purple-800">✍️ Report Generation</p>
              <p className="text-sm text-purple-600">Generate professional breeding reports automatically</p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="font-medium text-orange-800">🔄 Simplify Content</p>
              <p className="text-sm text-orange-600">Rewrite technical content for farmers and stakeholders</p>
            </div>
            <div className="p-4 bg-pink-50 rounded-lg">
              <p className="font-medium text-pink-800">✅ Quality Check</p>
              <p className="text-sm text-pink-600">Proofread notes and documentation before sharing</p>
            </div>
            <div className="p-4 bg-cyan-50 rounded-lg">
              <p className="font-medium text-cyan-800">💬 Quick Answers</p>
              <p className="text-sm text-cyan-600">Get instant answers to breeding questions</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Privacy Notice */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-4">
          <div className="flex gap-3">
            <span className="text-2xl">🔒</span>
            <div>
              <p className="font-medium text-green-800">100% Private & Local</p>
              <p className="text-sm text-green-700">
                All Chrome Built-in AI processing happens locally on your device using Gemini Nano. 
                Your breeding data never leaves your computer. No API keys required. No cloud costs.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
