/**
 * Breeding Pipeline Page
 * Track germplasm through breeding stages
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface PipelineEntry {
  id: string
  name: string
  stage: string
  year: number
  status: 'active' | 'advanced' | 'dropped' | 'released'
  traits: { name: string; value: number; target: number }[]
}

const stages = [
  { id: 'F1', name: 'F1 Generation', color: 'bg-blue-500' },
  { id: 'F2', name: 'F2 Segregating', color: 'bg-indigo-500' },
  { id: 'F3', name: 'F3 Selection', color: 'bg-purple-500' },
  { id: 'F4', name: 'F4 Fixation', color: 'bg-pink-500' },
  { id: 'F5', name: 'F5 Preliminary', color: 'bg-red-500' },
  { id: 'AYT', name: 'Advanced Yield Trial', color: 'bg-orange-500' },
  { id: 'MLT', name: 'Multi-Location Trial', color: 'bg-amber-500' },
  { id: 'REL', name: 'Release Candidate', color: 'bg-green-500' },
]

const sampleData: PipelineEntry[] = [
  { id: 'L001', name: 'Elite Line 001', stage: 'MLT', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 4.8, target: 5.0 }, { name: 'Disease', value: 8, target: 7 }] },
  { id: 'L002', name: 'Elite Line 002', stage: 'AYT', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 4.5, target: 5.0 }, { name: 'Disease', value: 7, target: 7 }] },
  { id: 'L003', name: 'Elite Line 003', stage: 'AYT', year: 2024, status: 'advanced', traits: [{ name: 'Yield', value: 5.2, target: 5.0 }, { name: 'Disease', value: 9, target: 7 }] },
  { id: 'L004', name: 'Promising Line 004', stage: 'F5', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 4.2, target: 5.0 }, { name: 'Disease', value: 6, target: 7 }] },
  { id: 'L005', name: 'Promising Line 005', stage: 'F5', year: 2024, status: 'dropped', traits: [{ name: 'Yield', value: 3.5, target: 5.0 }, { name: 'Disease', value: 4, target: 7 }] },
  { id: 'L006', name: 'New Cross 006', stage: 'F4', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 4.0, target: 5.0 }, { name: 'Disease', value: 7, target: 7 }] },
  { id: 'L007', name: 'New Cross 007', stage: 'F3', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 3.8, target: 5.0 }, { name: 'Disease', value: 8, target: 7 }] },
  { id: 'L008', name: 'New Cross 008', stage: 'F2', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 0, target: 5.0 }, { name: 'Disease', value: 0, target: 7 }] },
  { id: 'L009', name: 'Fresh Cross 009', stage: 'F1', year: 2024, status: 'active', traits: [{ name: 'Yield', value: 0, target: 5.0 }, { name: 'Disease', value: 0, target: 7 }] },
  { id: 'REL-2023', name: 'Released Variety 2023', stage: 'REL', year: 2023, status: 'released', traits: [{ name: 'Yield', value: 5.5, target: 5.0 }, { name: 'Disease', value: 9, target: 7 }] },
]

export function BreedingPipeline() {
  const [selectedYear, setSelectedYear] = useState('2024')
  const [viewMode, setViewMode] = useState<'kanban' | 'funnel'>('kanban')

  const filteredData = sampleData.filter(d => d.year.toString() === selectedYear || d.status === 'released')

  const getEntriesByStage = (stageId: string) => filteredData.filter(d => d.stage === stageId)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-blue-100 text-blue-700'
      case 'advanced': return 'bg-green-100 text-green-700'
      case 'dropped': return 'bg-red-100 text-red-700'
      case 'released': return 'bg-purple-100 text-purple-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const totalActive = filteredData.filter(d => d.status === 'active').length
  const totalAdvanced = filteredData.filter(d => d.status === 'advanced').length
  const totalDropped = filteredData.filter(d => d.status === 'dropped').length

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Breeding Pipeline</h1>
          <p className="text-muted-foreground mt-1">Track germplasm through breeding stages</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2023">2023</SelectItem>
              <SelectItem value="2022">2022</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={viewMode === 'kanban' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('kanban')}
          >
            📋 Kanban
          </Button>
          <Button
            variant={viewMode === 'funnel' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('funnel')}
          >
            📊 Funnel
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{totalActive}</p>
              <p className="text-sm text-muted-foreground">Active Lines</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{totalAdvanced}</p>
              <p className="text-sm text-muted-foreground">Advanced</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{totalDropped}</p>
              <p className="text-sm text-muted-foreground">Dropped</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-600">{stages.length}</p>
              <p className="text-sm text-muted-foreground">Pipeline Stages</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {viewMode === 'kanban' ? (
        /* Kanban View */
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max">
            {stages.map((stage) => {
              const entries = getEntriesByStage(stage.id)
              return (
                <div key={stage.id} className="w-64 flex-shrink-0">
                  <div className={`${stage.color} text-white px-3 py-2 rounded-t-lg`}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{stage.name}</span>
                      <Badge variant="secondary" className="bg-white/20 text-white">
                        {entries.length}
                      </Badge>
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-b-lg p-2 min-h-[200px] space-y-2">
                    {entries.map((entry) => (
                      <Card key={entry.id} className="cursor-pointer hover:shadow-md transition-shadow">
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium text-sm">{entry.name}</p>
                              <p className="text-xs text-muted-foreground">{entry.id}</p>
                            </div>
                            <Badge className={getStatusColor(entry.status)} variant="secondary">
                              {entry.status}
                            </Badge>
                          </div>
                          {entry.traits[0]?.value > 0 && (
                            <div className="mt-2">
                              <div className="flex justify-between text-xs mb-1">
                                <span>Yield</span>
                                <span>{entry.traits[0].value}/{entry.traits[0].target}</span>
                              </div>
                              <Progress 
                                value={(entry.traits[0].value / entry.traits[0].target) * 100} 
                                className="h-1"
                              />
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                    {entries.length === 0 && (
                      <p className="text-center text-sm text-muted-foreground py-8">No entries</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        /* Funnel View */
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Funnel</CardTitle>
            <CardDescription>Germplasm distribution across stages</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stages.map((stage, index) => {
                const entries = getEntriesByStage(stage.id)
                const maxWidth = 100
                const width = Math.max(20, maxWidth - (index * 10))
                return (
                  <div key={stage.id} className="flex items-center gap-4">
                    <div className="w-32 text-sm font-medium">{stage.name}</div>
                    <div className="flex-1">
                      <div 
                        className={`${stage.color} h-10 rounded flex items-center justify-center text-white font-medium transition-all`}
                        style={{ width: `${width}%` }}
                      >
                        {entries.length} lines
                      </div>
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
