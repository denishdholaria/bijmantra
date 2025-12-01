/**
 * Audit Log Page
 * System activity and change tracking
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

interface AuditEntry {
  id: string
  timestamp: string
  user: string
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'VIEW' | 'EXPORT' | 'IMPORT'
  entity: string
  entityId: string
  entityName: string
  details?: string
  ipAddress?: string
}

const mockAuditLog: AuditEntry[] = [
  { id: 'a001', timestamp: '2024-02-20T10:30:00', user: 'john.smith@example.com', action: 'CREATE', entity: 'Germplasm', entityId: 'g001', entityName: 'IR64-2024', details: 'Created new germplasm entry' },
  { id: 'a002', timestamp: '2024-02-20T10:25:00', user: 'jane.doe@example.com', action: 'UPDATE', entity: 'Observation', entityId: 'obs001', entityName: 'Plant Height', details: 'Updated value from 85 to 87 cm' },
  { id: 'a003', timestamp: '2024-02-20T10:20:00', user: 'john.smith@example.com', action: 'IMPORT', entity: 'Germplasm', entityId: 'batch001', entityName: 'Batch Import', details: 'Imported 150 entries from CSV' },
  { id: 'a004', timestamp: '2024-02-20T10:15:00', user: 'admin@example.com', action: 'DELETE', entity: 'Sample', entityId: 's001', entityName: 'SAMPLE-001', details: 'Deleted duplicate sample' },
  { id: 'a005', timestamp: '2024-02-20T10:10:00', user: 'jane.doe@example.com', action: 'EXPORT', entity: 'Report', entityId: 'r001', entityName: 'Yield Analysis', details: 'Exported to Excel' },
  { id: 'a006', timestamp: '2024-02-20T10:05:00', user: 'john.smith@example.com', action: 'VIEW', entity: 'Study', entityId: 'study001', entityName: 'Rice Yield Trial', details: 'Viewed study details' },
  { id: 'a007', timestamp: '2024-02-20T10:00:00', user: 'admin@example.com', action: 'CREATE', entity: 'User', entityId: 'u001', entityName: 'new.user@example.com', details: 'Created new user account' },
  { id: 'a008', timestamp: '2024-02-19T16:45:00', user: 'jane.doe@example.com', action: 'UPDATE', entity: 'Trial', entityId: 't001', entityName: 'Wheat Trial 2024', details: 'Changed status to Active' },
]

export function AuditLog() {
  const [search, setSearch] = useState('')
  const [actionFilter, setActionFilter] = useState<string>('all')
  const [entityFilter, setEntityFilter] = useState<string>('all')

  const { data, isLoading } = useQuery({
    queryKey: ['auditLog', search, actionFilter, entityFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockAuditLog
      if (search) {
        filtered = filtered.filter(e => 
          e.user.toLowerCase().includes(search.toLowerCase()) ||
          e.entityName.toLowerCase().includes(search.toLowerCase()) ||
          e.details?.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (actionFilter !== 'all') {
        filtered = filtered.filter(e => e.action === actionFilter)
      }
      if (entityFilter !== 'all') {
        filtered = filtered.filter(e => e.entity === entityFilter)
      }
      return filtered
    },
  })

  const entries = data || []
  const entities = [...new Set(mockAuditLog.map(e => e.entity))]

  const getActionBadge = (action: AuditEntry['action']) => {
    const styles: Record<string, string> = {
      CREATE: 'bg-green-100 text-green-800',
      UPDATE: 'bg-blue-100 text-blue-800',
      DELETE: 'bg-red-100 text-red-800',
      VIEW: 'bg-gray-100 text-gray-800',
      EXPORT: 'bg-purple-100 text-purple-800',
      IMPORT: 'bg-orange-100 text-orange-800',
    }
    return styles[action]
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Audit Log</h1>
          <p className="text-muted-foreground mt-1">System activity and change history</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => toast.success('Export started (demo)')}>
            📥 Export Log
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by user, entity, or details..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="CREATE">Create</SelectItem>
                <SelectItem value="UPDATE">Update</SelectItem>
                <SelectItem value="DELETE">Delete</SelectItem>
                <SelectItem value="VIEW">View</SelectItem>
                <SelectItem value="EXPORT">Export</SelectItem>
                <SelectItem value="IMPORT">Import</SelectItem>
              </SelectContent>
            </Select>
            <Select value={entityFilter} onValueChange={setEntityFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Entity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Entities</SelectItem>
                {entities.map(e => (
                  <SelectItem key={e} value={e}>{e}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAuditLog.length}</div>
            <p className="text-sm text-muted-foreground">Total Entries</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAuditLog.filter(e => e.action === 'CREATE').length}</div>
            <p className="text-sm text-muted-foreground">Creates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockAuditLog.filter(e => e.action === 'UPDATE').length}</div>
            <p className="text-sm text-muted-foreground">Updates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{new Set(mockAuditLog.map(e => e.user)).size}</div>
            <p className="text-sm text-muted-foreground">Active Users</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>{entries.length} entries found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {formatTimestamp(entry.timestamp)}
                    </TableCell>
                    <TableCell className="font-medium">{entry.user}</TableCell>
                    <TableCell>
                      <Badge className={getActionBadge(entry.action)}>{entry.action}</Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{entry.entity}</p>
                        <p className="text-xs text-muted-foreground">{entry.entityName}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-xs truncate">
                      {entry.details}
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
