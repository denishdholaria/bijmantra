/**
 * Soil Analysis Page
 * Track and analyze soil test results
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

interface SoilSample {
  id: string
  location: string
  field: string
  sampleDate: string
  pH: number
  organicMatter: number
  nitrogen: number
  phosphorus: number
  potassium: number
  status: 'pending' | 'analyzed' | 'reviewed'
}

const sampleData: SoilSample[] = [
  { id: 'SS001', location: 'Field A', field: 'Block 1', sampleDate: '2024-11-15', pH: 6.5, organicMatter: 3.2, nitrogen: 45, phosphorus: 28, potassium: 180, status: 'analyzed' },
  { id: 'SS002', location: 'Field A', field: 'Block 2', sampleDate: '2024-11-15', pH: 6.8, organicMatter: 2.8, nitrogen: 38, phosphorus: 32, potassium: 165, status: 'analyzed' },
  { id: 'SS003', location: 'Field B', field: 'Block 1', sampleDate: '2024-11-20', pH: 5.9, organicMatter: 4.1, nitrogen: 52, phosphorus: 18, potassium: 145, status: 'reviewed' },
  { id: 'SS004', location: 'Field C', field: 'Block 1', sampleDate: '2024-11-25', pH: 7.2, organicMatter: 2.5, nitrogen: 35, phosphorus: 42, potassium: 210, status: 'pending' },
]

const optimalRanges = {
  pH: { min: 6.0, max: 7.0, unit: '' },
  organicMatter: { min: 3.0, max: 5.0, unit: '%' },
  nitrogen: { min: 40, max: 60, unit: 'ppm' },
  phosphorus: { min: 25, max: 50, unit: 'ppm' },
  potassium: { min: 150, max: 250, unit: 'ppm' },
}

export function SoilAnalysis() {
  const [samples] = useState<SoilSample[]>(sampleData)

  const getValueStatus = (value: number, param: keyof typeof optimalRanges) => {
    const range = optimalRanges[param]
    if (value < range.min) return { status: 'low', color: 'text-red-600' }
    if (value > range.max) return { status: 'high', color: 'text-orange-600' }
    return { status: 'optimal', color: 'text-green-600' }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      case 'analyzed': return 'bg-blue-100 text-blue-700'
      case 'reviewed': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Soil Analysis</h1>
          <p className="text-muted-foreground mt-1">Track soil test results</p>
        </div>
        <Button>➕ New Sample</Button>
      </div>

      {/* Optimal Ranges Reference */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Optimal Ranges</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div><span className="font-medium">pH:</span> 6.0-7.0</div>
            <div><span className="font-medium">OM:</span> 3-5%</div>
            <div><span className="font-medium">N:</span> 40-60 ppm</div>
            <div><span className="font-medium">P:</span> 25-50 ppm</div>
            <div><span className="font-medium">K:</span> 150-250 ppm</div>
          </div>
        </CardContent>
      </Card>

      {/* Samples */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {samples.map((sample) => (
          <Card key={sample.id}>
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-base">{sample.location} - {sample.field}</CardTitle>
                  <CardDescription>{sample.id} • {sample.sampleDate}</CardDescription>
                </div>
                <Badge className={getStatusColor(sample.status)}>{sample.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 gap-2">
                {(['pH', 'organicMatter', 'nitrogen', 'phosphorus', 'potassium'] as const).map((param) => {
                  const value = sample[param]
                  const { status, color } = getValueStatus(value, param)
                  const range = optimalRanges[param]
                  const labels = { pH: 'pH', organicMatter: 'OM', nitrogen: 'N', phosphorus: 'P', potassium: 'K' }
                  
                  return (
                    <div key={param} className="text-center p-2 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">{labels[param]}</p>
                      <p className={`text-lg font-bold ${color}`}>{value}</p>
                      <p className="text-xs text-muted-foreground">{range.unit}</p>
                      <Badge variant="outline" className={`text-xs mt-1 ${color}`}>{status}</Badge>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
