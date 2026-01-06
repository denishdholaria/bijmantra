/**
 * Doubled Haploid Page
 * DH production and management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Dna, FlaskConical, Microscope, Leaf, Target, Activity, Beaker, ArrowRight } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function DoubledHaploid() {
  const [activeTab, setActiveTab] = useState('protocols')
  const [selectedCrop, setSelectedCrop] = useState('all')
  const [selectedMethod, setSelectedMethod] = useState('all')

  // Fetch protocols
  const { data: protocols = [], isLoading: loadingProtocols } = useQuery({
    queryKey: ['dh-protocols', selectedCrop, selectedMethod],
    queryFn: () => apiClient.getDoubledHaploidProtocols({
      crop: selectedCrop !== 'all' ? selectedCrop : undefined,
      method: selectedMethod !== 'all' ? selectedMethod : undefined
    })
  })

  // Fetch batches
  const { data: batches = [], isLoading: loadingBatches } = useQuery({
    queryKey: ['dh-batches'],
    queryFn: () => apiClient.getDoubledHaploidBatches()
  })

  // Fetch statistics
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['dh-statistics'],
    queryFn: () => apiClient.getDoubledHaploidStatistics()
  })

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'bg-green-100 text-green-700'
      case 'completed': return 'bg-blue-100 text-blue-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getMethodIcon = (method: string) => {
    if (method?.toLowerCase().includes('anther')) return <FlaskConical className="h-5 w-5" />
    if (method?.toLowerCase().includes('microspore')) return <Microscope className="h-5 w-5" />
    return <Dna className="h-5 w-5" />
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Dna className="h-7 w-7 text-primary" />
            Doubled Haploid
          </h1>
          <p className="text-muted-foreground mt-1">DH production and management</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Crops</SelectItem>
              <SelectItem value="maize">Maize</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="barley">Barley</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedMethod} onValueChange={setSelectedMethod}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Method" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Methods</SelectItem>
              <SelectItem value="anther">Anther Culture</SelectItem>
              <SelectItem value="microspore">Microspore</SelectItem>
              <SelectItem value="vivo">In Vivo</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Beaker className="h-5 w-5 text-primary" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_protocols || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Protocols</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Activity className="h-5 w-5 text-green-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.active_batches || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Active Batches</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Leaf className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_dh_lines_produced || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">DH Lines Produced</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <Target className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{((stats?.avg_efficiency || 0) * 100).toFixed(1)}%</p>
                )}
                <p className="text-xs text-muted-foreground">Avg Efficiency</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="protocols">Protocols</TabsTrigger>
          <TabsTrigger value="batches">Production Batches</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
        </TabsList>

        <TabsContent value="protocols" className="space-y-6 mt-4">
          {loadingProtocols ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full" />)}
            </div>
          ) : protocols.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Dna className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No protocols found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {protocols.map((protocol: any) => (
                <Card key={protocol.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          {getMethodIcon(protocol.method)}
                        </div>
                        <div>
                          <h3 className="font-bold text-lg">{protocol.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {protocol.crop} • {protocol.method}
                          </p>
                        </div>
                      </div>
                      <Badge variant={protocol.status === 'active' ? 'default' : 'secondary'}>
                        {protocol.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Inducer</p>
                        <p className="font-medium">{protocol.inducer || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Induction Rate</p>
                        <p className="font-medium">{(protocol.induction_rate * 100).toFixed(0)}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Doubling Agent</p>
                        <p className="font-medium">{protocol.doubling_agent}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Doubling Rate</p>
                        <p className="font-medium">{(protocol.doubling_rate * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t text-sm">
                      <div>
                        <p className="text-muted-foreground">Overall Efficiency</p>
                        <p className="font-bold text-primary">{(protocol.overall_efficiency * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Days to Complete</p>
                        <p className="font-bold">{protocol.days_to_complete} days</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="batches" className="space-y-6 mt-4">
          {loadingBatches ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : batches.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FlaskConical className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No production batches</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {batches.map((batch: any) => (
                <Card key={batch.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-bold">{batch.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {batch.donor_cross} • Started {batch.start_date}
                        </p>
                      </div>
                      <Badge className={getStatusColor(batch.status)}>
                        {batch.status}
                      </Badge>
                    </div>
                    <div className="mb-3">
                      <p className="text-sm text-muted-foreground mb-1">Current Stage</p>
                      <Badge variant="outline" className="text-sm">{batch.stage}</Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Donor Plants</p>
                        <p className="font-bold">{batch.donor_plants}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {batch.haploids_induced ? 'Haploids Induced' : 'Anthers Cultured'}
                        </p>
                        <p className="font-bold">
                          {batch.haploids_induced || batch.anthers_cultured || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {batch.haploids_identified ? 'Identified' : 'Embryos'}
                        </p>
                        <p className="font-bold">
                          {batch.haploids_identified || batch.embryos_formed || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {batch.doubled_plants ? 'Doubled' : 'Regenerated'}
                        </p>
                        <p className="font-bold">
                          {batch.doubled_plants || batch.plants_regenerated || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Fertile DH Lines</p>
                        <p className="font-bold text-green-600">{batch.fertile_dh_lines}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="workflow" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Anther Culture Workflow */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FlaskConical className="h-5 w-5" />
                  Anther Culture Workflow
                </CardTitle>
                <CardDescription>In vitro DH production</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { step: 1, name: 'Donor plant growth', days: 60 },
                    { step: 2, name: 'Anther collection', days: 7 },
                    { step: 3, name: 'Culture initiation', days: 14 },
                    { step: 4, name: 'Embryo induction', days: 30 },
                    { step: 5, name: 'Plant regeneration', days: 45 },
                    { step: 6, name: 'Chromosome doubling', days: 14 },
                    { step: 7, name: 'Hardening & transfer', days: 28 },
                  ].map((stage, idx, arr) => (
                    <div key={stage.step} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold">
                        {stage.step}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{stage.name}</p>
                        <p className="text-xs text-muted-foreground">{stage.days} days</p>
                      </div>
                      {idx < arr.length - 1 && <ArrowRight className="h-4 w-4 text-muted-foreground" />}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* In Vivo Workflow */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Dna className="h-5 w-5" />
                  In Vivo Haploid Induction
                </CardTitle>
                <CardDescription>Maternal haploid induction (Maize)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { step: 1, name: 'Donor plant growth', days: 60 },
                    { step: 2, name: 'Pollination with inducer', days: 7 },
                    { step: 3, name: 'Seed harvest', days: 45 },
                    { step: 4, name: 'Haploid identification', days: 14 },
                    { step: 5, name: 'Chromosome doubling', days: 14 },
                    { step: 6, name: 'D0 plant growth', days: 60 },
                    { step: 7, name: 'Seed multiplication', days: 90 },
                  ].map((stage, idx, arr) => (
                    <div key={stage.step} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-sm font-bold text-green-600">
                        {stage.step}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{stage.name}</p>
                        <p className="text-xs text-muted-foreground">{stage.days} days</p>
                      </div>
                      {idx < arr.length - 1 && <ArrowRight className="h-4 w-4 text-muted-foreground" />}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Efficiency Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Method Comparison</CardTitle>
              <CardDescription>Efficiency by DH production method</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { method: 'Anther Culture (Wheat)', efficiency: 0.09, color: 'bg-blue-500' },
                  { method: 'Anther Culture (Rice)', efficiency: 0.14, color: 'bg-green-500' },
                  { method: 'Microspore Culture (Barley)', efficiency: 0.10, color: 'bg-purple-500' },
                  { method: 'In Vivo Maternal (Maize)', efficiency: 0.025, color: 'bg-amber-500' },
                ].map((item) => (
                  <div key={item.method} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{item.method}</span>
                      <span className="font-bold">{(item.efficiency * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={item.efficiency * 100 * 5} className="h-2" />
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
