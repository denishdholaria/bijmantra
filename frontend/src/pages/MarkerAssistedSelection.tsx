/**
 * Marker-Assisted Selection (MAS) Page
 * Tools for marker-based selection and foreground/background selection
 */
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

interface TargetMarker {
  id: string
  name: string
  chromosome: string
  position: number
  trait: string
  alleles: [string, string]
  favorableAllele: string
  effect: string
  validated: boolean
}

interface Candidate {
  id: string
  name: string
  markers: { [key: string]: string }
  foregroundScore: number
  backgroundScore: number
  totalScore: number
  selected: boolean
}

const targetMarkers: TargetMarker[] = [
  { id: 'm1', name: 'Sub1A', chromosome: '9', position: 6.2, trait: 'Submergence tolerance', alleles: ['A', 'G'], favorableAllele: 'A', effect: 'Major', validated: true },
  { id: 'm2', name: 'Xa21', chromosome: '11', position: 21.5, trait: 'Bacterial blight resistance', alleles: ['T', 'C'], favorableAllele: 'T', effect: 'Major', validated: true },
  { id: 'm3', name: 'Pi54', chromosome: '11', position: 24.8, trait: 'Blast resistance', alleles: ['G', 'A'], favorableAllele: 'G', effect: 'Major', validated: true },
  { id: 'm4', name: 'qDTY1.1', chromosome: '1', position: 38.4, trait: 'Drought tolerance', alleles: ['C', 'T'], favorableAllele: 'C', effect: 'Moderate', validated: true },
  { id: 'm5', name: 'Saltol', chromosome: '1', position: 10.8, trait: 'Salinity tolerance', alleles: ['A', 'G'], favorableAllele: 'A', effect: 'Major', validated: true },
  { id: 'm6', name: 'GW5', chromosome: '5', position: 5.4, trait: 'Grain width', alleles: ['T', 'A'], favorableAllele: 'T', effect: 'Moderate', validated: false },
]

const candidates: Candidate[] = [
  { id: 'c1', name: 'BC3F2-001', markers: { Sub1A: 'AA', Xa21: 'TT', Pi54: 'GG', 'qDTY1.1': 'CC', Saltol: 'AA', GW5: 'TT' }, foregroundScore: 100, backgroundScore: 92, totalScore: 96, selected: true },
  { id: 'c2', name: 'BC3F2-002', markers: { Sub1A: 'AA', Xa21: 'TT', Pi54: 'GA', 'qDTY1.1': 'CC', Saltol: 'AG', GW5: 'TT' }, foregroundScore: 83, backgroundScore: 88, totalScore: 86, selected: true },
  { id: 'c3', name: 'BC3F2-003', markers: { Sub1A: 'AA', Xa21: 'TC', Pi54: 'GG', 'qDTY1.1': 'CT', Saltol: 'AA', GW5: 'TA' }, foregroundScore: 75, backgroundScore: 95, totalScore: 85, selected: true },
  { id: 'c4', name: 'BC3F2-004', markers: { Sub1A: 'AG', Xa21: 'TT', Pi54: 'GG', 'qDTY1.1': 'CC', Saltol: 'AA', GW5: 'TT' }, foregroundScore: 92, backgroundScore: 78, totalScore: 85, selected: false },
  { id: 'c5', name: 'BC3F2-005', markers: { Sub1A: 'AA', Xa21: 'TT', Pi54: 'AA', 'qDTY1.1': 'CC', Saltol: 'AA', GW5: 'TT' }, foregroundScore: 83, backgroundScore: 82, totalScore: 83, selected: false },
  { id: 'c6', name: 'BC3F2-006', markers: { Sub1A: 'GG', Xa21: 'TT', Pi54: 'GG', 'qDTY1.1': 'TT', Saltol: 'GG', GW5: 'AA' }, foregroundScore: 33, backgroundScore: 90, totalScore: 62, selected: false },
]

