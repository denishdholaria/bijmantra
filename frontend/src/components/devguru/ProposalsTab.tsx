import { Proposal } from '@/types/devguru'
import { cn } from '@/lib/utils'

interface ProposalsTabProps {
  proposals: Proposal[]
  isLoading: boolean
  onReview: (id: number, approved: boolean, notes?: string) => void
}

export function ProposalsTab({ proposals, isLoading, onReview }: ProposalsTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading proposals...</p>
        </div>
      </div>
    )
  }

  if (proposals.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">📜</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Pending Proposals</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            DevGuru hasn't generated any proposals for your review yet. Ask it to create an experiment to see one here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {proposals.map(proposal => (
        <div key={proposal.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{proposal.title}</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">{proposal.description}</p>
            </div>
            <span className={cn(
              'px-2 py-0.5 text-[10px] rounded-full uppercase font-medium',
              proposal.status === 'draft' ? 'bg-yellow-100 text-yellow-700' :
              proposal.status === 'pending_review' ? 'bg-blue-100 text-blue-700' :
              proposal.status === 'approved' ? 'bg-green-100 text-green-700' :
              'bg-gray-100 text-gray-600'
            )}>
              {proposal.status.replace('_', ' ')}
            </span>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900/50 rounded p-3 mb-3">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">AI Rationale:</p>
            <p className="text-xs text-gray-600 dark:text-gray-400 italic">"{proposal.ai_rationale}"</p>
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
               <p className="text-[10px] text-gray-500">
                 Action: <span className="font-mono">{proposal.action_type}</span> • Confidence: {proposal.confidence_score}%
               </p>
            </div>
          </div>

          {/* Action Buttons */}
          {(proposal.status === 'draft' || proposal.status === 'pending_review') && (
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => onReview(proposal.id, false, "Rejected by user")}
                className="px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded border border-red-200 dark:border-red-800"
              >
                Reject
              </button>
              <button
                onClick={() => onReview(proposal.id, true, "Approved by user")}
                className="px-3 py-1.5 text-xs font-medium text-white bg-green-600 hover:bg-green-700 rounded shadow-sm"
              >
                Approve & Execute
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
