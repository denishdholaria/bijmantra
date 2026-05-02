import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Copy, Download, Maximize2, Minimize2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TabsContent } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import {
  createDeveloperMasterBoardArielma,
  developerMasterBoardArielmaLensOptions,
  type DeveloperMasterBoardArielmaLens,
} from '@/lib/devMasterBoardArielma'
import type { DeveloperMasterBoard } from '../../contracts/board'

type ArielmaTabProps = {
  parsedBoard: DeveloperMasterBoard | null
  jsonError: string | null
}

type DiagramSourceMode = 'generated' | 'pasted'
type PersistedArielmaDraft = {
  sourceMode: DiagramSourceMode
  pastedSource: string
}

const ARIELMA_DRAFT_STORAGE_KEY = 'bijmantra-dev-arielma-diagram-state'

function readPersistedArielmaDraft(): PersistedArielmaDraft {
  if (typeof window === 'undefined') {
    return { sourceMode: 'generated', pastedSource: '' }
  }

  try {
    const rawDraft = window.localStorage.getItem(ARIELMA_DRAFT_STORAGE_KEY)
    if (!rawDraft) {
      return { sourceMode: 'generated', pastedSource: '' }
    }

    const parsedDraft = JSON.parse(rawDraft) as Partial<PersistedArielmaDraft>
    return {
      sourceMode: parsedDraft.sourceMode === 'pasted' ? 'pasted' : 'generated',
      pastedSource: typeof parsedDraft.pastedSource === 'string' ? parsedDraft.pastedSource : '',
    }
  } catch {
    return { sourceMode: 'generated', pastedSource: '' }
  }
}

function persistArielmaDraft(draft: PersistedArielmaDraft) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(ARIELMA_DRAFT_STORAGE_KEY, JSON.stringify(draft))
  } catch {
    return
  }
}

function slugifyFilenamePart(value: string) {
  const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return slug || 'diagram'
}

function buildSvgExportFilename(sourceMode: DiagramSourceMode, lens: DeveloperMasterBoardArielmaLens) {
  if (sourceMode === 'generated') {
    return `bijmantra-developer-control-plane-${slugifyFilenamePart(lens)}.svg`
  }

  return 'bijmantra-arielma-preview.svg'
}

