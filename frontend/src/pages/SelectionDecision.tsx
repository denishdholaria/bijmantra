import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { useDemoMode } from '@/hooks/useDemoMode'
import {
  CheckSquare,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Search,
  Filter,
  Download,
  Save,
  TrendingUp,
  RefreshCw,
  History,
  BarChart3,
  Loader2
} from 'lucide-react'

interface SelectionCandidate {
  id: string
  name: string
  germplasm_id?: string
  program_id?: string
  program_name?: string
  generation?: string
  gebv: number
  yield_estimate?: number
  traits: string[]
  pedigree?: string
  trial_id?: string
  trial_name?: string
  location?: string
  decision?: 'advance' | 'reject' | 'hold' | null
  decision_notes?: string
  decision_date?: string
}

interface Statistics {
  total_candidates: number
  advanced: number
  rejected: number
  on_hold: number
  pending: number
  selection_rate: number
  avg_gebv_advanced?: number
  avg_gebv_rejected?: number
}

interface Program {
  id: string
  name: string
}

interface Trial {
  id: string
  name: string
  program_id: string
}

// Demo data for when demo mode is enabled or API fails
const DEMO_CANDIDATES: SelectionCandidate[] = [
  { id: '1', name: 'BM-2025-001', gebv: 2.45, yield_estimate: 7.2, traits: ['High yield', 'Disease resistant'], generation: 'F6', pedigree: 'IR64 / Swarna' },
  { id: '2', name: 'BM-2025-015', gebv: 2.38, yield_estimate: 6.9, traits: ['Drought tolerant', 'Early maturity'], generation: 'F6', pedigree: 'Sahbhagi Dhan / IR64' },
  { id: '3', name: 'BM-2025-023', gebv: 2.31, yield_estimate: 6.7, traits: ['Quality', 'High yield'], generation: 'F5', pedigree: 'Basmati 370 / IR64' },
  { id: '4', name: 'BM-2025-042', gebv: 2.28, yield_estimate: 6.5, traits: ['Disease resistant', 'Quality'], generation: 'F6', pedigree: 'Swarna-Sub1 / IR64' },
  { id: '5', name: 'BM-2025-056', gebv: 2.15, yield_estimate: 6.3, traits: ['Wide adaptation'], generation: 'F7', pedigree: 'HD2967 / PBW343' },
  { id: '6', name: 'BM-2025-078', gebv: 2.08, yield_estimate: 6.1, traits: ['Stress tolerant'], generation: 'F6', pedigree: 'DBW17 / HD2967' },
  { id: '7', name: 'BM-2025-089', gebv: 1.95, yield_estimate: 5.8, traits: ['Early maturity'], generation: 'F5', pedigree: 'IR64 / MTU1010' },
  { id: '8', name: 'BM-2025-102', gebv: 1.82, yield_estimate: 5.5, traits: ['Quality'], generation: 'F4', pedigree: 'Pusa Basmati 1 / IR64' }
]

