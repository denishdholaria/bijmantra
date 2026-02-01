/**
 * Nursery Management Page
 * Manage nursery activities and seedling production
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface NurseryBatch {
  id: string
  germplasm: string
  sowingDate: string
  expectedTransplant: string
  quantity: number
  germinated: number
  healthy: number
  status: 'sowing' | 'germinating' | 'growing' | 'ready' | 'transplanted'
  location: string
}

export function NurseryManagement() {
  const [search, setSearch] = useState('')
  const queryClient = useQueryClient()

  // Fetch batches from API
  const { data: batchesData, isLoading } = useQuery({
    queryKey: ['nursery-batches'],
    queryFn: () => apiClient.seedlingBatchService.getBatches(),
  })

  // Fetch stats from API
  const { data: statsData } = useQuery({
    queryKey: ['nursery-stats'],
    queryFn: () => apiClient.seedlingBatchService.getStats(),
  })

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiClient.seedlingBatchService.updateBatchStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nursery-batches'] })
      queryClient.invalidateQueries({ queryKey: ['nursery-stats'] })
      toast.success('Status updated')
    },
    onError: () => {
      toast.error('Failed to update status')
    },
  })

  const batches: NurseryBatch[] = batchesData?.batches || []

  const filteredBatches = batches.filter(b => 
    b.germplasm.toLowerCase().includes(search.toLowerCase()) ||
    b.id.toLowerCase().includes(search.toLowerCase())
  )

  const stats = statsData || {
    total: batches.length,
    sowing: batches.filter(b => b.status === 'sowing').length,
    growing: batches.filter(b => ['germinating', 'growing'].includes(b.status)).length,
    ready: batches.filter(b => b.status === 'ready').length,
    totalSeedlings: batches.reduce((sum, b) => sum + b.healthy, 0),
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sowing': return 'bg-gray-100 text-gray-700'
      case 'germinating': return 'bg-yellow-100 text-yellow-700'
      case 'growing': return 'bg-blue-100 text-blue-700'
      case 'ready': return 'bg-green-100 text-green-700'
      case 'transplanted': return 'bg-purple-100 text-purple-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const updateStatus = (id: string, newStatus: NurseryBatch['status']) => {
    updateStatusMutation.mutate({ id, status: newStatus })
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Nursery Management</h1>
            <p className="text-muted-foreground mt-1">Manage seedling production</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i}><CardContent className="pt-4"><Skeleton className="h-8 w-16 mx-auto" /></CardContent></Card>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i}><CardContent className="pt-4"><Skeleton className="h-32" /></CardContent></Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Nursery Management</h1>
          <p className="text-muted-foreground mt-1">Manage seedling production</p>
        </div>
        <Button>➕ New Batch</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total Batches</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-gray-600">{stats.sowing}</p><p className="text-xs text-muted-foreground">Sowing</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.growing}</p><p className="text-xs text-muted-foreground">Growing</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-600">{stats.ready}</p><p className="text-xs text-muted-foreground">Ready</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.totalSeedlings.toLocaleString()}</p><p className="text-xs text-muted-foreground">Healthy Seedlings</p></CardContent></Card>
      </div>

      {/* Search */}
      <Input
        placeholder="Search batches..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {/* Batches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBatches.map((batch) => {
          const germinationRate = batch.quantity > 0 ? (batch.germinated / batch.quantity) * 100 : 0
          const survivalRate = batch.germinated > 0 ? (batch.healthy / batch.germinated) * 100 : 0
          
          return (
            <Card key={batch.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{batch.germplasm}</CardTitle>
                    <CardDescription>{batch.id}</CardDescription>
                  </div>
                  <Badge className={getStatusColor(batch.status)}>{batch.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2 text-center text-sm">
                  <div>
                    <p className="font-bold">{batch.quantity}</p>
                    <p className="text-xs text-muted-foreground">Sown</p>
                  </div>
                  <div>
                    <p className="font-bold text-blue-600">{batch.germinated}</p>
                    <p className="text-xs text-muted-foreground">Germinated</p>
                  </div>
                  <div>
                    <p className="font-bold text-green-600">{batch.healthy}</p>
                    <p className="text-xs text-muted-foreground">Healthy</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Germination</span>
                      <span>{germinationRate.toFixed(0)}%</span>
                    </div>
                    <Progress value={germinationRate} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Survival</span>
                      <span>{survivalRate.toFixed(0)}%</span>
                    </div>
                    <Progress value={survivalRate} className="h-2" />
                  </div>
                </div>

                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>📍 {batch.location}</span>
                  <span>🗓️ {batch.expectedTransplant}</span>
                </div>

                {batch.status === 'ready' && (
                  <Button 
                    size="sm" 
                    className="w-full"
                    onClick={() => updateStatus(batch.id, 'transplanted')}
                  >
                    🌱 Mark Transplanted
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
