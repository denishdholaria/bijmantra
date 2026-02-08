import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from 'sonner'
import { 
  Users, UserPlus, Shield, Settings, Mail, 
  MoreVertical, CheckCircle, XCircle, Clock,
  Building, Key, Activity, Trash2
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function TeamManagement() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('members')
  const [searchQuery, setSearchQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')

  // Fetch members
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['team-members', roleFilter, searchQuery],
    queryFn: () => apiClient.teamManagementService.getMembers({
      role: roleFilter !== 'all' ? (roleFilter as any) : undefined,
      search: searchQuery || undefined,
    }),
  })

  // Fetch teams
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: () => apiClient.teamManagementService.getTeams(),
  })

  // Fetch invites
  const { data: invitesData } = useQuery({
    queryKey: ['team-invites'],
    queryFn: () => apiClient.teamManagementService.getInvites(),
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['team-stats'],
    queryFn: () => apiClient.teamManagementService.getStats(),
  })

  // Update member mutation
  const updateMemberMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => apiClient.teamManagementService.updateMember(id, data),
    onSuccess: () => {
      toast.success('Member updated')
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
      queryClient.invalidateQueries({ queryKey: ['team-stats'] })
    },
  })

  // Delete member mutation
  const deleteMemberMutation = useMutation({
    mutationFn: (id: string) => apiClient.teamManagementService.deleteMember(id),
    onSuccess: () => {
      toast.success('Member removed')
      queryClient.invalidateQueries({ queryKey: ['team-members'] })
      queryClient.invalidateQueries({ queryKey: ['team-stats'] })
    },
  })

  // Resend invite mutation
  const resendInviteMutation = useMutation({
    mutationFn: (id: string) => apiClient.teamManagementService.resendInvite(id),
    onSuccess: () => {
      toast.success('Invitation resent')
      queryClient.invalidateQueries({ queryKey: ['team-invites'] })
    },
  })

  // Delete invite mutation
  const deleteInviteMutation = useMutation({
    mutationFn: (id: string) => apiClient.teamManagementService.deleteInvite(id),
    onSuccess: () => {
      toast.success('Invitation cancelled')
      queryClient.invalidateQueries({ queryKey: ['team-invites'] })
    },
  })

  const members = membersData?.data || []
  const teams = teamsData?.data || []
  const invites = invitesData?.data || []
  const stats = statsData?.data || { total_members: 0, active_members: 0, total_teams: 0, pending_invites: 0, admins: 0 }

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

  const formatLastActive = (lastActive: string | null) => {
    if (!lastActive) return 'Never'
    const date = new Date(lastActive)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

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
            <div className="text-2xl font-bold">{stats.total_members}</div>
            <p className="text-xs text-muted-foreground">{stats.active_members} active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Teams</CardTitle>
            <Building className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_teams}</div>
            <p className="text-xs text-muted-foreground">Working groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Invites</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending_invites}</div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Admins</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.admins}</div>
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
              {membersLoading ? (
                <div className="p-8 text-center text-muted-foreground">Loading members...</div>
              ) : members.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">No members found</div>
              ) : (
                <div className="divide-y">
                  {members.map((member: any) => (
                    <div key={member.id} className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-4">
                        <Avatar>
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback>{member.name.split(' ').map((n: string) => n[0]).join('')}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{member.name}</p>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right text-sm">
                          <p className="text-muted-foreground">Joined {member.joined_at}</p>
                          <p className="text-xs text-muted-foreground">Active {formatLastActive(member.last_active)}</p>
                        </div>
                        <Badge className={roleColors[member.role] || 'bg-gray-100'}>{member.role}</Badge>
                        <Badge className={statusColors[member.status] || 'bg-gray-100'}>{member.status}</Badge>
                        <Button variant="ghost" size="icon" onClick={() => deleteMemberMutation.mutate(member.id)} aria-label={`Remove ${member.name}`}><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="teams" className="space-y-4">
          <div className="flex justify-end"><Button><Users className="mr-2 h-4 w-4" />Create Team</Button></div>
          <div className="grid gap-4 md:grid-cols-2">
            {teams.map((team: any) => (
              <Card key={team.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{team.name}</CardTitle>
                    <Button variant="ghost" size="icon" aria-label={`Settings for ${team.name}`}><Settings className="h-4 w-4" /></Button>
                  </div>
                  <CardDescription>{team.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1"><Users className="h-4 w-4 text-muted-foreground" /><span className="text-sm">{team.member_count} members</span></div>
                      <div className="flex items-center gap-1"><Activity className="h-4 w-4 text-muted-foreground" /><span className="text-sm">{team.project_count} projects</span></div>
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
              {invites.length > 0 ? (
                <div className="space-y-3">
                  {invites.map((invite: any) => (
                    <div key={invite.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <Mail className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{invite.email}</p>
                          <p className="text-sm text-muted-foreground">Sent {new Date(invite.sent_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={roleColors[invite.role] || 'bg-gray-100'}>{invite.role}</Badge>
                        <Button variant="outline" size="sm" onClick={() => resendInviteMutation.mutate(invite.id)}>Resend</Button>
                        <Button variant="ghost" size="icon" onClick={() => deleteInviteMutation.mutate(invite.id)} aria-label="Cancel invitation"><Trash2 className="h-4 w-4" /></Button>
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