export function SelectionDecision() {
  const { isDemoMode } = useDemoMode()
  const [searchQuery, setSearchQuery] = useState('')
  const [candidates, setCandidates] = useState<SelectionCandidate[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [programs, setPrograms] = useState<Program[]>([])
  const [trials, setTrials] = useState<Trial[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  
  // Filters
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const [selectedTrial, setSelectedTrial] = useState<string>('')
  const [decisionFilter, setDecisionFilter] = useState<string>('')
  
  // Notes dialog
  const [notesDialog, setNotesDialog] = useState<{ open: boolean; candidateId: string; decision: string }>({
    open: false,
    candidateId: '',
    decision: ''
  })
  const [decisionNotes, setDecisionNotes] = useState('')

  // Fetch data
  useEffect(() => {
    fetchData()
  }, [selectedProgram, selectedTrial, decisionFilter, isDemoMode])

  const fetchData = async () => {
    if (isDemoMode) {
      // Use demo data
      setCandidates(DEMO_CANDIDATES)
      setStatistics({
        total_candidates: DEMO_CANDIDATES.length,
        advanced: 0,
        rejected: 0,
        on_hold: 0,
        pending: DEMO_CANDIDATES.length,
        selection_rate: 0
      })
      setPrograms([{ id: 'prog-001', name: 'Rice Improvement Program' }])
      setTrials([{ id: 'trial-001', name: 'Advanced Yield Trial 2025', program_id: 'prog-001' }])
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      // Build query params
      const params = new URLSearchParams()
      if (selectedProgram) params.append('program_id', selectedProgram)
      if (selectedTrial) params.append('trial_id', selectedTrial)
      if (decisionFilter) params.append('decision_status', decisionFilter)
      if (searchQuery) params.append('search', searchQuery)

      // Fetch candidates
      const candidatesRes = await fetch(`/api/v2/selection-decisions/candidates?${params}`)
      if (candidatesRes.ok) {
        const data = await candidatesRes.json()
        setCandidates(data.data || [])
      }

      // Fetch statistics
      const statsParams = new URLSearchParams()
      if (selectedProgram) statsParams.append('program_id', selectedProgram)
      if (selectedTrial) statsParams.append('trial_id', selectedTrial)
      
      const statsRes = await fetch(`/api/v2/selection-decisions/statistics?${statsParams}`)
      if (statsRes.ok) {
        const data = await statsRes.json()
        setStatistics(data.data)
      }

      // Fetch programs
      const programsRes = await fetch('/api/v2/selection-decisions/programs')
      if (programsRes.ok) {
        const data = await programsRes.json()
        setPrograms(data.data || [])
      }

      // Fetch trials
      const trialsParams = selectedProgram ? `?program_id=${selectedProgram}` : ''
      const trialsRes = await fetch(`/api/v2/selection-decisions/trials${trialsParams}`)
      if (trialsRes.ok) {
        const data = await trialsRes.json()
        setTrials(data.data || [])
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      // Fall back to demo data on error
      setCandidates(DEMO_CANDIDATES)
      toast.error('Failed to load data, showing demo data')
    } finally {
      setLoading(false)
    }
  }

  const setDecision = async (id: string, decision: 'advance' | 'reject' | 'hold', notes?: string) => {
    if (isDemoMode) {
      // Local state update for demo mode
      setCandidates(prev => prev.map(c => c.id === id ? { ...c, decision } : c))
      toast.success(`Candidate marked as ${decision}`)
      return
    }

    try {
      const res = await fetch(`/api/v2/selection-decisions/candidates/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, notes })
      })

      if (res.ok) {
        setCandidates(prev => prev.map(c => c.id === id ? { ...c, decision, decision_notes: notes } : c))
        toast.success(`Candidate marked as ${decision}`)
        // Refresh statistics
        fetchData()
      } else {
        toast.error('Failed to record decision')
      }
    } catch (error) {
      console.error('Error recording decision:', error)
      toast.error('Failed to record decision')
    }
  }

  const handleDecisionWithNotes = (candidateId: string, decision: string) => {
    setNotesDialog({ open: true, candidateId, decision })
    setDecisionNotes('')
  }

  const confirmDecision = () => {
    setDecision(notesDialog.candidateId, notesDialog.decision as 'advance' | 'reject' | 'hold', decisionNotes || undefined)
    setNotesDialog({ open: false, candidateId: '', decision: '' })
  }

  const saveBulkDecisions = async () => {
    const decisionsToSave = candidates.filter(c => c.decision)
    if (decisionsToSave.length === 0) {
      toast.info('No decisions to save')
      return
    }

    if (isDemoMode) {
      toast.success(`${decisionsToSave.length} decisions saved (demo mode)`)
      return
    }

    setSaving(true)
    try {
      const res = await fetch('/api/v2/selection-decisions/decisions/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decisions: decisionsToSave.map(c => ({
            candidate_id: c.id,
            decision: c.decision,
            notes: c.decision_notes
          }))
        })
      })

      if (res.ok) {
        const data = await res.json()
        toast.success(`${data.successful} decisions saved successfully`)
      } else {
        toast.error('Failed to save decisions')
      }
    } catch (error) {
      console.error('Error saving decisions:', error)
      toast.error('Failed to save decisions')
    } finally {
      setSaving(false)
    }
  }

  const exportDecisions = () => {
    const csv = [
      ['Name', 'GEBV', 'Yield', 'Generation', 'Traits', 'Decision', 'Notes'].join(','),
      ...candidates.map(c => [
        c.name,
        c.gebv,
        c.yield_estimate || '',
        c.generation || '',
        `"${c.traits.join('; ')}"`,
        c.decision || 'pending',
        `"${c.decision_notes || ''}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `selection-decisions-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Decisions exported to CSV')
  }

  const stats = statistics || {
    total_candidates: candidates.length,
    advanced: candidates.filter(c => c.decision === 'advance').length,
    rejected: candidates.filter(c => c.decision === 'reject').length,
    on_hold: candidates.filter(c => c.decision === 'hold').length,
    pending: candidates.filter(c => !c.decision).length,
    selection_rate: 0
  }

  const filteredCandidates = candidates.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.pedigree?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.traits.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
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
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportDecisions}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Button onClick={saveBulkDecisions} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Save Decisions
          </Button>
        </div>
      </div>

      {/* Progress Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><CheckSquare className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_candidates}</div>
                <div className="text-sm text-muted-foreground">Total</div>
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
                <div className="text-2xl font-bold">{stats.on_hold}</div>
                <div className="text-sm text-muted-foreground">On Hold</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><BarChart3 className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.selection_rate}%</div>
                <div className="text-sm text-muted-foreground">Selection Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search by name, pedigree, or traits..." 
                value={searchQuery} 
                onChange={(e) => setSearchQuery(e.target.value)} 
                className="pl-10" 
              />
            </div>
            <Select value={selectedProgram} onValueChange={setSelectedProgram}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Programs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Programs</SelectItem>
                {programs.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedTrial} onValueChange={setSelectedTrial}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Trials" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Trials</SelectItem>
                {trials.map(t => (
                  <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={decisionFilter} onValueChange={setDecisionFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="advance">Advanced</SelectItem>
                <SelectItem value="reject">Rejected</SelectItem>
                <SelectItem value="hold">On Hold</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Candidates List */}
      <Card>
        <CardHeader>
          <CardTitle>Selection Candidates</CardTitle>
          <CardDescription>
            Review and make decisions for each candidate. Click decision buttons or long-press to add notes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : (
            <ScrollArea className="h-[500px]">
              <div className="space-y-4">
                {filteredCandidates.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No candidates found matching your criteria
                  </div>
                ) : (
                  filteredCandidates.map((candidate) => (
                    <div 
                      key={candidate.id} 
                      className={`p-4 border rounded-lg transition-colors ${
                        candidate.decision === 'advance' ? 'border-green-500 bg-green-50 dark:bg-green-950/20' : 
                        candidate.decision === 'reject' ? 'border-red-500 bg-red-50 dark:bg-red-950/20' : 
                        candidate.decision === 'hold' ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">{candidate.name}</h3>
                            {candidate.generation && (
                              <Badge variant="outline" className="text-xs">{candidate.generation}</Badge>
                            )}
                            {candidate.decision && (
                              <Badge 
                                variant={candidate.decision === 'advance' ? 'default' : candidate.decision === 'reject' ? 'destructive' : 'secondary'} 
                                className="capitalize"
                              >
                                {candidate.decision}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm mb-2">
                            <span className="flex items-center gap-1">
                              <TrendingUp className="h-4 w-4 text-green-600" />
                              GEBV: {candidate.gebv.toFixed(2)}
                            </span>
                            {candidate.yield_estimate && (
                              <span>Yield: {candidate.yield_estimate} t/ha</span>
                            )}
                            {candidate.pedigree && (
                              <span className="text-muted-foreground truncate max-w-[200px]" title={candidate.pedigree}>
                                {candidate.pedigree}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {candidate.traits.map((trait, i) => (
                              <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>
                            ))}
                          </div>
                          {candidate.decision_notes && (
                            <p className="text-sm text-muted-foreground mt-2 italic">
                              Note: {candidate.decision_notes}
                            </p>
                          )}
                        </div>
                        <div className="flex gap-2 ml-4">
                          <Button 
                            variant={candidate.decision === 'advance' ? 'default' : 'outline'} 
                            size="sm" 
                            onClick={() => setDecision(candidate.id, 'advance')}
                            onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'advance') }}
                            className={candidate.decision !== 'advance' ? 'text-green-600 hover:text-green-700 hover:bg-green-50' : ''}
                            title="Left-click to advance, right-click to add notes"
                          >
                            <ThumbsUp className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant={candidate.decision === 'hold' ? 'default' : 'outline'} 
                            size="sm" 
                            onClick={() => setDecision(candidate.id, 'hold')}
                            onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'hold') }}
                            className={candidate.decision !== 'hold' ? 'text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50' : ''}
                            title="Left-click to hold, right-click to add notes"
                          >
                            <Minus className="h-4 w-4" />
                          </Button>
                          <Button 
                            variant={candidate.decision === 'reject' ? 'default' : 'outline'} 
                            size="sm" 
                            onClick={() => setDecision(candidate.id, 'reject')}
                            onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'reject') }}
                            className={candidate.decision !== 'reject' ? 'text-red-600 hover:text-red-700 hover:bg-red-50' : ''}
                            title="Left-click to reject, right-click to add notes"
                          >
                            <ThumbsDown className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Notes Dialog */}
      <Dialog open={notesDialog.open} onOpenChange={(open) => setNotesDialog({ ...notesDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="capitalize">
              {notesDialog.decision} Candidate with Notes
            </DialogTitle>
            <DialogDescription>
              Add optional notes to explain your decision.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Enter notes for this decision..."
            value={decisionNotes}
            onChange={(e) => setDecisionNotes(e.target.value)}
            rows={4}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setNotesDialog({ open: false, candidateId: '', decision: '' })}>
              Cancel
            </Button>
            <Button onClick={confirmDecision}>
              Confirm {notesDialog.decision}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
