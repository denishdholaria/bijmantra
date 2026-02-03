import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { apiClient, HarvestRecord } from '@/lib/api-client'
import { toast } from 'sonner'
import { Wheat, Search, Scale, Package, TrendingUp, Download, Plus, RefreshCw } from 'lucide-react'

export function HarvestLog() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [qualityFilter, setQualityFilter] = useState<string>('all')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newRecord, setNewRecord] = useState({
    entry: '',
    plot: '',
    harvest_date: new Date().toISOString().split('T')[0],
    fresh_weight: 0,
    dry_weight: 0,
    moisture: 14.0,
    grain_yield: 0,
    quality: 'B',
    notes: '',
  })

  // Fetch harvest records
  const { data: records = [], isLoading, refetch } = useQuery({
    queryKey: ['harvest-records', searchQuery, qualityFilter],
    queryFn: () => apiClient.harvestService.getHarvestRecords({
      search: searchQuery || undefined,
      quality: qualityFilter !== 'all' ? qualityFilter : undefined,
    }),
  })

  // Fetch harvest summary
  const { data: summary } = useQuery({
    queryKey: ['harvest-summary'],
    queryFn: () => apiClient.harvestService.getHarvestSummary(),
  })

  // Create record mutation
  const createMutation = useMutation({
    mutationFn: (record: typeof newRecord) => apiClient.harvestService.createHarvestRecord(record),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['harvest-records'] })
      queryClient.invalidateQueries({ queryKey: ['harvest-summary'] })
      setIsCreateOpen(false)
      setNewRecord({
        entry: '',
        plot: '',
        harvest_date: new Date().toISOString().split('T')[0],
        fresh_weight: 0,
        dry_weight: 0,
        moisture: 14.0,
        grain_yield: 0,
        quality: 'B',
        notes: '',
      })
      toast.success('Harvest record created successfully')
    },
    onError: () => {
      toast.error('Failed to create harvest record')
    },
  })

  const getQualityColor = (quality: string) => {
    const colors: Record<string, string> = { 
      A: 'bg-green-100 text-green-800', 
      B: 'bg-yellow-100 text-yellow-800', 
      C: 'bg-red-100 text-red-800' 
    }
    return colors[quality] || 'bg-gray-100 text-gray-800'
  }

  const handleCreateRecord = () => {
    if (!newRecord.entry.trim() || !newRecord.plot.trim()) {
      toast.error('Please fill in entry and plot')
      return
    }
    createMutation.mutate(newRecord)
  }

  const handleExport = () => {
    // Create CSV content
    const headers = ['Entry', 'Plot', 'Date', 'Fresh Weight (kg)', 'Dry Weight (kg)', 'Moisture %', 'Yield (t/ha)', 'Quality']
    const rows = records.map((r: HarvestRecord) => [
      r.germplasm_name, r.plot_id, r.harvest_date, r.wet_weight, r.dry_weight, r.moisture_content, r.grain_yield, r.quality_grade
    ])
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `harvest-log-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Export downloaded')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Harvest Log</h1>
          <p className="text-muted-foreground">Record and track harvest data</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />Export
          </Button>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button><Plus className="mr-2 h-4 w-4" />Record Harvest</Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Record New Harvest</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Entry ID</Label>
                    <Input 
                      value={newRecord.entry} 
                      onChange={(e) => setNewRecord({ ...newRecord, entry: e.target.value })}
                      placeholder="BIJ-R-001"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Plot</Label>
                    <Input 
                      value={newRecord.plot} 
                      onChange={(e) => setNewRecord({ ...newRecord, plot: e.target.value })}
                      placeholder="A-001"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Harvest Date</Label>
                  <Input 
                    type="date" 
                    value={newRecord.harvest_date} 
                    onChange={(e) => setNewRecord({ ...newRecord, harvest_date: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Fresh Weight (kg)</Label>
                    <Input 
                      type="number" 
                      step="0.1"
                      value={newRecord.fresh_weight} 
                      onChange={(e) => setNewRecord({ ...newRecord, fresh_weight: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Dry Weight (kg)</Label>
                    <Input 
                      type="number" 
                      step="0.1"
                      value={newRecord.dry_weight} 
                      onChange={(e) => setNewRecord({ ...newRecord, dry_weight: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Moisture %</Label>
                    <Input 
                      type="number" 
                      step="0.1"
                      value={newRecord.moisture} 
                      onChange={(e) => setNewRecord({ ...newRecord, moisture: parseFloat(e.target.value) || 14 })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Grain Yield (t/ha)</Label>
                    <Input 
                      type="number" 
                      step="0.1"
                      value={newRecord.grain_yield} 
                      onChange={(e) => setNewRecord({ ...newRecord, grain_yield: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Quality Grade</Label>
                  <Select value={newRecord.quality} onValueChange={(v) => setNewRecord({ ...newRecord, quality: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A">Grade A - Excellent</SelectItem>
                      <SelectItem value="B">Grade B - Good</SelectItem>
                      <SelectItem value="C">Grade C - Fair</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Notes (optional)</Label>
                  <Input 
                    value={newRecord.notes} 
                    onChange={(e) => setNewRecord({ ...newRecord, notes: e.target.value })}
                    placeholder="Any observations..."
                  />
                </div>
                <Button onClick={handleCreateRecord} className="w-full" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Saving...' : 'Save Record'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Package className="h-8 w-8 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.total_records || 0}</p>
                <p className="text-xs text-muted-foreground">Plots Harvested</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.avg_yield || 0} t/ha</p>
                <p className="text-xs text-muted-foreground">Avg Yield</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Scale className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.total_dry_weight || 0} kg</p>
                <p className="text-xs text-muted-foreground">Total Weight</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Wheat className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.grade_a_count || 0}</p>
                <p className="text-xs text-muted-foreground">Grade A ({summary?.grade_a_percent || 0}%)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search by entry or plot..." 
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)} 
            className="pl-9" 
          />
        </div>
        <Select value={qualityFilter} onValueChange={setQualityFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Quality" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Grades</SelectItem>
            <SelectItem value="A">Grade A</SelectItem>
            <SelectItem value="B">Grade B</SelectItem>
            <SelectItem value="C">Grade C</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Records Table */}
      <Card>
        <CardHeader>
          <CardTitle>Harvest Records</CardTitle>
          <CardDescription>
            {records.length} records • Avg moisture: {summary?.avg_moisture || 0}%
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : records.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No harvest records found. Click "Record Harvest" to add one.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-3 text-left font-medium">Entry</th>
                    <th className="p-3 text-left font-medium">Plot</th>
                    <th className="p-3 text-left font-medium">Date</th>
                    <th className="p-3 text-right font-medium">Fresh (kg)</th>
                    <th className="p-3 text-right font-medium">Dry (kg)</th>
                    <th className="p-3 text-right font-medium">Moisture %</th>
                    <th className="p-3 text-right font-medium">Yield (t/ha)</th>
                    <th className="p-3 text-center font-medium">Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record: HarvestRecord) => (
                    <tr key={record.id} className="border-b hover:bg-accent">
                      <td className="p-3 font-medium">{record.germplasm_name}</td>
                      <td className="p-3">{record.plot_id}</td>
                      <td className="p-3">{record.harvest_date}</td>
                      <td className="p-3 text-right">{record.wet_weight}</td>
                      <td className="p-3 text-right">{record.dry_weight}</td>
                      <td className="p-3 text-right">{record.moisture_content}</td>
                      <td className="p-3 text-right font-medium">{record.grain_yield}</td>
                      <td className="p-3 text-center">
                        <Badge className={getQualityColor(record.quality_grade || '')}>{record.quality_grade}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
