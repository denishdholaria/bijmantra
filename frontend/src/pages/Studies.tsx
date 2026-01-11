/**
 * Studies Page - List all studies
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'

export function Studies() {
  const [page, setPage] = useState(0)
  const [deleteStudyId, setDeleteStudyId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['studies', page],
    queryFn: () => apiClient.getStudies(page, pageSize),
  })

  const deleteMutation = useMutation({
    mutationFn: (studyDbId: string) => apiClient.deleteStudy(studyDbId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      setDeleteStudyId(null)
    },
  })

  const studies = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl lg:rounded-2xl shadow-xl p-4 lg:p-8 text-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-4xl font-bold mb-1 lg:mb-2">Studies</h1>
            <p className="text-blue-100 text-sm lg:text-lg">Manage your breeding studies</p>
          </div>
          <Link
            to="/studies/new"
            className="px-4 lg:px-6 py-2 lg:py-3 bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 rounded-lg font-semibold hover:bg-blue-50 dark:hover:bg-slate-700 transition-colors shadow-lg hover:shadow-xl text-sm lg:text-base whitespace-nowrap"
          >
            ➕ New Study
          </Link>
        </div>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading studies...</div>
        ) : error ? (
          <div className="text-center py-12 text-red-500 dark:text-red-400">Error loading studies</div>
        ) : studies.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📊</div>
            <p className="text-gray-500 dark:text-gray-400 mb-4">No studies yet</p>
            <Link
              to="/studies/new"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create your first study
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-slate-700" style={{ minWidth: '640px' }}>
                <thead className="bg-gray-50 dark:bg-slate-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Study Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Trial
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Season
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-700">
                  {studies.map((study: any) => (
                    <tr key={study.studyDbId} className="hover:bg-gray-50 dark:hover:bg-slate-700">
                      <td className="px-6 py-4">
                        <Link
                          to={`/studies/${study.studyDbId}`}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
                        >
                          {study.studyName}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        {study.trialName || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        {study.locationName || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {study.seasons?.join(', ') || '-'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                        <Link
                          to={`/studies/${study.studyDbId}`}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                        >
                          View
                        </Link>
                        <Link
                          to={`/studies/${study.studyDbId}/edit`}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => setDeleteStudyId(study.studyDbId)}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700 flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount} studies
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="px-3 py-1 border border-gray-300 dark:border-slate-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-slate-700 dark:text-gray-200"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-3 py-1 border border-gray-300 dark:border-slate-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-slate-700 dark:text-gray-200"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <ConfirmDialog
        isOpen={deleteStudyId !== null}
        onClose={() => setDeleteStudyId(null)}
        onConfirm={() => deleteStudyId && deleteMutation.mutate(deleteStudyId)}
        title="Delete Study"
        message="Are you sure you want to delete this study? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
