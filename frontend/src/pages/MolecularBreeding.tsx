/**
 * Molecular Breeding Page
 * Integrated molecular breeding tools and workflows
 * Connected to /api/v2/molecular-breeding/* endpoints
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dna, Target, Layers, Workflow, AlertCircle, FileText, Plus } from 'lucide-react'
import { molecularBreedingAPI, BreedingScheme, IntrogressionLine, MolecularBreedingStatistics } from '@/lib/api-client'

export function MolecularBreeding() {
  const [activeTab, setActiveTab] = useState('schemes')
  const [selectedScheme, setSelectedScheme] = useState('bs1')

  // Fetch breeding schemes
  const { data: schemesData, isLoading: schemesLoading, error: schemesError } = useQuery({
    queryKey: ['molecular-breeding-schemes'],
    queryFn: () => molecularBreedingAPI.getSchemes(),
  })

  // Fetch introgression lines
  const { data: linesData } = useQuery({
    queryKey: ['molecular-breeding-lines'],
    queryFn: () => molecularBreedingAPI.getLines(),
  })

  // Fetch statistics
  const { data: statsData } = useQuery({
    queryKey: ['molecular-breeding-stats'],
    queryFn: () => molecularBreedingAPI.getStatistics(),
  })

  const schemes: BreedingScheme[] = schemesData?.schemes || []
  const lines: IntrogressionLine[] = linesData?.lines || []
  const stats: MolecularBreedingStatistics = statsData?.data || { 
    total_schemes: schemes.length, 
    active_schemes: schemes.filter(s => s.status === 'active').length, 
    total_lines: lines.length, 
    fixed_lines: lines.filter(l => l.foreground_status === 'fixed').length, 
    target_genes: 0, 
    avg_progress: 0 
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-700">Active</Badge>
      case 'completed': return <Badge className="bg-blue-100 text-blue-700">Completed</Badge>
      default: return <Badge variant="secondary">Planned</Badge>
    }
  }

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'MABC': return <Badge className="bg-purple-100 text-purple-700">MABC</Badge>
      case 'MARS': return <Badge className="bg-orange-100 text-orange-700">MARS</Badge>
      case 'GS': return <Badge className="bg-blue-100 text-blue-700">GS</Badge>
      case 'Speed': return <Badge className="bg-green-100 text-green-700">Speed</Badge>
      default: return <Badge variant="secondary">{type}</Badge>
    }
  }

  const getForegroundBadge = (status: string) => {
    switch (status) {
      case 'fixed': return <Badge className="bg-green-100 text-green-700">Fixed</Badge>
      case 'segregating': return <Badge className="bg-yellow-100 text-yellow-700">Segregating</Badge>
      default: return <Badge className="bg-red-100 text-red-700">Absent</Badge>
    }
  }

  if (schemesLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Dna className="h-7 w-7 text-primary" />
            Molecular Breeding
          </h1>
          <p className="text-muted-foreground mt-1">Integrated molecular breeding workflows</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><FileText className="h-4 w-4 mr-2" />Reports</Button>
          <Button><Plus className="h-4 w-4 mr-2" />New Scheme</Button>
        </div>
      </div>

      {schemesError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load molecular breeding data. Please try again.</AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{stats.total_schemes}</p>
            <p className="text-sm text-muted-foreground">Active Schemes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-600">{stats.total_lines}</p>
            <p className="text-sm text-muted-foreground">Introgression Lines</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{stats.target_genes}</p>
            <p className="text-sm text-muted-foreground">Target Genes</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{stats.avg_progress}%</p>
            <p className="text-sm text-muted-foreground">Avg Progress</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="schemes" className="flex items-center gap-1"><Target className="h-4 w-4" />Breeding Schemes</TabsTrigger>
          <TabsTrigger value="mabc" className="flex items-center gap-1"><Dna className="h-4 w-4" />MABC</TabsTrigger>
          <TabsTrigger value="pyramiding" className="flex items-center gap-1"><Layers className="h-4 w-4" />Gene Pyramiding</TabsTrigger>
          <TabsTrigger value="workflow" className="flex items-center gap-1"><Workflow className="h-4 w-4" />Workflow</TabsTrigger>
        </TabsList>

        <TabsContent value="schemes" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Breeding Schemes</CardTitle>
              <CardDescription>Molecular breeding projects and progress</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {schemes.map((scheme) => (
                  <div key={scheme.id} className={`p-4 border rounded-lg cursor-pointer transition-all ${selectedScheme === scheme.id ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'}`} onClick={() => setSelectedScheme(scheme.id)}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <h4 className="font-bold">{scheme.name}</h4>
                        {getTypeBadge(scheme.type)}
                      </div>
                      {getStatusBadge(scheme.status)}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                      <span>Generation: <strong>{scheme.generation}</strong></span>
                      <span>Targets: {scheme.target_traits.join(', ')}</span>
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
                    {lines.map((line) => (
                      <tr key={line.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{line.name}</td>
                        <td className="p-3"><Badge variant="outline">{line.target_gene}</Badge></td>
                        <td className="p-3">{line.donor}</td>
                        <td className="p-3">{line.recurrent}</td>
                        <td className="p-3 text-center">BC{line.bc_generation}</td>
                        <td className="p-3 text-right">
                          <span className={line.rp_recovery >= 90 ? 'text-green-600 font-bold' : line.rp_recovery >= 80 ? 'text-yellow-600' : 'text-red-600'}>
                            {line.rp_recovery}%
                          </span>
                        </td>
                        <td className="p-3 text-center">{getForegroundBadge(line.foreground_status)}</td>
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
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center text-sm font-bold ${i <= 3 ? 'bg-green-100 text-green-700' : 'bg-muted text-muted-foreground'}`}>{gen}</div>
                    {i < 5 && <div className="w-8 h-0.5 bg-muted-foreground/30" />}
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-muted-foreground">
                <span>Foreground</span><span>Background</span><span>Background</span><span>Background</span><span>Selfing</span><span>Fixation</span>
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
              <div className="p-4 bg-muted rounded-lg mb-4">
                <h4 className="font-bold mb-2">Disease Resistance Pyramid</h4>
                <div className="flex flex-wrap gap-2 mb-3">
                  <Badge className="bg-blue-100 text-blue-700">Xa21 (BB)</Badge>
                  <Badge className="bg-green-100 text-green-700">Pi54 (Blast)</Badge>
                  <Badge className="bg-purple-100 text-purple-700">Sub1A (Submergence)</Badge>
                </div>
              </div>
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
                    ].map((row, i) => {
                      const stack = [row.xa21, row.pi54, row.sub1a].filter(Boolean).length
                      return (
                        <tr key={i} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{row.line}</td>
                          <td className="p-3 text-center">{row.xa21 ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">{row.pi54 ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">{row.sub1a ? '✓' : '✗'}</td>
                          <td className="p-3 text-center">
                            <Badge className={stack === 3 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>{stack}/3</Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
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
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${item.status === 'completed' ? 'bg-green-100 text-green-700' : item.status === 'active' ? 'bg-blue-100 text-blue-700' : 'bg-muted text-muted-foreground'}`}>{item.step}</div>
                    <div className="flex-1">
                      <p className="font-medium">{item.title}</p>
                      <p className="text-sm text-muted-foreground">{item.desc}</p>
                    </div>
                    <Badge className={item.status === 'completed' ? 'bg-green-100 text-green-700' : item.status === 'active' ? 'bg-blue-100 text-blue-700' : 'bg-muted text-muted-foreground'}>
                      {item.status === 'completed' ? 'Done' : item.status === 'active' ? 'Active' : 'Pending'}
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
