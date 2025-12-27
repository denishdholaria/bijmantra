/**
 * Data Collection Interface
 * Mobile-friendly phenotyping data entry
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'

interface ObservationEntry {
  observationUnitDbId: string
  observationVariableDbId: string
  value: string
  observationTimeStamp: string
}

export function DataCollect() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selectedStudy, setSelectedStudy] = useState(searchParams.get('studyDbId') || '')
  const [selectedVariable, setSelectedVariable] = useState('')
  const [entries, setEntries] = useState<ObservationEntry[]>([])
  const [currentValue, setCurrentValue] = useState('')
  const [currentUnit, setCurrentUnit] = useState('')

  const { data: studiesData } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 100),
  })

  const { data: variablesData } = useQuery({
    queryKey: ['variables'],
    queryFn: () => apiClient.getObservationVariables(0, 100),
  })

  const { data: unitsData } = useQuery({
    queryKey: ['observationUnits', selectedStudy],
    queryFn: () => apiClient.getObservationUnits(selectedStudy, 0, 100),
    enabled: !!selectedStudy,
  })

  const studies = studiesData?.result?.data || []
  const variables = variablesData?.result?.data || []
  const units = unitsData?.result?.data || []

  const submitMutation = useMutation({
    mutationFn: (data: ObservationEntry[]) => apiClient.createObservations(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['observations'] })
      toast.success(`${entries.length} observations saved!`)
      setEntries([])
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to save observations')
    },
  })

  const addEntry = () => {
    if (!currentUnit || !selectedVariable || !currentValue) {
      toast.error('Please fill all fields')
      return
    }
    
    const newEntry: ObservationEntry = {
      observationUnitDbId: currentUnit,
      observationVariableDbId: selectedVariable,
      value: currentValue,
      observationTimeStamp: new Date().toISOString(),
    }
    
    setEntries([...entries, newEntry])
    setCurrentValue('')
    toast.success('Entry added')
  }

  const removeEntry = (index: number) => {
    setEntries(entries.filter((_, i) => i !== index))
  }

  const submitAll = () => {
    if (entries.length === 0) {
      toast.error('No entries to submit')
      return
    }
    submitMutation.mutate(entries)
  }

  const selectedVariableData = variables.find((v: any) => v.observationVariableDbId === selectedVariable)

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Data Collection</h1>
          <p className="text-muted-foreground mt-1">Record phenotypic observations</p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/observations">← Back to Observations</Link>
        </Button>
      </div>

      {/* Setup */}
      <Card>
        <CardHeader>
          <CardTitle>1. Select Study & Variable</CardTitle>
          <CardDescription>Choose what you're measuring</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Study</Label>
              <Select value={selectedStudy} onValueChange={setSelectedStudy}>
                <SelectTrigger>
                  <SelectValue placeholder="Select study..." />
                </SelectTrigger>
                <SelectContent>
                  {studies.map((s: any) => (
                    <SelectItem key={s.studyDbId} value={s.studyDbId}>{s.studyName}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Observation Variable</Label>
              <Select value={selectedVariable} onValueChange={setSelectedVariable}>
                <SelectTrigger>
                  <SelectValue placeholder="Select variable..." />
                </SelectTrigger>
                <SelectContent>
                  {variables.map((v: any) => (
                    <SelectItem key={v.observationVariableDbId} value={v.observationVariableDbId}>
                      {v.observationVariableName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {selectedVariableData && (
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">{selectedVariableData.trait?.traitName || 'Trait'}</Badge>
                <Badge variant="outline">{selectedVariableData.scale?.dataType || 'Numerical'}</Badge>
                {selectedVariableData.scale?.validValues && (
                  <Badge variant="outline">
                    Range: {selectedVariableData.scale.validValues.min} - {selectedVariableData.scale.validValues.max}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Data Entry */}
      {selectedStudy && selectedVariable && (
        <Card>
          <CardHeader>
            <CardTitle>2. Record Observations</CardTitle>
            <CardDescription>Enter values for each observation unit</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Observation Unit</Label>
                <Select value={currentUnit} onValueChange={setCurrentUnit}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select unit..." />
                  </SelectTrigger>
                  <SelectContent>
                    {units.length > 0 ? (
                      units.map((u: any) => (
                        <SelectItem key={u.observationUnitDbId} value={u.observationUnitDbId}>
                          {u.observationUnitName || u.observationUnitDbId}
                        </SelectItem>
                      ))
                    ) : (
                      <SelectItem value="manual" disabled>No units found - enter manually</SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {units.length === 0 && (
                  <Input 
                    placeholder="Enter unit ID manually" 
                    value={currentUnit}
                    onChange={(e) => setCurrentUnit(e.target.value)}
                  />
                )}
              </div>
              <div className="space-y-2">
                <Label>Value</Label>
                <Input
                  type={selectedVariableData?.scale?.dataType === 'Numerical' ? 'number' : 'text'}
                  step="any"
                  value={currentValue}
                  onChange={(e) => setCurrentValue(e.target.value)}
                  placeholder="Enter value..."
                  onKeyDown={(e) => e.key === 'Enter' && addEntry()}
                />
              </div>
              <div className="space-y-2">
                <Label>&nbsp;</Label>
                <Button onClick={addEntry} className="w-full">
                  ➕ Add Entry
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pending Entries */}
      {entries.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>3. Review & Submit</CardTitle>
            <CardDescription>{entries.length} entries pending</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 mb-4 max-h-64 overflow-y-auto">
              {entries.map((entry, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-sm">{entry.observationUnitDbId}</span>
                    <Badge>{entry.value}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(entry.observationTimeStamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeEntry(index)}>
                    ❌
                  </Button>
                </div>
              ))}
            </div>
            <div className="flex gap-4">
              <Button onClick={submitAll} disabled={submitMutation.isPending} className="flex-1">
                {submitMutation.isPending ? '💾 Saving...' : `💾 Save ${entries.length} Observations`}
              </Button>
              <Button variant="outline" onClick={() => setEntries([])}>
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Tips */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">💡</span>
            <div className="text-sm text-muted-foreground">
              <p className="font-medium text-foreground mb-1">Tips for efficient data collection:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Press Enter after typing a value to quickly add the entry</li>
                <li>Entries are saved locally until you submit</li>
                <li>Review all entries before submitting</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
