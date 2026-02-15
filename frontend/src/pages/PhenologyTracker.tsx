/**
 * Phenology Tracker Page
 * Track plant growth stages and development - Connected to backend API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Plus, Leaf, Calendar, TrendingUp, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'

interface GrowthStage {
  code: number
  name: string
  description: string
  color: string
}

interface PhenologyRecord {
  id: string
  germplasm_id: string
  germplasm_name: string
  study_id: string
  plot_id: string
  sowing_date: string
  current_stage: number
  current_stage_name: string
  expected_maturity: number
  days_from_sowing: number
  crop: string
  observations: { stage: number; stage_name: string; date: string; notes: string }[]
}

const defaultStages: GrowthStage[] = [
  { code: 0, name: 'Germination', description: 'Seed emergence', color: 'bg-yellow-500' },
  { code: 10, name: 'Seedling', description: 'First leaves', color: 'bg-lime-500' },
  { code: 20, name: 'Tillering', description: 'Side shoots', color: 'bg-green-500' },
  { code: 30, name: 'Stem Elongation', description: 'Stem growth', color: 'bg-emerald-500' },
  { code: 40, name: 'Booting', description: 'Flag leaf', color: 'bg-teal-500' },
  { code: 50, name: 'Heading', description: 'Head emergence', color: 'bg-cyan-500' },
  { code: 60, name: 'Flowering', description: 'Anthesis', color: 'bg-blue-500' },
  { code: 70, name: 'Grain Fill', description: 'Grain development', color: 'bg-indigo-500' },
  { code: 80, name: 'Ripening', description: 'Grain maturation', color: 'bg-purple-500' },
  { code: 90, name: 'Maturity', description: 'Harvest ready', color: 'bg-orange-500' },
]

export function PhenologyTracker() {
  const queryClient = useQueryClient()
  const [selectedStudy, setSelectedStudy] = useState<string>('all')
  const [selectedCrop, setSelectedCrop] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isObservationOpen, setIsObservationOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<PhenologyRecord | null>(null)

  // Fetch growth stages
  const { data: stagesData } = useQuery({
    queryKey: ['phenology-stages', selectedCrop],
    queryFn: () => apiClient.phenologyService.getPhenologyGrowthStages(selectedCrop !== 'all' ? selectedCrop : undefined),
  })

  const stages = stagesData?.stages || defaultStages

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['phenology-stats', selectedStudy],
    queryFn: () => apiClient.phenologyService.getPhenologyStats(selectedStudy !== 'all' ? selectedStudy : undefined),
  })

  // Fetch records
  const { data: recordsData, isLoading, error } = useQuery({
    queryKey: ['phenology-records', selectedStudy, selectedCrop],
    queryFn: () => apiClient.phenologyService.getPhenologyRecords({
      study_id: selectedStudy !== 'all' ? selectedStudy : undefined,
      crop: selectedCrop !== 'all' ? selectedCrop : undefined,
      limit: 100,
    }),
  })

  // Create record mutation
  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof apiClient.phenologyService.createPhenologyRecord>[0]) =>
      apiClient.phenologyService.createPhenologyRecord(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phenology-records'] })
      queryClient.invalidateQueries({ queryKey: ['phenology-stats'] })
      setIsCreateOpen(false)
      toast.success('Phenology record created')
    },
    onError: () => toast.error('Failed to create record'),
  })

  // Record observation mutation
  const observationMutation = useMutation({
    mutationFn: ({ recordId, data }: { recordId: string; data: Parameters<typeof apiClient.phenologyService.recordPhenologyObservation>[1] }) =>
      apiClient.phenologyService.recordPhenologyObservation(recordId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phenology-records'] })
      setIsObservationOpen(false)
      setSelectedRecord(null)
      toast.success('Observation recorded')
    },
    onError: () => toast.error('Failed to record observation'),
  })

  const records = recordsData?.records || []

  const getStageColor = (stageCode: number) => {
    const stage = stages.find((s: GrowthStage) => s.code <= stageCode)
    return stage?.color || 'bg-gray-500'
  }

  const getProgress = (stageCode: number) => (stageCode / 90) * 100

  const handleCreateSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    createMutation.mutate({
      germplasm_name: formData.get('germplasm_name') as string,
      study_id: formData.get('study_id') as string,
      plot_id: formData.get('plot_id') as string,
      sowing_date: formData.get('sowing_date') as string,
      expected_maturity: parseInt(formData.get('expected_maturity') as string) || 120,
      crop: formData.get('crop') as string || 'rice',
    })
  }

  const handleObservationSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!selectedRecord) return
    const formData = new FormData(e.currentTarget)
    observationMutation.mutate({
      recordId: selectedRecord.id,
      data: {
        stage: parseInt(formData.get('stage') as string),
        date: formData.get('date') as string || undefined,
        notes: formData.get('notes') as string || undefined,
      },
    })
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">Failed to load phenology data</p>
          <Button variant="outline" className="mt-4" onClick={() => queryClient.invalidateQueries({ queryKey: ['phenology-records'] })}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Phenology Tracker</h1>
          <p className="text-muted-foreground mt-1">Track plant growth stages (Zadoks Scale)</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Crops</SelectItem>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="maize">Maize</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedStudy} onValueChange={setSelectedStudy}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Study" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Studies</SelectItem>
              <SelectItem value="study-2024">Study 2024</SelectItem>
              <SelectItem value="study-2023">Study 2023</SelectItem>
            </SelectContent>
          </Select>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Record</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Phenology Record</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="germplasm_name">Germplasm Name *</Label>
                    <Input id="germplasm_name" name="germplasm_name" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="plot_id">Plot ID *</Label>
                    <Input id="plot_id" name="plot_id" required placeholder="A-01" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="study_id">Study ID *</Label>
                    <Input id="study_id" name="study_id" required defaultValue="study-2024" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="crop">Crop</Label>
                    <Select name="crop" defaultValue="rice">
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rice">Rice</SelectItem>
                        <SelectItem value="wheat">Wheat</SelectItem>
                        <SelectItem value="maize">Maize</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="sowing_date">Sowing Date *</Label>
                    <Input id="sowing_date" name="sowing_date" type="date" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="expected_maturity">Expected Maturity (days)</Label>
                    <Input id="expected_maturity" name="expected_maturity" type="number" defaultValue={120} />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Record
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Leaf className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.total_records || records.length}</p>
                <p className="text-xs text-muted-foreground">Total Records</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.avg_days_to_maturity || 115}</p>
                <p className="text-xs text-muted-foreground">Avg Days to Maturity</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.by_stage?.['Flowering'] || 0}</p>
                <p className="text-xs text-muted-foreground">At Flowering</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Leaf className="h-5 w-5 text-orange-600" />
              <div>
                <p className="text-2xl font-bold">{stats?.by_stage?.['Maturity'] || 0}</p>
                <p className="text-xs text-muted-foreground">At Maturity</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Growth Stage Legend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Growth Stages (Zadoks Scale)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {stages.map((stage: GrowthStage) => (
              <div key={stage.code} className="flex items-center gap-1">
                <div className={`w-3 h-3 rounded-full ${stage.color}`}></div>
                <span className="text-xs">{stage.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Records */}
      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : records.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Leaf className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No phenology records found</p>
            <Button variant="outline" className="mt-4" onClick={() => setIsCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />Create First Record
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {records.map((record: PhenologyRecord) => (
            <Card key={record.id}>
              <CardContent className="pt-4">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{record.germplasm_name}</span>
                      <Badge variant="outline">{record.plot_id}</Badge>
                      <Badge className={getStageColor(record.current_stage)}>
                        {record.current_stage_name || `Stage ${record.current_stage}`}
                      </Badge>
                      <Badge variant="secondary">{record.crop}</Badge>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="relative">
                      <Progress value={getProgress(record.current_stage)} className="h-6" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-xs font-medium text-white drop-shadow">
                          {record.current_stage}% - {record.current_stage_name || `Stage ${record.current_stage}`}
                        </span>
                      </div>
                    </div>

                    {/* Stage Markers */}
                    <div className="flex justify-between mt-1">
                      {stages.filter((_: GrowthStage, i: number) => i % 2 === 0).map((stage: GrowthStage) => (
                        <div
                          key={stage.code}
                          className={`w-2 h-2 rounded-full ${record.current_stage >= stage.code ? stage.color : 'bg-gray-200'}`}
                          title={stage.name}
                        />
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-4 text-sm">
                    <div className="text-center">
                      <p className="font-bold text-blue-600">{record.days_from_sowing}</p>
                      <p className="text-xs text-muted-foreground">Days</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-green-600">{record.expected_maturity}</p>
                      <p className="text-xs text-muted-foreground">Expected</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-orange-600">
                        {Math.max(0, record.expected_maturity - record.days_from_sowing)}
                      </p>
                      <p className="text-xs text-muted-foreground">Remaining</p>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedRecord(record)
                      setIsObservationOpen(true)
                    }}
                  >
                    📝 Record
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Observation Dialog */}
      <Dialog open={isObservationOpen} onOpenChange={setIsObservationOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Stage Observation</DialogTitle>
          </DialogHeader>
          {selectedRecord && (
            <form onSubmit={handleObservationSubmit} className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Recording for: <strong>{selectedRecord.germplasm_name}</strong> ({selectedRecord.plot_id})
              </p>
              <div className="space-y-2">
                <Label htmlFor="stage">Growth Stage *</Label>
                <Select name="stage" defaultValue={String(selectedRecord.current_stage)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {stages.map((stage: GrowthStage) => (
                      <SelectItem key={stage.code} value={String(stage.code)}>
                        {stage.code} - {stage.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="date">Observation Date</Label>
                <Input id="date" name="date" type="date" defaultValue={new Date().toISOString().split('T')[0]} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea id="notes" name="notes" placeholder="Optional observation notes..." />
              </div>
              <Button type="submit" className="w-full" disabled={observationMutation.isPending}>
                {observationMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Record Observation
              </Button>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
