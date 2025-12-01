/**
 * Population Genetics Page
 * Population structure, admixture, and evolutionary analyses
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

interface Population {
  id: string
  name: string
  size: number
  region: string
  admixture: number[]
}

interface PCAResult {
  sample: string
  population: string
  pc1: number
  pc2: number
  pc3: number
}

const populations: Population[] = [
  { id: 'pop1', name: 'South Asian', size: 120, region: 'India', admixture: [0.85, 0.10, 0.05] },
  { id: 'pop2', name: 'East Asian', size: 95, region: 'China/Japan', admixture: [0.08, 0.88, 0.04] },
  { id: 'pop3', name: 'African', size: 78, region: 'Sub-Saharan', admixture: [0.05, 0.05, 0.90] },
  { id: 'pop4', name: 'European', size: 85, region: 'Europe', admixture: [0.45, 0.35, 0.20] },
  { id: 'pop5', name: 'American', size: 62, region: 'Americas', admixture: [0.30, 0.25, 0.45] },
]

const pcaResults: PCAResult[] = [
  { sample: 'SA001', population: 'South Asian', pc1: -2.5, pc2: 1.2, pc3: 0.3 },
  { sample: 'SA002', population: 'South Asian', pc1: -2.3, pc2: 1.4, pc3: 0.1 },
  { sample: 'EA001', population: 'East Asian', pc1: 2.8, pc2: 1.8, pc3: -0.5 },
  { sample: 'EA002', population: 'East Asian', pc1: 2.6, pc2: 2.0, pc3: -0.3 },
  { sample: 'AF001', population: 'African', pc1: 0.2, pc2: -3.5, pc3: 1.2 },
  { sample: 'AF002', population: 'African', pc1: 0.4, pc2: -3.2, pc3: 1.0 },
  { sample: 'EU001', population: 'European', pc1: -0.5, pc2: 0.8, pc3: -1.5 },
  { sample: 'AM001', population: 'American', pc1: 0.8, pc2: -0.5, pc3: 0.8 },
]

const fstMatrix = [
  { pop1: 'South Asian', pop2: 'East Asian', fst: 0.082 },
  { pop1: 'South Asian', pop2: 'African', fst: 0.145 },
  { pop1: 'South Asian', pop2: 'European', fst: 0.048 },
  { pop1: 'East Asian', pop2: 'African', fst: 0.168 },
  { pop1: 'East Asian', pop2: 'European', fst: 0.095 },
  { pop1: 'African', pop2: 'European', fst: 0.152 },
]

export function PopulationGenetics() {
  const [activeTab, setActiveTab] = useState('structure')
  const [kValue, setKValue] = useState([3])
  const [selectedPop, setSelectedPop] = useState('all')

  const getClusterColor = (index: number) => {
    const colors = ['bg-blue-500', 'bg-green-500', 'bg-orange-500', 'bg-purple-500', 'bg-pink-500']
    return colors[index % colors.length]
  }

  const getPopColor = (pop: string) => {
    const colors: { [key: string]: string } = {
      'South Asian': 'bg-blue-500',
      'East Asian': 'bg-green-500',
      'African': 'bg-orange-500',
      'European': 'bg-purple-500',
      'American': 'bg-pink-500',
    }
    return colors[pop] || 'bg-gray-500'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Population Genetics</h1>
          <p className="text-muted-foreground mt-1">Population structure and evolutionary analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedPop} onValueChange={setSelectedPop}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Population" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Populations</SelectItem>
              {populations.map(p => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>🧬 Run Analysis</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="structure">Population Structure</TabsTrigger>
          <TabsTrigger value="pca">PCA</TabsTrigger>
          <TabsTrigger value="fst">Fst Analysis</TabsTrigger>
          <TabsTrigger value="migration">Migration</TabsTrigger>
        </TabsList>

        <TabsContent value="structure" className="space-y-6 mt-4">
          {/* K Selection */}
          <Card>
            <CardHeader>
              <CardTitle>STRUCTURE/ADMIXTURE Analysis</CardTitle>
              <CardDescription>Infer population structure and admixture proportions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Number of Clusters (K): {kValue[0]}</Label>
                  <Slider
                    value={kValue}
                    onValueChange={setKValue}
                    min={2}
                    max={10}
                    step={1}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Burn-in</Label>
                  <Input type="number" defaultValue="10000" />
                </div>
                <div className="space-y-2">
                  <Label>MCMC Iterations</Label>
                  <Input type="number" defaultValue="50000" />
                </div>
              </div>

              {/* Structure Bar Plot */}
              <div>
                <h4 className="font-medium mb-3">Admixture Proportions (K={kValue[0]})</h4>
                <div className="space-y-3">
                  {populations.map((pop) => (
                    <div key={pop.id} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{pop.name}</span>
                        <span className="text-muted-foreground">{pop.size} samples</span>
                      </div>
                      <div className="flex h-8 rounded overflow-hidden">
                        {pop.admixture.slice(0, kValue[0]).map((prop, i) => (
                          <div 
                            key={i}
                            className={getClusterColor(i)}
                            style={{ width: `${prop * 100}%` }}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-4 mt-4 text-sm">
                  {Array.from({ length: kValue[0] }).map((_, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <div className={`w-4 h-4 ${getClusterColor(i)} rounded`} />
                      <span>Cluster {i + 1}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Delta K */}
          <Card>
            <CardHeader>
              <CardTitle>Optimal K Selection</CardTitle>
              <CardDescription>Evanno's ΔK method for determining optimal number of clusters</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg p-4">
                <div className="h-full flex items-end justify-around">
                  {[2, 3, 4, 5, 6, 7, 8].map((k) => {
                    const deltaK = k === 3 ? 245 : k === 4 ? 85 : k === 5 ? 42 : Math.random() * 30
                    return (
                      <div key={k} className="flex flex-col items-center">
                        <div 
                          className={`w-8 ${k === 3 ? 'bg-primary' : 'bg-muted-foreground/30'} rounded-t`}
                          style={{ height: `${(deltaK / 250) * 100}%` }}
                        />
                        <span className="text-xs mt-1">K={k}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
              <p className="text-sm text-center mt-2 text-muted-foreground">
                Optimal K = 3 (ΔK = 245.8)
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pca" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Principal Component Analysis</CardTitle>
              <CardDescription>Visualize population structure using PCA</CardDescription>
            </CardHeader>
            <CardContent>
              {/* PCA Plot Simulation */}
              <div className="h-64 bg-muted rounded-lg p-4 relative">
                {pcaResults.map((result, i) => (
                  <div
                    key={i}
                    className={`absolute w-3 h-3 rounded-full ${getPopColor(result.population)} cursor-pointer hover:scale-150 transition-transform`}
                    style={{
                      left: `${50 + result.pc1 * 10}%`,
                      top: `${50 - result.pc2 * 10}%`,
                    }}
                    title={`${result.sample} (${result.population})`}
                  />
                ))}
                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 text-xs text-muted-foreground">
                  PC1 (32.5%)
                </div>
                <div className="absolute left-2 top-1/2 transform -translate-y-1/2 -rotate-90 text-xs text-muted-foreground">
                  PC2 (18.2%)
                </div>
              </div>
              <div className="flex flex-wrap gap-4 mt-4 justify-center">
                {populations.map((pop) => (
                  <div key={pop.id} className="flex items-center gap-1">
                    <div className={`w-3 h-3 rounded-full ${getPopColor(pop.name)}`} />
                    <span className="text-sm">{pop.name}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Variance Explained */}
          <Card>
            <CardHeader>
              <CardTitle>Variance Explained</CardTitle>
              <CardDescription>Proportion of variance explained by each PC</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { pc: 'PC1', variance: 32.5 },
                  { pc: 'PC2', variance: 18.2 },
                  { pc: 'PC3', variance: 12.8 },
                  { pc: 'PC4', variance: 8.5 },
                  { pc: 'PC5', variance: 5.2 },
                ].map((item) => (
                  <div key={item.pc} className="flex items-center gap-4">
                    <span className="w-12 font-medium">{item.pc}</span>
                    <Progress value={item.variance} className="flex-1 h-3" />
                    <span className="w-16 text-right">{item.variance}%</span>
                  </div>
                ))}
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                Cumulative variance (PC1-5): 77.2%
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fst" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Pairwise Fst</CardTitle>
              <CardDescription>Genetic differentiation between populations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Population 1</th>
                      <th className="text-left p-3">Population 2</th>
                      <th className="text-right p-3">Fst</th>
                      <th className="text-center p-3">Differentiation</th>
                      <th className="text-right p-3">P-value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fstMatrix.map((row, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{row.pop1}</td>
                        <td className="p-3">{row.pop2}</td>
                        <td className="p-3 text-right font-mono">{row.fst.toFixed(3)}</td>
                        <td className="p-3 text-center">
                          <Badge className={
                            row.fst < 0.05 ? 'bg-green-100 text-green-700' :
                            row.fst < 0.15 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }>
                            {row.fst < 0.05 ? 'Low' : row.fst < 0.15 ? 'Moderate' : 'High'}
                          </Badge>
                        </td>
                        <td className="p-3 text-right font-mono text-xs">&lt;0.001</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">Fst Interpretation (Wright, 1978)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-100 text-green-700">0-0.05</Badge>
                    <span>Little</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-yellow-100 text-yellow-700">0.05-0.15</Badge>
                    <span>Moderate</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-orange-100 text-orange-700">0.15-0.25</Badge>
                    <span>Great</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-red-100 text-red-700">&gt;0.25</Badge>
                    <span>Very great</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Global Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-primary">0.098</p>
                <p className="text-sm text-muted-foreground">Global Fst</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-600">0.72</p>
                <p className="text-sm text-muted-foreground">Mean He</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-blue-600">0.68</p>
                <p className="text-sm text-muted-foreground">Mean Ho</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-purple-600">0.055</p>
                <p className="text-sm text-muted-foreground">Inbreeding (Fis)</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="migration" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Gene Flow & Migration</CardTitle>
              <CardDescription>Estimate migration rates between populations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">🌍</span>
                  <p className="mt-2 text-muted-foreground">Migration Network</p>
                  <p className="text-xs text-muted-foreground">Gene flow visualization</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Migration Rates */}
          <Card>
            <CardHeader>
              <CardTitle>Estimated Migration Rates (Nm)</CardTitle>
              <CardDescription>Number of migrants per generation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">From</th>
                      <th className="text-left p-3">To</th>
                      <th className="text-right p-3">Nm</th>
                      <th className="text-center p-3">Gene Flow</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { from: 'South Asian', to: 'European', nm: 4.95 },
                      { from: 'East Asian', to: 'South Asian', nm: 2.80 },
                      { from: 'African', to: 'European', nm: 1.40 },
                      { from: 'American', to: 'African', nm: 0.85 },
                    ].map((row, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{row.from}</td>
                        <td className="p-3">{row.to}</td>
                        <td className="p-3 text-right font-mono">{row.nm.toFixed(2)}</td>
                        <td className="p-3 text-center">
                          <Badge className={
                            row.nm > 4 ? 'bg-green-100 text-green-700' :
                            row.nm > 1 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }>
                            {row.nm > 4 ? 'High' : row.nm > 1 ? 'Moderate' : 'Low'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                Nm &gt; 1 indicates sufficient gene flow to prevent genetic differentiation
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
