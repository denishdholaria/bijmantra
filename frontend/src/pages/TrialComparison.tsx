import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  TrendingUp, TrendingDown,
  Download
} from 'lucide-react'

interface TrialData {
  id: string
  name: string
  location: string
  year: number
  entries: number
  avgYield: number
  topEntry: string
  topYield: number
}

export function TrialComparison() {
  const [trial1, setTrial1] = useState('')
  const [trial2, setTrial2] = useState('')

  const trials: TrialData[] = [
    { id: '1', name: 'Rice Yield Trial 2024', location: 'Station A', year: 2024, entries: 150, avgYield: 6.8, topEntry: 'BIJ-R-001', topYield: 8.2 },
    { id: '2', name: 'Rice Yield Trial 2025', location: 'Station A', year: 2025, entries: 175, avgYield: 7.2, topEntry: 'BIJ-R-015', topYield: 8.9 },
    { id: '3', name: 'Wheat Multi-Location 2024', location: 'Multiple', year: 2024, entries: 80, avgYield: 5.5, topEntry: 'BIJ-W-003', topYield: 6.8 },
    { id: '4', name: 'Drought Screening 2025', location: 'Station B', year: 2025, entries: 200, avgYield: 4.2, topEntry: 'BIJ-R-042', topYield: 5.8 },
  ]

  const selectedTrial1 = trials.find(t => t.id === trial1)
  const selectedTrial2 = trials.find(t => t.id === trial2)

  const comparisonMetrics = selectedTrial1 && selectedTrial2 ? [
    { metric: 'Entries', val1: selectedTrial1.entries, val2: selectedTrial2.entries, unit: '' },
    { metric: 'Avg Yield', val1: selectedTrial1.avgYield, val2: selectedTrial2.avgYield, unit: 't/ha' },
    { metric: 'Top Yield', val1: selectedTrial1.topYield, val2: selectedTrial2.topYield, unit: 't/ha' },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Trial Comparison</h1>
          <p className="text-muted-foreground">Compare performance across trials</p>
        </div>
        <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Trial 1</CardTitle></CardHeader>
          <CardContent>
            <Select value={trial1} onValueChange={setTrial1}>
              <SelectTrigger><SelectValue placeholder="Select trial" /></SelectTrigger>
              <SelectContent>
                {trials.map(t => (<SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>))}
              </SelectContent>
            </Select>
            {selectedTrial1 && (
              <div className="mt-4 space-y-2 text-sm">
                <p><span className="text-muted-foreground">Location:</span> {selectedTrial1.location}</p>
                <p><span className="text-muted-foreground">Year:</span> {selectedTrial1.year}</p>
                <p><span className="text-muted-foreground">Entries:</span> {selectedTrial1.entries}</p>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Trial 2</CardTitle></CardHeader>
          <CardContent>
            <Select value={trial2} onValueChange={setTrial2}>
              <SelectTrigger><SelectValue placeholder="Select trial" /></SelectTrigger>
              <SelectContent>
                {trials.filter(t => t.id !== trial1).map(t => (<SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>))}
              </SelectContent>
            </Select>
            {selectedTrial2 && (
              <div className="mt-4 space-y-2 text-sm">
                <p><span className="text-muted-foreground">Location:</span> {selectedTrial2.location}</p>
                <p><span className="text-muted-foreground">Year:</span> {selectedTrial2.year}</p>
                <p><span className="text-muted-foreground">Entries:</span> {selectedTrial2.entries}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {comparisonMetrics.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Comparison Results</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-4">
              {comparisonMetrics.map((m) => {
                const diff = m.val2 - m.val1
                const pctChange = ((diff / m.val1) * 100).toFixed(1)
                return (
                  <div key={m.metric} className="flex items-center justify-between p-4 border rounded-lg">
                    <span className="font-medium">{m.metric}</span>
                    <div className="flex items-center gap-8">
                      <span>{m.val1} {m.unit}</span>
                      <div className={`flex items-center gap-1 ${diff >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {diff >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                        {diff >= 0 ? '+' : ''}{pctChange}%
                      </div>
                      <span>{m.val2} {m.unit}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
