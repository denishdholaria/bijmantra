/**
 * Backup & Restore Page
 * Database backup and restore management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

interface Backup {
  id: string
  name: string
  size: string
  type: 'full' | 'incremental' | 'manual'
  status: 'completed' | 'in_progress' | 'failed'
  created_at: string
  created_by: string
}

export function BackupRestore() {
  const queryClient = useQueryClient()

  // Fetch backups
  const { data: backups = [], isLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: () => apiClient.backupService.listBackups(),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['backup-stats'],
    queryFn: () => apiClient.backupService.getStats(),
  })

  // Create backup mutation
  const createBackupMutation = useMutation({
    mutationFn: (type: 'full' | 'incremental' | 'manual') => apiClient.backupService.createBackup(type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] })
      queryClient.invalidateQueries({ queryKey: ['backup-stats'] })
      toast.success('Backup request recorded')
    },
    onError: () => {
      toast.error('Failed to record backup request')
    }
  })

  // Delete backup mutation
  const deleteBackupMutation = useMutation({
    mutationFn: (backupId: string) => apiClient.backupService.deleteBackup(backupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] })
      queryClient.invalidateQueries({ queryKey: ['backup-stats'] })
      toast.success('Backup deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete backup')
    }
  })

  const handleDelete = (backup: Backup) => {
    deleteBackupMutation.mutate(backup.id)
  }

  const getStatusBadge = (status: Backup['status']) => {
    const styles: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
    }
    return styles[status]
  }

  const getTypeBadge = (type: Backup['type']) => {
    const styles: Record<string, string> = {
      full: 'bg-purple-100 text-purple-800',
      incremental: 'bg-blue-100 text-blue-800',
      manual: 'bg-orange-100 text-orange-800',
    }
    return styles[type]
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Backup & Restore</h1>
          <p className="text-muted-foreground mt-1">Review backup records and recorded backup requests</p>
        </div>
        <Button onClick={() => createBackupMutation.mutate('manual')} disabled={createBackupMutation.isPending}>
          {createBackupMutation.isPending ? 'Requesting Backup...' : 'Request Backup'}
        </Button>
      </div>

      {createBackupMutation.isPending && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-1 text-sm">
              <p className="font-medium">Submitting backup request...</p>
              <p className="text-muted-foreground">This page does not estimate completion until the backend reports actual backup job progress.</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.total_backups || backups.length}</div>
            <p className="text-sm text-muted-foreground">Total Backups</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.successful_backups || backups.filter(b => b.status === 'completed').length}</div>
            <p className="text-sm text-muted-foreground">Successful</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.latest_size || backups[0]?.size || '-'}</div>
            <p className="text-sm text-muted-foreground">Latest Size</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats?.auto_backup_schedule || 'Unavailable'}</div>
            <p className="text-sm text-muted-foreground">Automatic Backup</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Backup History</CardTitle>
            <CardDescription>{backups.length} backup records reported</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Download and restore actions remain unavailable here until verified backup artifacts and restore execution are wired end to end.
            </p>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {backups.map((backup) => (
                  <TableRow key={backup.id}>
                    <TableCell className="font-medium">{backup.name}</TableCell>
                    <TableCell>
                      <Badge className={getTypeBadge(backup.type)}>{backup.type}</Badge>
                    </TableCell>
                    <TableCell>{backup.size}</TableCell>
                    <TableCell>
                      <Badge className={getStatusBadge(backup.status)}>{backup.status}</Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(backup.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" disabled aria-label={`Download unavailable for ${backup.name}`}>
                          📥
                        </Button>
                        <Button size="sm" variant="ghost" disabled aria-label={`Restore unavailable for ${backup.name}`}>
                          🔄
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(backup)}>
                          🗑️
                        </Button>
                      </div>
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
