/**
 * Doubled Haploid Page
 * DH production and management for rapid homozygosity
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface DHProduction {
  id: string
  name: string
  cross: string
  method: 'anther' | 'microspore' | 'wide' | 'inducer'
  donorPlants: number
  embryosProduced: number
  plantsRegenerated: number
  dhLines: number
  efficiency: number
  status: 'active' | 'completed'
}

interface DHLine {
  id: string
  name: string
  cross: string
  ploidy: '2n' | 'n' | 'unknown'
  vigor: 'high' | 'medium' | 'low'
  fertility: number
  selected: boolean
}

const dhProductions: DHProduction[] = [
  { id: 'dh1', name: 'DH-2024-Wheat-01', cross: 'Elite-A × Elite-B', method: 'anther', donorPlants: 50, embryosProduced: 450, plantsRegenerated: 180, dhLines: 145, efficiency: 32, status: 'completed' },
  { id: 'dh2', name: 'DH-2024-Barley-01', cross: 'Var-X × Var-Y', method: 'microspore', donorPlants: 40, embryosProduced: 520, plantsRegenerated: 210, dhLines: 168, efficiency: 42, status: 'completed' },
  { id: 'dh3', name: 'DH-2024-Maize-01', cross: 'Inbred-1 × Inbred-2', method: 'inducer', donorPlants: 100, embryosProduced: 850, plantsRegenerated: 420, dhLines: 380, efficiency: 38, status: 'active' },
  { id: 'dh4', name: 'DH-2024-Rice-01', cross: 'IR64 × Donor', method: 'anther', donorPlants: 60, embryosProduced: 380, plantsRegenerated: 150, dhLines: 0, efficiency: 25, status: 'active' },
]

const dhLines: DHLine[] = [
  { id: 'dl1', name: 'DH-W-001', cross: 'Elite-A × Elite-B', ploidy: '2n', vigor: 'high', fertility: 95, selected: true },
  { id: 'dl2', name: 'DH-W-002', cross: 'Elite-A × Elite-B', ploidy: '2n', vigor: 'high', fertility: 92, selected: true },
  { id: 'dl3', name: 'DH-W-003', cross: 'Elite-A × Elite-B', ploidy: '2n', vigor: 'medium', fertility: 88, selected: true },
  { id: 'dl4', name: 'DH-W-004', cross: 'Elite-A × Elite-B', ploidy: 'n', vigor: 'low', fertility: 0, selected: false },
  { id: 'dl5', name: 'DH-W-005', cross: 'Elite-A × Elite-B', ploidy: '2n', vigor: 'medium', fertility: 85, selected: false },
  { id: 'dl6', name: 'DH-W-006', cross: 'Elite-A × Elite-B', ploidy: 'unknown', vigor: 'low', fertility: 45, selected: false },
]

export function DoubledHaploid() {
  const [activeTab, setActiveTab] = useState('production')
  const [selectedMethod, setSelectedMethod] = useState('all')

  const getMethodBadge = (method: string) => {
    switch (method) {
      case 'anther':
        return <Badge className="bg-blue-100 text-blue-700">Anther Culture</Badge>
      case 'microspore':
        return <Badge className="bg-green-100 text-green-700">Microspore</Badge>
      case 'wide':
        return <Badge className="bg-purple-100 text-purple-700">Wide Cross</Badge>
      case 'inducer':
        return <Badge className="bg-orange-100 text-orange-700">Haploid Inducer</Badge>
      default:
        return <Badge variant="secondary">{method}</Badge>
    }
  }

  const getPloidyBadge = (ploidy: string) => {
    switch (ploidy) {
      case '2n':
        return <Badge className="bg-green-100 text-green-700">2n (DH)</Badge>
      case 'n':
        return <Badge className="bg-red-100 text-red-700">n (Haploid)</Badge>
      default:
        return <Badge variant="secondary">Unknown</Badge>
    }
  }

  const totalDHLines = dhProductions.reduce((sum, p) => sum + p.dhLines, 0)
  const avgEfficiency = Math.round(dhProductions.reduce((sum, p) => sum + p.efficiency, 0) / dhProductions.length)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Doubled Haploid</h1>
          <p className="text-muted-foreground mt-1">DH production for instant homozygosity</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedMethod} onValueChange={setSelectedMethod}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Method" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Methods</SelectItem>
              <SelectItem value="anther">Anther Culture</SelectItem>
              <SelectItem value="microspore">Microspore</SelectItem>
              <SelectItem value="inducer">Haploid Inducer</SelectItem>
            </SelectContent>
          </Select>
          <Button>➕ New Production</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{dhProductions.length}</p>
            <p className="text-sm text-muted-foreground">Productions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{totalDHLines}</p>
            <p className="text-sm text-muted-foreground">DH Lines</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{avgEfficiency}%</p>
            <p className="text-sm text-muted-foreground">Avg Efficiency</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">100%</p>
            <p className="text-sm text-muted-foreground">Homozygosity</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="production">Production</TabsTrigger>
          <TabsTrigger value="lines">DH Lines</TabsTrigger>
          <TabsTrigger value="protocol">Protocol</TabsTrigger>
          <TabsTrigger value="benefits">Benefits</TabsTrigger>
        </TabsList>

        <TabsContent value="production" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>DH Production Batches</CardTitle>
              <CardDescription>Track doubled haploid production progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Production</th>
                      <th className="text-left p-3">Cross</th>
                      <th className="text-center p-3">Method</th>
                      <th className="text-right p-3">Donors</th>
                      <th className="text-right p-3">Embryos</th>
                      <th className="text-right p-3">Regenerated</th>
                      <th className="text-right p-3">DH Lines</th>
                      <th className="text-right p-3">Efficiency</th>
                      <th className="text-center p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dhProductions.map((prod) => (
                      <tr key={prod.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{prod.name}</td>
                        <td className="p-3 text-sm">{prod.cross}</td>
                        <td className="p-3 text-center">{getMethodBadge(prod.method)}</td>
                        <td className="p-3 text-right">{prod.donorPlants}</td>
                        <td className="p-3 text-right">{prod.embryosProduced}</td>
                        <td className="p-3 text-right">{prod.plantsRegenerated}</td>
                        <td className="p-3 text-right font-bold">{prod.dhLines}</td>
                        <td className="p-3 text-right">
                          <span className={prod.efficiency >= 35 ? 'text-green-600' : prod.efficiency >= 25 ? 'text-yellow-600' : 'text-red-600'}>
                            {prod.efficiency}%
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Badge className={prod.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}>
                            {prod.status === 'completed' ? '✓ Done' : '🔄 Active'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Production Pipeline */}
          <Card>
            <CardHeader>
              <CardTitle>Production Pipeline</CardTitle>
              <CardDescription>DH production workflow stages</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                {[
                  { stage: 'Donor Plants', count: 250 },
                  { stage: 'Culture', count: 2200 },
                  { stage: 'Embryos', count: 960 },
                  { stage: 'Regeneration', count: 693 },
                  { stage: 'DH Lines', count: 693 },
                ].map((item, i) => (
                  <div key={item.stage} className="flex items-center">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-1">
                        <span className="font-bold text-primary">{item.count}</span>
                      </div>
                      <span className="text-xs">{item.stage}</span>
                    </div>
                    {i < 4 && <div className="w-8 h-0.5 bg-muted-foreground/30 mx-1" />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lines" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>DH Line Characterization</CardTitle>
              <CardDescription>Ploidy verification and vigor assessment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Line</th>
                      <th className="text-left p-3">Cross</th>
                      <th className="text-center p-3">Ploidy</th>
                      <th className="text-center p-3">Vigor</th>
                      <th className="text-right p-3">Fertility (%)</th>
                      <th className="text-center p-3">Selected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dhLines.map((line) => (
                      <tr key={line.id} className={`border-b hover:bg-muted/50 ${line.selected ? 'bg-green-50' : ''}`}>
                        <td className="p-3 font-medium">{line.name}</td>
                        <td className="p-3 text-sm">{line.cross}</td>
                        <td className="p-3 text-center">{getPloidyBadge(line.ploidy)}</td>
                        <td className="p-3 text-center">
                          <Badge className={
                            line.vigor === 'high' ? 'bg-green-100 text-green-700' :
                            line.vigor === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }>
                            {line.vigor}
                          </Badge>
                        </td>
                        <td className="p-3 text-right">
                          <span className={line.fertility >= 80 ? 'text-green-600' : line.fertility >= 50 ? 'text-yellow-600' : 'text-red-600'}>
                            {line.fertility}%
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          {line.selected ? (
                            <Badge className="bg-green-100 text-green-700">✓ Yes</Badge>
                          ) : (
                            <Badge variant="secondary">No</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Ploidy Distribution */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-green-700">{dhLines.filter(l => l.ploidy === '2n').length}</p>
                <p className="text-sm text-green-600">Doubled Haploids (2n)</p>
              </CardContent>
            </Card>
            <Card className="bg-red-50 border-red-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-red-700">{dhLines.filter(l => l.ploidy === 'n').length}</p>
                <p className="text-sm text-red-600">Haploids (n)</p>
              </CardContent>
            </Card>
            <Card className="bg-gray-50 border-gray-200">
              <CardContent className="pt-4 text-center">
                <p className="text-3xl font-bold text-gray-700">{dhLines.filter(l => l.ploidy === 'unknown').length}</p>
                <p className="text-sm text-gray-600">Unknown</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="protocol" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>DH Production Methods</CardTitle>
              <CardDescription>Available techniques for different crops</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { method: 'Anther Culture', crops: ['Wheat', 'Rice', 'Barley'], efficiency: '20-40%', time: '6-8 months', desc: 'Culture anthers on nutrient media' },
                  { method: 'Microspore Culture', crops: ['Barley', 'Rapeseed', 'Wheat'], efficiency: '30-50%', time: '4-6 months', desc: 'Isolated microspore culture' },
                  { method: 'Wide Hybridization', crops: ['Wheat', 'Barley'], efficiency: '15-30%', time: '3-4 months', desc: 'Cross with Hordeum bulbosum' },
                  { method: 'Haploid Inducer', crops: ['Maize'], efficiency: '8-12%', time: '2-3 months', desc: 'In vivo haploid induction' },
                ].map((item) => (
                  <div key={item.method} className="p-4 border rounded-lg">
                    <h4 className="font-bold mb-2">{item.method}</h4>
                    <p className="text-sm text-muted-foreground mb-3">{item.desc}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-muted-foreground">Crops</p>
                        <p className="font-medium">{item.crops.join(', ')}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Efficiency</p>
                        <p className="font-medium text-green-600">{item.efficiency}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Timeline</p>
                        <p className="font-medium">{item.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="benefits" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>DH Technology Benefits</CardTitle>
              <CardDescription>Advantages over conventional inbreeding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { benefit: '100% Homozygosity', desc: 'Instant fixation in one generation', icon: '🎯' },
                  { benefit: 'Time Savings', desc: 'Skip 6-8 generations of selfing', icon: '⏱️' },
                  { benefit: 'Reduced Costs', desc: 'Less field space and labor', icon: '💰' },
                  { benefit: 'Better Selection', desc: 'No masking by heterozygosity', icon: '🔍' },
                  { benefit: 'QTL Mapping', desc: 'Ideal populations for genetic studies', icon: '🧬' },
                  { benefit: 'Hybrid Development', desc: 'Rapid inbred line development', icon: '🌱' },
                ].map((item) => (
                  <div key={item.benefit} className="flex items-start gap-4 p-3 bg-muted rounded-lg">
                    <span className="text-2xl">{item.icon}</span>
                    <div>
                      <h4 className="font-bold">{item.benefit}</h4>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Timeline Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline Comparison</CardTitle>
              <CardDescription>DH vs Conventional breeding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">DH Technology</span>
                    <span className="text-sm text-green-600">1-2 years</span>
                  </div>
                  <Progress value={20} className="h-3 bg-green-100" />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">Conventional (SSD)</span>
                    <span className="text-sm text-orange-600">6-8 years</span>
                  </div>
                  <Progress value={80} className="h-3 bg-orange-100" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
