/**
 * Backup & Restore Page
 * Database backup and restore management
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
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
  const [isBackupRunning, setIsBackupRunning] = useState(false)
  const [backupProgress, setBackupProgress] = useState(0)
  const [isRestoreOpen, setIsRestoreOpen] = useState(false)
  const [selectedBackup, setSelectedBackup] = useState<Backup | null>(null)
  const queryClient = useQueryClient()

  // Fetch backups
  const { data: backups = [], isLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: apiClient.backupService.listBackups,
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['backup-stats'],
    queryFn: apiClient.backupService.getStats,
  })

  // Create backup mutation
  const createBackupMutation = useMutation({
    mutationFn: (type: 'full' | 'incremental' | 'manual') => apiClient.backupService.createBackup(type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backups'] })
      queryClient.invalidateQueries({ queryKey: ['backup-stats'] })
      toast.success('Backup completed successfully')
    },
    onError: () => {
      toast.error('Failed to create backup')
    }
  })

  // Restore backup mutation
  const restoreBackupMutation = useMutation({
    mutationFn: (backupId: string) => apiClient.backupService.restoreBackup(backupId),
    onSuccess: () => {
      toast.success('Restore initiated successfully')
      setIsRestoreOpen(false)
    },
    onError: () => {
      toast.error('Failed to restore backup')
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

  const startBackup = async () => {
    setIsBackupRunning(true)
    setBackupProgress(0)
    
    // Simulate backup progress
    const progressInterval = setInterval(() => {
      setBackupProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 10
      })
    }, 500)
    
    try {
      await createBackupMutation.mutateAsync('manual')
    } finally {
      clearInterval(progressInterval)
      setIsBackupRunning(false)
      setBackupProgress(0)
    }
  }

  const handleRestore = () => {
    if (selectedBackup) {
      restoreBackupMutation.mutate(selectedBackup.id)
    }
  }

  const handleDownload = async (backup: Backup) => {
    try {
      const result = await apiClient.backupService.downloadBackup(backup.id)
      toast.success(result.message || `Downloading ${backup.name}...`)
    } catch {
      toast.error('Failed to download backup')
    }
  }

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
          <p className="text-muted-foreground mt-1">Manage database backups</p>
        </div>
        <Button onClick={startBackup} disabled={isBackupRunning}>
          {isBackupRunning ? '🔄 Backing up...' : '💾 Create Backup'}
        </Button>
      </div>

      {isBackupRunning && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Creating backup...</span>
                <span>{backupProgress}%</span>
              </div>
              <Progress value={backupProgress} />
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
            <div className="text-2xl font-bold">Daily</div>
            <p className="text-sm text-muted-foreground">Auto Backup</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Backup History</CardTitle>
            <CardDescription>{backups.length} backups available</CardDescription>
          </CardHeader>
          <CardContent>
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
                        <Button size="sm" variant="ghost" onClick={() => handleDownload(backup)}>
                          📥
                        </Button>
                        <Dialog open={isRestoreOpen && selectedBackup?.id === backup.id} onOpenChange={(open) => {
                          setIsRestoreOpen(open)
                          if (open) setSelectedBackup(backup)
                        }}>
                          <DialogTrigger asChild>
                            <Button size="sm" variant="ghost" disabled={backup.status !== 'completed'}>
                              🔄
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Restore Backup</DialogTitle>
                              <DialogDescription>
                                Are you sure you want to restore from {backup.name}? This will overwrite current data.
                              </DialogDescription>
                            </DialogHeader>
                            <div className="py-4">
                              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <p className="text-sm text-yellow-800">
                                  ⚠️ Warning: This action cannot be undone. All current data will be replaced.
                                </p>
                              </div>
                            </div>
                            <DialogFooter>
                              <Button variant="outline" onClick={() => setIsRestoreOpen(false)}>Cancel</Button>
                              <Button variant="destructive" onClick={handleRestore}>Restore</Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
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
