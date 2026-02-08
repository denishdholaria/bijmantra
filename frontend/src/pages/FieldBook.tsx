/**
 * Field Book Page
 * Digital field book for data collection with Field Mode support
 * Optimized for outdoor use with large touch targets and high contrast
 */
import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { FieldNumberInput } from '@/components/field/FieldNumberInput'
import { FieldPlotNavigator } from '@/components/field/FieldPlotNavigator'
import { useFieldMode, useIsFieldMode } from '@/hooks/useFieldMode'
import { toast } from 'sonner'
import { ChevronLeft, ChevronRight, Save, Sun, Grid3X3, BarChart3, Clipboard } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface FieldEntry {
  plotId: string
  germplasm: string
  rep: string
  row: number
  col: number
  traits: Record<string, string | number>
}

interface Trait {
  id: string
  name: string
  unit: string
  min: number
  max: number
  step: number
}

export function FieldBook() {
  const [selectedStudyId, setSelectedStudyId] = useState<string>('STD-001')
  const [selectedTrait, setSelectedTrait] = useState<string>('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const isFieldMode = useIsFieldMode()
  const { triggerHaptic } = useFieldMode()
  const queryClient = useQueryClient()

  // Fetch studies
  const { data: studiesData, isLoading: studiesLoading } = useQuery({
    queryKey: ['field-book-studies'],
    queryFn: () => apiClient.fieldBookService.getStudies(),
  })

  // Fetch entries for selected study
  const { data: entriesData, isLoading: entriesLoading } = useQuery({
    queryKey: ['field-book-entries', selectedStudyId],
    queryFn: () => apiClient.fieldBookService.getStudyEntries(selectedStudyId),
    enabled: !!selectedStudyId,
  })

  // Fetch traits for selected study
  const { data: traitsData } = useQuery({
    queryKey: ['field-book-traits', selectedStudyId],
    queryFn: () => apiClient.fieldBookService.getStudyTraits(selectedStudyId),
    enabled: !!selectedStudyId,
  })

  // Fetch progress
  const { data: progressData } = useQuery({
    queryKey: ['field-book-progress', selectedStudyId],
    queryFn: () => apiClient.fieldBookService.getProgress(selectedStudyId),
    enabled: !!selectedStudyId,
  })

  // Record observation mutation
  const recordObservationMutation = useMutation({
    mutationFn: (data: { studyId: string; plotId: string; traitId: string; value: any }) =>
      apiClient.fieldBookService.recordObservation({
        study_id: data.studyId,
        plot_id: data.plotId,
        trait_id: data.traitId,
        value: data.value,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field-book-entries', selectedStudyId] })
      queryClient.invalidateQueries({ queryKey: ['field-book-progress', selectedStudyId] })
    },
  })

  const studies = studiesData?.studies || []
  const traits: Trait[] = (traitsData?.traits || []).map((t: any) => ({
    id: t.id,
    name: t.name,
    unit: t.unit || '',
    min: t.min || 0,
    max: t.max || 1000,
    step: t.step || 1,
  }))

  // Set default trait when traits load
  useEffect(() => {
    if (traits.length > 0 && !selectedTrait) {
      setSelectedTrait(traits[0].id)
    }
  }, [traits, selectedTrait])

  const entries: FieldEntry[] = (entriesData?.entries || []).map((e: any) => ({
    plotId: e.plot_id,
    germplasm: e.germplasm,
    rep: e.rep,
    row: e.row,
    col: e.col,
    traits: e.traits || {},
  }))

  const currentEntry = entries[currentIndex] || { plotId: '', germplasm: '', rep: '', row: 0, col: 0, traits: {} }
  
  const selectedTraitObj = traits.find(t => t.id === selectedTrait)
  const traitName = selectedTraitObj?.name || selectedTrait

  const completedCount = entries.filter(e => e.traits[selectedTrait] !== '' && e.traits[selectedTrait] !== null && e.traits[selectedTrait] !== undefined).length
  const progress = entries.length > 0 ? (completedCount / entries.length) * 100 : 0

  const updateValue = useCallback((value: string | number | null) => {
    if (!currentEntry.plotId || !selectedTrait) return
    
    recordObservationMutation.mutate({
      studyId: selectedStudyId,
      plotId: currentEntry.plotId,
      traitId: selectedTrait,
      value: value ?? '',
    })
    triggerHaptic(30)
  }, [currentEntry.plotId, selectedTrait, selectedStudyId, recordObservationMutation, triggerHaptic])

  const goNext = useCallback(() => {
    if (currentIndex < entries.length - 1) {
      setCurrentIndex(currentIndex + 1)
      triggerHaptic(50)
    } else {
      toast.success('Reached end of field book')
    }
  }, [currentIndex, entries.length, triggerHaptic])

  const goPrev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      triggerHaptic(50)
    }
  }, [currentIndex, triggerHaptic])

  const saveData = useCallback(() => {
    toast.success(`Saved ${completedCount} observations for ${traitName}`)
    triggerHaptic([50, 50, 50])
  }, [completedCount, traitName, triggerHaptic])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault()
        goNext()
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        goPrev()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [goNext, goPrev])

  // Get trait config for validation
  const getTraitConfig = (traitId: string) => {
    const trait = traits.find(t => t.id === traitId)
    if (trait) {
      return { min: trait.min, max: trait.max, step: trait.step, unit: trait.unit }
    }
    return { min: 0, max: 1000, step: 1, unit: '' }
  }

  const traitConfig = getTraitConfig(selectedTrait)

  if (studiesLoading || entriesLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Field Book</h1>
            <p className="text-muted-foreground mt-1">Digital data collection</p>
          </div>
        </div>
        <Card><CardContent className="pt-4"><Skeleton className="h-16" /></CardContent></Card>
        <Card><CardContent className="pt-4"><Skeleton className="h-64" /></CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Field Book</h1>
          <p className="text-muted-foreground mt-1">Digital data collection</p>
        </div>
        <Button onClick={saveData} size={isFieldMode ? 'field' : 'default'}>
          <Save className="h-4 w-4 mr-2" />
          Save All
        </Button>
      </div>

      <Tabs defaultValue="collect">
        <TabsList className={isFieldMode ? 'h-14' : ''}>
          <TabsTrigger value="collect" className={isFieldMode ? 'h-12 px-6 text-base' : ''}>
            <Clipboard className="h-4 w-4 mr-2" />
            Collect
          </TabsTrigger>
          <TabsTrigger value="grid" className={isFieldMode ? 'h-12 px-6 text-base' : ''}>
            <Grid3X3 className="h-4 w-4 mr-2" />
            Grid
          </TabsTrigger>
          <TabsTrigger value="summary" className={isFieldMode ? 'h-12 px-6 text-base' : ''}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Summary
          </TabsTrigger>
        </TabsList>

        <TabsContent value="collect" className="space-y-4 mt-4">
          {/* Trait Selection */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
                <div className="flex-1 space-y-2 w-full sm:w-auto">
                  <Label className={isFieldMode ? 'text-lg' : ''}>Trait</Label>
                  <Select value={selectedTrait} onValueChange={setSelectedTrait}>
                    <SelectTrigger className={isFieldMode ? 'h-14 text-lg' : ''}>
                      <SelectValue placeholder="Select trait" />
                    </SelectTrigger>
                    <SelectContent>
                      {traits.map(t => (
                        <SelectItem key={t.id} value={t.id} className={isFieldMode ? 'h-12 text-lg' : ''}>
                          {t.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1 w-full sm:w-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-muted-foreground ${isFieldMode ? 'text-base' : 'text-sm'}`}>
                      Progress
                    </span>
                    <span className={`font-bold ${isFieldMode ? 'text-lg' : 'text-sm'}`}>
                      {completedCount}/{entries.length}
                    </span>
                  </div>
                  <Progress value={progress} className={isFieldMode ? 'h-4' : 'h-2'} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Entry Card - Field Mode Optimized */}
          <Card className="border-2 border-primary">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className={isFieldMode ? 'text-2xl' : ''}>{currentEntry.plotId}</CardTitle>
                  <CardDescription className={isFieldMode ? 'text-lg' : ''}>{currentEntry.germplasm}</CardDescription>
                </div>
                <Badge className={isFieldMode ? 'text-lg px-4 py-2' : ''}>{currentEntry.rep}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className={`grid grid-cols-2 gap-4 ${isFieldMode ? 'text-lg' : 'text-sm'}`}>
                <div className="p-3 bg-muted rounded-lg text-center">
                  <span className="text-muted-foreground">Row</span>
                  <span className="font-bold ml-2">{currentEntry.row}</span>
                </div>
                <div className="p-3 bg-muted rounded-lg text-center">
                  <span className="text-muted-foreground">Col</span>
                  <span className="font-bold ml-2">{currentEntry.col}</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label className={isFieldMode ? 'text-xl' : 'text-lg'}>
                  {traitName}
                  {traitConfig.unit && (
                    <span className="text-muted-foreground ml-2">({traitConfig.unit})</span>
                  )}
                </Label>
                
                {isFieldMode ? (
                  <FieldNumberInput
                    value={Number(currentEntry.traits[selectedTrait]) || null}
                    onChange={(val) => updateValue(val)}
                    min={traitConfig.min}
                    max={traitConfig.max}
                    step={traitConfig.step}
                    unit={traitConfig.unit}
                    autoFocus
                  />
                ) : (
                  <Input
                    type="number"
                    value={currentEntry.traits[selectedTrait] || ''}
                    onChange={(e) => updateValue(e.target.value)}
                    placeholder={`Enter ${traitName}`}
                    className="text-2xl h-16 text-center"
                    min={traitConfig.min}
                    max={traitConfig.max}
                    step={traitConfig.step}
                    autoFocus
                  />
                )}
              </div>

              {/* Navigation */}
              {isFieldMode ? (
                <FieldPlotNavigator
                  plots={entries.map((e, idx) => ({
                    id: e.plotId,
                    name: e.plotId,
                    row: e.row,
                    column: e.col,
                    status: e.traits[selectedTrait] !== '' ? 'complete' as const : 'pending' as const,
                  }))}
                  currentIndex={currentIndex}
                  onNavigate={setCurrentIndex}
                  showProgress
                  enableSwipe
                />
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      onClick={goPrev} 
                      disabled={currentIndex === 0} 
                      className="flex-1 h-12"
                    >
                      <ChevronLeft className="h-5 w-5 mr-1" />
                      Previous
                    </Button>
                    <Button 
                      onClick={goNext} 
                      disabled={currentIndex === entries.length - 1} 
                      className="flex-1 h-12"
                    >
                      Next
                      <ChevronRight className="h-5 w-5 ml-1" />
                    </Button>
                  </div>
                  <div className="text-center text-sm text-muted-foreground">
                    Entry {currentIndex + 1} of {entries.length}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Quick Jump - Field Mode */}
          {isFieldMode && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Quick Jump</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2">
                  {entries.slice(0, 9).map((entry, idx) => {
                    const hasValue = entry.traits[selectedTrait] !== ''
                    return (
                      <Button
                        key={entry.plotId}
                        variant={idx === currentIndex ? 'default' : hasValue ? 'secondary' : 'outline'}
                        size="field"
                        onClick={() => {
                          setCurrentIndex(idx)
                          triggerHaptic(30)
                        }}
                        className="h-14"
                      >
                        {entry.plotId}
                        {hasValue && <span className="ml-1">✓</span>}
                      </Button>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="grid" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Grid View - {traitName}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className={`p-2 text-left ${isFieldMode ? 'text-base p-3' : ''}`}>Plot</th>
                      <th className={`p-2 text-left ${isFieldMode ? 'text-base p-3' : ''}`}>Germplasm</th>
                      <th className={`p-2 text-left ${isFieldMode ? 'text-base p-3' : ''}`}>Rep</th>
                      <th className={`p-2 text-right ${isFieldMode ? 'text-base p-3' : ''}`}>{traitName}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry, i) => (
                      <tr 
                        key={entry.plotId} 
                        className={`border-b cursor-pointer hover:bg-muted/50 ${i === currentIndex ? 'bg-primary/10' : ''} ${isFieldMode ? 'h-14' : ''}`}
                        onClick={() => {
                          setCurrentIndex(i)
                          triggerHaptic(30)
                        }}
                      >
                        <td className={`p-2 font-mono ${isFieldMode ? 'text-base p-3' : ''}`}>{entry.plotId}</td>
                        <td className={`p-2 ${isFieldMode ? 'text-base p-3' : ''}`}>{entry.germplasm}</td>
                        <td className={`p-2 ${isFieldMode ? 'text-base p-3' : ''}`}>{entry.rep}</td>
                        <td className={`p-2 text-right ${isFieldMode ? 'text-base p-3' : ''}`}>
                          {entry.traits[selectedTrait] || <span className="text-muted-foreground">-</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Collection Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {traits.map(trait => {
                  const collected = entries.filter(e => e.traits[trait.id] !== '' && e.traits[trait.id] !== null && e.traits[trait.id] !== undefined).length
                  const pct = entries.length > 0 ? Math.round((collected / entries.length) * 100) : 0
                  return (
                    <div 
                      key={trait.id} 
                      className={`p-4 bg-muted rounded-lg text-center cursor-pointer hover:bg-muted/80 ${selectedTrait === trait.id ? 'ring-2 ring-primary' : ''}`}
                      onClick={() => setSelectedTrait(trait.id)}
                    >
                      <p className={`font-bold ${isFieldMode ? 'text-3xl' : 'text-2xl'}`}>
                        {collected}/{entries.length}
                      </p>
                      <Progress value={pct} className="h-2 my-2" />
                      <p className={`text-muted-foreground ${isFieldMode ? 'text-base' : 'text-sm'}`}>{trait.name}</p>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default FieldBook
