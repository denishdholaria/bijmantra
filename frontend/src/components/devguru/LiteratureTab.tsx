import { Paper, LiteratureStats } from '@/types/devguru'

interface LiteratureTabProps {
  papers: Paper[]
  stats: LiteratureStats | undefined
  isLoading: boolean
  onUpdatePaper: (paperId: string, data: Partial<Paper>) => Promise<void>
  onDeletePaper?: (paperId: string) => Promise<void>
}

export function LiteratureTab({ papers, stats, isLoading, onUpdatePaper }: LiteratureTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading papers...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.total_papers}</p>
            <p className="text-xs text-blue-700">Total</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.read}</p>
            <p className="text-xs text-green-700">Read</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.reading}</p>
            <p className="text-xs text-yellow-700">Reading</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-gray-600">{stats.unread}</p>
            <p className="text-xs text-gray-700">Unread</p>
          </div>
        </div>
      )}

      {/* Papers List */}
      {papers.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-4xl mb-4 block">📚</span>
          <p className="text-gray-500">No papers yet. Add your first paper!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {papers.map(paper => (
            <div key={paper.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">{paper.title}</h4>
                  <p className="text-sm text-gray-500 mt-1">{paper.authors.join(', ')}</p>
                  {paper.journal && <p className="text-xs text-gray-400">{paper.journal} {paper.year && `(${paper.year})`}</p>}
                </div>
                <select
                  value={paper.read_status}
                  onChange={(e) => onUpdatePaper(paper.id, { read_status: e.target.value as Paper['read_status'] })}
                  className="text-xs border rounded px-2 py-1"
                >
                  <option value="unread">Unread</option>
                  <option value="reading">Reading</option>
                  <option value="read">Read</option>
                  <option value="to_revisit">To Revisit</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
