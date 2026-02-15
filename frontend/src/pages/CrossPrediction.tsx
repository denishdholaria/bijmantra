import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Crosshair,
  TrendingUp,
  Dna,
  Target,
  BarChart3,
  Sparkles,
  ArrowRight,
  Download,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface CrossPredictionResult {
  trait: string
  parentMean: number
  predictedMean: number
  predictedRange: [number, number]
  heritability: number
  heterosis: number
}

export function CrossPrediction() {
  const [parent1, setParent1] = useState('')
  const [parent2, setParent2] = useState('')

  // Fetch germplasm from database for parent selection
  const { data: germplasmData, isLoading: loadingParents } = useQuery({
    queryKey: ['cross-prediction-parents'],
    queryFn: () => apiClient.get<{ result?: { data?: any[] }; data?: any[] }>('/brapi/v2/germplasm?pageSize=100'),
  })

  const parents = (germplasmData?.result?.data || germplasmData?.data || []).map((g: any) => ({
    id: String(g.germplasmDbId || g.id),
    name: g.germplasmName || g.name || '',
    traits: [g.commonCropName, g.species].filter(Boolean),
  }))

  // Predict cross outcome via API
  const predictionMutation = useMutation({
    mutationFn: (data: { parent1_id: string; parent2_id: string }) =>
      apiClient.post<{ data: CrossPredictionResult[] }>('/api/v2/crosses/predict', data),
  })

  const predictions: CrossPredictionResult[] = predictionMutation.data?.data || []
  const showResults = predictionMutation.isSuccess && predictions.length > 0

  const handlePredict = () => {
    if (parent1 && parent2) {
      predictionMutation.mutate({ parent1_id: parent1, parent2_id: parent2 })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Crosshair className="h-8 w-8 text-primary" />
            Cross Prediction
          </h1>
          <p className="text-muted-foreground mt-1">Predict progeny performance from parental crosses</p>
        </div>
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Results</Button>
      </div>

      {/* Parent Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Parents</CardTitle>
          <CardDescription>Choose two parents to predict cross outcomes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Female Parent</label>
              {loadingParents ? (
                <Skeleton className="h-10 w-full" />
              ) : parents.length === 0 ? (
                <div className="text-sm text-muted-foreground p-3 border rounded-md">
                  <AlertCircle className="h-4 w-4 inline mr-1" />
                  No germplasm found. Add germplasm to your database first.
                </div>
              ) : (
              <Select value={parent1} onValueChange={setParent1}>
                <SelectTrigger><SelectValue placeholder="Select female parent" /></SelectTrigger>
                <SelectContent>
                  {parents.map((p: any) => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              )}
              {parent1 && (
                <div className="flex gap-1 mt-2">
                  {parents.find((p: any) => p.id === parent1)?.traits.map((t: string, i: number) => (
                    <Badge key={i} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                </div>
              )}
            </div>
            <ArrowRight className="h-6 w-6 text-muted-foreground" />
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Male Parent</label>
              {loadingParents ? (
                <Skeleton className="h-10 w-full" />
              ) : parents.length === 0 ? (
                <div className="text-sm text-muted-foreground p-3 border rounded-md">
                  <AlertCircle className="h-4 w-4 inline mr-1" />
                  No germplasm available.
                </div>
              ) : (
              <Select value={parent2} onValueChange={setParent2}>
                <SelectTrigger><SelectValue placeholder="Select male parent" /></SelectTrigger>
                <SelectContent>
                  {parents.filter((p: any) => p.id !== parent1).map((p: any) => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              )}
              {parent2 && (
                <div className="flex gap-1 mt-2">
                  {parents.find((p: any) => p.id === parent2)?.traits.map((t: string, i: number) => (
                    <Badge key={i} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                </div>
              )}
            </div>
            <Button onClick={handlePredict} disabled={!parent1 || !parent2 || predictionMutation.isPending} size="lg">
              {predictionMutation.isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              Predict
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Results */}
      {predictionMutation.isPending && (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      )}

      {predictionMutation.isError && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
            <p className="font-medium">Cross prediction requires phenotypic data for both parents</p>
            <p className="text-sm text-muted-foreground mt-1">
              Ensure observations exist for the selected germplasm to enable trait predictions.
            </p>
          </CardContent>
        </Card>
      )}

      {showResults && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {predictions.length > 0 
                        ? `${predictions.reduce((s, p) => s + p.heterosis, 0) / predictions.length > 0 ? '+' : ''}${(predictions.reduce((s, p) => s + p.heterosis, 0) / predictions.length).toFixed(1)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">Avg. Heterosis</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg"><Dna className="h-5 w-5 text-blue-600" /></div>
                  <div>
                    <div className="text-2xl font-bold">{predictions.length}</div>
                    <div className="text-sm text-muted-foreground">Traits Predicted</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg"><Target className="h-5 w-5 text-purple-600" /></div>
                  <div>
                    <div className="text-2xl font-bold">
                      {predictions.length > 0
                        ? `${(predictions.reduce((s, p) => s + p.heritability, 0) / predictions.length * 100).toFixed(0)}%`
                        : '—'}
                    </div>
                    <div className="text-sm text-muted-foreground">Avg. Heritability</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg"><BarChart3 className="h-5 w-5 text-orange-600" /></div>
                  <div>
                    <div className="text-2xl font-bold">
                      {parents.find((p: any) => p.id === parent1)?.name || '?'} × {parents.find((p: any) => p.id === parent2)?.name || '?'}
                    </div>
                    <div className="text-sm text-muted-foreground">Cross</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Trait Predictions</CardTitle>
              <CardDescription>Expected progeny performance for key traits</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {predictions.map((pred, i) => (
                  <div key={i} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{pred.trait}</h4>
                      <Badge variant={pred.heterosis > 0 ? 'default' : 'secondary'}>
                        {pred.heterosis > 0 ? '+' : ''}{pred.heterosis.toFixed(1)}% heterosis
                      </Badge>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Parent Mean</div>
                        <div className="font-bold">{pred.parentMean}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Predicted Mean</div>
                        <div className="font-bold text-primary">{pred.predictedMean}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Range (95% CI)</div>
                        <div className="font-bold">{pred.predictedRange[0]} - {pred.predictedRange[1]}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Heritability</div>
                        <div className="font-bold">{(pred.heritability * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
