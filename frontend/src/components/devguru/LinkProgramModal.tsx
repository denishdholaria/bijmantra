import { useState } from 'react'
import { linkProgram } from '@/services/devguru'
import { BrAPIProgram } from '@/types/devguru'
import { cn } from '@/lib/utils'

interface LinkProgramModalProps {
  projectId: string
  programs: BrAPIProgram[]
  onClose: () => void
  onLinked: () => void
}

export function LinkProgramModal({ projectId, programs, onClose, onLinked }: LinkProgramModalProps) {
  const [selectedProgram, setSelectedProgram] = useState<number | null>(null)
  const [isLinking, setIsLinking] = useState(false)

  const handleLink = async () => {
    if (!selectedProgram) return
    setIsLinking(true)
    try {
      await linkProgram(projectId, selectedProgram)
      onLinked()
    } catch (error) {
      console.error('Failed to link program:', error)
    } finally {
      setIsLinking(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">🔗 Link BrAPI Program</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">✕</button>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Select a breeding program to link with your research project. This will enable experiment tracking and AI synthesis.
          </p>

          {programs.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-gray-500 dark:text-gray-400 text-sm">No programs available</p>
              <p className="text-xs text-gray-400 mt-1">Create a program in the Breeding module first</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {programs.map(program => (
                <button
                  key={program.id}
                  onClick={() => setSelectedProgram(program.id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    selectedProgram === program.id
                      ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                >
                  <p className="font-medium text-sm text-gray-900 dark:text-white">{program.program_name}</p>
                  {program.objective && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{program.objective}</p>
                  )}
                  <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">{program.trials_count || 0} trials</p>
                </button>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6">
            <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Cancel
            </button>
            <button
              onClick={handleLink}
              disabled={!selectedProgram || isLinking}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLinking ? 'Linking...' : 'Link Program'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
