import { cn } from '@/lib/utils'

interface ProposalPreview {
  id: number
  title: string
  status: string
  description: string
}

interface ProposalCardProps {
  proposal: ProposalPreview
  onReview: (id: number) => void
  reviewed?: boolean // To disable reviewing again locally if we track it
}

export function ProposalCard({ proposal, onReview, reviewed }: ProposalCardProps) {
  const isDraft = proposal.status === 'DRAFT'
  
  return (
    <div className="mt-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      {/* Top Banner */}
      <div className="h-1 bg-gradient-to-r from-purple-500 to-indigo-500"></div>
      
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-wider">
                ✨ Proposal #{proposal.id}
              </span>
              <span className={cn(
                "px-2 py-0.5 text-[10px] font-medium rounded-full",
                proposal.status === 'DRAFT' ? "bg-amber-100 text-amber-800" :
                proposal.status === 'APPROVED' ? "bg-green-100 text-green-800" :
                proposal.status === 'EXECUTED' ? "bg-blue-100 text-blue-800" :
                "bg-red-100 text-red-800"
              )}>
                {proposal.status}
              </span>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">{proposal.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">{proposal.description}</p>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 p-2 rounded-lg text-purple-600 dark:text-purple-400">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => onReview(proposal.id)}
            disabled={!isDraft && !reviewed} // Just basic checking
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2",
              "bg-purple-600 hover:bg-purple-700 text-white shadow-sm"
            )}
          >
            {isDraft ? "Review Proposal" : "View Details"}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
