/**
 * Phenology Tracker Page
 * Track plant growth stages and development
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface PhenologyRecord {
  id: string
  germplasm: string
  plot: string
  currentStage: string
  stageCode: number
  daysFromSowing: number
  expectedMaturity: number
  observations: { stage: string; date: string; notes: string }[]
}

const growthStages = [
  { code: 0, name: 'Germination', color: 'bg-yellow-500' },
  { code: 10, name: 'Seedling', color: 'bg-lime-500' },
  { code: 20, name: 'Tillering', color: 'bg-green-500' },
  { code: 30, name: 'Stem Elongation', color: 'bg-emerald-500' },
  { code: 40, name: 'Booting', color: 'bg-teal-500' },
  { code: 50, name: 'Heading', color: 'bg-cyan-500' },
  { code: 60, name: 'Flowering', color: 'bg-blue-500' },
  { code: 70, name: 'Grain Fill', color: 'bg-indigo-500' },
  { code: 80, name: 'Ripening', color: 'bg-purple-500' },
  { code: 90, name: 'Maturity', color: 'bg-orange-500' },
]

const sampleRecords: PhenologyRecord[] = [
  { id: 'P001', germplasm: 'Elite Variety 2024', plot: 'A-01', currentStage: 'Heading', stageCode: 50, daysFromSowing: 75, expectedMaturity: 120, observations: [{ stage: 'Germination', date: '2024-09-20', notes: 'Good emergence' }] },
  { id: 'P002', germplasm: 'High Yield Line A', plot: 'A-02', currentStage: 'Flowering', stageCode: 60, daysFromSowing: 80, expectedMaturity: 115, observations: [] },
  { id: 'P003', germplasm: 'Disease Resistant B', plot: 'A-03', currentStage: 'Booting', stageCode: 40, daysFromSowing: 70, expectedMaturity: 125, observations: [] },
  { id: 'P004', germplasm: 'Early Maturing C', plot: 'B-01', currentStage: 'Grain Fill', stageCode: 70, daysFromSowing: 85, expectedMaturity: 105, observations: [] },
  { id: 'P005', germplasm: 'Late Variety D', plot: 'B-02', currentStage: 'Tillering', stageCode: 20, daysFromSowing: 45, expectedMaturity: 140, observations: [] },
]

export function PhenologyTracker() {
  const [records] = useState<PhenologyRecord[]>(sampleRecords)
  const [selectedStudy, setSelectedStudy] = useState('study-2024')

  const getStageColor = (stageCode: number) => {
    const stage = growthStages.find(s => s.code === stageCode)
    return stage?.color || 'bg-gray-500'
  }

  const getProgress = (stageCode: number) => (stageCode / 90) * 100

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Phenology Tracker</h1>
          <p className="text-muted-foreground mt-1">Track plant growth stages</p>
        </div>
        <Select value={selectedStudy} onValueChange={setSelectedStudy}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="study-2024">Study 2024</SelectItem>
            <SelectItem value="study-2023">Study 2023</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Growth Stage Legend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Growth Stages (Zadoks Scale)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {growthStages.map((stage) => (
              <div key={stage.code} className="flex items-center gap-1">
                <div className={`w-3 h-3 rounded-full ${stage.color}`}></div>
                <span className="text-xs">{stage.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Records */}
      <div className="space-y-4">
        {records.map((record) => (
          <Card key={record.id}>
            <CardContent className="pt-4">
              <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium">{record.germplasm}</span>
                    <Badge variant="outline">{record.plot}</Badge>
                    <Badge className={getStageColor(record.stageCode)}>{record.currentStage}</Badge>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="relative">
                    <Progress value={getProgress(record.stageCode)} className="h-6" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs font-medium text-white drop-shadow">
                        {record.stageCode}% - {record.currentStage}
                      </span>
                    </div>
                  </div>

                  {/* Stage Markers */}
                  <div className="flex justify-between mt-1">
                    {growthStages.filter((_, i) => i % 2 === 0).map((stage) => (
                      <div
                        key={stage.code}
                        className={`w-2 h-2 rounded-full ${record.stageCode >= stage.code ? stage.color : 'bg-gray-200'}`}
                        title={stage.name}
                      />
                    ))}
                  </div>
                </div>

                <div className="flex gap-4 text-sm">
                  <div className="text-center">
                    <p className="font-bold text-blue-600">{record.daysFromSowing}</p>
                    <p className="text-xs text-muted-foreground">Days</p>
                  </div>
                  <div className="text-center">
                    <p className="font-bold text-green-600">{record.expectedMaturity}</p>
                    <p className="text-xs text-muted-foreground">Expected</p>
                  </div>
                  <div className="text-center">
                    <p className="font-bold text-orange-600">{record.expectedMaturity - record.daysFromSowing}</p>
                    <p className="text-xs text-muted-foreground">Remaining</p>
                  </div>
                </div>

                <Button size="sm" variant="outline">📝 Record</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
