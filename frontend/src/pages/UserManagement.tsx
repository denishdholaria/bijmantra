/**
 * User Management Page
 * Admin page for managing system users
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

interface User {
  userId: string
  email: string
  fullName: string
  role: 'admin' | 'breeder' | 'technician' | 'viewer'
  status: 'active' | 'inactive' | 'pending'
  lastLogin?: string
  createdAt: string
  programAccess: string[]
}

const mockUsers: User[] = [
  { userId: 'u001', email: 'admin@example.org', fullName: 'System Admin', role: 'admin', status: 'active', lastLogin: '2024-02-20T10:30:00', createdAt: '2023-01-01', programAccess: ['all'] },
  { userId: 'u002', email: 'john.smith@example.com', fullName: 'John Smith', role: 'breeder', status: 'active', lastLogin: '2024-02-20T09:15:00', createdAt: '2023-06-15', programAccess: ['Rice Breeding', 'Wheat Breeding'] },
  { userId: 'u003', email: 'jane.doe@example.com', fullName: 'Jane Doe', role: 'technician', status: 'active', lastLogin: '2024-02-19T16:45:00', createdAt: '2023-08-20', programAccess: ['Rice Breeding'] },
  { userId: 'u004', email: 'bob.wilson@example.com', fullName: 'Bob Wilson', role: 'viewer', status: 'inactive', lastLogin: '2024-01-15T11:00:00', createdAt: '2023-10-01', programAccess: ['Maize Breeding'] },
  { userId: 'u005', email: 'new.user@example.com', fullName: 'New User', role: 'technician', status: 'pending', createdAt: '2024-02-18', programAccess: [] },
]

export function UserManagement() {
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['users', search, roleFilter],
    queryFn: async () => {
      await new Promise(r => setTimeout(r, 400))
      let filtered = mockUsers
      if (search) {
        filtered = filtered.filter(u => 
          u.fullName.toLowerCase().includes(search.toLowerCase()) ||
          u.email.toLowerCase().includes(search.toLowerCase())
        )
      }
      if (roleFilter !== 'all') {
        filtered = filtered.filter(u => u.role === roleFilter)
      }
      return filtered
    },
  })

  const users = data || []

  const getRoleBadge = (role: User['role']) => {
    const styles: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      breeder: 'bg-blue-100 text-blue-800',
      technician: 'bg-green-100 text-green-800',
      viewer: 'bg-gray-100 text-gray-800',
    }
    return styles[role]
  }

  const getStatusBadge = (status: User['status']) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      pending: 'bg-yellow-100 text-yellow-800',
    }
    return styles[status]
  }

  const handleCreate = () => {
    toast.success('User invitation sent (demo)')
    setIsCreateOpen(false)
  }

  const handleStatusChange = (userId: string, newStatus: string) => {
    toast.success(`User status updated to ${newStatus} (demo)`)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">User Management</h1>
          <p className="text-muted-foreground mt-1">Manage system users and permissions</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>👤 Invite User</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite New User</DialogTitle>
              <DialogDescription>Send an invitation to join the system</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Email Address</Label>
                <Input type="email" placeholder="user@example.com" />
              </div>
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input placeholder="John Smith" />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select defaultValue="technician">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Administrator</SelectItem>
                    <SelectItem value="breeder">Breeder</SelectItem>
                    <SelectItem value="technician">Technician</SelectItem>
                    <SelectItem value="viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Program Access</Label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select programs..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Programs</SelectItem>
                    <SelectItem value="rice">Rice Breeding</SelectItem>
                    <SelectItem value="wheat">Wheat Breeding</SelectItem>
                    <SelectItem value="maize">Maize Breeding</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Send Invitation</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="breeder">Breeder</SelectItem>
                <SelectItem value="technician">Technician</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockUsers.length}</div>
            <p className="text-sm text-muted-foreground">Total Users</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockUsers.filter(u => u.status === 'active').length}</div>
            <p className="text-sm text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockUsers.filter(u => u.status === 'pending').length}</div>
            <p className="text-sm text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{mockUsers.filter(u => u.role === 'admin').length}</div>
            <p className="text-sm text-muted-foreground">Admins</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <CardDescription>{users.length} users found</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Program Access</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.userId}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{user.fullName}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getRoleBadge(user.role)}>{user.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusBadge(user.status)}>{user.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {user.programAccess.slice(0, 2).map(p => (
                          <Badge key={p} variant="outline" className="text-xs">{p}</Badge>
                        ))}
                        {user.programAccess.length > 2 && (
                          <Badge variant="outline" className="text-xs">+{user.programAccess.length - 2}</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {user.lastLogin ? new Date(user.lastLogin).toLocaleDateString() : 'Never'}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost">Edit</Button>
                        {user.status === 'active' ? (
                          <Button size="sm" variant="ghost" onClick={() => handleStatusChange(user.userId, 'inactive')}>
                            Deactivate
                          </Button>
                        ) : (
                          <Button size="sm" variant="ghost" onClick={() => handleStatusChange(user.userId, 'active')}>
                            Activate
                          </Button>
                        )}
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
