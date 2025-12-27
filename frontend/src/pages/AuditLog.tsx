/**
 * Audit Log Page
 * System activity and change tracking - Connected to real backend API
 */
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface AuditEntry {
  id: string
  timestamp: string
  category: string
  severity: string
  action: string
  actor: string | null
  target: string | null
  source_ip: string | null
  details: Record<string, any>
  success: boolean
}

interface AuditStats {
  total_entries: number
  entries_last_24h: number
  by_category: Record<string, number>
  by_severity: Record<string, number>
  failed_actions: number
  unique_actors: number
  unique_ips: number
}

const CATEGORIES = [
  { id: 'authentication', name: 'Authentication' },
  { id: 'authorization', name: 'Authorization' },
  { id: 'data_access', name: 'Data Access' },
  { id: 'security_event', name: 'Security Event' },
  { id: 'threat_detected', name: 'Threat Detected' },
  { id: 'response_action', name: 'Response Action' },
  { id: 'configuration', name: 'Configuration' },
  { id: 'system', name: 'System' },
]

const SEVERITIES = [
  { id: 'info', name: 'Info' },
  { id: 'warning', name: 'Warning' },
  { id: 'error', name: 'Error' },
  { id: 'critical', name: 'Critical' },
]

export function AuditLog() {
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [hoursFilter, setHoursFilter] = useState<string>('24')

  // Fetch audit entries
  const { data: entriesData, isLoading: entriesLoading, refetch } = useQuery({
    queryKey: ['auditEntries', categoryFilter, severityFilter, hoursFilter],
    queryFn: async () => {
      const params: Record<string, any> = { limit: 200 }
      if (categoryFilter !== 'all') params.category = categoryFilter
      if (severityFilter !== 'all') params.severity = severityFilter
      if (hoursFilter !== 'all') params.hours = parseInt(hoursFilter)
      return apiClient.getAuditEntries(params)
    },
  })

  // Fetch audit stats
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['auditStats', hoursFilter],
    queryFn: () => apiClient.getAuditStats(hoursFilter !== 'all' ? parseInt(hoursFilter) : 24),
  })

  // Search audit logs
  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ['auditSearch', search],
    queryFn: () => apiClient.searchAuditLogs(search),
    enabled: search.length >= 2,
  })

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async (format: 'json' | 'csv') => {
      const now = new Date()
      const startDate = new Date(now.getTime() - parseInt(hoursFilter || '24') * 60 * 60 * 1000)
      return apiClient.exportAuditLogs({
        start_date: startDate.toISOString(),
        end_date: now.toISOString(),
        format,
      })
    },
    onSuccess: (data, format) => {
      // Download the file
      const blob = new Blob([typeof data.data === 'string' ? data.data : JSON.stringify(data.data, null, 2)], {
        type: format === 'json' ? 'application/json' : 'text/csv',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit-log-${new Date().toISOString().split('T')[0]}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(`Exported audit log as ${format.toUpperCase()}`)
    },
    onError: () => {
      toast.error('Failed to export audit log')
    },
  })

  // Use search results if searching, otherwise use filtered entries
  const entries: AuditEntry[] = search.length >= 2 
    ? (searchData?.results || [])
    : (entriesData?.entries || [])
  
  const stats: AuditStats | null = statsData || null
  const isLoading = entriesLoading || (search.length >= 2 && searchLoading)

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      info: 'bg-gray-100 text-gray-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      critical: 'bg-red-600 text-white',
    }
    return styles[severity] || 'bg-gray-100 text-gray-800'
  }

  const getCategoryBadge = (category: string) => {
    const styles: Record<string, string> = {
      authentication: 'bg-blue-100 text-blue-800',
      authorization: 'bg-purple-100 text-purple-800',
      data_access: 'bg-green-100 text-green-800',
      security_event: 'bg-orange-100 text-orange-800',
      threat_detected: 'bg-red-100 text-red-800',
      response_action: 'bg-indigo-100 text-indigo-800',
      configuration: 'bg-cyan-100 text-cyan-800',
      system: 'bg-gray-100 text-gray-800',
    }
    return styles[category] || 'bg-gray-100 text-gray-800'
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const formatCategory = (category: string) => {
    return category.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Security Audit Log</h1>
          <p className="text-muted-foreground mt-1">System security events and activity tracking</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => exportMutation.mutate('csv')}
            disabled={exportMutation.isPending}
          >
            📥 Export CSV
          </Button>
          <Button 
            variant="outline" 
            onClick={() => exportMutation.mutate('json')}
            disabled={exportMutation.isPending}
          >
            📥 Export JSON
          </Button>
          <Button variant="outline" onClick={() => refetch()}>
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by action, actor, target, or details (min 2 chars)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map(c => (
                  <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                {SEVERITIES.map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={hoursFilter} onValueChange={setHoursFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Last Hour</SelectItem>
                <SelectItem value="6">Last 6 Hours</SelectItem>
                <SelectItem value="24">Last 24 Hours</SelectItem>
                <SelectItem value="72">Last 3 Days</SelectItem>
                <SelectItem value="168">Last Week</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      {statsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total_entries}</div>
              <p className="text-sm text-muted-foreground">Total Entries</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.entries_last_24h}</div>
              <p className="text-sm text-muted-foreground">Last 24 Hours</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-600">{stats.failed_actions}</div>
              <p className="text-sm text-muted-foreground">Failed Actions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.unique_actors}</div>
              <p className="text-sm text-muted-foreground">Unique Actors</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Severity Breakdown */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-gray-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Info</span>
                <Badge className="bg-gray-100 text-gray-800">{stats.by_severity.info || 0}</Badge>
              </div>
            </CardContent>
          </Card>
          <Card className="border-yellow-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Warning</span>
                <Badge className="bg-yellow-100 text-yellow-800">{stats.by_severity.warning || 0}</Badge>
              </div>
            </CardContent>
          </Card>
          <Card className="border-red-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Error</span>
                <Badge className="bg-red-100 text-red-800">{stats.by_severity.error || 0}</Badge>
              </div>
            </CardContent>
          </Card>
          <Card className="border-red-400">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Critical</span>
                <Badge className="bg-red-600 text-white">{stats.by_severity.critical || 0}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Entries Table */}
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Activity Log</CardTitle>
            <CardDescription>
              {search.length >= 2 
                ? `${entries.length} results for "${search}"`
                : `${entries.length} entries found`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                      No audit entries found
                    </TableCell>
                  </TableRow>
                ) : (
                  entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                        {formatTimestamp(entry.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge className={getCategoryBadge(entry.category)}>
                          {formatCategory(entry.category)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getSeverityBadge(entry.severity)}>
                          {entry.severity.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">{entry.action}</TableCell>
                      <TableCell className="text-sm">
                        {entry.actor || <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell className="text-sm max-w-xs truncate">
                        {entry.target || <span className="text-muted-foreground">—</span>}
                      </TableCell>
                      <TableCell>
                        {entry.success ? (
                          <Badge className="bg-green-100 text-green-800">Success</Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">Failed</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
