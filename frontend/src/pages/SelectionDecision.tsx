import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  CheckSquare,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Search,
  Filter,
  Download,
  Save,
  TrendingUp
} from 'lucide-react'

interface SelectionCandidate {
  id: string
  name: string
  gebv: number
  yield: number
  traits: string[]
  decision?: 'advance' | 'reject' | 'hold'
  notes?: string
}

export function SelectionDecision() {
  const [searchQuery, setSearchQuery] = useState('')
  const [candidates, setCandidates] = useState<SelectionCandidate[]>([
    { id: '1', name: 'BM-2025-001', gebv: 2.45, yield: 7.2, traits: ['High yield', 'Disease resistant'] },
    { id: '2', name: 'BM-2025-015', gebv: 2.38, yield: 6.9, traits: ['Drought tolerant', 'Early maturity'] },
    { id: '3', name: 'BM-2025-023', gebv: 2.31, yield: 6.7, traits: ['Quality', 'High yield'] },
    { id: '4', name: 'BM-2025-042', gebv: 2.28, yield: 6.5, traits: ['Disease resistant', 'Quality'] },
    { id: '5', name: 'BM-2025-056', gebv: 2.15, yield: 6.3, traits: ['Wide adaptation'] },
    { id: '6', name: 'BM-2025-078', gebv: 2.08, yield: 6.1, traits: ['Stress tolerant'] },
    { id: '7', name: 'BM-2025-089', gebv: 1.95, yield: 5.8, traits: ['Early maturity'] },
    { id: '8', name: 'BM-2025-102', gebv: 1.82, yield: 5.5, traits: ['Quality'] }
  ])

  const setDecision = (id: string, decision: 'advance' | 'reject' | 'hold') => {
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, decision } : c))
  }

  const stats = {
    total: candidates.length,
    advanced: candidates.filter(c => c.decision === 'advance').length,
    rejected: candidates.filter(c => c.decision === 'reject').length,
    pending: candidates.filter(c => !c.decision).length
  }

  const filteredCandidates = candidates.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CheckSquare className="h-8 w-8 text-primary" />
            Selection Decision
          </h1>
          <p className="text-muted-foreground mt-1">Make advancement decisions for breeding candidates</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button><Save className="h-4 w-4 mr-2" />Save Decisions</Button>
        </div>
      </div>

      {/* Progress */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><CheckSquare className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total}</div>
                <div className="text-sm text-muted-foreground">Total Candidates</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><ThumbsUp className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.advanced}</div>
                <div className="text-sm text-muted-foreground">Advanced</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg"><ThumbsDown className="h-5 w-5 text-red-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.rejected}</div>
                <div className="text-sm text-muted-foreground">Rejected</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Minus className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.pending}</div>
                <div className="text-sm text-muted-foreground">Pending</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search candidates..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Button variant="outline"><Filter className="h-4 w-4 mr-2" />Filter</Button>
          </div>
        </CardContent>
      </Card>

      {/* Candidates */}
      <Card>
        <CardHeader>
          <CardTitle>Selection Candidates</CardTitle>
          <CardDescription>Review and make decisions for each candidate</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              {filteredCandidates.map((candidate) => (
                <div key={candidate.id} className={`p-4 border rounded-lg ${candidate.decision === 'advance' ? 'border-green-500 bg-green-50' : candidate.decision === 'reject' ? 'border-red-500 bg-red-50' : ''}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold">{candidate.name}</h3>
                        {candidate.decision && (
                          <Badge variant={candidate.decision === 'advance' ? 'default' : candidate.decision === 'reject' ? 'destructive' : 'secondary'} className="capitalize">{candidate.decision}</Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm mb-2">
                        <span className="flex items-center gap-1"><TrendingUp className="h-4 w-4 text-green-600" />GEBV: {candidate.gebv.toFixed(2)}</span>
                        <span>Yield: {candidate.yield} t/ha</span>
                      </div>
                      <div className="flex gap-1">
                        {candidate.traits.map((trait, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant={candidate.decision === 'advance' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'advance')} className="text-green-600 hover:text-green-700">
                        <ThumbsUp className="h-4 w-4" />
                      </Button>
                      <Button variant={candidate.decision === 'hold' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'hold')} className="text-yellow-600 hover:text-yellow-700">
                        <Minus className="h-4 w-4" />
                      </Button>
                      <Button variant={candidate.decision === 'reject' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'reject')} className="text-red-600 hover:text-red-700">
                        <ThumbsDown className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
