import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  PieChart,
  DollarSign,
  Users,
  MapPin,
  Beaker,
  Calendar,
  TrendingUp,
  Settings,
  Download
} from 'lucide-react'

interface ResourceCategory {
  name: string
  allocated: number
  used: number
  unit: string
  status: 'on-track' | 'over' | 'under'
}

export function ResourceAllocation() {
  const [selectedYear, setSelectedYear] = useState('2025')

  const budgetCategories: ResourceCategory[] = [
    { name: 'Field Operations', allocated: 150000, used: 98000, unit: '$', status: 'on-track' },
    { name: 'Laboratory', allocated: 80000, used: 72000, unit: '$', status: 'on-track' },
    { name: 'Personnel', allocated: 250000, used: 208000, unit: '$', status: 'on-track' },
    { name: 'Equipment', allocated: 50000, used: 55000, unit: '$', status: 'over' },
    { name: 'Consumables', allocated: 30000, used: 18000, unit: '$', status: 'under' }
  ]

  const staffAllocation = [
    { role: 'Breeders', count: 4, projects: 8 },
    { role: 'Technicians', count: 12, projects: 15 },
    { role: 'Data Analysts', count: 2, projects: 6 },
    { role: 'Field Workers', count: 20, projects: 12 }
  ]

  const fieldAllocation = [
    { field: 'Field A - Main', area: 5.0, trials: 4, utilization: 85 },
    { field: 'Field B - North', area: 3.5, trials: 3, utilization: 72 },
    { field: 'Field C - South', area: 4.0, trials: 2, utilization: 45 },
    { field: 'Greenhouse', area: 0.5, trials: 6, utilization: 95 }
  ]

  const totalBudget = budgetCategories.reduce((sum, c) => sum + c.allocated, 0)
  const totalUsed = budgetCategories.reduce((sum, c) => sum + c.used, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <PieChart className="h-8 w-8 text-primary" />
            Resource Allocation
          </h1>
          <p className="text-muted-foreground mt-1">Manage budget, staff, and field resources</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
          <Button><Settings className="h-4 w-4 mr-2" />Configure</Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><DollarSign className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">${(totalBudget / 1000).toFixed(0)}K</div>
                <div className="text-sm text-muted-foreground">Total Budget</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><TrendingUp className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{((totalUsed / totalBudget) * 100).toFixed(0)}%</div>
                <div className="text-sm text-muted-foreground">Budget Used</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Users className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{staffAllocation.reduce((sum, s) => sum + s.count, 0)}</div>
                <div className="text-sm text-muted-foreground">Staff Members</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><MapPin className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{fieldAllocation.reduce((sum, f) => sum + f.area, 0)} ha</div>
                <div className="text-sm text-muted-foreground">Field Area</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="budget" className="space-y-4">
        <TabsList>
          <TabsTrigger value="budget"><DollarSign className="h-4 w-4 mr-2" />Budget</TabsTrigger>
          <TabsTrigger value="staff"><Users className="h-4 w-4 mr-2" />Staff</TabsTrigger>
          <TabsTrigger value="fields"><MapPin className="h-4 w-4 mr-2" />Fields</TabsTrigger>
        </TabsList>

        <TabsContent value="budget">
          <Card>
            <CardHeader>
              <CardTitle>Budget Allocation</CardTitle>
              <CardDescription>Track spending across categories</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {budgetCategories.map((cat, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{cat.name}</span>
                        <Badge variant={cat.status === 'on-track' ? 'default' : cat.status === 'over' ? 'destructive' : 'secondary'} className="capitalize">{cat.status}</Badge>
                      </div>
                      <div className="text-sm">
                        <span className="font-bold">${(cat.used / 1000).toFixed(0)}K</span>
                        <span className="text-muted-foreground"> / ${(cat.allocated / 1000).toFixed(0)}K</span>
                      </div>
                    </div>
                    <Progress value={(cat.used / cat.allocated) * 100} className={cat.status === 'over' ? 'bg-red-100' : ''} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staff">
          <Card>
            <CardHeader>
              <CardTitle>Staff Allocation</CardTitle>
              <CardDescription>Team distribution across projects</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {staffAllocation.map((staff, i) => (
                  <div key={i} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{staff.role}</h4>
                      <Badge variant="outline">{staff.count} people</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">Assigned to {staff.projects} projects</div>
                    <div className="mt-2">
                      <Progress value={(staff.projects / staff.count) * 50} />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fields">
          <Card>
            <CardHeader>
              <CardTitle>Field Utilization</CardTitle>
              <CardDescription>Field space allocation and usage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {fieldAllocation.map((field, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="font-medium">{field.field}</div>
                      <div className="text-sm text-muted-foreground">{field.area} hectares • {field.trials} trials</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-32">
                        <div className="text-sm text-right mb-1">{field.utilization}% utilized</div>
                        <Progress value={field.utilization} />
                      </div>
                      <Badge variant={field.utilization > 80 ? 'destructive' : field.utilization > 50 ? 'default' : 'secondary'}>
                        {field.utilization > 80 ? 'High' : field.utilization > 50 ? 'Medium' : 'Low'}
                      </Badge>
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
