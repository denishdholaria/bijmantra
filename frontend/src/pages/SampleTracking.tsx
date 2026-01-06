/**
 * Sample Tracking Page
 * Track samples through the pipeline - Connected to real API
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Package, Search, QrCode, MapPin, Clock, CheckCircle, AlertCircle, Truck, Loader2 } from 'lucide-react'
import { sampleTrackingAPI, Sample } from '@/lib/api-client'

export function SampleTracking() {
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Fetch samples from API
  const { data: samplesData, isLoading, error } = useQuery({
    queryKey: ['sample-tracking', activeTab, searchQuery],
    queryFn: async () => {
      const params: { status?: string; search?: string } = {}
      if (activeTab !== 'all') params.status = activeTab
      if (searchQuery) params.search = searchQuery
      const response = await sampleTrackingAPI.getSamples(params)
      return response.data
    },
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['sample-tracking-stats'],
    queryFn: () => sampleTrackingAPI.getStats(),
  })

  const samples: Sample[] = samplesData || []
  const stats = statsData || { total: 0, collected: 0, processing: 0, stored: 0, shipped: 0 }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'collected': return <Package className="h-4 w-4 text-blue-500" />
      case 'processing': return <Clock className="h-4 w-4 text-yellow-500" />
      case 'stored': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'shipped': return <Truck className="h-4 w-4 text-purple-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { 
      collected: 'bg-blue-100 text-blue-800', 
      processing: 'bg-yellow-100 text-yellow-800', 
      stored: 'bg-green-100 text-green-800', 
      shipped: 'bg-purple-100 text-purple-800' 
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { 
      leaf: 'bg-green-100 text-green-800', 
      seed: 'bg-orange-100 text-orange-800', 
      dna: 'bg-pink-100 text-pink-800' 
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        Failed to load samples. Please try again.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sample Tracking</h1>
          <p className="text-muted-foreground">Track samples through the pipeline</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><QrCode className="mr-2 h-4 w-4" />Scan</Button>
          <Button><Package className="mr-2 h-4 w-4" />New Sample</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.collected}</p>
              <p className="text-xs text-muted-foreground">Collected</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">{stats.processing}</p>
              <p className="text-xs text-muted-foreground">Processing</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{stats.stored}</p>
              <p className="text-xs text-muted-foreground">Stored</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{stats.shipped}</p>
              <p className="text-xs text-muted-foreground">Shipped</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search samples..." 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
            className="pl-9" 
          />
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="collected">Collected</TabsTrigger>
          <TabsTrigger value="processing">Processing</TabsTrigger>
          <TabsTrigger value="stored">Stored</TabsTrigger>
          <TabsTrigger value="shipped">Shipped</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                </div>
              ) : samples.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No samples found
                </div>
              ) : (
                <div className="divide-y">
                  {samples.map((sample) => (
                    <div key={sample.id} className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4">
                        {getStatusIcon(sample.status)}
                        <div>
                          <p className="font-medium">{sample.sampleId}</p>
                          <p className="text-sm text-muted-foreground">Source: {sample.source}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right text-sm">
                          <p className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />{sample.location}
                          </p>
                          <p className="text-muted-foreground">Collected: {sample.collectedAt}</p>
                        </div>
                        <Badge className={getTypeColor(sample.type)}>{sample.type}</Badge>
                        <Badge className={getStatusColor(sample.status)}>{sample.status}</Badge>
                        <Button variant="outline" size="sm">Track</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
