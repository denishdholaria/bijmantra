/**
 * Vendor Orders Page - BrAPI Genotyping Module
 * Genotyping service orders management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

interface VendorOrder {
  orderId: string
  clientId: string
  serviceId: string
  serviceName: string
  numberOfSamples: number
  status: 'submitted' | 'received' | 'inProgress' | 'completed' | 'rejected'
  submittedDate: string
  expectedDate?: string
  completedDate?: string
}

const mockOrders: VendorOrder[] = [
  { orderId: 'ORD-2024-001', clientId: 'CLIENT001', serviceId: 'GBS', serviceName: 'GBS Sequencing', numberOfSamples: 96, status: 'completed', submittedDate: '2024-01-10', expectedDate: '2024-02-10', completedDate: '2024-02-08' },
  { orderId: 'ORD-2024-002', clientId: 'CLIENT001', serviceId: 'SNP', serviceName: 'SNP Array', numberOfSamples: 384, status: 'inProgress', submittedDate: '2024-02-01', expectedDate: '2024-03-01' },
  { orderId: 'ORD-2024-003', clientId: 'CLIENT002', serviceId: 'WGS', serviceName: 'Whole Genome Seq', numberOfSamples: 24, status: 'received', submittedDate: '2024-02-15', expectedDate: '2024-04-15' },
  { orderId: 'ORD-2024-004', clientId: 'CLIENT001', serviceId: 'GBS', serviceName: 'GBS Sequencing', numberOfSamples: 192, status: 'submitted', submittedDate: '2024-02-20', expectedDate: '2024-03-20' },
]

export function VendorOrders() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['vendorOrders', search, statusFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockOrders
      if (search) {
        filtered = filtered.filter(o => 
          o.orderId.toLowerCase().includes(search.toLowerCase()) ||
          o.serviceName.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (statusFilter !== 'all') {
        filtered = filtered.filter(o => o.status === statusFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const orders = data?.result?.data || []

  const getStatusBadge = (status: VendorOrder['status']) => {
    const styles: Record<string, string> = {
      submitted: 'bg-blue-100 text-blue-800',
      received: 'bg-yellow-100 text-yellow-800',
      inProgress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
    }
    const labels: Record<string, string> = {
      submitted: 'Submitted',
      received: 'Received',
      inProgress: 'In Progress',
      completed: 'Completed',
      rejected: 'Rejected',
    }
    return <Badge className={styles[status]}>{labels[status]}</Badge>
  }

  const handleCreate = () => {
    toast.success('Order submitted (demo)')
    setIsCreateOpen(false)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Vendor Orders</h1>
          <p className="text-muted-foreground mt-1">Genotyping service orders</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>📦 New Order</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit New Order</DialogTitle>
              <DialogDescription>Create a genotyping service order</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Service Type</Label>
                <Select defaultValue="GBS">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GBS">GBS Sequencing</SelectItem>
                    <SelectItem value="SNP">SNP Array</SelectItem>
                    <SelectItem value="WGS">Whole Genome Sequencing</SelectItem>
                    <SelectItem value="KASP">KASP Genotyping</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Number of Samples</Label>
                <Input type="number" placeholder="96" />
              </div>
              <div className="space-y-2">
                <Label>Plate IDs (comma-separated)</Label>
                <Input placeholder="PLATE_001, PLATE_002" />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Input placeholder="Special instructions..." />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Submit Order</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search orders..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="submitted">Submitted</SelectItem>
                <SelectItem value="received">Received</SelectItem>
                <SelectItem value="inProgress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockOrders.length}</div>
            <p className="text-sm text-muted-foreground">Total Orders</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockOrders.filter(o => o.status === 'inProgress').length}</div>
            <p className="text-sm text-muted-foreground">In Progress</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockOrders.reduce((a, o) => a + o.numberOfSamples, 0)}</div>
            <p className="text-sm text-muted-foreground">Total Samples</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockOrders.filter(o => o.status === 'completed').length}</div>
            <p className="text-sm text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Orders</CardTitle>
            <CardDescription>{orders.length} orders found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order ID</TableHead>
                  <TableHead>Service</TableHead>
                  <TableHead>Samples</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.orderId}>
                    <TableCell className="font-medium">{order.orderId}</TableCell>
                    <TableCell>{order.serviceName}</TableCell>
                    <TableCell>{order.numberOfSamples}</TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell>{order.submittedDate}</TableCell>
                    <TableCell>{order.expectedDate || '-'}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost">View</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
