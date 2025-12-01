/**
 * Seed Request Page
 * Manage seed requests and distribution
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { toast } from 'sonner'

interface SeedRequest {
  id: string
  requester: string
  organization: string
  germplasm: string
  quantity: number
  unit: string
  purpose: string
  status: 'pending' | 'approved' | 'shipped' | 'delivered' | 'rejected'
  requestDate: string
}

const sampleRequests: SeedRequest[] = [
  { id: 'REQ001', requester: 'Dr. Smith', organization: 'University A', germplasm: 'Elite Variety 2024', quantity: 500, unit: 'g', purpose: 'Research trial', status: 'pending', requestDate: '2024-11-28' },
  { id: 'REQ002', requester: 'Dr. Johnson', organization: 'Research Institute B', germplasm: 'Disease Resistant B', quantity: 1000, unit: 'g', purpose: 'Multi-location trial', status: 'approved', requestDate: '2024-11-25' },
  { id: 'REQ003', requester: 'Dr. Williams', organization: 'Seed Company C', germplasm: 'High Yield Line A', quantity: 2000, unit: 'g', purpose: 'Variety testing', status: 'shipped', requestDate: '2024-11-20' },
  { id: 'REQ004', requester: 'Dr. Brown', organization: 'University D', germplasm: 'Check Variety', quantity: 200, unit: 'g', purpose: 'Teaching', status: 'delivered', requestDate: '2024-11-15' },
]

export function SeedRequest() {
  const [requests, setRequests] = useState<SeedRequest[]>(sampleRequests)
  const [showNew, setShowNew] = useState(false)
  const [filter, setFilter] = useState('all')

  const filteredRequests = requests.filter(r => filter === 'all' || r.status === filter)

  const stats = {
    total: requests.length,
    pending: requests.filter(r => r.status === 'pending').length,
    approved: requests.filter(r => r.status === 'approved').length,
    shipped: requests.filter(r => r.status === 'shipped').length,
  }

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

  const updateStatus = (id: string, status: SeedRequest['status']) => {
    setRequests(prev => prev.map(r => r.id === id ? { ...r, status } : r))
    toast.success('Status updated')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Seed Requests</h1>
          <p className="text-muted-foreground mt-1">Manage seed distribution requests</p>
        </div>
        <Dialog open={showNew} onOpenChange={setShowNew}>
          <DialogTrigger asChild>
            <Button>➕ New Request</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Seed Request</DialogTitle>
              <DialogDescription>Submit a request for germplasm</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Germplasm</Label>
                <Input placeholder="Enter germplasm name" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Quantity</Label>
                  <Input type="number" placeholder="Amount" />
                </div>
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
              <div className="space-y-2">
                <Label>Purpose</Label>
                <Textarea placeholder="Describe the intended use" />
              </div>
              <Button className="w-full" onClick={() => { setShowNew(false); toast.success('Request submitted') }}>
                Submit Request
              </Button>
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
          <Button key={f} size="sm" variant={filter === f ? 'default' : 'outline'} onClick={() => setFilter(f)} className="capitalize">
            {f}
          </Button>
        ))}
      </div>

      {/* Requests List */}
      <Card>
        <CardHeader>
          <CardTitle>Requests</CardTitle>
          <CardDescription>{filteredRequests.length} requests</CardDescription>
        </CardHeader>
        <CardContent>
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
                    <Button size="sm" variant="outline" onClick={() => updateStatus(req.id, 'approved')}>✓</Button>
                    <Button size="sm" variant="outline" onClick={() => updateStatus(req.id, 'rejected')}>✕</Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
