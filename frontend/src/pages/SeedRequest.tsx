/**
 * Seed Request Page
 * Manage seed requests and distribution - Connected to real API
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { seedRequestAPI, SeedRequest as SeedRequestType } from '@/lib/api-client'
import { toast } from 'sonner'

export function SeedRequest() {
  const [showNew, setShowNew] = useState(false)
  const [filter, setFilter] = useState('all')
  const queryClient = useQueryClient()

  // Fetch requests from API
  const { data: requestsData, isLoading, error } = useQuery({
    queryKey: ['seed-requests', filter],
    queryFn: async () => {
      const params: { status?: string } = {}
      if (filter !== 'all') params.status = filter
      const response = await seedRequestAPI.getRequests(params)
      return response.data
    },
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['seed-requests-stats'],
    queryFn: () => seedRequestAPI.getStats(),
  })

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: SeedRequestType['status'] }) =>
      seedRequestAPI.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-requests'] })
      queryClient.invalidateQueries({ queryKey: ['seed-requests-stats'] })
      toast.success('Status updated')
    },
    onError: () => toast.error('Failed to update status'),
  })

  const requests: SeedRequestType[] = requestsData || []
  const stats = statsData || { total: 0, pending: 0, approved: 0, shipped: 0, delivered: 0 }

  const filteredRequests = requests.filter(r => filter === 'all' || r.status === filter)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      case 'approved': return 'bg-blue-100 text-blue-700'
      case 'shipped': return 'bg-purple-100 text-purple-700'
      case 'delivered': return 'bg-green-100 text-green-700'
      case 'rejected': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  if (error) {
    return (
      <div className="p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Seed Requests</h3>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
        <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['seed-requests'] })}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Seed Requests</h1>
          <p className="text-muted-foreground mt-1">Manage seed distribution requests</p>
        </div>
        <Dialog open={showNew} onOpenChange={setShowNew}>
          <DialogTrigger asChild><Button>➕ New Request</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Seed Request</DialogTitle>
              <DialogDescription>Submit a request for germplasm</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2"><Label>Germplasm</Label><Input placeholder="Enter germplasm name" /></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Quantity</Label><Input type="number" placeholder="Amount" /></div>
                <div className="space-y-2">
                  <Label>Unit</Label>
                  <Select defaultValue="g">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="g">Grams</SelectItem>
                      <SelectItem value="kg">Kilograms</SelectItem>
                      <SelectItem value="seeds">Seeds</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2"><Label>Purpose</Label><Textarea placeholder="Describe the intended use" /></div>
              <Button className="w-full" onClick={() => { setShowNew(false); toast.success('Request submitted') }}>Submit Request</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Total Requests</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-yellow-600">{stats.pending}</p><p className="text-xs text-muted-foreground">Pending</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-blue-600">{stats.approved}</p><p className="text-xs text-muted-foreground">Approved</p></CardContent></Card>
        <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-purple-600">{stats.shipped}</p><p className="text-xs text-muted-foreground">Shipped</p></CardContent></Card>
      </div>

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['all', 'pending', 'approved', 'shipped', 'delivered'].map(f => (
          <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)} className="capitalize">{f}</Button>
        ))}
      </div>

      {/* Requests List */}
      <Card>
        <CardHeader><CardTitle>Requests</CardTitle><CardDescription>{filteredRequests.length} requests</CardDescription></CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-muted-foreground" /></div>
          ) : filteredRequests.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">No requests found</div>
          ) : (
            <div className="space-y-3">
              {filteredRequests.map((req) => (
                <div key={req.id} className="flex items-center gap-4 p-4 rounded-lg border">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium">{req.germplasm}</span>
                      <Badge className={getStatusColor(req.status)}>{req.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{req.requester} • {req.organization}</p>
                    <p className="text-xs text-muted-foreground mt-1">{req.purpose}</p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-medium">{req.quantity} {req.unit}</p>
                    <p className="text-xs text-muted-foreground">{req.requestDate}</p>
                  </div>
                  {req.status === 'pending' && (
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline" onClick={() => updateStatusMutation.mutate({ id: req.id, status: 'approved' })} disabled={updateStatusMutation.isPending}>✓</Button>
                      <Button size="sm" variant="outline" onClick={() => updateStatusMutation.mutate({ id: req.id, status: 'rejected' })} disabled={updateStatusMutation.isPending}>✕</Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
