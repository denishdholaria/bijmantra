/**
 * Backup & Restore Page
 * Database backup and restore management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { toast } from 'sonner'

interface Backup {
  id: string
  name: string
  size: string
  type: 'full' | 'incremental' | 'manual'
  status: 'completed' | 'in_progress' | 'failed'
  createdAt: string
  createdBy: string
}

const mockBackups: Backup[] = [
  { id: 'b001', name: 'backup_2024-02-20_auto', size: '2.4 GB', type: 'full', status: 'completed', createdAt: '2024-02-20T03:00:00', createdBy: 'System' },
  { id: 'b002', name: 'backup_2024-02-19_auto', size: '2.3 GB', type: 'full', status: 'completed', createdAt: '2024-02-19T03:00:00', createdBy: 'System' },
  { id: 'b003', name: 'backup_2024-02-18_manual', size: '2.3 GB', type: 'manual', status: 'completed', createdAt: '2024-02-18T14:30:00', createdBy: 'admin@example.org' },
  { id: 'b004', name: 'backup_2024-02-17_auto', size: '2.2 GB', type: 'full', status: 'completed', createdAt: '2024-02-17T03:00:00', createdBy: 'System' },
  { id: 'b005', name: 'backup_2024-02-16_auto', size: '2.2 GB', type: 'incremental', status: 'failed', createdAt: '2024-02-16T03:00:00', createdBy: 'System' },
]

export function BackupRestore() {
  const [isBackupRunning, setIsBackupRunning] = useState(false)
  const [backupProgress, setBackupProgress] = useState(0)
  const [isRestoreOpen, setIsRestoreOpen] = useState(false)
  const [selectedBackup, setSelectedBackup] = useState<Backup | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['backups'],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      return mockBackups
    },
  })

  const backups = data || []

  const startBackup = async () => {
    setIsBackupRunning(true)
    setBackupProgress(0)
    
    // Simulate backup progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(r => setTimeout(r, 500))
      setBackupProgress(i)
    }
    
    setIsBackupRunning(false)
    toast.success('Backup completed successfully')
  }

  const handleRestore = () => {
    toast.success(`Restore from ${selectedBackup?.name} initiated (demo)`)
    setIsRestoreOpen(false)
  }

  const handleDownload = (backup: Backup) => {
    toast.success(`Downloading ${backup.name}...`)
  }

  const handleDelete = (backup: Backup) => {
    toast.success(`Deleted ${backup.name}`)
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
            <div className="text-2xl font-bold">{mockBackups.length}</div>
            <p className="text-sm text-muted-foreground">Total Backups</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockBackups.filter(b => b.status === 'completed').length}</div>
            <p className="text-sm text-muted-foreground">Successful</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockBackups[0]?.size || '-'}</div>
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
                      {new Date(backup.createdAt).toLocaleString()}
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
