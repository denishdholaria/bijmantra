import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Users, UserPlus, Shield, Settings, Mail, 
  MoreVertical, CheckCircle, XCircle, Clock,
  Building, Key, Activity, Trash2
} from 'lucide-react'

interface TeamMember {
  id: string
  name: string
  email: string
  role: 'admin' | 'breeder' | 'technician' | 'viewer'
  status: 'active' | 'pending' | 'inactive'
  joinedAt: string
  lastActive: string
  avatar?: string
}

interface Team {
  id: string
  name: string
  description: string
  members: number
  projects: number
}

export function TeamManagement() {
  const [activeTab, setActiveTab] = useState('members')
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')

  const members: TeamMember[] = [
    { id: '1', name: 'Dr. Sarah Chen', email: '[email]', role: 'admin', status: 'active', joinedAt: 'Jan 2024', lastActive: '2 min ago' },
    { id: '2', name: 'Raj Patel', email: '[email]', role: 'breeder', status: 'active', joinedAt: 'Mar 2024', lastActive: '15 min ago' },
    { id: '3', name: 'Maria Garcia', email: '[email]', role: 'technician', status: 'active', joinedAt: 'Jun 2024', lastActive: '1 hour ago' },
    { id: '4', name: 'John Smith', email: '[email]', role: 'breeder', status: 'active', joinedAt: 'Aug 2024', lastActive: '3 hours ago' },
    { id: '5', name: 'Aisha Okonkwo', email: '[email]', role: 'viewer', status: 'pending', joinedAt: 'Nov 2024', lastActive: 'Never' },
    { id: '6', name: 'Chen Wei', email: '[email]', role: 'technician', status: 'inactive', joinedAt: 'Feb 2024', lastActive: '2 weeks ago' },
  ]

  const teams: Team[] = [
    { id: '1', name: 'Rice Breeding', description: 'Main rice improvement program', members: 8, projects: 12 },
    { id: '2', name: 'Wheat Research', description: 'Wheat variety development', members: 5, projects: 6 },
    { id: '3', name: 'Genomics Lab', description: 'Molecular marker analysis', members: 4, projects: 8 },
    { id: '4', name: 'Field Operations', description: 'Trial management and data collection', members: 12, projects: 24 },
  ]

  const pendingInvites = [
    { id: '1', email: '[email]', role: 'breeder', sentAt: '2 days ago' },
    { id: '2', email: '[email]', role: 'technician', sentAt: '5 days ago' },
  ]

  const roleColors: Record<string, string> = {
    admin: 'bg-red-100 text-red-800',
    breeder: 'bg-blue-100 text-blue-800',
    technician: 'bg-green-100 text-green-800',
    viewer: 'bg-gray-100 text-gray-800',
  }

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    inactive: 'bg-gray-100 text-gray-800',
  }

  const filteredMembers = members.filter(m => 
    (roleFilter === 'all' || m.role === roleFilter) &&
    (searchQuery === '' || m.name.toLowerCase().includes(searchQuery.toLowerCase()) || m.email.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Team Management</h1>
          <p className="text-muted-foreground">Manage team members, roles, and permissions</p>
        </div>
        <Button><UserPlus className="mr-2 h-4 w-4" />Invite Member</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{members.length}</div>
            <p className="text-xs text-muted-foreground">{members.filter(m => m.status === 'active').length} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Teams</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{teams.length}</div>
            <p className="text-xs text-muted-foreground">Working groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Invites</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingInvites.length}</div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Admins</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{members.filter(m => m.role === 'admin').length}</div>
            <p className="text-xs text-muted-foreground">With full access</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="members"><Users className="mr-2 h-4 w-4" />Members</TabsTrigger>
          <TabsTrigger value="teams"><Building className="mr-2 h-4 w-4" />Teams</TabsTrigger>
          <TabsTrigger value="roles"><Shield className="mr-2 h-4 w-4" />Roles</TabsTrigger>
          <TabsTrigger value="invites"><Mail className="mr-2 h-4 w-4" />Invites</TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="space-y-4">
          <div className="flex gap-4">
            <Input placeholder="Search members..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="max-w-sm" />
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="Role" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="breeder">Breeder</SelectItem>
                <SelectItem value="technician">Technician</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {filteredMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <Avatar>
                        <AvatarImage src={member.avatar} />
                        <AvatarFallback>{member.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{member.name}</p>
                        <p className="text-sm text-muted-foreground">{member.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p className="text-muted-foreground">Joined {member.joinedAt}</p>
                        <p className="text-xs text-muted-foreground">Active {member.lastActive}</p>
                      </div>
                      <Badge className={roleColors[member.role]}>{member.role}</Badge>
                      <Badge className={statusColors[member.status]}>{member.status}</Badge>
                      <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="teams" className="space-y-4">
          <div className="flex justify-end"><Button><Users className="mr-2 h-4 w-4" />Create Team</Button></div>
          <div className="grid gap-4 md:grid-cols-2">
            {teams.map((team) => (
              <Card key={team.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{team.name}</CardTitle>
                    <Button variant="ghost" size="icon"><Settings className="h-4 w-4" /></Button>
                  </div>
                  <CardDescription>{team.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1"><Users className="h-4 w-4 text-muted-foreground" /><span className="text-sm">{team.members} members</span></div>
                      <div className="flex items-center gap-1"><Activity className="h-4 w-4 text-muted-foreground" /><span className="text-sm">{team.projects} projects</span></div>
                    </div>
                    <Button variant="outline" size="sm">Manage</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="roles" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Role Permissions</CardTitle><CardDescription>Configure what each role can access</CardDescription></CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { role: 'Admin', permissions: ['Full access', 'Manage users', 'System settings', 'Delete data'], color: 'red' },
                  { role: 'Breeder', permissions: ['Create trials', 'Edit germplasm', 'Run analyses', 'Export data'], color: 'blue' },
                  { role: 'Technician', permissions: ['Collect data', 'View trials', 'Upload images', 'Edit observations'], color: 'green' },
                  { role: 'Viewer', permissions: ['View data', 'Generate reports', 'Export limited data'], color: 'gray' },
                ].map((r) => (
                  <div key={r.role} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Shield className={`h-5 w-5 text-${r.color}-500`} />
                        <span className="font-medium">{r.role}</span>
                      </div>
                      <Button variant="outline" size="sm"><Key className="mr-2 h-3 w-3" />Edit Permissions</Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {r.permissions.map((p) => (<Badge key={p} variant="secondary">{p}</Badge>))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invites" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Pending Invitations</CardTitle><CardDescription>Invites awaiting acceptance</CardDescription></CardHeader>
            <CardContent>
              {pendingInvites.length > 0 ? (
                <div className="space-y-3">
                  {pendingInvites.map((invite) => (
                    <div key={invite.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Mail className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{invite.email}</p>
                          <p className="text-sm text-muted-foreground">Sent {invite.sentAt}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={roleColors[invite.role]}>{invite.role}</Badge>
                        <Button variant="outline" size="sm">Resend</Button>
                        <Button variant="ghost" size="icon"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">No pending invitations</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