export function MarkerAssistedSelection() {
  const [activeTab, setActiveTab] = useState('foreground')
  const [selectedMarkers, setSelectedMarkers] = useState<string[]>(['m1', 'm2', 'm3'])

  const getGenotypeColor = (marker: TargetMarker, genotype: string) => {
    const favorable = marker.favorableAllele
    if (genotype === favorable + favorable) return 'bg-green-100 text-green-700'
    if (genotype.includes(favorable)) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Marker-Assisted Selection</h1>
          <p className="text-muted-foreground mt-1">Foreground and background selection tools</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📥 Import Genotypes</Button>
          <Button>🎯 Run Selection</Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="foreground">Foreground Selection</TabsTrigger>
          <TabsTrigger value="background">Background Selection</TabsTrigger>
          <TabsTrigger value="combined">Combined Selection</TabsTrigger>
          <TabsTrigger value="markers">Target Markers</TabsTrigger>
        </TabsList>

        <TabsContent value="foreground" className="space-y-6 mt-4">
          {/* Target Marker Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Target Markers for Foreground Selection</CardTitle>
              <CardDescription>Select markers to screen for favorable alleles</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {targetMarkers.map((marker) => (
                  <div 
                    key={marker.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      selectedMarkers.includes(marker.id) ? 'border-primary bg-primary/5' : 'hover:border-muted-foreground'
                    }`}
                    onClick={() => {
                      setSelectedMarkers(prev => 
                        prev.includes(marker.id) 
                          ? prev.filter(m => m !== marker.id)
                          : [...prev, marker.id]
                      )
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-bold">{marker.name}</p>
                        <p className="text-xs text-muted-foreground">Chr {marker.chromosome}</p>
                      </div>
                      <Checkbox checked={selectedMarkers.includes(marker.id)} />
                    </div>
                    <p className="text-sm mt-1">{marker.trait}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant={marker.effect === 'Major' ? 'default' : 'secondary'} className="text-xs">
                        {marker.effect}
                      </Badge>
                      {marker.validated && (
                        <Badge className="bg-green-100 text-green-700 text-xs">✓ Validated</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Foreground Screening Results */}
          <Card>
            <CardHeader>
              <CardTitle>Foreground Screening Results</CardTitle>
              <CardDescription>Genotype calls for target markers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Candidate</th>
                      {targetMarkers.filter(m => selectedMarkers.includes(m.id)).map(m => (
                        <th key={m.id} className="text-center p-3">
                          <div>{m.name}</div>
                          <div className="text-xs font-normal text-muted-foreground">{m.favorableAllele}{m.favorableAllele}</div>
                        </th>
                      ))}
                      <th className="text-right p-3">Score</th>
                      <th className="text-center p-3">Select</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((cand) => (
                      <tr key={cand.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-medium">{cand.name}</td>
                        {targetMarkers.filter(m => selectedMarkers.includes(m.id)).map(marker => (
                          <td key={marker.id} className="p-3 text-center">
                            <Badge className={getGenotypeColor(marker, cand.markers[marker.name])}>
                              {cand.markers[marker.name]}
                            </Badge>
                          </td>
                        ))}
                        <td className={`p-3 text-right font-bold ${getScoreColor(cand.foregroundScore)}`}>
                          {cand.foregroundScore}%
                        </td>
                        <td className="p-3 text-center">
                          <Checkbox defaultChecked={cand.foregroundScore >= 80} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 flex gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-green-100 rounded" />
                  <span>Homozygous favorable</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-yellow-100 rounded" />
                  <span>Heterozygous</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 bg-red-100 rounded" />
                  <span>Unfavorable</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="background" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Background Recovery</CardTitle>
              <CardDescription>Recurrent parent genome recovery percentage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {candidates.map((cand) => (
                  <div key={cand.id} className="flex items-center gap-4">
                    <span className="w-32 font-medium">{cand.name}</span>
                    <div className="flex-1">
                      <Progress value={cand.backgroundScore} className="h-4" />
                    </div>
                    <span className={`w-16 text-right font-bold ${getScoreColor(cand.backgroundScore)}`}>
                      {cand.backgroundScore}%
                    </span>
                    <Badge variant={cand.backgroundScore >= 90 ? 'default' : 'secondary'}>
                      {cand.backgroundScore >= 95 ? 'Excellent' : cand.backgroundScore >= 90 ? 'Good' : cand.backgroundScore >= 80 ? 'Fair' : 'Low'}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Chromosome-wise Recovery */}
          <Card>
            <CardHeader>
              <CardTitle>Chromosome-wise Recovery</CardTitle>
              <CardDescription>Background recovery by chromosome for top candidate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-6 md:grid-cols-12 gap-2">
                {Array.from({ length: 12 }).map((_, i) => {
                  // Deterministic recovery based on top candidate's backgroundScore
                  // with chromosome-specific variation based on index
                  const topCandidate = candidates[0];
                  const baseRecovery = topCandidate?.backgroundScore || 90;
                  // Vary by chromosome: some lower (donor segments), most at base
                  const chromosomeVariation = [0, -15, 0, 0, -8, 0, 0, 0, -12, 0, 0, 0][i] || 0;
                  const recovery = Math.max(70, Math.min(100, baseRecovery + chromosomeVariation));

                  return (
                    <div key={i} className="text-center">
                      <div 
                        className={`h-16 rounded ${
                          recovery >= 95 ? 'bg-green-500' : recovery >= 85 ? 'bg-green-300' : recovery >= 75 ? 'bg-yellow-400' : 'bg-red-400'
                        }`}
                        style={{ opacity: recovery / 100 }}
                      />
                      <p className="text-xs mt-1">Chr {i + 1}</p>
                      <p className="text-xs font-bold">{recovery.toFixed(0)}%</p>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="combined" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Combined Selection Index</CardTitle>
              <CardDescription>Weighted foreground and background scores</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Foreground Weight</Label>
                  <Input type="number" defaultValue="60" min="0" max="100" />
                </div>
                <div className="space-y-2">
                  <Label>Background Weight</Label>
                  <Input type="number" defaultValue="40" min="0" max="100" />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-center p-3">Rank</th>
                      <th className="text-left p-3">Candidate</th>
                      <th className="text-right p-3">Foreground</th>
                      <th className="text-right p-3">Background</th>
                      <th className="text-right p-3">Combined</th>
                      <th className="text-center p-3">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...candidates]
                      .sort((a, b) => b.totalScore - a.totalScore)
                      .map((cand, i) => (
                        <tr key={cand.id} className={`border-b hover:bg-muted/50 ${i < 3 ? 'bg-green-50' : ''}`}>
                          <td className="p-3 text-center font-bold">{i + 1}</td>
                          <td className="p-3 font-medium">{cand.name}</td>
                          <td className={`p-3 text-right ${getScoreColor(cand.foregroundScore)}`}>
                            {cand.foregroundScore}%
                          </td>
                          <td className={`p-3 text-right ${getScoreColor(cand.backgroundScore)}`}>
                            {cand.backgroundScore}%
                          </td>
                          <td className={`p-3 text-right font-bold ${getScoreColor(cand.totalScore)}`}>
                            {cand.totalScore}%
                          </td>
                          <td className="p-3 text-center">
                            {i === 0 ? (
                              <Badge className="bg-green-100 text-green-700">⭐ Best</Badge>
                            ) : i < 3 ? (
                              <Badge className="bg-blue-100 text-blue-700">✓ Select</Badge>
                            ) : (
                              <Badge variant="secondary">Backup</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button>📋 Export Selected</Button>
            <Button variant="outline">📊 Generate Report</Button>
          </div>
        </TabsContent>

        <TabsContent value="markers" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Target Marker Database</CardTitle>
              <CardDescription>Manage markers for MAS programs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Marker</th>
                      <th className="text-left p-3">Trait</th>
                      <th className="text-center p-3">Chr</th>
                      <th className="text-right p-3">Position</th>
                      <th className="text-center p-3">Alleles</th>
                      <th className="text-center p-3">Favorable</th>
                      <th className="text-center p-3">Effect</th>
                      <th className="text-center p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {targetMarkers.map((marker) => (
                      <tr key={marker.id} className="border-b hover:bg-muted/50">
                        <td className="p-3 font-bold">{marker.name}</td>
                        <td className="p-3">{marker.trait}</td>
                        <td className="p-3 text-center">{marker.chromosome}</td>
                        <td className="p-3 text-right font-mono">{marker.position.toFixed(1)} Mb</td>
                        <td className="p-3 text-center font-mono">{marker.alleles.join('/')}</td>
                        <td className="p-3 text-center">
                          <Badge className="bg-green-100 text-green-700">{marker.favorableAllele}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={marker.effect === 'Major' ? 'default' : 'secondary'}>
                            {marker.effect}
                          </Badge>
                        </td>
                        <td className="p-3 text-center">
                          {marker.validated ? (
                            <Badge className="bg-green-100 text-green-700">✓ Validated</Badge>
                          ) : (
                            <Badge variant="outline">Candidate</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Button className="mt-4">➕ Add Marker</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
