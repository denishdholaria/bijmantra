/**
 * Speed Breeding Page
 * Accelerated generation advancement and rapid cycling
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface SpeedCycle {
  id: string
  name: string
  crop: string
  startDate: string
  currentGen: string
  targetGen: string
  daysPerGen: number
  progress: number
  status: 'active' | 'completed' | 'planned'
}

interface EnvironmentProtocol {
  parameter: string
  value: string
  unit: string
  optimal: string
}

const speedCycles: SpeedCycle[] = [
  { id: 'sc1', name: 'Elite Advancement 2024', crop: 'Wheat', startDate: '2024-01-15', currentGen: 'F5', targetGen: 'F8', daysPerGen: 42, progress: 62, status: 'active' },
  { id: 'sc2', name: 'Disease Resistance Lines', crop: 'Rice', startDate: '2024-02-01', currentGen: 'F4', targetGen: 'F6', daysPerGen: 45, progress: 67, status: 'active' },
  { id: 'sc3', name: 'Quality Improvement', crop: 'Barley', startDate: '2024-03-10', currentGen: 'F3', targetGen: 'F7', daysPerGen: 38, progress: 43, status: 'active' },
  { id: 'sc4', name: 'Drought Tolerance', crop: 'Chickpea', startDate: '2023-11-01', currentGen: 'F8', targetGen: 'F8', daysPerGen: 48, progress: 100, status: 'completed' },
]

const environmentProtocol: EnvironmentProtocol[] = [
  { parameter: 'Photoperiod', value: '22', unit: 'hours', optimal: '20-22 hours' },
  { parameter: 'Light Intensity', value: '500', unit: 'μmol/m²/s', optimal: '400-600' },
  { parameter: 'Temperature (Day)', value: '25', unit: '°C', optimal: '22-28°C' },
  { parameter: 'Temperature (Night)', value: '18', unit: '°C', optimal: '15-20°C' },
  { parameter: 'Humidity', value: '60', unit: '%', optimal: '50-70%' },
  { parameter: 'CO₂ Level', value: '400', unit: 'ppm', optimal: '400-800' },
]

export function SpeedBreeding() {
  const [activeTab, setActiveTab] = useState('cycles')
  const [selectedCrop, setSelectedCrop] = useState('all')

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-700">🔄 Active</Badge>
      case 'completed':
        return <Badge className="bg-blue-100 text-blue-700">✓ Completed</Badge>
      default:
        return <Badge variant="secondary">📋 Planned</Badge>
    }
  }

  const activeCycles = speedCycles.filter(c => c.status === 'active').length
  const avgDaysPerGen = Math.round(speedCycles.reduce((sum, c) => sum + c.daysPerGen, 0) / speedCycles.length)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Speed Breeding</h1>
          <p className="text-muted-foreground mt-1">Accelerated generation advancement</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Crops</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="barley">Barley</SelectItem>
            </SelectContent>
          </Select>
          <Button>➕ New Cycle</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{activeCycles}</p>
            <p className="text-sm text-muted-foreground">Active Cycles</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{avgDaysPerGen}</p>
            <p className="text-sm text-muted-foreground">Avg Days/Generation</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">6-8</p>
            <p className="text-sm text-muted-foreground">Generations/Year</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">3x</p>
            <p className="text-sm text-muted-foreground">Faster than Field</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="cycles">Breeding Cycles</TabsTrigger>
          <TabsTrigger value="protocol">Protocol</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="cycles" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Speed Breeding Cycles</CardTitle>
              <CardDescription>Track generation advancement progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {speedCycles.map((cycle) => (
                  <div key={cycle.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h4 className="font-bold">{cycle.name}</h4>
                        <p className="text-sm text-muted-foreground">{cycle.crop} | Started: {cycle.startDate}</p>
                      </div>
                      {getStatusBadge(cycle.status)}
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                      <div>
                        <p className="text-muted-foreground">Current</p>
                        <p className="font-bold text-lg">{cycle.currentGen}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Target</p>
                        <p className="font-bold text-lg">{cycle.targetGen}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Days/Gen</p>
                        <p className="font-bold text-lg">{cycle.daysPerGen}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Progress</p>
                        <p className="font-bold text-lg text-primary">{cycle.progress}%</p>
                      </div>
                    </div>
                    <Progress value={cycle.progress} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="protocol" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Speed Breeding Protocol</CardTitle>
              <CardDescription>Optimized environmental conditions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Parameter</th>
                      <th className="text-right p-3">Current Value</th>
                      <th className="text-left p-3">Unit</th>
                      <th className="text-left p-3">Optimal Range</th>
                      <th className="text-center p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {environmentProtocol.map((param) => (
                      <tr key={param.parameter} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{param.parameter}</td>
                        <td className="p-3 text-right font-bold">{param.value}</td>
                        <td className="p-3">{param.unit}</td>
                        <td className="p-3 text-muted-foreground">{param.optimal}</td>
                        <td className="p-3 text-center">
                          <Badge className="bg-green-100 text-green-700">✓ Optimal</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Growth Chamber Layout */}
          <Card>
            <CardHeader>
              <CardTitle>Growth Chamber Setup</CardTitle>
              <CardDescription>LED lighting and climate control</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-bold mb-2">💡 Lighting System</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Full spectrum LED (400-700nm)</li>
                    <li>• Extended photoperiod (22h light)</li>
                    <li>• Intensity: 500 μmol/m²/s</li>
                    <li>• Red:Blue ratio optimized</li>
                  </ul>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-bold mb-2">🌡️ Climate Control</h4>
                  <ul className="text-sm space-y-1">
                    <li>• Day/Night temperature cycling</li>
                    <li>• Humidity control (50-70%)</li>
                    <li>• CO₂ supplementation optional</li>
                    <li>• Air circulation fans</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Generation Timeline</CardTitle>
              <CardDescription>Speed breeding vs conventional timeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Speed Breeding Timeline */}
                <div>
                  <h4 className="font-medium mb-2 text-green-700">⚡ Speed Breeding (6-8 weeks/generation)</h4>
                  <div className="flex items-center gap-2">
                    {['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8'].map((gen, i) => (
                      <div key={gen} className="flex items-center">
                        <div className="w-10 h-10 rounded-full bg-green-100 text-green-700 flex items-center justify-center text-xs font-bold">
                          {gen}
                        </div>
                        {i < 7 && <div className="w-4 h-0.5 bg-green-300" />}
                      </div>
                    ))}
                    <span className="ml-2 text-sm text-green-600 font-medium">~1 year</span>
                  </div>
                </div>

                {/* Conventional Timeline */}
                <div>
                  <h4 className="font-medium mb-2 text-orange-700">🌾 Conventional (4-6 months/generation)</h4>
                  <div className="flex items-center gap-2">
                    {['F1', 'F2', 'F3'].map((gen, i) => (
                      <div key={gen} className="flex items-center">
                        <div className="w-10 h-10 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center text-xs font-bold">
                          {gen}
                        </div>
                        {i < 2 && <div className="w-8 h-0.5 bg-orange-300" />}
                      </div>
                    ))}
                    <span className="ml-2 text-sm text-orange-600 font-medium">~1 year</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Speed Breeding Benefits</CardTitle>
              <CardDescription>Comparison with conventional breeding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Aspect</th>
                      <th className="text-center p-3">Conventional</th>
                      <th className="text-center p-3">Speed Breeding</th>
                      <th className="text-center p-3">Improvement</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { aspect: 'Generations/Year', conv: '2-3', speed: '6-8', imp: '3x faster' },
                      { aspect: 'Time to Homozygosity', conv: '4-5 years', speed: '1-2 years', imp: '60% reduction' },
                      { aspect: 'Variety Development', conv: '10-12 years', speed: '5-7 years', imp: '40% faster' },
                      { aspect: 'Space Required', conv: 'Large fields', speed: 'Growth chambers', imp: '90% less' },
                      { aspect: 'Season Dependency', conv: 'High', speed: 'None', imp: 'Year-round' },
                    ].map((row, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{row.aspect}</td>
                        <td className="p-3 text-center">{row.conv}</td>
                        <td className="p-3 text-center font-bold text-green-600">{row.speed}</td>
                        <td className="p-3 text-center">
                          <Badge className="bg-green-100 text-green-700">{row.imp}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
