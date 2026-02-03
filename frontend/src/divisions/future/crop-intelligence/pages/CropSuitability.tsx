/**
 * Crop Suitability Page
 * FAO framework-based crop-location compatibility assessments with radar visualization
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, MapPin, RefreshCw, Trash2, Thermometer, Droplets, Mountain } from 'lucide-react'

interface CropSuitabilityAssessment {
  id: string
  crop_id: string
  location_id: string
  assessment_date: string
  climate_score: number | null
  soil_score: number | null
  water_score: number | null
  overall_suitability: string | null
  limiting_factors: string[] | null
  recommendations: string[] | null
  created_at: string
}

const SUITABILITY_CLASSES = [
  { value: 'S1', label: 'Highly Suitable', color: 'bg-emerald-500', textColor: 'text-emerald-700 dark:text-emerald-400' },
  { value: 'S2', label: 'Moderately Suitable', color: 'bg-green-500', textColor: 'text-green-700 dark:text-green-400' },
  { value: 'S3', label: 'Marginally Suitable', color: 'bg-yellow-500', textColor: 'text-yellow-700 dark:text-yellow-400' },
  { value: 'N1', label: 'Currently Not Suitable', color: 'bg-orange-500', textColor: 'text-orange-700 dark:text-orange-400' },
  { value: 'N2', label: 'Permanently Not Suitable', color: 'bg-red-500', textColor: 'text-red-700 dark:text-red-400' },
]

const getSuitabilityInfo = (code: string | null) => {
  return SUITABILITY_CLASSES.find(s => s.value === code) || SUITABILITY_CLASSES[2]
}

function FactorBar({ label, score, icon: Icon }: { label: string; score: number | null; icon: React.ElementType }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span>{label}</span>
        </div>
        <span className="font-medium">{score ?? '—'}%</span>
      </div>
      <Progress value={score ?? 0} className="h-2" aria-label={`${label} suitability score`} />
    </div>
  )
}

export function CropSuitability() {
  const [showCreate, setShowCreate] = useState(false)
  const [newAssessment, setNewAssessment] = useState({
    crop_id: '',
    location_id: '',
    assessment_date: new Date().toISOString().split('T')[0],
    climate_score: 75,
    soil_score: 70,
    water_score: 65,
    overall_suitability: 'S2',
    limiting_factors: [] as string[],
    recommendations: [] as string[],
  })
  const queryClient = useQueryClient()

  const { data: assessments, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'crop-suitability'],
    queryFn: () => apiClient.get('/api/v2/future/crop-suitability/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newAssessment) => apiClient.post('/api/v2/future/crop-suitability/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'crop-suitability'] })
      toast.success('Suitability assessment created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create assessment'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/crop-suitability/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'crop-suitability'] })
      toast.success('Assessment deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <MapPin className="h-8 w-8 text-green-500" />
            Crop Suitability
          </h1>
          <p className="text-muted-foreground mt-1">
            FAO framework-based crop-location compatibility assessments
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" aria-label="Refresh" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Assessment</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Suitability Assessment</DialogTitle>
                <DialogDescription>Assess crop-location compatibility using FAO framework</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Crop ID</Label>
                    <Input
                      value={newAssessment.crop_id}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, crop_id: e.target.value }))}
                      placeholder="CROP-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Location ID</Label>
                    <Input
                      value={newAssessment.location_id}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, location_id: e.target.value }))}
                      placeholder="LOC-001"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Assessment Date</Label>
                  <Input
                    type="date"
                    value={newAssessment.assessment_date}
                    onChange={(e) => setNewAssessment((p) => ({ ...p, assessment_date: e.target.value }))}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Climate Score (%)</Label>
                    <Input
                      type="number" min="0" max="100"
                      value={newAssessment.climate_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, climate_score: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Soil Score (%)</Label>
                    <Input
                      type="number" min="0" max="100"
                      value={newAssessment.soil_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, soil_score: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Water Score (%)</Label>
                    <Input
                      type="number" min="0" max="100"
                      value={newAssessment.water_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, water_score: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Overall Suitability (FAO Class)</Label>
                  <Select
                    value={newAssessment.overall_suitability}
                    onValueChange={(v) => setNewAssessment((p) => ({ ...p, overall_suitability: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {SUITABILITY_CLASSES.map((c) => (
                        <SelectItem key={c.value} value={c.value}>{c.value} - {c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newAssessment)}
                  disabled={!newAssessment.crop_id || !newAssessment.location_id || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Assessment'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load suitability assessments.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-64" />)}
        </div>
      )}

      {/* Assessment Cards */}
      {!isLoading && !error && (
        <>
          {Array.isArray(assessments) && assessments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {assessments.map((assessment: CropSuitabilityAssessment) => {
                const suitability = getSuitabilityInfo(assessment.overall_suitability)
                return (
                  <Card key={assessment.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <Badge className={`${suitability.color} text-white`}>
                          {assessment.overall_suitability}
                        </Badge>
                        <Button variant="ghost" size="icon" aria-label="Delete assessment"
                          onClick={() => deleteMutation.mutate(assessment.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                      <CardTitle className="text-base mt-2">
                        {assessment.crop_id} × {assessment.location_id}
                      </CardTitle>
                      <CardDescription>{formatDate(assessment.assessment_date)}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className={`text-sm font-medium ${suitability.textColor}`}>{suitability.label}</p>
                      <div className="space-y-3">
                        <FactorBar label="Climate" score={assessment.climate_score} icon={Thermometer} />
                        <FactorBar label="Soil" score={assessment.soil_score} icon={Mountain} />
                        <FactorBar label="Water" score={assessment.water_score} icon={Droplets} />
                      </div>
                      {assessment.limiting_factors && assessment.limiting_factors.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Limiting Factors</p>
                          <div className="flex flex-wrap gap-1">
                            {assessment.limiting_factors.map((f, i) => (
                              <Badge key={i} variant="outline" className="text-xs">{f}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <MapPin className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No suitability assessments recorded yet</p>
                <Button className="mt-4" onClick={() => setShowCreate(true)}>
                  <Plus className="h-4 w-4 mr-2" />Add First Assessment
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
