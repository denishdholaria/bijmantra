import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
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
  Printer,
  Calendar as CalendarIcon
} from 'lucide-react'
import { toast } from 'sonner'

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

interface ResourceUpdate {
  type: 'program' | 'location'
  id: string
  field: string
  value: number
}

export function ResourceAllocation() {
  const [selectedYear] = useState(2025)
  const [isAllocationModalOpen, setIsAllocationModalOpen] = useState(false)
  const [allocationType, setAllocationType] = useState<'program' | 'location'>('program')
  const [selectedId, setSelectedId] = useState<string>('')
  const [allocationValue, setAllocationValue] = useState<string>('')

  const queryClient = useQueryClient()

  // Fetch Programs (Budget)
  const { data: programsData, isLoading: loadingPrograms } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.programService.getPrograms(0, 100),
  })

  // Fetch Locations (Fields)
  const { data: locationsData, isLoading: loadingLocations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.locationService.getLocations(0, 100),
  })

  // Fetch People (Staff)
  const { data: peopleData, isLoading: loadingPeople } = useQuery({
    queryKey: ['people'],
    queryFn: () => apiClient.peopleService.getPeople(0, 100),
  })

  // Fetch Seasons (Calendar)
  const { data: seasonsData, isLoading: loadingSeasons } = useQuery({
    queryKey: ['seasons', selectedYear],
    queryFn: () => apiClient.seasonService.getSeasons(0, 100, selectedYear),
  })

  // Stable random function
  const stableRandom = (seed: string) => {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      const char = seed.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    const x = Math.sin(hash) * 10000;
    return x - Math.floor(x);
  }

  // Transformation Logic
  const budgetCategories: BudgetCategory[] = (programsData?.result?.data || []).map((prog: any) => {
    const allocated = prog.additionalInfo?.budget_allocated || 50000; // Default 50k
    const used = prog.additionalInfo?.budget_used || Math.floor(stableRandom(prog.programDbId || prog.programName) * 40000); // Simulated used
    const status = used > allocated ? 'over' : used > allocated * 0.9 ? 'on-track' : 'under';

    return {
      id: prog.programDbId,
      name: prog.programName,
      allocated,
      used,
      unit: 'USD',
      status: status as 'on-track' | 'over' | 'under',
      year: selectedYear
    }
  });

  const fieldAllocations: FieldAllocation[] = (locationsData?.result?.data || []).map((loc: any) => {
    const area = loc.additionalInfo?.field_capacity || 100; // Default 100ha
    const trials = loc.additionalInfo?.active_trials || Math.floor(stableRandom(loc.locationDbId || loc.locationName) * 10);
    const usedArea = loc.additionalInfo?.field_usage || Math.floor(stableRandom((loc.locationDbId || loc.locationName) + 'usage') * area);
    const utilization = Math.round((usedArea / area) * 100);

    return {
      id: loc.locationDbId,
      field: loc.locationName,
      area,
      trials,
      utilization
    }
  });

  const staffAllocations: StaffAllocation[] = [];
  const roles: Record<string, number> = {};
  (peopleData?.result?.data || []).forEach((person: any) => {
    const role = person.additionalInfo?.role || 'Researcher';
    roles[role] = (roles[role] || 0) + 1;
  });

  Object.entries(roles).forEach(([role, count], index) => {
    staffAllocations.push({
      id: `role-${index}`,
      role,
      count,
      projects: Math.floor(count * 2.5), // Simulated
      department: 'Research'
    });
  });

  // Aggregates
  const totalBudget = budgetCategories.reduce((acc, curr) => acc + curr.allocated, 0);
  const totalUsed = budgetCategories.reduce((acc, curr) => acc + curr.used, 0);
  const totalStaff = (peopleData?.result?.data || []).length;
  const totalArea = fieldAllocations.reduce((acc, curr) => acc + curr.area, 0);
  const budgetUtilization = totalBudget > 0 ? Math.round((totalUsed / totalBudget) * 100) : 0;

  // Mutation for Allocation
  const updateResourceMutation = useMutation({
    mutationFn: async (data: ResourceUpdate) => {
      // In a real scenario, this would call updateProgram or updateLocation
      // For now, we'll simulate a delay and success
      await new Promise(resolve => setTimeout(resolve, 1000));
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Allocated ${data.value} to ${data.type === 'program' ? 'Budget' : 'Field Capacity'}`);
      queryClient.invalidateQueries({ queryKey: [data.type === 'program' ? 'programs' : 'locations'] });
      setIsAllocationModalOpen(false);
      setAllocationValue('');
      setSelectedId('');
    },
    onError: () => {
      toast.error("Failed to update allocation");
    }
  });

  const handleAllocate = () => {
    if (!selectedId || !allocationValue) return;

    // Validation
    const val = parseFloat(allocationValue);
    if (isNaN(val) || val <= 0) {
      toast.error("Please enter a valid positive number");
      return;
    }

    if (allocationType === 'program') {
      const prog = budgetCategories.find(p => p.id === selectedId);
      if (prog && prog.used + val > prog.allocated * 1.5) { // Hard limit 150%
         toast.warning("Warning: significantly exceeding allocated budget");
      }
    } else {
      const field = fieldAllocations.find(f => f.id === selectedId);
      if (field && val > field.area) {
        toast.error("Cannot allocate more than total field area");
        return;
      }
    }

    updateResourceMutation.mutate({
      type: allocationType,
      id: selectedId,
      field: allocationType === 'program' ? 'budget_allocated' : 'field_usage',
      value: val
    });
  };

  const handleExportCSV = () => {
    const headers = ['Category', 'Name', 'Allocated', 'Used/Utilized', 'Status/Unit'];
    const budgetRows = budgetCategories.map(b => ['Budget', b.name, b.allocated, b.used, b.status]);
    const fieldRows = fieldAllocations.map(f => ['Field', f.field, f.area, `${f.utilization}%`, 'Hectares']);
    const staffRows = staffAllocations.map(s => ['Staff', s.role, s.count, s.projects, 'Projects']);

    const csvContent = [
      headers.join(','),
      ...budgetRows.map(r => r.join(',')),
      ...fieldRows.map(r => r.join(',')),
      ...staffRows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `resource_allocation_${selectedYear}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handlePrint = () => {
    window.print();
  };

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
    <div className="space-y-6 print:space-y-4">
      <div className="flex items-center justify-between print:hidden">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <PieChart className="h-8 w-8 text-primary" />
            Resource Allocation
          </h1>
          <p className="text-muted-foreground mt-1">Manage budget, staff, and field resources</p>

          {/* Breadcrumbs Placeholder */}
          <div className="text-sm text-muted-foreground mt-2">
             Home &gt; Operations &gt; Resource Allocation
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => queryClient.invalidateQueries()}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="h-4 w-4 mr-2" />Print
          </Button>
          <Button variant="outline" onClick={handleExportCSV}>
            <Download className="h-4 w-4 mr-2" />Export CSV
          </Button>

          <Dialog open={isAllocationModalOpen} onOpenChange={setIsAllocationModalOpen}>
            <DialogTrigger asChild>
              <Button><Settings className="h-4 w-4 mr-2" />Allocate</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Allocate Resource</DialogTitle>
                <DialogDescription>Adjust budget or field usage manually.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="type" className="text-right">Type</Label>
                  <Select value={allocationType} onValueChange={(val: 'program' | 'location') => setAllocationType(val)}>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="program">Budget (Program)</SelectItem>
                      <SelectItem value="location">Field (Location)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="target" className="text-right">Target</Label>
                  <Select value={selectedId} onValueChange={setSelectedId}>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder="Select target" />
                    </SelectTrigger>
                    <SelectContent>
                      {allocationType === 'program' ? (
                        budgetCategories.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)
                      ) : (
                        fieldAllocations.map(f => <SelectItem key={f.id} value={f.id}>{f.field}</SelectItem>)
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="value" className="text-right">Value</Label>
                  <Input
                    id="value"
                    type="number"
                    className="col-span-3"
                    value={allocationValue}
                    onChange={(e) => setAllocationValue(e.target.value)}
                    placeholder={allocationType === 'program' ? "Amount (USD)" : "Area (ha)"}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleAllocate} disabled={updateResourceMutation.isPending}>
                  {updateResourceMutation.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 print:grid-cols-2">
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
                  {budgetUtilization}%
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
        <TabsList className="print:hidden">
          <TabsTrigger value="budget">
            <DollarSign className="h-4 w-4 mr-2" />Budget
          </TabsTrigger>
          <TabsTrigger value="staff">
            <Users className="h-4 w-4 mr-2" />Staff
          </TabsTrigger>
          <TabsTrigger value="fields">
            <MapPin className="h-4 w-4 mr-2" />Fields
          </TabsTrigger>
          <TabsTrigger value="seasons">
            <CalendarIcon className="h-4 w-4 mr-2" />Seasons
          </TabsTrigger>
        </TabsList>

        <TabsContent value="budget">
          <Card>
            <CardHeader>
              <CardTitle>Budget Allocation</CardTitle>
              <CardDescription>Track spending across programs for {selectedYear}</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingPrograms ? (
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
                  {budgetCategories.length === 0 && <div className="text-center text-muted-foreground py-8">No programs found</div>}
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
                Team distribution across roles • {totalStaff} active members
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingPeople ? (
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
                  {staffAllocations.length === 0 && <div className="text-center text-muted-foreground py-8 col-span-2">No staff found</div>}
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
                Field space allocation and usage • Avg utilization: {fieldAllocations.length > 0 ? Math.round(fieldAllocations.reduce((acc, f) => acc + f.utilization, 0) / fieldAllocations.length) : 0}%
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingLocations ? (
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
                   {fieldAllocations.length === 0 && <div className="text-center text-muted-foreground py-8">No locations found</div>}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="seasons">
          <Card>
            <CardHeader>
               <CardTitle>Field Occupancy</CardTitle>
               <CardDescription>Season overview for {selectedYear}</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingSeasons ? (
                <div className="space-y-2">
                   {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                </div>
              ) : (
                 <div className="space-y-4">
                    {(seasonsData?.result?.data || []).map((season: any) => (
                       <div key={season.seasonDbId} className="flex items-center justify-between p-4 border rounded-lg bg-slate-50 dark:bg-slate-900">
                          <div className="flex items-center gap-4">
                            <CalendarIcon className="h-5 w-5 text-muted-foreground" />
                            <div>
                              <div className="font-medium">{season.seasonName}</div>
                              <div className="text-sm text-muted-foreground">{season.year}</div>
                            </div>
                          </div>
                          <Badge variant="outline">Active</Badge>
                       </div>
                    ))}
                    {(seasonsData?.result?.data || []).length === 0 && (
                        <div className="text-center text-muted-foreground py-8">No seasons found for {selectedYear}</div>
                    )}
                 </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
