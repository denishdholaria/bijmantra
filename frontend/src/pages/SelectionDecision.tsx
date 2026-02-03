/**
 * Selection Decision Page
 * 
 * Make advancement decisions for breeding candidates.
 * Connects to /api/v2/selection-decisions endpoints.
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import {
  CheckSquare, ThumbsUp, ThumbsDown, Minus, Search, Download,
  Save, TrendingUp, RefreshCw, BarChart3, Loader2
} from 'lucide-react'
import { apiClient, SelectionCandidate, SelectionStatistics } from '@/lib/api-client'

export function SelectionDecision() {
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProgram, setSelectedProgram] = useState('')
  const [selectedTrial, setSelectedTrial] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('')
  const [notesDialog, setNotesDialog] = useState<{ open: boolean; candidateId: string; decision: string }>({ open: false, candidateId: '', decision: '' })
  const [decisionNotes, setDecisionNotes] = useState('')
  const [localDecisions, setLocalDecisions] = useState<Record<string, { decision: string; notes?: string }>>({})

  const { data: candidatesData, isLoading: isLoadingCandidates, refetch } = useQuery({
    queryKey: ['selection-candidates', selectedProgram, selectedTrial, decisionFilter, searchQuery],
    queryFn: () => apiClient.selectionDecisionsService.getCandidates({
      program_id: selectedProgram || undefined,
      trial_id: selectedTrial || undefined,
      status: decisionFilter || undefined,
      search: searchQuery || undefined,
    }),
  })

  const { data: statsData, isLoading: isLoadingStats } = useQuery({
    queryKey: ['selection-statistics', selectedProgram, selectedTrial],
    queryFn: () => apiClient.selectionDecisionsService.getStatistics({
      program_id: selectedProgram || undefined,
      trial_id: selectedTrial || undefined,
    }),
  })

  const { data: programsData } = useQuery({
    queryKey: ['selection-programs'],
    queryFn: () => apiClient.selectionDecisionsService.getPrograms(),
  })

  const { data: trialsData } = useQuery({
    queryKey: ['selection-trials', selectedProgram],
    queryFn: () => apiClient.selectionDecisionsService.getTrials(selectedProgram || undefined),
  })

  const decisionMutation = useMutation({
    mutationFn: ({ candidateId, decision, notes }: { candidateId: string; decision: string; notes?: string }) =>
      apiClient.selectionDecisionsService.makeDecision(candidateId, decision as "advance" | "reject" | "hold", notes),
    onSuccess: (_, variables) => {
      toast.success(`Candidate marked as ${variables.decision}`)
      queryClient.invalidateQueries({ queryKey: ['selection-candidates'] })
      queryClient.invalidateQueries({ queryKey: ['selection-statistics'] })
    },
    onError: () => toast.error('Failed to record decision'),
  })

  const bulkSaveMutation = useMutation({
    mutationFn: () => {
      const decisions = Object.entries(localDecisions).map(([candidate_id, { decision, notes }]) => ({
        candidate_id, decision, notes
      }))
      return apiClient.selectionDecisionsService.recordBulkDecisions(decisions)
    },
    onSuccess: (data) => {
      toast.success(`${data.successful} decisions saved`)
      setLocalDecisions({})
      queryClient.invalidateQueries({ queryKey: ['selection-candidates'] })
      queryClient.invalidateQueries({ queryKey: ['selection-statistics'] })
    },
    onError: () => toast.error('Failed to save decisions'),
  })

  const candidates: SelectionCandidate[] = candidatesData?.data || []
  const statistics: SelectionStatistics | null = statsData?.data || null
  const programs = programsData?.data || []
  const trials = trialsData?.data || []

  const setDecision = (id: string, decision: 'advance' | 'reject' | 'hold', notes?: string) => {
    setLocalDecisions(prev => ({ ...prev, [id]: { decision, notes } }))
    decisionMutation.mutate({ candidateId: id, decision, notes })
  }

  const handleDecisionWithNotes = (candidateId: string, decision: string) => {
    setNotesDialog({ open: true, candidateId, decision })
    setDecisionNotes('')
  }

  const confirmDecision = () => {
    setDecision(notesDialog.candidateId, notesDialog.decision as 'advance' | 'reject' | 'hold', decisionNotes || undefined)
    setNotesDialog({ open: false, candidateId: '', decision: '' })
  }

  const exportDecisions = () => {
    const csv = [
      ['Name', 'GEBV', 'Yield', 'Generation', 'Traits', 'Decision', 'Notes'].join(','),
      ...candidates.map(c => [
        c.name, c.gebv, c.yield_estimate || '', c.generation || '',
        `"${c.traits.join('; ')}"`, localDecisions[c.id]?.decision || c.decision || 'pending',
        `"${localDecisions[c.id]?.notes || c.decision_notes || ''}"`
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
    advanced: candidates.filter(c => (localDecisions[c.id]?.decision || c.decision) === 'advance').length,
    rejected: candidates.filter(c => (localDecisions[c.id]?.decision || c.decision) === 'reject').length,
    on_hold: candidates.filter(c => (localDecisions[c.id]?.decision || c.decision) === 'hold').length,
    pending: candidates.filter(c => !(localDecisions[c.id]?.decision || c.decision)).length,
    selection_rate: 0
  }

  const isLoading = isLoadingCandidates || isLoadingStats

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
          <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Button variant="outline" onClick={exportDecisions}><Download className="h-4 w-4 mr-2" />Export</Button>
          <Button onClick={() => bulkSaveMutation.mutate()} disabled={bulkSaveMutation.isPending || Object.keys(localDecisions).length === 0}>
            {bulkSaveMutation.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Save ({Object.keys(localDecisions).length})
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-blue-100 rounded-lg"><CheckSquare className="h-5 w-5 text-blue-600" /></div><div><div className="text-2xl font-bold">{stats.total_candidates}</div><div className="text-sm text-muted-foreground">Total</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-green-100 rounded-lg"><ThumbsUp className="h-5 w-5 text-green-600" /></div><div><div className="text-2xl font-bold">{stats.advanced}</div><div className="text-sm text-muted-foreground">Advanced</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-red-100 rounded-lg"><ThumbsDown className="h-5 w-5 text-red-600" /></div><div><div className="text-2xl font-bold">{stats.rejected}</div><div className="text-sm text-muted-foreground">Rejected</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-yellow-100 rounded-lg"><Minus className="h-5 w-5 text-yellow-600" /></div><div><div className="text-2xl font-bold">{stats.on_hold}</div><div className="text-sm text-muted-foreground">On Hold</div></div></div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="flex items-center gap-3"><div className="p-2 bg-purple-100 rounded-lg"><BarChart3 className="h-5 w-5 text-purple-600" /></div><div><div className="text-2xl font-bold">{stats.selection_rate}%</div><div className="text-sm text-muted-foreground">Selection Rate</div></div></div></CardContent></Card>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search by name, pedigree, or traits..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
            </div>
            <Select value={selectedProgram || '__all__'} onValueChange={(v) => setSelectedProgram(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="All Programs" /></SelectTrigger>
              <SelectContent><SelectItem value="__all__">All Programs</SelectItem>{programs.map(p => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={selectedTrial || '__all__'} onValueChange={(v) => setSelectedTrial(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[200px]"><SelectValue placeholder="All Trials" /></SelectTrigger>
              <SelectContent><SelectItem value="__all__">All Trials</SelectItem>{trials.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={decisionFilter || '__all__'} onValueChange={(v) => setDecisionFilter(v === '__all__' ? '' : v)}>
              <SelectTrigger className="w-[150px]"><SelectValue placeholder="All Status" /></SelectTrigger>
              <SelectContent><SelectItem value="__all__">All Status</SelectItem><SelectItem value="pending">Pending</SelectItem><SelectItem value="advance">Advanced</SelectItem><SelectItem value="reject">Rejected</SelectItem><SelectItem value="hold">On Hold</SelectItem></SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Selection Candidates</CardTitle><CardDescription>Review and make decisions for each candidate</CardDescription></CardHeader>
        <CardContent>
          {isLoadingCandidates ? (
            <div className="space-y-4">{[1,2,3,4].map(i => <Skeleton key={i} className="h-24 w-full" />)}</div>
          ) : (
            <ScrollArea className="h-[500px]">
              <div className="space-y-4">
                {candidates.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">No candidates found</div>
                ) : candidates.map((candidate) => {
                  const currentDecision = localDecisions[candidate.id]?.decision || candidate.decision
                  return (
                    <div key={candidate.id} className={`p-4 border rounded-lg transition-colors ${
                      currentDecision === 'advance' ? 'border-green-500 bg-green-50 dark:bg-green-950/20' :
                      currentDecision === 'reject' ? 'border-red-500 bg-red-50 dark:bg-red-950/20' :
                      currentDecision === 'hold' ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20' : ''
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">{candidate.name}</h3>
                            {candidate.generation && <Badge variant="outline" className="text-xs">{candidate.generation}</Badge>}
                            {currentDecision && <Badge variant={currentDecision === 'advance' ? 'default' : currentDecision === 'reject' ? 'destructive' : 'secondary'} className="capitalize">{currentDecision}</Badge>}
                          </div>
                          <div className="flex items-center gap-4 text-sm mb-2">
                            <span className="flex items-center gap-1"><TrendingUp className="h-4 w-4 text-green-600" />GEBV: {candidate.gebv.toFixed(2)}</span>
                            {candidate.yield_estimate && <span>Yield: {candidate.yield_estimate} t/ha</span>}
                            {candidate.pedigree && <span className="text-muted-foreground truncate max-w-[200px]" title={candidate.pedigree}>{candidate.pedigree}</span>}
                          </div>
                          <div className="flex flex-wrap gap-1">{candidate.traits.map((trait, i) => <Badge key={i} variant="outline" className="text-xs">{trait}</Badge>)}</div>
                          {(localDecisions[candidate.id]?.notes || candidate.decision_notes) && <p className="text-sm text-muted-foreground mt-2 italic">Note: {localDecisions[candidate.id]?.notes || candidate.decision_notes}</p>}
                        </div>
                        <div className="flex gap-2 ml-4">
                          <Button variant={currentDecision === 'advance' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'advance')} onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'advance') }} className={currentDecision !== 'advance' ? 'text-green-600 hover:text-green-700 hover:bg-green-50' : ''} title="Left-click to advance, right-click to add notes"><ThumbsUp className="h-4 w-4" /></Button>
                          <Button variant={currentDecision === 'hold' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'hold')} onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'hold') }} className={currentDecision !== 'hold' ? 'text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50' : ''} title="Left-click to hold, right-click to add notes"><Minus className="h-4 w-4" /></Button>
                          <Button variant={currentDecision === 'reject' ? 'default' : 'outline'} size="sm" onClick={() => setDecision(candidate.id, 'reject')} onContextMenu={(e) => { e.preventDefault(); handleDecisionWithNotes(candidate.id, 'reject') }} className={currentDecision !== 'reject' ? 'text-red-600 hover:text-red-700 hover:bg-red-50' : ''} title="Left-click to reject, right-click to add notes"><ThumbsDown className="h-4 w-4" /></Button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      <Dialog open={notesDialog.open} onOpenChange={(open) => setNotesDialog({ ...notesDialog, open })}>
        <DialogContent>
          <DialogHeader><DialogTitle className="capitalize">{notesDialog.decision} Candidate with Notes</DialogTitle><DialogDescription>Add optional notes to explain your decision.</DialogDescription></DialogHeader>
          <Textarea placeholder="Enter notes for this decision..." value={decisionNotes} onChange={(e) => setDecisionNotes(e.target.value)} rows={4} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setNotesDialog({ open: false, candidateId: '', decision: '' })}>Cancel</Button>
            <Button onClick={confirmDecision}>Confirm {notesDialog.decision}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default SelectionDecision
