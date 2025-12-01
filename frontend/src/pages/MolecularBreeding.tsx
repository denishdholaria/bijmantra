/**
 * Molecular Breeding Page
 * Integrated molecular breeding tools and workflows
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'

interface BreedingScheme {
  id: string
  name: string
  type: 'MABC' | 'MARS' | 'GS' | 'Speed'
  status: 'active' | 'completed' | 'planned'
  generation: string
  progress: number
  targetTraits: string[]
}

interface IntrogressionLine {
  id: string
  name: string
  donor: string
  recurrent: string
  targetGene: string
  bcGeneration: number
  rpRecovery: number
  foregroundStatus: 'fixed' | 'segregating' | 'absent'
}

const breedingSchemes: BreedingScheme[] = [
  { id: 'bs1', name: 'Drought Tolerance Introgression', type: 'MABC', status: 'active', generation: 'BC3F2', progress: 75, targetTraits: ['qDTY1.1', 'qDTY3.1'] },
  { id: 'bs2', name: 'Disease Resistance Pyramiding', type: 'MABC', status: 'active', generation: 'BC2F3', progress: 60, targetTraits: ['Xa21', 'Pi54', 'Sub1A'] },
  { id: 'bs3', name: 'Yield Improvement GS', type: 'GS', status: 'active', generation: 'C2', progress: 40, targetTraits: ['Grain Yield', 'Grain Weight'] },
  { id: 'bs4', name: 'Quality Enhancement MARS', type: 'MARS', status: 'planned', generation: 'F2', progress: 10, targetTraits: ['Protein', 'Amylose'] },
  { id: 'bs5', name: 'Speed Breeding Elite', type: 'Speed', status: 'active', generation: 'F5', progress: 85, targetTraits: ['Multiple'] },
]

const introgressionLines: IntrogressionLine[] = [
  { id: 'il1', name: 'IL-DT-001', donor: 'Donor-A', recurrent: 'Elite-001', targetGene: 'qDTY1.1', bcGeneration: 3, rpRecovery: 92, foregroundStatus: 'fixed' },
  { id: 'il2', name: 'IL-DT-002', donor: 'Donor-A', recurrent: 'Elite-001', targetGene: 'qDTY1.1', bcGeneration: 3, rpRecovery: 88, foregroundStatus: 'fixed' },
  { id: 'il3', name: 'IL-BR-001', donor: 'Donor-B', recurrent: 'Elite-002', targetGene: 'Xa21', bcGeneration: 2, rpRecovery: 78, foregroundStatus: 'segregating' },
  { id: 'il4', name: 'IL-BR-002', donor: 'Donor-C', recurrent: 'Elite-002', targetGene: 'Pi54', bcGeneration: 2, rpRecovery: 82, foregroundStatus: 'fixed' },
  { id: 'il5', name: 'IL-SUB-001', donor: 'FR13A', recurrent: 'Elite-003', targetGene: 'Sub1A', bcGeneration: 3, rpRecovery: 95, foregroundStatus: 'fixed' },
]

export function MolecularBreeding() {
  const [activeTab, setActiveTab] = useState('schemes')
  const [selectedScheme, setSelectedScheme] = useState('bs1')

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

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'MABC':
        return <Badge className="bg-purple-100 text-purple-700">MABC</Badge>
      case 'MARS':
        return <Badge className="bg-orange-100 text-orange-700">MARS</Badge>
      case 'GS':
        return <Badge className="bg-blue-100 text-blue-700">GS</Badge>
      case 'Speed':
        return <Badge className="bg-green-100 text-green-700">Speed</Badge>
      default:
        return <Badge variant="secondary">{type}</Badge>
    }
  }

  const getForegroundBadge = (status: string) => {
    switch (status) {
      case 'fixed':
        return <Badge className="bg-green-100 text-green-700">✓ Fixed</Badge>
      case 'segregating':
        return <Badge className="bg-yellow-100 text-yellow-700">~ Segregating</Badge>
      default:
        return <Badge className="bg-red-100 text-red-700">✗ Absent</Badge>
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Molecular Breeding</h1>
          <p className="text-muted-foreground mt-1">Integrated molecular breeding workflows</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📊 Reports</Button>
          <Button>➕ New Scheme</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{breedingSchemes.length}</p>
            <p className="text-sm text-muted-foreground">Active Schemes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{introgressionLines.length}</p>
            <p className="text-sm text-muted-foreground">Introgression Lines</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">8</p>
            <p className="text-sm text-muted-foreground">Target Genes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">65%</p>
            <p className="text-sm text-muted-foreground">Avg Progress</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="schemes">Breeding Schemes</TabsTrigger>
          <TabsTrigger value="mabc">MABC</TabsTrigger>
          <TabsTrigger value="pyramiding">Gene Pyramiding</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
        </TabsList>

        <TabsContent value="schemes" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Breeding Schemes</CardTitle>
              <CardDescription>Molecular breeding projects and progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {breedingSchemes.map((scheme) => (
                  <div 
                    key={scheme.id} 
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedScheme === scheme.id ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'
                    }`}
                    onClick={() => setSelectedScheme(scheme.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <h4 className="font-bold">{scheme.name}</h4>
                        {getTypeBadge(scheme.type)}
                      </div>
                      {getStatusBadge(scheme.status)}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                      <span>Generation: <strong>{scheme.generation}</strong></span>
                      <span>Targets: {scheme.targetTraits.join(', ')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={scheme.progress} className="flex-1 h-2" />
                      <span className="text-sm font-bold">{scheme.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="mabc" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Marker-Assisted Backcrossing</CardTitle>
              <CardDescription>Introgression line development and tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Line</th>
                      <th className="text-left p-3">Target Gene</th>
                      <th className="text-left p-3">Donor</th>
                      <th className="text-left p-3">Recurrent</th>
                      <th className="text-center p-3">BC Gen</th>
                      <th className="text-right p-3">RP Recovery</th>
                      <th className="text-center p-3">Foreground</th>
                    </tr>
                  </thead>
                  <tbody>
                    {introgressionLines.map((line) => (
                      <tr key={line.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{line.name}</td>
                        <td className="p-3">
                          <Badge variant="outline">{line.targetGene}</Badge>
                        </td>
                        <td className="p-3">{line.donor}</td>
                        <td className="p-3">{line.recurrent}</td>
                        <td className="p-3 text-center">BC{line.bcGeneration}</td>
                        <td className="p-3 text-right">
                          <span className={line.rpRecovery >= 90 ? 'text-green-600 font-bold' : line.rpRecovery >= 80 ? 'text-yellow-600' : 'text-red-600'}>
                            {line.rpRecovery}%
                          </span>
                        </td>
                        <td className="p-3 text-center">{getForegroundBadge(line.foregroundStatus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* MABC Workflow */}
          <Card>
            <CardHeader>
              <CardTitle>MABC Workflow</CardTitle>
              <CardDescription>Standard backcross breeding pipeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                {['F1', 'BC1F1', 'BC2F1', 'BC3F1', 'BC3F2', 'BC3F3'].map((gen, i) => (
                  <div key={gen} className="flex items-center">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center text-sm font-bold ${
                      i <= 3 ? 'bg-green-100 text-green-700' : 'bg-muted text-muted-foreground'
                    }`}>
                      {gen}
                    </div>
                    {i < 5 && <div className="w-8 h-0.5 bg-muted-foreground/30" />}
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>Foreground</span>
                <span>Background</span>
                <span>Background</span>
                <span>Background</span>
                <span>Selfing</span>
                <span>Fixation</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pyramiding" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Gene Pyramiding</CardTitle>
              <CardDescription>Stack multiple genes in elite background</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-bold mb-2">Disease Resistance Pyramid</h4>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <Badge className="bg-blue-100 text-blue-700">Xa21 (BB)</Badge>
                    <Badge className="bg-green-100 text-green-700">Pi54 (Blast)</Badge>
                    <Badge className="bg-purple-100 text-purple-700">Sub1A (Submergence)</Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Target Lines</p>
                      <p className="font-bold">12</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Triple Stack</p>
                      <p className="font-bold text-green-600">3 lines</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Generation</p>
                      <p className="font-bold">BC2F3</p>
                    </div>
                  </div>
                </div>

                {/* Pyramiding Matrix */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Line</th>
                        <th className="text-center p-3">Xa21</th>
                        <th className="text-center p-3">Pi54</th>
                        <th className="text-center p-3">Sub1A</th>
                        <th className="text-center p-3">Stack</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { line: 'Pyramid-001', xa21: true, pi54: true, sub1a: true },
                        { line: 'Pyramid-002', xa21: true, pi54: true, sub1a: false },
                        { line: 'Pyramid-003', xa21: true, pi54: false, sub1a: true },
                        { line: 'Pyramid-004', xa21: false, pi54: true, sub1a: true },
                      ].map((row, i) => {
                        const stack = [row.xa21, row.pi54, row.sub1a].filter(Boolean).length
                        return (
                          <tr key={i} className="border-b hover:bg-muted/50">
                            <td className="p-3 font-medium">{row.line}</td>
                            <td className="p-3 text-center">{row.xa21 ? '✓' : '✗'}</td>
                            <td className="p-3 text-center">{row.pi54 ? '✓' : '✗'}</td>
                            <td className="p-3 text-center">{row.sub1a ? '✓' : '✗'}</td>
                            <td className="p-3 text-center">
                              <Badge className={stack === 3 ? 'bg-green-100 text-green-700' : stack === 2 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}>
                                {stack}/3
                              </Badge>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflow" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Molecular Breeding Workflow</CardTitle>
              <CardDescription>Step-by-step breeding process</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { step: 1, title: 'Define Objectives', desc: 'Identify target traits and genes', status: 'completed' },
                  { step: 2, title: 'Donor Selection', desc: 'Select donors with target alleles', status: 'completed' },
                  { step: 3, title: 'Marker Development', desc: 'Develop/validate markers for MAS', status: 'completed' },
                  { step: 4, title: 'Crossing', desc: 'Make initial crosses', status: 'completed' },
                  { step: 5, title: 'Foreground Selection', desc: 'Screen for target genes', status: 'active' },
                  { step: 6, title: 'Background Selection', desc: 'Recover recurrent parent genome', status: 'active' },
                  { step: 7, title: 'Phenotyping', desc: 'Validate trait expression', status: 'pending' },
                  { step: 8, title: 'Release', desc: 'Variety release and deployment', status: 'pending' },
                ].map((item) => (
                  <div key={item.step} className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      item.status === 'completed' ? 'bg-green-100 text-green-700' :
                      item.status === 'active' ? 'bg-blue-100 text-blue-700' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {item.step}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{item.title}</p>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                    <Badge className={
                      item.status === 'completed' ? 'bg-green-100 text-green-700' :
                      item.status === 'active' ? 'bg-blue-100 text-blue-700' :
                      'bg-muted text-muted-foreground'
                    }>
                      {item.status === 'completed' ? '✓ Done' : item.status === 'active' ? '🔄 Active' : '⏳ Pending'}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
