import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sprout, TrendingUp, Calendar, Ruler, Leaf, Sun } from 'lucide-react'

interface GrowthRecord {
  id: string
  entry: string
  stage: string
  daysAfterPlanting: number
  height: number
  tillers: number
  healthScore: number
  lastObservation: string
}

export function GrowthTracker() {
  const [selectedTrial, setSelectedTrial] = useState('all')

  const records: GrowthRecord[] = [
    { id: '1', entry: 'BIJ-R-001', stage: 'Tillering', daysAfterPlanting: 45, height: 52, tillers: 12, healthScore: 92, lastObservation: '2 days ago' },
    { id: '2', entry: 'BIJ-R-002', stage: 'Booting', daysAfterPlanting: 65, height: 78, tillers: 15, healthScore: 88, lastObservation: '1 day ago' },
    { id: '3', entry: 'BIJ-R-003', stage: 'Vegetative', daysAfterPlanting: 30, height: 35, tillers: 8, healthScore: 95, lastObservation: '3 days ago' },
    { id: '4', entry: 'BIJ-R-004', stage: 'Heading', daysAfterPlanting: 80, height: 95, tillers: 14, healthScore: 85, lastObservation: '1 day ago' },
  ]

  const getStageColor = (stage: string) => {
    const colors: Record<string, string> = { Vegetative: 'bg-green-100 text-green-800', Tillering: 'bg-blue-100 text-blue-800', Booting: 'bg-yellow-100 text-yellow-800', Heading: 'bg-orange-100 text-orange-800', Maturity: 'bg-purple-100 text-purple-800' }
    return colors[stage] || 'bg-gray-100 text-gray-800'
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Growth Tracker</h1>
          <p className="text-muted-foreground">Monitor plant growth and development</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrial} onValueChange={setSelectedTrial}>
            <SelectTrigger className="w-[200px]"><SelectValue placeholder="Select trial" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Trials</SelectItem>
              <SelectItem value="rice-2025">Rice Yield Trial 2025</SelectItem>
              <SelectItem value="drought">Drought Screening</SelectItem>
            </SelectContent>
          </Select>
          <Button><Sprout className="mr-2 h-4 w-4" />Record Growth</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Sprout className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{records.length}</p><p className="text-xs text-muted-foreground">Entries Tracked</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Ruler className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.height, 0) / records.length)} cm</p><p className="text-xs text-muted-foreground">Avg Height</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Leaf className="h-8 w-8 text-green-500" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.tillers, 0) / records.length)}</p><p className="text-xs text-muted-foreground">Avg Tillers</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Sun className="h-8 w-8 text-yellow-500" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.healthScore, 0) / records.length)}%</p><p className="text-xs text-muted-foreground">Avg Health</p></div></div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Growth Records</CardTitle><CardDescription>Track development stages and measurements</CardDescription></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {records.map((record) => (
              <div key={record.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <Sprout className="h-8 w-8 text-green-500" />
                  <div>
                    <p className="font-medium">{record.entry}</p>
                    <p className="text-sm text-muted-foreground">{record.daysAfterPlanting} DAP</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center"><p className="text-lg font-medium">{record.height} cm</p><p className="text-xs text-muted-foreground">Height</p></div>
                  <div className="text-center"><p className="text-lg font-medium">{record.tillers}</p><p className="text-xs text-muted-foreground">Tillers</p></div>
                  <div className="text-center"><p className={`text-lg font-medium ${getHealthColor(record.healthScore)}`}>{record.healthScore}%</p><p className="text-xs text-muted-foreground">Health</p></div>
                  <Badge className={getStageColor(record.stage)}>{record.stage}</Badge>
                  <Button variant="outline" size="sm">Update</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
