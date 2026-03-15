import { Chapter, WritingStats } from '@/types/devguru'
import { cn } from '@/lib/utils'

interface WritingTabProps {
  chapters: Chapter[]
  stats: WritingStats | undefined
  isLoading: boolean
  projectId: string | null
  onGenerateDefaults: () => Promise<void>
  onLogSession: (chapterId: string, data: { words_written: number; duration_minutes?: number; notes?: string }) => Promise<void>
}

export function WritingTab({ chapters, stats, isLoading, onGenerateDefaults }: WritingTabProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading chapters...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-purple-600">{stats.overall_progress}%</p>
            <p className="text-xs text-purple-700">Progress</p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.total_written_words.toLocaleString()}</p>
            <p className="text-xs text-blue-700">Words Written</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{stats.completed_chapters}/{stats.total_chapters}</p>
            <p className="text-xs text-green-700">Chapters Done</p>
          </div>
        </div>
      )}

      {/* Chapters */}
      {chapters.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-4xl mb-4 block">✍️</span>
          <p className="text-gray-500 mb-4">No chapters yet.</p>
          <button
            onClick={onGenerateDefaults}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm"
          >
            Generate Default Chapters
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {chapters.map(chapter => (
            <div key={chapter.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    Ch. {chapter.chapter_number}: {chapter.title}
                  </h4>
                  <p className="text-xs text-gray-500">{chapter.chapter_type}</p>
                </div>
                <span className={cn(
                  'text-xs px-2 py-1 rounded',
                  chapter.status === 'complete' ? 'bg-green-100 text-green-700' :
                  chapter.status === 'revising' ? 'bg-blue-100 text-blue-700' :
                  chapter.status === 'drafting' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                )}>
                  {chapter.status}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (chapter.current_word_count / chapter.target_word_count) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {chapter.current_word_count.toLocaleString()} / {chapter.target_word_count.toLocaleString()} words
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
