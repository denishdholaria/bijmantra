import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sprout, TrendingUp, Calendar, Ruler, Leaf, Sun } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { GrowthPredictionResult } from '@/lib/api/calculators'

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
    const colors: Record<string, string> = {
      Vegetative: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      Tillering: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      Booting: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      Heading: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      Maturity: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
    }
    return colors[stage] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600 dark:text-green-400'
    if (score >= 80) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const { data: predictions } = useQuery({
    queryKey: ['growth-predictions'],
    queryFn: async () => {
       const results = await Promise.all(records.map(async (r) => {
           // Simulate planting date based on DAP
           const plantingDate = new Date();
           plantingDate.setDate(plantingDate.getDate() - r.daysAfterPlanting);
           const pDateStr = plantingDate.toISOString().split('T')[0];

           // Simulate GDD (approx 12-15 per day)
           const currentGDD = r.daysAfterPlanting * 14;

           try {
             const pred = await apiClient.calculatorService.predictGrowth({
                 crop: 'Rice',
                 planting_date: pDateStr,
                 current_gdd: currentGDD
             });
             return { id: r.id, prediction: pred };
           } catch (e) {
             return { id: r.id, prediction: null };
           }
       }));
       return results.reduce((acc, curr) => ({...acc, [curr.id]: curr.prediction}), {} as Record<string, GrowthPredictionResult | null>);
    }
  })

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

      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Sprout className="h-8 w-8 text-green-500 dark:text-green-400" /><div><p className="text-2xl font-bold">{records.length}</p><p className="text-xs text-muted-foreground">Entries Tracked</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Ruler className="h-8 w-8 text-blue-500 dark:text-blue-400" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.height, 0) / records.length)} cm</p><p className="text-xs text-muted-foreground">Avg Height</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Leaf className="h-8 w-8 text-green-500 dark:text-green-400" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.tillers, 0) / records.length)}</p><p className="text-xs text-muted-foreground">Avg Tillers</p></div></div></CardContent></Card>
        <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Sun className="h-8 w-8 text-yellow-500 dark:text-yellow-400" /><div><p className="text-2xl font-bold">{Math.round(records.reduce((s, r) => s + r.healthScore, 0) / records.length)}%</p><p className="text-xs text-muted-foreground">Avg Health</p></div></div></CardContent></Card>
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
                  <div className="flex flex-col items-center">
                    <Badge className={getStageColor(record.stage)}>{record.stage}</Badge>
                    {predictions && predictions[record.id] && (
                      <span className="text-[10px] text-muted-foreground mt-1">
                        Next: {predictions[record.id]?.next_stage || 'Maturity'}
                      </span>
                    )}
                  </div>
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
