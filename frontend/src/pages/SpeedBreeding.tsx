/**
 * Speed Breeding Page
 * Accelerated generation advancement protocols
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
import { Zap, Sun, Thermometer, Droplets, Clock, Leaf, Box, Activity } from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function SpeedBreeding() {
  const [activeTab, setActiveTab] = useState('protocols')
  const [selectedCrop, setSelectedCrop] = useState('all')

  // Fetch protocols
  const { data: protocols = [], isLoading: loadingProtocols } = useQuery({
    queryKey: ['speed-breeding-protocols', selectedCrop],
    queryFn: () => apiClient.speedBreedingService.getSpeedBreedingProtocols({
      crop: selectedCrop !== 'all' ? selectedCrop : undefined
    })
  })

  // Fetch batches
  const { data: batches = [], isLoading: loadingBatches } = useQuery({
    queryKey: ['speed-breeding-batches'],
    queryFn: () => apiClient.speedBreedingService.getSpeedBreedingBatches()
  })

  // Fetch chambers
  const { data: chambers = [], isLoading: loadingChambers } = useQuery({
    queryKey: ['speed-breeding-chambers'],
    queryFn: () => apiClient.speedBreedingService.getSpeedBreedingChambers()
  })

  // Fetch statistics
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['speed-breeding-statistics'],
    queryFn: () => apiClient.speedBreedingService.getSpeedBreedingStatistics()
  })

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'growing': return 'bg-green-100 text-green-700'
      case 'flowering': return 'bg-purple-100 text-purple-700'
      case 'harvesting': return 'bg-amber-100 text-amber-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Zap className="h-7 w-7 text-primary" />
            Speed Breeding
          </h1>
          <p className="text-muted-foreground mt-1">Accelerated generation advancement</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedCrop} onValueChange={setSelectedCrop}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Crop" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Crops</SelectItem>
              <SelectItem value="rice">Rice</SelectItem>
              <SelectItem value="wheat">Wheat</SelectItem>
              <SelectItem value="chickpea">Chickpea</SelectItem>
            </SelectContent>
          </Select>
          <Button>
            <Leaf className="h-4 w-4 mr-2" />
            New Batch
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Activity className="h-5 w-5 text-primary" />
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
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Leaf className="h-5 w-5 text-green-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.total_entries?.toLocaleString() || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Total Entries</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/10 rounded-lg">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.avg_generations_per_year || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Gen/Year (Avg)</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Box className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                {loadingStats ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold">{stats?.chambers_in_use || 0}</p>
                )}
                <p className="text-xs text-muted-foreground">Chambers Active</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="protocols">Protocols</TabsTrigger>
          <TabsTrigger value="batches">Active Batches</TabsTrigger>
          <TabsTrigger value="chambers">Growth Chambers</TabsTrigger>
        </TabsList>

        <TabsContent value="protocols" className="space-y-6 mt-4">
          {loadingProtocols ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : protocols.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Zap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No protocols found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {protocols.map((protocol: any) => (
                <Card key={protocol.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-bold text-lg">{protocol.name}</h3>
                        <p className="text-sm text-muted-foreground">{protocol.crop}</p>
                      </div>
                      <Badge variant={protocol.status === 'active' ? 'default' : 'secondary'}>
                        {protocol.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="flex items-center gap-2">
                        <Sun className="h-4 w-4 text-amber-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Photoperiod</p>
                          <p className="text-sm font-medium">{protocol.photoperiod}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-red-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Temperature</p>
                          <p className="text-sm font-medium">
                            {protocol.temperature?.day}°C / {protocol.temperature?.night}°C
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Droplets className="h-4 w-4 text-blue-500" />
                        <div>
                          <p className="text-xs text-muted-foreground">Humidity</p>
                          <p className="text-sm font-medium">{protocol.humidity}%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-primary" />
                        <div>
                          <p className="text-xs text-muted-foreground">Gen/Year</p>
                          <p className="text-sm font-bold text-primary">{protocol.generations_per_year}</p>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t text-sm">
                      <div>
                        <p className="text-muted-foreground">Days to Flower</p>
                        <p className="font-bold">{protocol.days_to_flower}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Days to Harvest</p>
                        <p className="font-bold">{protocol.days_to_harvest}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Success Rate</p>
                        <p className="font-bold text-green-600">{(protocol.success_rate * 100).toFixed(0)}%</p>
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
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full" />)}
            </div>
          ) : batches.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Leaf className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No active batches</p>
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
                          {batch.generation} • {batch.chamber}
                        </p>
                      </div>
                      <Badge className={getStatusColor(batch.status)}>
                        {batch.status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                      <div>
                        <p className="text-muted-foreground">Entries</p>
                        <p className="font-bold">{batch.entries}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Start Date</p>
                        <p className="font-bold">{batch.start_date}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Expected Harvest</p>
                        <p className="font-bold">{batch.expected_harvest}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Progress</p>
                        <p className="font-bold">{batch.progress}%</p>
                      </div>
                    </div>
                    <Progress value={batch.progress} className="h-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="chambers" className="space-y-6 mt-4">
          {loadingChambers ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 w-full" />)}
            </div>
          ) : chambers.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Box className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No chambers configured</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {chambers.map((chamber: any) => (
                <Card key={chamber.name} className={chamber.status === 'active' ? 'border-green-200' : ''}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Box className="h-5 w-5" />
                        {chamber.name}
                      </span>
                      <Badge variant={chamber.status === 'active' ? 'default' : 'outline'}>
                        {chamber.status}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {chamber.batches} batch(es) • {chamber.occupied}/{chamber.capacity} capacity
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <Progress value={(chamber.occupied / chamber.capacity) * 100} className="h-2" />
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Thermometer className="h-4 w-4 text-red-500" />
                          <span>{chamber.temperature}°C</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Droplets className="h-4 w-4 text-blue-500" />
                          <span>{chamber.humidity}%</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Sun className="h-4 w-4 text-amber-500" />
                          <span>{chamber.light_hours}h light</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
