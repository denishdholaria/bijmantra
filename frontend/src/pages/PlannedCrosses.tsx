/**
 * Planned Crosses Page - BrAPI Germplasm Module
 * Plan and schedule breeding crosses
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { toast } from 'sonner'

interface PlannedCross {
  plannedCrossDbId: string
  crossingProjectDbId: string
  crossingProjectName: string
  parent1DbId: string
  parent1Name: string
  parent2DbId: string
  parent2Name: string
  crossType: string
  plannedCrossName?: string
  status: 'pending' | 'scheduled' | 'completed' | 'failed'
  plannedDate?: string
}

const mockPlannedCrosses: PlannedCross[] = [
  { plannedCrossDbId: 'pc001', crossingProjectDbId: 'cp001', crossingProjectName: 'Rice Yield 2024', parent1DbId: 'g001', parent1Name: 'IR64', parent2DbId: 'g002', parent2Name: 'Nipponbare', crossType: 'BIPARENTAL', plannedCrossName: 'IR64 × Nipponbare', status: 'completed', plannedDate: '2024-01-15' },
  { plannedCrossDbId: 'pc002', crossingProjectDbId: 'cp001', crossingProjectName: 'Rice Yield 2024', parent1DbId: 'g003', parent1Name: 'Kasalath', parent2DbId: 'g004', parent2Name: 'Azucena', crossType: 'BIPARENTAL', plannedCrossName: 'Kasalath × Azucena', status: 'scheduled', plannedDate: '2024-02-20' },
  { plannedCrossDbId: 'pc003', crossingProjectDbId: 'cp001', crossingProjectName: 'Rice Yield 2024', parent1DbId: 'g005', parent1Name: 'Moroberekan', parent2DbId: 'g006', parent2Name: 'CO39', crossType: 'BIPARENTAL', status: 'pending' },
  { plannedCrossDbId: 'pc004', crossingProjectDbId: 'cp003', crossingProjectName: 'Wheat Quality', parent1DbId: 'g007', parent1Name: 'Chinese Spring', parent2DbId: 'g008', parent2Name: 'Opata', crossType: 'BIPARENTAL', status: 'pending' },
]

export function PlannedCrosses() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedCrosses, setSelectedCrosses] = useState<string[]>([])
  const [isCreateOpen, setIsCreateOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['plannedCrosses', search, statusFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockPlannedCrosses
      if (search) {
        filtered = filtered.filter(c => 
          c.parent1Name.toLowerCase().includes(search.toLowerCase()) ||
          c.parent2Name.toLowerCase().includes(search.toLowerCase()) ||
          c.plannedCrossName?.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (statusFilter !== 'all') {
        filtered = filtered.filter(c => c.status === statusFilter)
      }
      return { result: { data: filtered } }
    },
  })

  const crosses = data?.result?.data || []

  const getStatusBadge = (status: PlannedCross['status']) => {
    const styles: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return <Badge className={styles[status]}>{status}</Badge>
  }

  const handleCreate = () => {
    toast.success('Planned cross created (demo)')
    setIsCreateOpen(false)
  }

  const handleBulkSchedule = () => {
    if (selectedCrosses.length === 0) {
      toast.error('Select crosses to schedule')
      return
    }
    toast.success(`${selectedCrosses.length} crosses scheduled (demo)`)
    setSelectedCrosses([])
  }

  const toggleSelect = (id: string) => {
    setSelectedCrosses(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedCrosses.length === crosses.length) {
      setSelectedCrosses([])
    } else {
      setSelectedCrosses(crosses.map(c => c.plannedCrossDbId))
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Planned Crosses</h1>
          <p className="text-muted-foreground mt-1">Schedule and manage breeding crosses</p>
        </div>
        <div className="flex gap-2">
          {selectedCrosses.length > 0 && (
            <Button variant="outline" onClick={handleBulkSchedule}>
              📅 Schedule ({selectedCrosses.length})
            </Button>
          )}
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>➕ Plan Cross</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Plan New Cross</DialogTitle>
                <DialogDescription>Define a new planned cross</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Crossing Project</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cp001">Rice Yield 2024</SelectItem>
                      <SelectItem value="cp003">Wheat Quality</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Female Parent (♀)</Label>
                    <Input placeholder="Search germplasm..." />
                  </div>
                  <div className="space-y-2">
                    <Label>Male Parent (♂)</Label>
                    <Input placeholder="Search germplasm..." />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Cross Type</Label>
                    <Select defaultValue="BIPARENTAL">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="BIPARENTAL">Biparental</SelectItem>
                        <SelectItem value="SELF">Self</SelectItem>
                        <SelectItem value="OPEN_POLLINATED">Open Pollinated</SelectItem>
                        <SelectItem value="BACKCROSS">Backcross</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Planned Date</Label>
                    <Input type="date" />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                <Button onClick={handleCreate}>Plan Cross</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by parent name..."
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
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlannedCrosses.length}</div>
            <p className="text-sm text-muted-foreground">Total Planned</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlannedCrosses.filter(c => c.status === 'pending').length}</div>
            <p className="text-sm text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlannedCrosses.filter(c => c.status === 'scheduled').length}</div>
            <p className="text-sm text-muted-foreground">Scheduled</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockPlannedCrosses.filter(c => c.status === 'completed').length}</div>
            <p className="text-sm text-muted-foreground">Completed</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Planned Crosses</CardTitle>
            <CardDescription>{crosses.length} crosses found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox 
                      checked={selectedCrosses.length === crosses.length && crosses.length > 0}
                      onCheckedChange={toggleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Cross</TableHead>
                  <TableHead>Female (♀)</TableHead>
                  <TableHead>Male (♂)</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {crosses.map((cross) => (
                  <TableRow key={cross.plannedCrossDbId}>
                    <TableCell>
                      <Checkbox 
                        checked={selectedCrosses.includes(cross.plannedCrossDbId)}
                        onCheckedChange={() => toggleSelect(cross.plannedCrossDbId)}
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      {cross.plannedCrossName || `${cross.parent1Name} × ${cross.parent2Name}`}
                    </TableCell>
                    <TableCell>
                      <Link to={`/germplasm/${cross.parent1DbId}`} className="text-pink-600 hover:underline">
                        {cross.parent1Name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link to={`/germplasm/${cross.parent2DbId}`} className="text-blue-600 hover:underline">
                        {cross.parent2Name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{cross.crossType}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(cross.status)}</TableCell>
                    <TableCell>{cross.plannedDate || '-'}</TableCell>
                    <TableCell>
                      <Button size="sm" variant="ghost">Execute</Button>
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
