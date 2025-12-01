/**
 * Parentage Analysis Page
 * Paternity/maternity testing and pedigree verification
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

interface ParentageResult {
  offspring: string
  claimedParent1: string
  claimedParent2: string
  verifiedParent1: string
  verifiedParent2: string
  confidence: number
  mismatches: number
  status: 'verified' | 'mismatch' | 'unknown'
}

interface CandidateParent {
  id: string
  name: string
  likelihood: number
  exclusionProb: number
  mendelianErrors: number
  rank: number
}

const parentageResults: ParentageResult[] = [
  { offspring: 'F1-2024-001', claimedParent1: 'Elite-A', claimedParent2: 'Elite-B', verifiedParent1: 'Elite-A', verifiedParent2: 'Elite-B', confidence: 99.8, mismatches: 0, status: 'verified' },
  { offspring: 'F1-2024-002', claimedParent1: 'Elite-A', claimedParent2: 'Elite-C', verifiedParent1: 'Elite-A', verifiedParent2: 'Elite-C', confidence: 99.5, mismatches: 1, status: 'verified' },
  { offspring: 'F1-2024-003', claimedParent1: 'Elite-B', claimedParent2: 'Elite-D', verifiedParent1: 'Elite-B', verifiedParent2: 'Elite-E', confidence: 98.2, mismatches: 0, status: 'mismatch' },
  { offspring: 'F1-2024-004', claimedParent1: 'Elite-C', claimedParent2: 'Elite-D', verifiedParent1: 'Elite-C', verifiedParent2: 'Elite-D', confidence: 99.9, mismatches: 0, status: 'verified' },
  { offspring: 'F1-2024-005', claimedParent1: 'Elite-A', claimedParent2: 'Elite-E', verifiedParent1: 'Unknown', verifiedParent2: 'Elite-E', confidence: 45.2, mismatches: 8, status: 'unknown' },
]

const candidateParents: CandidateParent[] = [
  { id: 'cp1', name: 'Elite-A', likelihood: 0.998, exclusionProb: 0.002, mendelianErrors: 0, rank: 1 },
  { id: 'cp2', name: 'Elite-B', likelihood: 0.125, exclusionProb: 0.875, mendelianErrors: 5, rank: 2 },
  { id: 'cp3', name: 'Elite-C', likelihood: 0.045, exclusionProb: 0.955, mendelianErrors: 8, rank: 3 },
  { id: 'cp4', name: 'Elite-D', likelihood: 0.012, exclusionProb: 0.988, mendelianErrors: 12, rank: 4 },
  { id: 'cp5', name: 'Elite-E', likelihood: 0.003, exclusionProb: 0.997, mendelianErrors: 18, rank: 5 },
]

export function ParentageAnalysis() {
  const [activeTab, setActiveTab] = useState('verification')
  const [selectedOffspring, setSelectedOffspring] = useState('')

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'verified':
        return <Badge className="bg-green-100 text-green-700">✓ Verified</Badge>
      case 'mismatch':
        return <Badge className="bg-red-100 text-red-700">✗ Mismatch</Badge>
      default:
        return <Badge className="bg-yellow-100 text-yellow-700">? Unknown</Badge>
    }
  }

  const verifiedCount = parentageResults.filter(r => r.status === 'verified').length
  const mismatchCount = parentageResults.filter(r => r.status === 'mismatch').length

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Parentage Analysis</h1>
          <p className="text-muted-foreground mt-1">Pedigree verification and parent identification</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">📥 Import Genotypes</Button>
          <Button>🔬 Run Analysis</Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-primary">{parentageResults.length}</p>
            <p className="text-sm text-muted-foreground">Total Tested</p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-green-700">{verifiedCount}</p>
            <p className="text-sm text-green-600">Verified</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-red-700">{mismatchCount}</p>
            <p className="text-sm text-red-600">Mismatches</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{((verifiedCount / parentageResults.length) * 100).toFixed(0)}%</p>
            <p className="text-sm text-muted-foreground">Accuracy Rate</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="verification">Pedigree Verification</TabsTrigger>
          <TabsTrigger value="assignment">Parent Assignment</TabsTrigger>
          <TabsTrigger value="exclusion">Exclusion Analysis</TabsTrigger>
          <TabsTrigger value="markers">Marker Panel</TabsTrigger>
        </TabsList>

        <TabsContent value="verification" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Pedigree Verification Results</CardTitle>
              <CardDescription>Compare claimed vs verified parentage</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3">Offspring</th>
                      <th className="text-left p-3">Claimed Parent 1</th>
                      <th className="text-left p-3">Claimed Parent 2</th>
                      <th className="text-left p-3">Verified Parent 1</th>
                      <th className="text-left p-3">Verified Parent 2</th>
                      <th className="text-right p-3">Confidence</th>
                      <th className="text-center p-3">Mismatches</th>
                      <th className="text-center p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parentageResults.map((result) => (
                      <tr key={result.offspring} className={`border-b hover:bg-muted/50 ${result.status === 'mismatch' ? 'bg-red-50' : ''}`}>
                        <td className="p-3 font-medium">{result.offspring}</td>
                        <td className="p-3">{result.claimedParent1}</td>
                        <td className="p-3">{result.claimedParent2}</td>
                        <td className={`p-3 ${result.claimedParent1 !== result.verifiedParent1 ? 'text-red-600 font-bold' : ''}`}>
                          {result.verifiedParent1}
                        </td>
                        <td className={`p-3 ${result.claimedParent2 !== result.verifiedParent2 ? 'text-red-600 font-bold' : ''}`}>
                          {result.verifiedParent2}
                        </td>
                        <td className="p-3 text-right">
                          <span className={result.confidence >= 95 ? 'text-green-600' : result.confidence >= 80 ? 'text-yellow-600' : 'text-red-600'}>
                            {result.confidence.toFixed(1)}%
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={result.mismatches === 0 ? 'secondary' : 'destructive'}>
                            {result.mismatches}
                          </Badge>
                        </td>
                        <td className="p-3 text-center">{getStatusBadge(result.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="assignment" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Parent Assignment</CardTitle>
              <CardDescription>Identify most likely parents from candidate pool</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Select Offspring</Label>
                  <Select value={selectedOffspring} onValueChange={setSelectedOffspring}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select offspring" />
                    </SelectTrigger>
                    <SelectContent>
                      {parentageResults.map(r => (
                        <SelectItem key={r.offspring} value={r.offspring}>{r.offspring}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Candidate Pool</Label>
                  <Input placeholder="All available parents" disabled />
                </div>
              </div>

              <div className="mt-6">
                <h4 className="font-medium mb-3">Candidate Parent Rankings</h4>
                <div className="space-y-3">
                  {candidateParents.map((parent) => (
                    <div key={parent.id} className={`p-4 border rounded-lg ${parent.rank === 1 ? 'border-green-500 bg-green-50' : ''}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge variant={parent.rank === 1 ? 'default' : 'secondary'}>#{parent.rank}</Badge>
                          <span className="font-bold">{parent.name}</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <span>Errors: <span className={parent.mendelianErrors === 0 ? 'text-green-600' : 'text-red-600'}>{parent.mendelianErrors}</span></span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm w-20">Likelihood:</span>
                        <Progress value={parent.likelihood * 100} className="flex-1 h-2" />
                        <span className="text-sm w-16 text-right">{(parent.likelihood * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="exclusion" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Exclusion Analysis</CardTitle>
              <CardDescription>Mendelian inheritance check for parent-offspring trios</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Exclusion Criteria</h4>
                  <p className="text-sm text-muted-foreground">
                    A candidate parent is excluded if the offspring has an allele that could not have been inherited from either parent.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Marker</th>
                        <th className="text-center p-3">Offspring</th>
                        <th className="text-center p-3">Parent 1</th>
                        <th className="text-center p-3">Parent 2</th>
                        <th className="text-center p-3">Inheritance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { marker: 'SNP_001', offspring: 'AG', parent1: 'AA', parent2: 'GG', valid: true },
                        { marker: 'SNP_002', offspring: 'CC', parent1: 'AC', parent2: 'CC', valid: true },
                        { marker: 'SNP_003', offspring: 'TT', parent1: 'AA', parent2: 'AA', valid: false },
                        { marker: 'SNP_004', offspring: 'GT', parent1: 'GG', parent2: 'TT', valid: true },
                        { marker: 'SNP_005', offspring: 'AA', parent1: 'AG', parent2: 'AG', valid: true },
                      ].map((row, i) => (
                        <tr key={i} className={`border-b hover:bg-muted/50 ${!row.valid ? 'bg-red-50' : ''}`}>
                          <td className="p-3 font-mono">{row.marker}</td>
                          <td className="p-3 text-center font-mono">{row.offspring}</td>
                          <td className="p-3 text-center font-mono">{row.parent1}</td>
                          <td className="p-3 text-center font-mono">{row.parent2}</td>
                          <td className="p-3 text-center">
                            {row.valid ? (
                              <Badge className="bg-green-100 text-green-700">✓ Valid</Badge>
                            ) : (
                              <Badge className="bg-red-100 text-red-700">✗ Error</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="markers" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Parentage Marker Panel</CardTitle>
              <CardDescription>Markers used for parentage analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-blue-700">96</p>
                    <p className="text-sm text-blue-600">Total Markers</p>
                  </CardContent>
                </Card>
                <Card className="bg-green-50 border-green-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-green-700">0.45</p>
                    <p className="text-sm text-green-600">Mean MAF</p>
                  </CardContent>
                </Card>
                <Card className="bg-purple-50 border-purple-200">
                  <CardContent className="pt-4 text-center">
                    <p className="text-3xl font-bold text-purple-700">99.99%</p>
                    <p className="text-sm text-purple-600">Exclusion Power</p>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium">Marker Statistics</h4>
                {[
                  { name: 'Polymorphism Information Content (PIC)', value: 0.42 },
                  { name: 'Expected Heterozygosity (He)', value: 0.48 },
                  { name: 'Combined Exclusion Probability', value: 0.9999 },
                  { name: 'Identity Probability', value: 1e-35 },
                ].map((stat, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted rounded">
                    <span>{stat.name}</span>
                    <span className="font-bold font-mono">
                      {typeof stat.value === 'number' && stat.value < 0.001 
                        ? stat.value.toExponential(0) 
                        : stat.value.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
