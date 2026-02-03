/**
 * Soil Health Page
 * Display soil health scores with gauge visualizations for physical, chemical, and biological health
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { AlertCircle, Plus, Heart, RefreshCw, Trash2, Activity, Droplets, Leaf } from 'lucide-react'

interface SoilHealthScore {
  id: string
  location_id: string
  assessment_date: string
  physical_score: number | null
  chemical_score: number | null
  biological_score: number | null
  overall_score: number | null
  limiting_factors: string[] | null
  recommendations: string[] | null
  created_at: string
}

const getScoreColor = (score: number | null): string => {
  if (score === null) return 'bg-gray-200 dark:bg-gray-700'
  if (score >= 80) return 'bg-emerald-500'
  if (score >= 60) return 'bg-green-500'
  if (score >= 40) return 'bg-yellow-500'
  if (score >= 20) return 'bg-orange-500'
  return 'bg-red-500'
}

const getScoreLabel = (score: number | null): string => {
  if (score === null) return 'Unknown'
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Moderate'
  if (score >= 20) return 'Poor'
  return 'Critical'
}

function ScoreGauge({ label, score, icon: Icon }: { label: string; score: number | null; icon: React.ElementType }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{label}</span>
        </div>
        <span className="text-sm font-bold">{score ?? '—'}/100</span>
      </div>
      <Progress value={score ?? 0} className="h-2" aria-label={`${label} score`} />
      <p className="text-xs text-muted-foreground text-right">{getScoreLabel(score)}</p>
    </div>
  )
}

export function SoilHealth() {
  const [showCreate, setShowCreate] = useState(false)
  const [newAssessment, setNewAssessment] = useState({
    location_id: '',
    assessment_date: new Date().toISOString().split('T')[0],
    physical_score: 70,
    chemical_score: 65,
    biological_score: 60,
    overall_score: 65,
    limiting_factors: [] as string[],
    recommendations: [] as string[],
  })
  const queryClient = useQueryClient()

  const { data: assessments, isLoading, error, refetch } = useQuery({
    queryKey: ['future', 'soil-health'],
    queryFn: () => apiClient.get('/api/v2/future/soil-health/'),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newAssessment) => apiClient.post('/api/v2/future/soil-health/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'soil-health'] })
      toast.success('Soil health assessment created')
      setShowCreate(false)
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to create assessment'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v2/future/soil-health/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'soil-health'] })
      toast.success('Assessment deleted')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Failed to delete'),
  })

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Heart className="h-8 w-8 text-red-500" />
            Soil Health
          </h1>
          <p className="text-muted-foreground mt-1">
            Physical, chemical, and biological soil health assessments
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
                <DialogTitle>Record Soil Health Assessment</DialogTitle>
                <DialogDescription>Enter soil health scores (0-100 scale)</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Location ID</Label>
                    <Input
                      value={newAssessment.location_id}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, location_id: e.target.value }))}
                      placeholder="LOC-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Assessment Date</Label>
                    <Input
                      type="date"
                      value={newAssessment.assessment_date}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, assessment_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Physical Score (0-100)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={newAssessment.physical_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, physical_score: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Chemical Score (0-100)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={newAssessment.chemical_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, chemical_score: Number(e.target.value) }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Biological Score (0-100)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={newAssessment.biological_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, biological_score: Number(e.target.value) }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Overall Score (0-100)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={newAssessment.overall_score}
                      onChange={(e) => setNewAssessment((p) => ({ ...p, overall_score: Number(e.target.value) }))}
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newAssessment)}
                  disabled={!newAssessment.location_id || createMutation.isPending}
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
            Failed to load soil health data.
            <Button variant="link" size="sm" onClick={() => refetch()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      )}

      {/* Assessment Cards */}
      {!isLoading && !error && (
        <>
          {Array.isArray(assessments) && assessments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {assessments.map((assessment: SoilHealthScore) => (
                <Card key={assessment.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{assessment.location_id}</CardTitle>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Delete assessment"
                        onClick={() => deleteMutation.mutate(assessment.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                    <CardDescription>{formatDate(assessment.assessment_date)}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Overall Score */}
                    <div className="text-center p-4 rounded-lg bg-slate-50 dark:bg-slate-800">
                      <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${getScoreColor(assessment.overall_score)} text-white font-bold text-xl mb-2`}>
                        {assessment.overall_score ?? '—'}
                      </div>
                      <p className="text-sm font-medium">{getScoreLabel(assessment.overall_score)}</p>
                    </div>

                    {/* Component Scores */}
                    <div className="space-y-3">
                      <ScoreGauge label="Physical" score={assessment.physical_score} icon={Activity} />
                      <ScoreGauge label="Chemical" score={assessment.chemical_score} icon={Droplets} />
                      <ScoreGauge label="Biological" score={assessment.biological_score} icon={Leaf} />
                    </div>

                    {/* Limiting Factors */}
                    {assessment.limiting_factors && assessment.limiting_factors.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-muted-foreground mb-1">Limiting Factors</p>
                        <div className="flex flex-wrap gap-1">
                          {assessment.limiting_factors.map((factor, i) => (
                            <Badge key={i} variant="outline" className="text-xs">{factor}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <Heart className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No soil health assessments recorded yet</p>
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
