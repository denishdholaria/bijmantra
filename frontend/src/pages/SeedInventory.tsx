/**
 * Seed Inventory Page
 * Track seed stock levels and movements
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'

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

const sampleStock: SeedStock[] = [
  { id: 'S001', germplasm: 'Elite Variety 2024', lotNumber: 'LOT-2024-001', quantity: 5000, unit: 'g', location: 'Cold Storage A', germinationRate: 95, harvestDate: '2024-06-15', expiryDate: '2026-06-15', status: 'available' },
  { id: 'S002', germplasm: 'High Yield Line A', lotNumber: 'LOT-2024-002', quantity: 2500, unit: 'g', location: 'Cold Storage A', germinationRate: 92, harvestDate: '2024-06-20', expiryDate: '2026-06-20', status: 'available' },
  { id: 'S003', germplasm: 'Disease Resistant B', lotNumber: 'LOT-2024-003', quantity: 500, unit: 'g', location: 'Cold Storage B', germinationRate: 88, harvestDate: '2024-05-10', expiryDate: '2026-05-10', status: 'low' },
  { id: 'S004', germplasm: 'Drought Tolerant C', lotNumber: 'LOT-2023-015', quantity: 100, unit: 'g', location: 'Cold Storage B', germinationRate: 75, harvestDate: '2023-06-01', expiryDate: '2025-06-01', status: 'critical' },
  { id: 'S005', germplasm: 'Old Variety X', lotNumber: 'LOT-2022-008', quantity: 200, unit: 'g', location: 'Archive', germinationRate: 45, harvestDate: '2022-06-15', expiryDate: '2024-06-15', status: 'expired' },
  { id: 'S006', germplasm: 'Hybrid Parent A', lotNumber: 'LOT-2024-010', quantity: 8000, unit: 'g', location: 'Cold Storage A', germinationRate: 98, harvestDate: '2024-07-01', expiryDate: '2026-07-01', status: 'available' },
]

export function SeedInventory() {
  const [stock, setStock] = useState<SeedStock[]>(sampleStock)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'available' | 'low' | 'critical' | 'expired'>('all')

  const filteredStock = stock.filter(s => {
    const matchesSearch = s.germplasm.toLowerCase().includes(search.toLowerCase()) ||
                          s.lotNumber.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'all' || s.status === filter
    return matchesSearch && matchesFilter
  })

  const stats = {
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
