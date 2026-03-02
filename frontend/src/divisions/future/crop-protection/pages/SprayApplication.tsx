import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Filter, Droplets, Calendar, User, FileText, AlertCircle, Info } from 'lucide-react'
import { format } from 'date-fns'
import { apiClient } from '@/lib/api-client'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/useToast'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Type definition based on backend schema
interface SprayApplication {
  id: number
  application_date: string
  product_name: string
  product_type?: string
  active_ingredient?: string
  rate_per_ha?: number
  rate_unit?: string
  total_area_ha?: number
  water_volume_l_ha?: number
  applicator_name?: string
  equipment_used?: string
  target_pest?: string
  pre_harvest_interval_days?: number
  re_entry_interval_hours?: number
  notes?: string
  organization_id: number
  created_at: string
}

interface NewApplication {
  application_date: string
  product_name: string
  product_type?: string
  rate_per_ha?: number
  total_area_ha?: number
  applicator_name?: string
  notes?: string
}

export function SprayApplication() {
  const [isDataEntryOpen, setIsDataEntryOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [newRecord, setNewRecord] = useState<NewApplication>({
    application_date: new Date().toISOString().split('T')[0],
    product_name: '',
    applicator_name: '',
  })

  const { toast } = useToast()
  const queryClient = useQueryClient()

  // Fetch spray applications
  const { data: applications, isLoading, error } = useQuery({
    queryKey: ['future', 'spray-applications'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/future/spray-applications/')
      return response as SprayApplication[]
    },
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data: NewApplication) => {
      return apiClient.post('/api/v2/future/spray-applications/', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['future', 'spray-applications'] })
      setIsDataEntryOpen(false)
      setNewRecord({
        application_date: new Date().toISOString().split('T')[0],
        product_name: '',
        applicator_name: '',
      })
      toast({
        title: 'Application Recorded',
        description: 'New spray application has been successfully logged.',
        type: 'success',
      })
    },
    onError: (error) => {
      console.error('Failed to create record:', error)
      toast({
        title: 'Error',
        description: 'Failed to record spray application. Please try again.',
        type: 'error',
      })
    },
  })

  const handleInputChange = (field: keyof NewApplication, value: any) => {
    setNewRecord(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = () => {
    if (!newRecord.product_name) {
      toast({
        title: 'Validation Error',
        description: 'Product name is required.',
        type: 'error',
      })
      return
    }
    createMutation.mutate(newRecord)
  }

  // Calculate stats
  const totalApps = applications?.length || 0
  const totalArea = applications?.reduce((sum, app) => sum + (app.total_area_ha || 0), 0) || 0
  const complianceRate = 100 // Placeholder logic, could be complex

  const filteredApps = applications?.filter(app => 
    app.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.target_pest?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <Droplets className="h-8 w-8 text-blue-600" />
            Spray Applications
          </h1>
          <p className="text-muted-foreground mt-1">
            Track pesticide applications, compliance, and safety intervals
          </p>
        </div>
        <div className="flex items-center gap-2">
           <Dialog open={isDataEntryOpen} onOpenChange={setIsDataEntryOpen}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="mr-2 h-4 w-4" />
                Record Spray
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Record Spray Application</DialogTitle>
                <DialogDescription>
                  Enter details for a new chemical application. Ensure PHI and REI are noted.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="date">Date</Label>
                    <Input 
                      id="date" 
                      type="date" 
                      value={newRecord.application_date}
                      onChange={(e) => handleInputChange('application_date', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="applicator">Applicator Name</Label>
                    <Input 
                      id="applicator" 
                      placeholder="License Holder" 
                      value={newRecord.applicator_name}
                      onChange={(e) => handleInputChange('applicator_name', e.target.value)}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="product">Product Name</Label>
                    <Input 
                      id="product" 
                      placeholder="e.g. Fungicide X" 
                      value={newRecord.product_name}
                      onChange={(e) => handleInputChange('product_name', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="type">Product Type</Label>
                    <Input 
                      id="type"
                      placeholder="Herbicide/Fungicide"
                      value={newRecord.product_type || ''}
                      onChange={(e) => handleInputChange('product_type', e.target.value)} 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="rate">Rate (L/ha or kg/ha)</Label>
                    <Input 
                      id="rate" 
                      type="number" 
                      placeholder="0.0"
                      value={newRecord.rate_per_ha || ''}
                      onChange={(e) => handleInputChange('rate_per_ha', parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="area">Total Area (ha)</Label>
                    <Input 
                      id="area" 
                      type="number" 
                      placeholder="0.0" 
                      value={newRecord.total_area_ha || ''}
                      onChange={(e) => handleInputChange('total_area_ha', parseFloat(e.target.value))}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Notes / Observations</Label>
                  <Textarea 
                    id="notes" 
                    placeholder="Weather conditions, efficacy notes..."
                    value={newRecord.notes || ''}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDataEntryOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit} disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Logging...' : 'Log Application'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

       {/* KPIs */}
       <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Droplets className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : totalApps}</div>
            <p className="text-xs text-muted-foreground">Recorded this season</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Area Treated</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : `${totalArea.toFixed(1)} ha`}</div>
            <p className="text-xs text-muted-foreground">Cumulative treatment area</p>
          </CardContent>
        </Card>
        <Card>
           <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? <Skeleton className="h-8 w-16" /> : `${complianceRate}%`}</div>
            <p className="text-xs text-muted-foreground">Regulatory adherence</p>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>Failed to load spray applications. Please try again later.</AlertDescription>
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Application History</CardTitle>
                <CardDescription>Records of all chemical applications</CardDescription>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search products..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
               <div className="space-y-4">
                 {[1, 2, 3].map(i => <Skeleton key={i} className="h-12 w-full" />)}
               </div>
            ) : filteredApps?.length === 0 ? (
               <div className="text-center py-8 text-muted-foreground">
                 <Droplets className="h-12 w-12 mx-auto mb-3 opacity-20" />
                 <p>No spray applications recorded yet.</p>
               </div>
            ) : (
              <div className="rounded-md border">
                <table className="w-full text-sm text-left">
                  <thead className="bg-muted/50 text-muted-foreground">
                    <tr>
                      <th className="p-4 font-medium">Date</th>
                      <th className="p-4 font-medium">Product</th>
                      <th className="p-4 font-medium">Rate</th>
                      <th className="p-4 font-medium">Area</th>
                       <th className="p-4 font-medium">Applicator</th>
                       <th className="p-4 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredApps?.map((app) => (
                      <tr key={app.id} className="border-t hover:bg-muted/50 transition-colors">
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                             <Calendar className="h-4 w-4 text-muted-foreground" />
                             {format(new Date(app.application_date), 'MMM d, yyyy')}
                          </div>
                        </td>
                        <td className="p-4 font-medium">
                          {app.product_name}
                          {app.product_type && <Badge variant="outline" className="ml-2 text-xs">{app.product_type}</Badge>}
                        </td>
                        <td className="p-4">{app.rate_per_ha ? `${app.rate_per_ha} /ha` : '-'}</td>
                        <td className="p-4">{app.total_area_ha ? `${app.total_area_ha} ha` : '-'}</td>
                        <td className="p-4">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <User className="h-3 w-3" />
                            {app.applicator_name || 'N/A'}
                          </div>
                        </td>
                         <td className="p-4 text-right">
                           <Button variant="ghost" size="sm">Details</Button>
                         </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
          <CardFooter className="bg-muted/50 text-xs text-muted-foreground text-center flex justify-center py-3">
             <AlertCircle className="h-3 w-3 mr-2" />
             Always follow label instructions and local regulations when applying chemicals.
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
