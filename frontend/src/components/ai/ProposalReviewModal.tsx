import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface ProposalReviewModalProps {
  proposalId: number
  isOpen: boolean
  onClose: () => void
  onActionComplete: () => void // Refresh chat or update UI
}

interface ProposalDetails {
  id: number
  title: string
  description: string
  action_type: string
  target_data: any
  ai_rationale: string
  confidence_score: number
  status: string
  created_at: string
}

export function ProposalReviewModal({ proposalId, isOpen, onClose, onActionComplete }: ProposalReviewModalProps) {
  const [proposal, setProposal] = useState<ProposalDetails | null>(null)
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (isOpen && proposalId) {
      fetchProposal()
    }
  }, [isOpen, proposalId])

  const fetchProposal = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<ProposalDetails>(`/api/v2/proposals/${proposalId}`)
      setProposal(data)
    } catch (e) {
      setError('Failed to load proposal details')
    } finally {
      setLoading(false)
    }
  }

  const handleReview = async (approved: boolean) => {
    setProcessing(true)
    try {
      // 1. Review (Approve/Reject)
      await apiClient.post(`/api/v2/proposals/${proposalId}/review`, {
        approved,
        notes
      })
      
      // 2. If approved, Execute immediately (for now, simpler UX)
      if (approved) {
        await apiClient.post(`/api/v2/proposals/${proposalId}/execute`, {})
      }
      
      onActionComplete()
      onClose()
    } catch (e) {
      setError('Failed to process review')
    } finally {
      setProcessing(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex justify-between items-center bg-muted/20">
          <div>
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                📜 Proposal Review
                <span className="text-xs font-normal px-2 py-0.5 bg-muted rounded-full text-muted-foreground">#{proposalId}</span>
              </h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : error ? (
            <div className="text-red-500 text-center py-8">{error}</div>
          ) : proposal ? (
            <>
              {/* Summary */}
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-1">{proposal.title}</h3>
                <p className="text-muted-foreground text-sm">{proposal.description}</p>
              </div>

              {/* Rationale */}
              <div className="bg-prakruti-patta-pale dark:bg-prakruti-patta/10 p-4 rounded-xl border border-prakruti-patta/20">
                <h4 className="text-xs font-bold text-prakruti-patta uppercase tracking-wider mb-2">AI Rationale</h4>
                <p className="text-sm text-prakruti-patta-dark dark:text-prakruti-patta-light italic">"{proposal.ai_rationale}"</p>
                <div className="mt-2 text-xs text-prakruti-patta font-medium">
                  Confidence Score: {proposal.confidence_score}%
                </div>
              </div>

              {/* Data Diff / Details */}
              <div className="bg-muted p-4 rounded-xl border border-border font-mono text-sm overflow-x-auto">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Proposed Changes ({proposal.action_type})</h4>
                <pre className="text-foreground">
                  {JSON.stringify(proposal.target_data, null, 2)}
                </pre>
              </div>

              {/* Reviewer Notes */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Reviewer Notes (Optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary bg-background"
                  rows={3}
                  placeholder="Reason for approval or rejection..."
                />
              </div>
            </>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-3 bg-muted/30">
          <button
            onClick={() => handleReview(false)}
            disabled={processing || loading}
            className="px-4 py-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors font-medium border border-transparent hover:border-destructive/20"
          >
            Reject
          </button>
          <button
            onClick={() => handleReview(true)}
            disabled={processing || loading}
            className={cn(
              "px-6 py-2 bg-primary text-primary-foreground rounded-lg shadow-sm hover:bg-primary/90 transition-all font-medium flex items-center gap-2",
              processing && "opacity-70 cursor-wait"
            )}
          >
            {processing ? 'Processing...' : 'Approve & Execute'}
          </button>
        </div>
      </div>
    </div>
  )
}
