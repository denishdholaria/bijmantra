/**
 * Vendor Orders Page - BrAPI Genotyping Module
 * Genotyping service orders management
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import { apiClient } from '@/lib/api-client'

interface VendorOrder {
  vendorOrderDbId: string
  orderId: string
  clientId: string
  numberOfSamples: number
  status: string
  submissionDate: string
  resultDate?: string
  requiredServiceInfo?: { serviceId: string; serviceName: string }
  serviceIds?: string[]
}

export function VendorOrders() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newOrder, setNewOrder] = useState({ clientId: 'client001', numberOfSamples: 96, serviceIds: ['GBS'] })
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['vendorOrders', statusFilter],
    queryFn: () => apiClient.getVendorOrders({
      status: statusFilter !== 'all' ? statusFilter : undefined,
      pageSize: 100,
    }),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof newOrder) => apiClient.createVendorOrder(data),
    onSuccess: () => {
      toast.success('Order submitted')
      setIsCreateOpen(false)
      setNewOrder({ clientId: 'client001', numberOfSamples: 96, serviceIds: ['GBS'] })
      queryClient.invalidateQueries({ queryKey: ['vendorOrders'] })
    },
    onError: () => toast.error('Failed to submit order'),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiClient.updateVendorOrderStatus(id, status),
    onSuccess: () => {
      toast.success('Status updated')
      queryClient.invalidateQueries({ queryKey: ['vendorOrders'] })
    },
  })

  const orders: VendorOrder[] = data?.result?.data || []
  const filteredOrders = search ? orders.filter(o => o.orderId.toLowerCase().includes(search.toLowerCase())) : orders

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      submitted: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
    }
    return <Badge className={styles[status] || 'bg-gray-100'}>{status}</Badge>
  }

  const stats = {
    total: orders.length,
    inProgress: orders.filter(o => o.status === 'in_progress').length,
    completed: orders.filter(o => o.status === 'completed').length,
    totalSamples: orders.reduce((a, o) => a + o.numberOfSamples, 0),
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Vendor Orders</h1>
          <p className="text-muted-foreground mt-1">Genotyping service orders</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild><Button>📦 New Order</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Submit New Order</DialogTitle><DialogDescription>Create a genotyping service order</DialogDescription></DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Service Type</Label>
                <Select value={newOrder.serviceIds[0]} onValueChange={(v) => setNewOrder({ ...newOrder, serviceIds: [v] })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GBS">GBS Sequencing</SelectItem>
                    <SelectItem value="SNP_ARRAY">SNP Array</SelectItem>
                    <SelectItem value="WGS">Whole Genome Sequencing</SelectItem>
                    <SelectItem value="KASP">KASP Genotyping</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2"><Label>Number of Samples</Label><Input type="number" value={newOrder.numberOfSamples} onChange={(e) => setNewOrder({ ...newOrder, numberOfSamples: parseInt(e.target.value) || 0 })} /></div>
              <div className="space-y-2"><Label>Client ID</Label><Input value={newOrder.clientId} onChange={(e) => setNewOrder({ ...newOrder, clientId: e.target.value })} /></div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={() => createMutation.mutate(newOrder)}>Submit Order</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input placeholder="Search orders..." value={search} onChange={(e) => setSearch(e.target.value)} className="flex-1" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="submitted">Submitted</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.total}</div><p className="text-sm text-muted-foreground">Total Orders</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.inProgress}</div><p className="text-sm text-muted-foreground">In Progress</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.totalSamples}</div><p className="text-sm text-muted-foreground">Total Samples</p></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{stats.completed}</div><p className="text-sm text-muted-foreground">Completed</p></CardContent></Card>
      </div>

      {isLoading ? <Skeleton className="h-64 w-full" /> : (
        <Card>
          <CardHeader><CardTitle>Orders</CardTitle><CardDescription>{filteredOrders.length} orders</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Order ID</TableHead><TableHead>Service</TableHead><TableHead>Samples</TableHead><TableHead>Status</TableHead><TableHead>Submitted</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.vendorOrderDbId}>
                    <TableCell className="font-medium">{order.orderId}</TableCell>
                    <TableCell>{order.requiredServiceInfo?.serviceName || order.serviceIds?.join(', ')}</TableCell>
                    <TableCell>{order.numberOfSamples}</TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell>{order.submissionDate}</TableCell>
                    <TableCell>
                      <Select value={order.status} onValueChange={(v) => updateStatusMutation.mutate({ id: order.vendorOrderDbId, status: v })}>
                        <SelectTrigger className="w-28 h-8"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="submitted">Submitted</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                        </SelectContent>
                      </Select>
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
