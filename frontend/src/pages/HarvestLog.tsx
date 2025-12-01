import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Wheat, Search, Calendar, Scale, Package, TrendingUp, Download } from 'lucide-react'

interface HarvestRecord {
  id: string
  entry: string
  plot: string
  harvestDate: string
  freshWeight: number
  dryWeight: number
  moisture: number
  grainYield: number
  quality: 'A' | 'B' | 'C'
}

export function HarvestLog() {
  const [searchQuery, setSearchQuery] = useState('')

  const records: HarvestRecord[] = [
    { id: '1', entry: 'BIJ-R-001', plot: 'A-001', harvestDate: '2025-11-15', freshWeight: 12.5, dryWeight: 10.2, moisture: 14.2, grainYield: 8.5, quality: 'A' },
    { id: '2', entry: 'BIJ-R-002', plot: 'A-002', harvestDate: '2025-11-15', freshWeight: 11.8, dryWeight: 9.6, moisture: 14.8, grainYield: 7.9, quality: 'A' },
    { id: '3', entry: 'BIJ-R-003', plot: 'A-003', harvestDate: '2025-11-16', freshWeight: 10.2, dryWeight: 8.1, moisture: 15.5, grainYield: 6.8, quality: 'B' },
    { id: '4', entry: 'BIJ-R-004', plot: 'A-004', harvestDate: '2025-11-16', freshWeight: 13.1, dryWeight: 10.8, moisture: 13.9, grainYield: 9.1, quality: 'A' },
  ]

  const stats = {
    total: records.length,
    avgYield: (records.reduce((s, r) => s + r.grainYield, 0) / records.length).toFixed(1),
    totalWeight: records.reduce((s, r) => s + r.dryWeight, 0).toFixed(1),
    gradeA: records.filter(r => r.quality === 'A').length
  }

  const getQualityColor = (quality: string) => {
    const colors: Record<string, string> = { A: 'bg-green-100 text-green-800', B: 'bg-yellow-100 text-yellow-800', C: 'bg-red-100 text-red-800' }
    return colors[quality] || 'bg-gray-100 text-gray-800'
  }

  const filteredRecords = records.filter(r => 
    r.entry.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.plot.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Harvest Log</h1>
          <p className="text-muted-foreground">Record and track harvest data</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
          <Button><Wheat className="mr-2 h-4 w-4" />Record Harvest</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Package className="h-8 w-8 text-orange-500" /><div><p className="text-2xl font-bold">{stats.total}</p><p className="text-xs text-muted-foreground">Plots Harvested</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><TrendingUp className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{stats.avgYield} t/ha</p><p className="text-xs text-muted-foreground">Avg Yield</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Scale className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{stats.totalWeight} kg</p><p className="text-xs text-muted-foreground">Total Weight</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Wheat className="h-8 w-8 text-yellow-500" /><div><p className="text-2xl font-bold">{stats.gradeA}</p><p className="text-xs text-muted-foreground">Grade A</p></div></div></CardContent></Card>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search records..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle>Harvest Records</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-3 text-left">Entry</th>
                  <th className="p-3 text-left">Plot</th>
                  <th className="p-3 text-left">Date</th>
                  <th className="p-3 text-right">Fresh (kg)</th>
                  <th className="p-3 text-right">Dry (kg)</th>
                  <th className="p-3 text-right">Moisture %</th>
                  <th className="p-3 text-right">Yield (t/ha)</th>
                  <th className="p-3 text-center">Quality</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record) => (
                  <tr key={record.id} className="border-b hover:bg-accent">
                    <td className="p-3 font-medium">{record.entry}</td>
                    <td className="p-3">{record.plot}</td>
                    <td className="p-3">{record.harvestDate}</td>
                    <td className="p-3 text-right">{record.freshWeight}</td>
                    <td className="p-3 text-right">{record.dryWeight}</td>
                    <td className="p-3 text-right">{record.moisture}</td>
                    <td className="p-3 text-right font-medium">{record.grainYield}</td>
                    <td className="p-3 text-center"><Badge className={getQualityColor(record.quality)}>{record.quality}</Badge></td>
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
