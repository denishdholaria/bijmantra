import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient } from '@/lib/api-client'
import {
  PieChart,
  DollarSign,
  Users,
  MapPin,
  TrendingUp,
  Settings,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react'

interface BudgetCategory {
  id: string
  name: string
  allocated: number
  used: number
  unit: string
  status: 'on-track' | 'over' | 'under'
  year: number
}

interface StaffAllocation {
  id: string
  role: string
  count: number
  projects: number
  department: string
}

interface FieldAllocation {
  id: string
  field: string
  area: number
  trials: number
  utilization: number
}

export function ResourceAllocation() {
  const [selectedYear] = useState(2025)

  // Fetch budget categories
  const { data: budgetCategories = [], isLoading: loadingBudget, refetch: refetchBudget } = useQuery({
    queryKey: ['budget-categories', selectedYear],
    queryFn: () => apiClient.getBudgetCategories(selectedYear),
  })

  // Fetch budget summary
  const { data: budgetSummary } = useQuery({
    queryKey: ['budget-summary', selectedYear],
    queryFn: () => apiClient.getBudgetSummary(selectedYear),
  })

  // Fetch staff allocations
  const { data: staffAllocations = [], isLoading: loadingStaff } = useQuery({
    queryKey: ['staff-allocations'],
    queryFn: () => apiClient.getStaffAllocations(),
  })

  // Fetch staff summary
  const { data: staffSummary } = useQuery({
    queryKey: ['staff-summary'],
    queryFn: () => apiClient.getStaffSummary(),
  })

  // Fetch field allocations
  const { data: fieldAllocations = [], isLoading: loadingFields } = useQuery({
    queryKey: ['field-allocations'],
    queryFn: () => apiClient.getFieldAllocations(),
  })

  // Fetch field summary
  const { data: fieldSummary } = useQuery({
    queryKey: ['field-summary'],
    queryFn: () => apiClient.getFieldAllocationSummary(),
  })

  const totalBudget = budgetSummary?.total_allocated || 0
  const totalUsed = budgetSummary?.total_used || 0
  const totalStaff = staffSummary?.total_staff || 0
  const totalArea = fieldSummary?.total_area_ha || 0

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'on-track':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />On Track</Badge>
      case 'over':
        return <Badge variant="destructive"><AlertTriangle className="h-3 w-3 mr-1" />Over Budget</Badge>
      case 'under':
        return <Badge variant="secondary">Under Budget</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

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
          <Button variant="outline" onClick={() => refetchBudget()}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Report</Button>
          <Button><Settings className="h-4 w-4 mr-2" />Configure</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  ${(totalBudget / 1000).toFixed(0)}K
                </div>
                <div className="text-sm text-muted-foreground">Total Budget</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {budgetSummary?.utilization_percent || 0}%
                </div>
                <div className="text-sm text-muted-foreground">Budget Used</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalStaff}</div>
                <div className="text-sm text-muted-foreground">Staff Members</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <MapPin className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalArea} ha</div>
                <div className="text-sm text-muted-foreground">Field Area</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="budget" className="space-y-4">
        <TabsList>
          <TabsTrigger value="budget">
            <DollarSign className="h-4 w-4 mr-2" />Budget
          </TabsTrigger>
          <TabsTrigger value="staff">
            <Users className="h-4 w-4 mr-2" />Staff
          </TabsTrigger>
          <TabsTrigger value="fields">
            <MapPin className="h-4 w-4 mr-2" />Fields
          </TabsTrigger>
        </TabsList>

        <TabsContent value="budget">
          <Card>
            <CardHeader>
              <CardTitle>Budget Allocation</CardTitle>
              <CardDescription>Track spending across categories for {selectedYear}</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingBudget ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-6">
                  {budgetCategories.map((cat: BudgetCategory) => (
                    <div key={cat.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{cat.name}</span>
                          {getStatusBadge(cat.status)}
                        </div>
                        <div className="text-sm">
                          <span className="font-bold">${(cat.used / 1000).toFixed(0)}K</span>
                          <span className="text-muted-foreground"> / ${(cat.allocated / 1000).toFixed(0)}K</span>
                        </div>
                      </div>
                      <Progress 
                        value={(cat.used / cat.allocated) * 100} 
                        className={cat.status === 'over' ? 'bg-red-100' : ''} 
                      />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="staff">
          <Card>
            <CardHeader>
              <CardTitle>Staff Allocation</CardTitle>
              <CardDescription>
                Team distribution across projects • {staffSummary?.total_projects || 0} active projects
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingStaff ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-24 w-full" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {staffAllocations.map((staff: StaffAllocation) => (
                    <div key={staff.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{staff.role}</h4>
                        <Badge variant="outline">{staff.count} people</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {staff.department} • Assigned to {staff.projects} projects
                      </div>
                      <div className="mt-2">
                        <Progress value={Math.min((staff.projects / staff.count) * 50, 100)} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fields">
          <Card>
            <CardHeader>
              <CardTitle>Field Utilization</CardTitle>
              <CardDescription>
                Field space allocation and usage • Avg utilization: {fieldSummary?.avg_utilization || 0}%
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingFields ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {fieldAllocations.map((field: FieldAllocation) => (
                    <div key={field.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <div className="font-medium">{field.field}</div>
                        <div className="text-sm text-muted-foreground">
                          {field.area} hectares • {field.trials} trials
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="w-32">
                          <div className="text-sm text-right mb-1">{field.utilization}% utilized</div>
                          <Progress value={field.utilization} />
                        </div>
                        <Badge 
                          variant={field.utilization > 80 ? 'destructive' : field.utilization > 50 ? 'default' : 'secondary'}
                        >
                          {field.utilization > 80 ? 'High' : field.utilization > 50 ? 'Medium' : 'Low'}
                        </Badge>
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
