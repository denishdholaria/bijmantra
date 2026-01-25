import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Crosshair,
  TrendingUp,
  Dna,
  Target,
  BarChart3,
  Sparkles,
  ArrowRight,
  Download,
  RefreshCw
} from 'lucide-react'

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
  const [showResults, setShowResults] = useState(false)

  const parents = [
    { id: 'ir64', name: 'IR64', traits: ['High yield', 'Good quality'] },
    { id: 'swarna', name: 'Swarna', traits: ['Wide adaptation', 'High yield'] },
    { id: 'fr13a', name: 'FR13A', traits: ['Submergence tolerance'] },
    { id: 'pokkali', name: 'Pokkali', traits: ['Salt tolerance'] },
    { id: 'n22', name: 'N22', traits: ['Heat tolerance', 'Drought tolerance'] }
  ]

  const predictions: CrossPredictionResult[] = [
    { trait: 'Grain Yield (t/ha)', parentMean: 5.2, predictedMean: 5.8, predictedRange: [4.9, 6.7], heritability: 0.45, heterosis: 11.5 },
    { trait: 'Plant Height (cm)', parentMean: 105, predictedMean: 98, predictedRange: [85, 115], heritability: 0.72, heterosis: -6.7 },
    { trait: 'Days to Maturity', parentMean: 125, predictedMean: 122, predictedRange: [115, 130], heritability: 0.68, heterosis: -2.4 },
    { trait: 'Disease Score (1-9)', parentMean: 4.5, predictedMean: 3.2, predictedRange: [2.0, 5.0], heritability: 0.55, heterosis: -28.9 }
  ]

  const handlePredict = () => {
    if (parent1 && parent2) {
      setShowResults(true)
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
              <Select value={parent1} onValueChange={setParent1}>
                <SelectTrigger><SelectValue placeholder="Select female parent" /></SelectTrigger>
                <SelectContent>
                  {parents.map(p => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {parent1 && (
                <div className="flex gap-1 mt-2">
                  {parents.find(p => p.id === parent1)?.traits.map((t, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                </div>
              )}
            </div>
            <ArrowRight className="h-6 w-6 text-muted-foreground" />
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Male Parent</label>
              <Select value={parent2} onValueChange={setParent2}>
                <SelectTrigger><SelectValue placeholder="Select male parent" /></SelectTrigger>
                <SelectContent>
                  {parents.filter(p => p.id !== parent1).map(p => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {parent2 && (
                <div className="flex gap-1 mt-2">
                  {parents.find(p => p.id === parent2)?.traits.map((t, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                </div>
              )}
            </div>
            <Button onClick={handlePredict} disabled={!parent1 || !parent2} size="lg">
              <Sparkles className="h-4 w-4 mr-2" />Predict
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Results */}
      {showResults && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg"><TrendingUp className="h-5 w-5 text-green-600" /></div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">+8.5%</div>
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
                    <div className="text-2xl font-bold">0.42</div>
                    <div className="text-sm text-muted-foreground">Genetic Distance</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg"><Target className="h-5 w-5 text-purple-600" /></div>
                  <div>
                    <div className="text-2xl font-bold">78%</div>
                    <div className="text-sm text-muted-foreground">Success Probability</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg"><BarChart3 className="h-5 w-5 text-orange-600" /></div>
                  <div>
                    <div className="text-2xl font-bold">A</div>
                    <div className="text-sm text-muted-foreground">Cross Rating</div>
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
