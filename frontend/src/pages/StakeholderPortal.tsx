import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Users, Building, Handshake, Mail, Phone,
  Globe, FileText, Calendar, MessageSquare, Plus
} from 'lucide-react'

interface Stakeholder {
  id: string
  name: string
  organization: string
  type: 'farmer' | 'seed-company' | 'research' | 'government' | 'ngo'
  email: string
  phone: string
  country: string
  engagement: 'active' | 'moderate' | 'inactive'
  lastContact: string
}

interface Partnership {
  id: string
  partner: string
  type: string
  status: 'active' | 'pending' | 'completed'
  startDate: string
  description: string
}

export function StakeholderPortal() {
  const [activeTab, setActiveTab] = useState('stakeholders')

  const stakeholders: Stakeholder[] = [
    { id: '1', name: 'AgriCorp Seeds', organization: 'AgriCorp International', type: 'seed-company', email: '[email]', phone: '[phone]', country: 'India', engagement: 'active', lastContact: '2 days ago' },
    { id: '2', name: 'National Research Institute', organization: 'NARI', type: 'research', email: '[email]', phone: '[phone]', country: 'Philippines', engagement: 'active', lastContact: '1 week ago' },
    { id: '3', name: 'Ministry of Agriculture', organization: 'Government', type: 'government', email: '[email]', phone: '[phone]', country: 'Thailand', engagement: 'moderate', lastContact: '2 weeks ago' },
    { id: '4', name: 'Farmers Cooperative', organization: 'Regional Coop', type: 'farmer', email: '[email]', phone: '[phone]', country: 'Vietnam', engagement: 'active', lastContact: '3 days ago' },
    { id: '5', name: 'Food Security NGO', organization: 'Global Food Initiative', type: 'ngo', email: '[email]', phone: '[phone]', country: 'Kenya', engagement: 'moderate', lastContact: '1 month ago' },
  ]

  const partnerships: Partnership[] = [
    { id: '1', partner: 'AgriCorp International', type: 'Seed Licensing', status: 'active', startDate: '2024-01-15', description: 'Exclusive licensing for drought-tolerant varieties' },
    { id: '2', partner: 'NARI', type: 'Research Collaboration', status: 'active', startDate: '2023-06-01', description: 'Joint QTL mapping project' },
    { id: '3', partner: 'Global Food Initiative', type: 'Technology Transfer', status: 'pending', startDate: '2025-01-01', description: 'Capacity building in Africa' },
    { id: '4', partner: 'Regional Coop', type: 'Field Testing', status: 'active', startDate: '2024-06-15', description: 'On-farm variety trials' },
  ]

  const stats = {
    total: stakeholders.length,
    active: stakeholders.filter(s => s.engagement === 'active').length,
    partnerships: partnerships.filter(p => p.status === 'active').length,
    countries: new Set(stakeholders.map(s => s.country)).size
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = { 'seed-company': 'bg-blue-100 text-blue-800', research: 'bg-purple-100 text-purple-800', government: 'bg-red-100 text-red-800', farmer: 'bg-green-100 text-green-800', ngo: 'bg-orange-100 text-orange-800' }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getEngagementColor = (engagement: string) => {
    const colors: Record<string, string> = { active: 'bg-green-100 text-green-800', moderate: 'bg-yellow-100 text-yellow-800', inactive: 'bg-gray-100 text-gray-800' }
    return colors[engagement] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = { active: 'bg-green-100 text-green-800', pending: 'bg-yellow-100 text-yellow-800', completed: 'bg-blue-100 text-blue-800' }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Stakeholder Portal</h1>
          <p className="text-muted-foreground">Manage relationships with partners and stakeholders</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Add Stakeholder</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stakeholders</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Total contacts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <Handshake className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active}</div>
            <p className="text-xs text-muted-foreground">Engaged partners</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Partnerships</CardTitle>
            <Building className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.partnerships}</div>
            <p className="text-xs text-muted-foreground">Active agreements</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Countries</CardTitle>
            <Globe className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.countries}</div>
            <p className="text-xs text-muted-foreground">Geographic reach</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="stakeholders"><Users className="mr-2 h-4 w-4" />Stakeholders</TabsTrigger>
          <TabsTrigger value="partnerships"><Handshake className="mr-2 h-4 w-4" />Partnerships</TabsTrigger>
          <TabsTrigger value="communications"><MessageSquare className="mr-2 h-4 w-4" />Communications</TabsTrigger>
        </TabsList>

        <TabsContent value="stakeholders" className="space-y-4">
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {stakeholders.map((s) => (
                  <div key={s.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <Avatar>
                        <AvatarFallback>{s.name.split(' ').map(n => n[0]).join('').slice(0, 2)}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{s.name}</p>
                        <p className="text-sm text-muted-foreground">{s.organization}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <p className="flex items-center gap-1"><Globe className="h-3 w-3" />{s.country}</p>
                        <p className="text-muted-foreground">Last contact: {s.lastContact}</p>
                      </div>
                      <Badge className={getTypeColor(s.type)}>{s.type}</Badge>
                      <Badge className={getEngagementColor(s.engagement)}>{s.engagement}</Badge>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" aria-label={`Email ${s.name}`}><Mail className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" aria-label={`Call ${s.name}`}><Phone className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="partnerships" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {partnerships.map((p) => (
              <Card key={p.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{p.partner}</CardTitle>
                    <Badge className={getStatusColor(p.status)}>{p.status}</Badge>
                  </div>
                  <CardDescription>{p.type}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">{p.description}</p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>Started: {p.startDate}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="communications"><Card><CardContent className="pt-6"><p className="text-muted-foreground">Communication history and outreach</p></CardContent></Card></TabsContent>
      </Tabs>
    </div>
  )
}
