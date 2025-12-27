/**
 * Collaboration Hub
 * Team collaboration, real-time presence, and shared workspaces
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { 
  Users, MessageSquare, FolderKanban, Activity, 
  CheckSquare, Plus, Search, Circle,
  MoreHorizontal, Calendar
} from 'lucide-react'
import { collaborationHubAPI } from '@/lib/api-client'

// Types
interface TeamMember {
  id: string
  name: string
  email: string
  role: string
  status: 'online' | 'away' | 'busy' | 'offline'
  last_active: string
  current_workspace?: string
}

interface Workspace {
  id: string
  name: string
  type: string
  description?: string
  owner_id: string
  members: string[]
  member_details?: TeamMember[]
  created_at: string
  updated_at: string
}

interface ActivityEntry {
  id: string
  user_id: string
  user_name: string
  activity_type: string
  entity_type: string
  entity_id: string
  entity_name: string
  description: string
  timestamp: string
}

interface Task {
  id: string
  title: string
  description?: string
  assignee_id?: string
  assignee_name?: string
  workspace_id?: string
  status: string
  priority: string
  due_date?: string
  created_at: string
}

interface CollaborationStats {
  total_members: number
  online_members: number
  active_workspaces: number
  pending_tasks: number
  comments_today: number
  activities_today: number
}

export function CollaborationHub() {
  const [activeTab, setActiveTab] = useState('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const queryClient = useQueryClient()

  // Queries
  const { data: stats } = useQuery<CollaborationStats>({
    queryKey: ['collaboration-stats'],
    queryFn: () => collaborationHubAPI.getStats(),
  })

  const { data: membersData, isLoading: membersLoading } = useQuery<{ members: TeamMember[] }>({
    queryKey: ['collaboration-members'],
    queryFn: () => collaborationHubAPI.getMembers(),
  })

  const { data: workspacesData, isLoading: workspacesLoading } = useQuery<{ workspaces: Workspace[] }>({
    queryKey: ['collaboration-workspaces'],
    queryFn: () => collaborationHubAPI.getWorkspaces(),
  })

  const { data: activitiesData, isLoading: activitiesLoading } = useQuery<{ activities: ActivityEntry[] }>({
    queryKey: ['collaboration-activities'],
    queryFn: () => collaborationHubAPI.getActivities(20),
  })

  const { data: tasksData, isLoading: tasksLoading } = useQuery<{ tasks: Task[] }>({
    queryKey: ['collaboration-tasks'],
    queryFn: () => collaborationHubAPI.getTasks(),
  })

  // Mutations
  const createTaskMutation = useMutation({
    mutationFn: (title: string) => collaborationHubAPI.createTask(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['collaboration-stats'] })
      setNewTaskTitle('')
    },
  })

  const updateTaskMutation = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      collaborationHubAPI.updateTask(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaboration-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['collaboration-stats'] })
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'away': return 'bg-yellow-500'
      case 'busy': return 'bg-red-500'
      default: return 'bg-gray-400'
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'created': return '➕'
      case 'updated': return '✏️'
      case 'commented': return '💬'
      case 'shared': return '🔗'
      case 'completed': return '✅'
      case 'assigned': return '👤'
      default: return '📝'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    }
  }

  const members = membersData?.members || []
  const workspaces = workspacesData?.workspaces || []
  const activities = activitiesData?.activities || []
  const tasks = tasksData?.tasks || []

  const filteredMembers = members.filter(m => 
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const onlineMembers = members.filter(m => m.status !== 'offline')
  const pendingTasks = tasks.filter(t => t.status !== 'done')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Collaboration Hub</h1>
          <p className="text-muted-foreground">Team collaboration, workspaces, and activity tracking</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Users className="mr-2 h-4 w-4" />
            Invite Member
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Workspace
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Team Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_members || 0}</div>
            <p className="text-xs text-muted-foreground">{stats?.online_members || 0} online</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Workspaces</CardTitle>
            <FolderKanban className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_workspaces || 0}</div>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            <CheckSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_tasks || 0}</div>
            <p className="text-xs text-muted-foreground">To complete</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Comments</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.comments_today || 0}</div>
            <p className="text-xs text-muted-foreground">Today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Activities</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.activities_today || 0}</div>
            <p className="text-xs text-muted-foreground">Today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online Now</CardTitle>
            <Circle className="h-4 w-4 text-green-500 fill-green-500" />
          </CardHeader>
          <CardContent>
            <div className="flex -space-x-2">
              {onlineMembers.slice(0, 4).map(m => (
                <Avatar key={m.id} className="h-8 w-8 border-2 border-background">
                  <AvatarFallback className="text-xs">{m.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                </Avatar>
              ))}
              {onlineMembers.length > 4 && (
                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs border-2 border-background">
                  +{onlineMembers.length - 4}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview"><Activity className="mr-2 h-4 w-4" />Overview</TabsTrigger>
          <TabsTrigger value="team"><Users className="mr-2 h-4 w-4" />Team</TabsTrigger>
          <TabsTrigger value="workspaces"><FolderKanban className="mr-2 h-4 w-4" />Workspaces</TabsTrigger>
          <TabsTrigger value="tasks"><CheckSquare className="mr-2 h-4 w-4" />Tasks</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Activity Feed */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>What's happening in your team</CardDescription>
              </CardHeader>
              <CardContent>
                {activitiesLoading ? (
                  <div className="text-center py-4 text-muted-foreground">Loading...</div>
                ) : (
                  <div className="space-y-4">
                    {activities.slice(0, 8).map(activity => (
                      <div key={activity.id} className="flex items-start gap-3">
                        <span className="text-lg">{getActivityIcon(activity.activity_type)}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm">
                            <span className="font-medium">{activity.user_name}</span>{' '}
                            <span className="text-muted-foreground">{activity.description}</span>
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(activity.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Tasks */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>My Tasks</CardTitle>
                    <CardDescription>Tasks assigned to you</CardDescription>
                  </div>
                  <Badge variant="secondary">{pendingTasks.length} pending</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Quick add task */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a quick task..."
                      value={newTaskTitle}
                      onChange={(e) => setNewTaskTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && newTaskTitle.trim()) {
                          createTaskMutation.mutate(newTaskTitle.trim())
                        }
                      }}
                    />
                    <Button 
                      size="icon" 
                      onClick={() => newTaskTitle.trim() && createTaskMutation.mutate(newTaskTitle.trim())}
                      disabled={!newTaskTitle.trim() || createTaskMutation.isPending}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  {tasksLoading ? (
                    <div className="text-center py-4 text-muted-foreground">Loading...</div>
                  ) : (
                    <div className="space-y-2">
                      {pendingTasks.slice(0, 5).map(task => (
                        <div key={task.id} className="flex items-center gap-3 p-2 border rounded-lg">
                          <input
                            type="checkbox"
                            checked={task.status === 'done'}
                            onChange={() => updateTaskMutation.mutate({ 
                              taskId: task.id, 
                              status: task.status === 'done' ? 'todo' : 'done' 
                            })}
                            className="h-4 w-4 rounded"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{task.title}</p>
                            {task.due_date && (
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {new Date(task.due_date).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                          <Badge className={getPriorityColor(task.priority)}>{task.priority}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="team" className="space-y-4">
          <div className="flex gap-4 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search team members..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>{members.length} members in your organization</CardDescription>
            </CardHeader>
            <CardContent>
              {membersLoading ? (
                <div className="text-center py-4 text-muted-foreground">Loading...</div>
              ) : (
                <div className="space-y-3">
                  {filteredMembers.map(member => (
                    <div key={member.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <Avatar>
                            <AvatarFallback>{member.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                          </Avatar>
                          <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background ${getStatusColor(member.status)}`} />
                        </div>
                        <div>
                          <p className="font-medium">{member.name}</p>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">{member.role}</Badge>
                        <Badge variant={member.status === 'online' ? 'default' : 'secondary'}>
                          {member.status}
                        </Badge>
                        <Button variant="ghost" size="icon">
                          <MessageSquare className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workspaces" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Shared Workspaces</CardTitle>
                  <CardDescription>Collaborate on trials, studies, and analyses</CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Workspace
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {workspacesLoading ? (
                <div className="text-center py-4 text-muted-foreground">Loading...</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {workspaces.map(workspace => (
                    <Card key={workspace.id} className="cursor-pointer hover:shadow-md transition-shadow">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{workspace.name}</CardTitle>
                          <Badge variant="outline">{workspace.type.replace('_', ' ')}</Badge>
                        </div>
                        {workspace.description && (
                          <CardDescription>{workspace.description}</CardDescription>
                        )}
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="flex -space-x-2">
                            {workspace.member_details?.slice(0, 4).map(m => (
                              <Avatar key={m.id} className="h-8 w-8 border-2 border-background">
                                <AvatarFallback className="text-xs">
                                  {m.name.split(' ').map(n => n[0]).join('')}
                                </AvatarFallback>
                              </Avatar>
                            ))}
                            {(workspace.member_details?.length || 0) > 4 && (
                              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs border-2 border-background">
                                +{(workspace.member_details?.length || 0) - 4}
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            Updated {new Date(workspace.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>All Tasks</CardTitle>
                  <CardDescription>Manage team tasks and assignments</CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Task
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {tasksLoading ? (
                <div className="text-center py-4 text-muted-foreground">Loading...</div>
              ) : (
                <div className="space-y-3">
                  {tasks.map(task => (
                    <div key={task.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <input
                          type="checkbox"
                          checked={task.status === 'done'}
                          onChange={() => updateTaskMutation.mutate({ 
                            taskId: task.id, 
                            status: task.status === 'done' ? 'todo' : 'done' 
                          })}
                          className="h-5 w-5 rounded"
                        />
                        <div>
                          <p className={`font-medium ${task.status === 'done' ? 'line-through text-muted-foreground' : ''}`}>
                            {task.title}
                          </p>
                          {task.description && (
                            <p className="text-sm text-muted-foreground">{task.description}</p>
                          )}
                          <div className="flex items-center gap-2 mt-1">
                            {task.assignee_name && (
                              <span className="text-xs text-muted-foreground">
                                Assigned to {task.assignee_name}
                              </span>
                            )}
                            {task.due_date && (
                              <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {new Date(task.due_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getPriorityColor(task.priority)}>{task.priority}</Badge>
                        <Badge variant={task.status === 'done' ? 'default' : 'secondary'}>
                          {task.status.replace('_', ' ')}
                        </Badge>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default CollaborationHub