export function ArielmaTab({ parsedBoard, jsonError }: ArielmaTabProps) {
  const previewSurfaceId = useId()
  const previewSurfaceRef = useRef<HTMLDivElement | null>(null)
  const diagramContainerRef = useRef<HTMLDivElement | null>(null)
  const [lens, setLens] = useState<DeveloperMasterBoardArielmaLens>('system-topology')
  const [sourceMode, setSourceMode] = useState<DiagramSourceMode>(() => readPersistedArielmaDraft().sourceMode)
  const [pastedSource, setPastedSource] = useState(() => readPersistedArielmaDraft().pastedSource)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [copyState, setCopyState] = useState<'idle' | 'copied'>('idle')
  const [exportState, setExportState] = useState<'idle' | 'exported'>('idle')
  const [renderState, setRenderState] = useState<'idle' | 'rendering' | 'ready' | 'error'>('idle')
  const [renderError, setRenderError] = useState<string | null>(null)
  const [renderedSvg, setRenderedSvg] = useState<string>('')

  const selectedLens = developerMasterBoardArielmaLensOptions.find((option) => option.value === lens) ?? developerMasterBoardArielmaLensOptions[0]
  const isGeneratedMode = sourceMode === 'generated'
  const arielmaSource = useMemo(() => {
    if (!parsedBoard) {
      return ''
    }

    return createDeveloperMasterBoardArielma(parsedBoard, lens)
  }, [parsedBoard, lens])
  const previewSource = isGeneratedMode ? arielmaSource : pastedSource
  const sourceSummary = isGeneratedMode
    ? {
        title: selectedLens.label,
        description: selectedLens.description,
      }
    : {
        title: 'Pasted diagram code',
        description: 'Paste diagram code to preview it here without changing the canonical board.',
      }

  useEffect(() => {
    persistArielmaDraft({ sourceMode, pastedSource })
  }, [pastedSource, sourceMode])

  useEffect(() => {
    if (typeof document === 'undefined') {
      return undefined
    }

    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === previewSurfaceRef.current)
    }

    handleFullscreenChange()
    document.addEventListener('fullscreenchange', handleFullscreenChange)

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  useEffect(() => {
    if (!diagramContainerRef.current) {
      return
    }

    if ((isGeneratedMode && (!parsedBoard || jsonError)) || !previewSource.trim()) {
      diagramContainerRef.current.innerHTML = ''
      setRenderState('idle')
      setRenderError(null)
      setRenderedSvg('')
      return
    }

    let cancelled = false

    const renderDiagram = async () => {
      setRenderState('rendering')
      setRenderError(null)

      try {
        const arielmaModule = await import('arielma')
        const arielma = arielmaModule.default
        arielma.initialize({
          startOnLoad: false,
          securityLevel: 'strict',
          theme: 'base',
          deterministicIds: true,
          fontFamily: 'ui-sans-serif, system-ui, sans-serif',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis',
          },
          themeVariables: {
            primaryColor: '#163b72',
            primaryTextColor: '#eff6ff',
            primaryBorderColor: '#93c5fd',
            lineColor: '#dbeafe',
            secondaryColor: '#0f766e',
            tertiaryColor: '#082f6b',
            background: '#0b3d91',
            mainBkg: '#163b72',
            nodeBorder: '#93c5fd',
          },
        })

        const { svg, bindFunctions } = await arielma.render(
          `bijmantra-arielma-${previewSurfaceId.replace(/:/g, '-')}`,
          previewSource
        )
        if (cancelled || !diagramContainerRef.current) {
          return
        }

        diagramContainerRef.current.innerHTML = svg
        bindFunctions?.(diagramContainerRef.current)
        setRenderedSvg(svg)
        setRenderState('ready')
      } catch (error) {
        if (cancelled) {
          return
        }

        setRenderState('error')
        setRenderError(error instanceof Error ? error.message : 'Unable to render diagram preview')
        setRenderedSvg('')
      }
    }

    void renderDiagram()

    return () => {
      cancelled = true
    }
  }, [isGeneratedMode, jsonError, parsedBoard, previewSource, previewSurfaceId])

  const toggleFullscreen = async () => {
    if (typeof document === 'undefined') {
      return
    }

    const previewSurface = previewSurfaceRef.current
    if (!previewSurface) {
      return
    }

    if (document.fullscreenElement === previewSurface) {
      await document.exitFullscreen()
      return
    }

    await previewSurface.requestFullscreen()
  }

  const handleCopySource = async () => {
    if (!previewSource || typeof navigator === 'undefined' || !navigator.clipboard) {
      return
    }

    await navigator.clipboard.writeText(previewSource)
    setCopyState('copied')
    window.setTimeout(() => setCopyState('idle'), 1600)
  }

  const handleExportSvg = () => {
    if (!renderedSvg || typeof window === 'undefined' || typeof document === 'undefined') {
      return
    }

    const blob = new Blob([renderedSvg], { type: 'image/svg+xml;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = buildSvgExportFilename(sourceMode, lens)
    anchor.click()
    window.URL.revokeObjectURL(url)
    setExportState('exported')
    window.setTimeout(() => setExportState('idle'), 1600)
  }

  return (
    <TabsContent value="arielma" className="space-y-4">
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-1">
              <CardTitle>Diagram View</CardTitle>
              <CardDescription>
                Generate control-plane diagrams from the same canonical JSON without replacing the native graph canvas.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex items-center rounded-2xl border border-slate-200 bg-white/80 p-1 dark:border-slate-800 dark:bg-slate-950/50">
                <Button
                  type="button"
                  variant={isGeneratedMode ? 'secondary' : 'ghost'}
                  size="sm"
                  aria-pressed={isGeneratedMode}
                  onClick={() => setSourceMode('generated')}
                >
                  Board source
                </Button>
                <Button
                  type="button"
                  variant={!isGeneratedMode ? 'secondary' : 'ghost'}
                  size="sm"
                  aria-pressed={!isGeneratedMode}
                  onClick={() => setSourceMode('pasted')}
                >
                  Paste code
                </Button>
              </div>
              {isGeneratedMode ? (
                <Select value={lens} onValueChange={(value) => setLens(value as DeveloperMasterBoardArielmaLens)}>
                  <SelectTrigger className="w-[15rem]" aria-label="Select diagram lens">
                    <SelectValue placeholder="Select lens" />
                  </SelectTrigger>
                  <SelectContent>
                    {developerMasterBoardArielmaLensOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : null}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => void handleCopySource()}
                disabled={!previewSource.trim()}
              >
                <Copy className="h-4 w-4" />
                <span>{copyState === 'copied' ? 'Copied' : 'Copy source'}</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={handleExportSvg}
                disabled={!renderedSvg || renderState !== 'ready'}
              >
                <Download className="h-4 w-4" />
                <span>{exportState === 'exported' ? 'SVG exported' : 'Export SVG'}</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-2"
                aria-controls={previewSurfaceId}
                aria-label={isFullscreen ? 'Exit diagram fullscreen' : 'Enter diagram fullscreen'}
                onClick={() => {
                  void toggleFullscreen()
                }}
              >
                {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                <span>{isFullscreen ? 'Exit Full Screen' : 'Full Screen'}</span>
              </Button>
            </div>
          </div>
          <div className="rounded-2xl border border-sky-200/70 bg-sky-50/80 px-4 py-3 text-sm text-sky-900 dark:border-sky-900/40 dark:bg-sky-950/20 dark:text-sky-100">
            <div className="font-medium">{sourceSummary.title}</div>
            <div className="mt-1 text-sky-800/90 dark:text-sky-100/80">{sourceSummary.description}</div>
          </div>
        </CardHeader>
        <CardContent>
          {isGeneratedMode && jsonError ? (
            <div className="rounded-2xl border border-rose-300/60 bg-rose-50 px-4 py-3 text-sm text-rose-900 dark:border-rose-900/40 dark:bg-rose-950/20 dark:text-rose-100">
              Diagram views derive from the canonical board JSON. Fix the JSON tab error first before generating diagrams.
            </div>
          ) : isGeneratedMode && !parsedBoard ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-300">
              Diagram view is waiting for a valid board payload.
            </div>
          ) : (
            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.9fr)]">
              <div
                id={previewSurfaceId}
                ref={previewSurfaceRef}
                data-testid="arielma-preview-surface"
                className={cn(
                  'overflow-hidden rounded-2xl border border-sky-200/70 bg-[radial-gradient(circle_at_top,rgba(125,211,252,0.22),transparent_40%),linear-gradient(180deg,rgba(14,116,144,0.18),transparent_22%),linear-gradient(135deg,#0f4aa3,#0b3d91_58%,#082f6b)] shadow-[inset_0_1px_0_rgba(255,255,255,0.18)] dark:border-sky-300/20',
                  isFullscreen ? 'h-[100dvh] rounded-none border-0' : 'min-h-[46rem]'
                )}
              >
                <div className="flex h-full flex-col">
                  <div className="border-b border-white/10 px-4 py-3 text-sm text-slate-100/90">
                    {isGeneratedMode
                      ? 'Diagram preview derived from the canonical control-plane board.'
                      : 'Diagram preview from pasted code.'}
                  </div>
                  <div className="relative min-h-0 flex-1 overflow-auto p-4">
                    {renderState === 'rendering' && previewSource.trim() && (
                      <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-slate-100/80">
                        Rendering diagram...
                      </div>
                    )}
                    {renderState === 'error' ? (
                      <div className="flex h-full min-h-[24rem] items-center justify-center px-6 text-center text-sm text-rose-100">
                        {renderError ?? 'Unable to render diagram preview'}
                      </div>
                    ) : !previewSource.trim() ? (
                      <div className="flex h-full min-h-[24rem] items-center justify-center px-6 text-center text-sm text-slate-100/80">
                        Paste diagram code to preview it here.
                      </div>
                    ) : (
                      <div
                        ref={diagramContainerRef}
                        data-testid="arielma-diagram-preview"
                        className="flex min-h-[40rem] items-center justify-center [&_svg]:h-auto [&_svg]:max-h-none [&_svg]:max-w-full"
                      />
                    )}
                  </div>
                </div>
              </div>

              <Card className="border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-950/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Diagram Source</CardTitle>
                  <CardDescription>
                    {isGeneratedMode
                      ? 'This source is generated from the same canonical board JSON. Edit the planner or JSON tabs to change it.'
                      : 'Paste diagram code here to preview it without changing the canonical board.'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <textarea
                    readOnly={isGeneratedMode}
                    value={previewSource}
                    onChange={isGeneratedMode ? undefined : (event) => setPastedSource(event.target.value)}
                    placeholder={isGeneratedMode ? undefined : 'Paste diagram code here to preview it.'}
                    className="h-[46rem] w-full resize-none rounded-2xl border border-slate-200 bg-white/90 p-4 font-mono text-xs leading-6 text-slate-900 shadow-sm outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100"
                    aria-label={isGeneratedMode ? 'Generated diagram source' : 'Editable diagram source'}
                    spellCheck={false}
                  />
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  )
}