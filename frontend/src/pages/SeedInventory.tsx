/**
 * Seed Inventory Page
 * Track seed stock levels and movements
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { seedInventoryEnhancedAPI } from '@/lib/api-client'

interface SeedStock {
  id: string
  germplasm: string
  lotNumber: string
  quantity: number
  unit: string
  location: string
  germinationRate: number
  harvestDate: string
  expiryDate: string
  status: 'available' | 'low' | 'critical' | 'expired'
}

export function SeedInventory() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'available' | 'low' | 'critical' | 'expired'>('all')

  // Fetch seed lots from API
  const { data: lotsData, isLoading } = useQuery({
    queryKey: ['seed-inventory-lots', filter !== 'all' ? filter : undefined],
    queryFn: () => seedInventoryEnhancedAPI.getLots(filter !== 'all' ? { status: filter } : undefined),
  })

  // Fetch summary stats from API
  const { data: summaryData } = useQuery({
    queryKey: ['seed-inventory-summary'],
    queryFn: () => seedInventoryEnhancedAPI.getSummary(),
  })

  // Transform API data to component format
  const stock: SeedStock[] = (lotsData?.lots || []).map((lot: any) => ({
    id: lot.lot_id,
    germplasm: lot.variety || lot.species,
    lotNumber: lot.lot_id,
    quantity: lot.quantity,
    unit: 'g',
    location: lot.storage_location,
    germinationRate: lot.current_viability || 0,
    harvestDate: lot.harvest_date,
    expiryDate: lot.expiry_date || '',
    status: lot.status as SeedStock['status'],
  }))

  const filteredStock = stock.filter(s => {
    const matchesSearch = s.germplasm.toLowerCase().includes(search.toLowerCase()) ||
                          s.lotNumber.toLowerCase().includes(search.toLowerCase())
    return matchesSearch
  })

  const stats = summaryData ? {
    total: summaryData.total_lots || 0,
    available: summaryData.by_status?.available || 0,
    low: summaryData.by_status?.low || 0,
    critical: summaryData.by_status?.critical || 0,
    expired: summaryData.by_status?.expired || 0,
    totalQuantity: summaryData.total_quantity || 0,
  } : {
    total: stock.length,
    available: stock.filter(s => s.status === 'available').length,
    low: stock.filter(s => s.status === 'low').length,
    critical: stock.filter(s => s.status === 'critical').length,
    expired: stock.filter(s => s.status === 'expired').length,
    totalQuantity: stock.reduce((sum, s) => sum + s.quantity, 0),
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-700'
      case 'low': return 'bg-yellow-100 text-yellow-700'
      case 'critical': return 'bg-red-100 text-red-700'
      case 'expired': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getGerminationColor = (rate: number) => {
    if (rate >= 90) return 'text-green-600'
    if (rate >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">Seed Inventory</h1>
            <p className="text-muted-foreground mt-1">Track seed stock and movements</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i}><CardContent className="pt-4"><Skeleton className="h-8 w-16 mx-auto" /></CardContent></Card>
          ))}
        </div>
        <Card><CardContent className="pt-4"><Skeleton className="h-64" /></CardContent></Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Seed Inventory</h1>
          <p className="text-muted-foreground mt-1">Track seed stock and movements</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📥 Receive</Button>
          <Button>📤 Distribute</Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{stats.total}</p>
            <p className="text-xs text-muted-foreground">Total Lots</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.available}</p>
            <p className="text-xs text-muted-foreground">Available</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.low}</p>
            <p className="text-xs text-muted-foreground">Low Stock</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-red-600">{stats.critical}</p>
            <p className="text-xs text-muted-foreground">Critical</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{(stats.totalQuantity / 1000).toFixed(1)}kg</p>
            <p className="text-xs text-muted-foreground">Total Stock</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Input
          placeholder="Search germplasm or lot number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-64"
        />
        <div className="flex gap-2 flex-wrap">
          {(['all', 'available', 'low', 'critical', 'expired'] as const).map((f) => (
            <Button
              key={f}
              size="sm"
              variant={filter === f ? 'default' : 'outline'}
              onClick={() => setFilter(f)}
              className="capitalize"
            >
              {f}
            </Button>
          ))}
        </div>
      </div>

      {/* Inventory Table */}
      <Card>
        <CardHeader>
          <CardTitle>Stock Levels</CardTitle>
          <CardDescription>{filteredStock.length} seed lots</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Germplasm</th>
                  <th className="text-left p-2">Lot #</th>
                  <th className="text-right p-2">Quantity</th>
                  <th className="text-center p-2">Germ %</th>
                  <th className="text-left p-2">Location</th>
                  <th className="text-left p-2">Expiry</th>
                  <th className="text-center p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredStock.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-muted/50">
                    <td className="p-2 font-medium">{item.germplasm}</td>
                    <td className="p-2 font-mono text-xs">{item.lotNumber}</td>
                    <td className="p-2 text-right">{item.quantity} {item.unit}</td>
                    <td className="p-2 text-center">
                      <span className={`font-medium ${getGerminationColor(item.germinationRate)}`}>
                        {item.germinationRate}%
                      </span>
                    </td>
                    <td className="p-2">{item.location}</td>
                    <td className="p-2">{item.expiryDate}</td>
                    <td className="p-2 text-center">
                      <Badge className={getStatusColor(item.status)}>{item.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
