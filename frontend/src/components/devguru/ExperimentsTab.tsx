import { useState } from 'react'
import { Experiment } from '@/types/devguru'
import { cn } from '@/lib/utils'

interface ExperimentsTabProps {
  experiments: Experiment[]
  isLoading: boolean
  hasLinkedProgram: boolean
  onLinkProgram: () => void
}

export function ExperimentsTab({ experiments, isLoading, hasLinkedProgram, onLinkProgram }: ExperimentsTabProps) {
  const [expandedTrial, setExpandedTrial] = useState<number | null>(null)

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-sm text-gray-500">Loading experiments...</p>
        </div>
      </div>
    )
  }

  if (!hasLinkedProgram) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">🔗</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Link a BrAPI Program</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Connect your research project to a BrAPI Program to track experiments (trials) and studies.
            This enables DevGuru to synthesize insights across your experimental data.
          </p>
          <button
            onClick={onLinkProgram}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700"
          >
            Link Program
          </button>
        </div>
      </div>
    )
  }

  if (experiments.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <span className="text-4xl mb-4 block">🧪</span>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Experiments Yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Your linked program doesn't have any trials yet. Create trials in the Breeding module to see them here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="space-y-3">
        {experiments.map(exp => (
          <div key={exp.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedTrial(expandedTrial === exp.id ? null : exp.id)}
              className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <div className="flex items-center gap-3">
                <span className={cn(
                  'w-2 h-2 rounded-full',
                  exp.active ? 'bg-green-500' : 'bg-gray-400'
                )} />
                <div className="text-left">
                  <p className="font-medium text-sm text-gray-900 dark:text-white">{exp.trial_name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{exp.trial_type || 'Trial'} • {exp.studies_count} studies</p>
                </div>
              </div>
              <span className="text-gray-400">{expandedTrial === exp.id ? '▼' : '▶'}</span>
            </button>

            {expandedTrial === exp.id && (
              <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
                {exp.trial_description && (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{exp.trial_description}</p>
                )}
                <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400 mb-3">
                  {exp.start_date && <span>Start: {exp.start_date}</span>}
                  {exp.end_date && <span>End: {exp.end_date}</span>}
                </div>

                {exp.studies.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">Studies:</p>
                    {exp.studies.map(study => (
                      <div key={study.id} className="flex items-center gap-2 pl-4 py-1">
                        <span className={cn(
                          'w-1.5 h-1.5 rounded-full',
                          study.active ? 'bg-blue-500' : 'bg-gray-400'
                        )} />
                        <span className="text-sm text-gray-600 dark:text-gray-300">{study.study_name}</span>
                        <span className="text-xs text-gray-400">({study.study_type || 'Study'})</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400 italic">No studies in this trial</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
