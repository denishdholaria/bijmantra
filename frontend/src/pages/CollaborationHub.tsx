import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Users, MessageSquare, Share2, Bell, Video, 
  FileText, Clock, CheckCircle, AlertCircle, Send,
  UserPlus, Settings, Globe, Lock, Eye
} from 'lucide-react'

interface TeamMember {
  id: string
  name: string
  email: string
  role: string
  avatar?: string
  status: 'online' | 'away' | 'offline'
  lastActive?: string
}

interface SharedItem {
  id: string
  type: 'trial' | 'study' | 'germplasm' | 'report'
  name: string
  sharedBy: string
  sharedAt: string
  permission: 'view' | 'edit' | 'admin'
}

interface Activity {
  id: string
  user: string
  action: string
  target: string
  timestamp: string
  type: 'create' | 'update' | 'share' | 'comment'
}

interface Message {
  id: string
  sender: string
  content: string
  timestamp: string
  isOwn: boolean
}

export function CollaborationHub() {
  const [activeTab, setActiveTab] = useState('team')
  const [newMessage, setNewMessage] = useState('')
  const [selectedChat, setSelectedChat] = useState<string | null>(null)

  const teamMembers: TeamMember[] = [
    { id: '1', name: 'Dr. Sarah Chen', email: '[email]', role: 'Lead Breeder', status: 'online' },
    { id: '2', name: 'Raj Patel', email: '[email]', role: 'Data Scientist', status: 'online' },
    { id: '3', name: 'Maria Garcia', email: '[email]', role: 'Field Technician', status: 'away', lastActive: '10 min ago' },
    { id: '4', name: 'John Smith', email: '[email]', role: 'Geneticist', status: 'offline', lastActive: '2 hours ago' },
    { id: '5', name: 'Aisha Okonkwo', email: '[email]', role: 'Research Associate', status: 'online' },
  ]

  const sharedItems: SharedItem[] = [
    { id: '1', type: 'trial', name: 'Rice Yield Trial 2025', sharedBy: 'Dr. Sarah Chen', sharedAt: '2 hours ago', permission: 'edit' },
    { id: '2', type: 'study', name: 'Drought Tolerance Study', sharedBy: 'Raj Patel', sharedAt: '1 day ago', permission: 'view' },
    { id: '3', type: 'germplasm', name: 'Elite Lines Collection', sharedBy: 'Maria Garcia', sharedAt: '3 days ago', permission: 'admin' },
    { id: '4', type: 'report', name: 'Q4 Breeding Progress', sharedBy: 'John Smith', sharedAt: '1 week ago', permission: 'view' },
  ]

  const activities: Activity[] = [
    { id: '1', user: 'Dr. Sarah Chen', action: 'created', target: 'New crossing block for F2 population', timestamp: '5 min ago', type: 'create' },
    { id: '2', user: 'Raj Patel', action: 'updated', target: 'Genomic selection model parameters', timestamp: '15 min ago', type: 'update' },
    { id: '3', user: 'Maria Garcia', action: 'shared', target: 'Field observation data with team', timestamp: '1 hour ago', type: 'share' },
    { id: '4', user: 'John Smith', action: 'commented on', target: 'QTL mapping results', timestamp: '2 hours ago', type: 'comment' },
    { id: '5', user: 'Aisha Okonkwo', action: 'created', target: 'Disease resistance screening protocol', timestamp: '3 hours ago', type: 'create' },
  ]

  const messages: Message[] = [
    { id: '1', sender: 'Dr. Sarah Chen', content: 'Has anyone reviewed the latest yield data from Block A?', timestamp: '10:30 AM', isOwn: false },
    { id: '2', sender: 'You', content: 'Yes, I noticed some outliers in plots 15-18. Should we investigate?', timestamp: '10:32 AM', isOwn: true },
    { id: '3', sender: 'Raj Patel', content: 'I can run a quick analysis. Give me 30 minutes.', timestamp: '10:35 AM', isOwn: false },
    { id: '4', sender: 'Dr. Sarah Chen', content: 'Perfect. Let\'s discuss in the afternoon standup.', timestamp: '10:36 AM', isOwn: false },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'away': return 'bg-yellow-500'
      default: return 'bg-gray-400'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trial': return '🧪'
      case 'study': return '📊'
      case 'germplasm': return '🌱'
      case 'report': return '📄'
      default: return '📁'
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'create': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'update': return <Clock className="h-4 w-4 text-blue-500" />
      case 'share': return <Share2 className="h-4 w-4 text-purple-500" />
      case 'comment': return <MessageSquare className="h-4 w-4 text-orange-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      // In real app, send via WebSocket
      console.log('Sending:', newMessage)
      setNewMessage('')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Collaboration Hub</h1>
          <p className="text-muted-foreground">
            Work together with your team in real-time
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Video className="mr-2 h-4 w-4" />
            Start Meeting
          </Button>
          <Button>
            <UserPlus className="mr-2 h-4 w-4" />
            Invite Member
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Team Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{teamMembers.length}</div>
            <p className="text-xs text-muted-foreground">
              {teamMembers.filter(m => m.status === 'online').length} online now
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Shared Items</CardTitle>
            <Share2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sharedItems.length}</div>
            <p className="text-xs text-muted-foreground">
              Across all projects
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Activity</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activities.length}</div>
            <p className="text-xs text-muted-foreground">
              Actions by team
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unread Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">
              In 2 conversations
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="team">
            <Users className="mr-2 h-4 w-4" />
            Team
          </TabsTrigger>
          <TabsTrigger value="chat">
            <MessageSquare className="mr-2 h-4 w-4" />
            Chat
          </TabsTrigger>
          <TabsTrigger value="shared">
            <Share2 className="mr-2 h-4 w-4" />
            Shared
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Bell className="mr-2 h-4 w-4" />
            Activity
          </TabsTrigger>
        </TabsList>

        <TabsContent value="team" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>
                Your breeding program collaborators
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {teamMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <Avatar>
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback>{member.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                        </Avatar>
                        <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white ${getStatusColor(member.status)}`} />
                      </div>
                      <div>
                        <p className="font-medium">{member.name}</p>
                        <p className="text-sm text-muted-foreground">{member.role}</p>
                        {member.status !== 'online' && member.lastActive && (
                          <p className="text-xs text-muted-foreground">Last active: {member.lastActive}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={member.status === 'online' ? 'default' : 'secondary'}>
                        {member.status}
                      </Badge>
                      <Button variant="ghost" size="icon">
                        <MessageSquare className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Video className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="chat" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="md:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Conversations</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[400px]">
                  <div className="space-y-1 p-2">
                    <div 
                      className="p-3 rounded-lg bg-accent cursor-pointer"
                      onClick={() => setSelectedChat('team')}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                          <Users className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">Team Chat</p>
                          <p className="text-xs text-muted-foreground truncate">
                            Dr. Sarah: Let's discuss in the afternoon...
                          </p>
                        </div>
                        <Badge variant="destructive" className="text-xs">3</Badge>
                      </div>
                    </div>
                    {teamMembers.slice(0, 3).map((member) => (
                      <div 
                        key={member.id}
                        className="p-3 rounded-lg hover:bg-accent cursor-pointer"
                        onClick={() => setSelectedChat(member.id)}
                      >
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <Avatar className="h-10 w-10">
                              <AvatarFallback>{member.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                            </Avatar>
                            <span className={`absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-white ${getStatusColor(member.status)}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{member.name}</p>
                            <p className="text-xs text-muted-foreground truncate">
                              Click to start conversation
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader className="border-b">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Team Chat</CardTitle>
                    <CardDescription>5 members • 3 online</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[300px] p-4">
                  <div className="space-y-4">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`flex ${msg.isOwn ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[70%] ${msg.isOwn ? 'order-2' : ''}`}>
                          {!msg.isOwn && (
                            <p className="text-xs text-muted-foreground mb-1">{msg.sender}</p>
                          )}
                          <div className={`p-3 rounded-lg ${msg.isOwn ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                            <p className="text-sm">{msg.content}</p>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">{msg.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
                <div className="p-4 border-t">
                  <div className="flex gap-2">
                    <Input 
                      placeholder="Type a message..." 
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    />
                    <Button onClick={handleSendMessage}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="shared" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Shared With Me</CardTitle>
                  <CardDescription>
                    Items shared by your team members
                  </CardDescription>
                </div>
                <Button variant="outline">
                  <Share2 className="mr-2 h-4 w-4" />
                  Share New Item
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sharedItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="text-2xl">{getTypeIcon(item.type)}</div>
                      <div>
                        <p className="font-medium">{item.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Shared by {item.sharedBy} • {item.sharedAt}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={item.permission === 'admin' ? 'default' : item.permission === 'edit' ? 'secondary' : 'outline'}>
                        {item.permission === 'view' && <Eye className="mr-1 h-3 w-3" />}
                        {item.permission === 'edit' && <FileText className="mr-1 h-3 w-3" />}
                        {item.permission === 'admin' && <Settings className="mr-1 h-3 w-3" />}
                        {item.permission}
                      </Badge>
                      <Button variant="outline" size="sm">Open</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                What your team has been working on
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className="mt-1">{getActivityIcon(activity.type)}</div>
                    <div className="flex-1">
                      <p>
                        <span className="font-medium">{activity.user}</span>
                        {' '}{activity.action}{' '}
                        <span className="text-primary">{activity.target}</span>
                      </p>
                      <p className="text-sm text-muted-foreground">{activity.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
