/**
 * Trials Page - List all trials
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, RefreshCw } from 'lucide-react'

export function Trials() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [deleteTrialId, setDeleteTrialId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['trials', page, search],
    queryFn: () => apiClient.trialService.getTrials(page, pageSize),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(0)
    setSearchParams(search ? { search } : {})
  }

  const deleteMutation = useMutation({
    mutationFn: (trialDbId: string) => apiClient.trialService.deleteTrial(trialDbId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trials'] })
      setDeleteTrialId(null)
    },
  })

  const trials = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl lg:rounded-2xl shadow-xl p-4 lg:p-8 text-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-4xl font-bold mb-1 lg:mb-2">Trials</h1>
            <p className="text-purple-100 text-sm lg:text-lg">Manage your breeding trials</p>
          </div>
          <Link
            to="/trials/new"
            className="px-4 lg:px-6 py-2 lg:py-3 bg-white dark:bg-slate-800 text-purple-600 dark:text-purple-400 rounded-lg font-semibold hover:bg-purple-50 dark:hover:bg-slate-700 transition-colors shadow-lg hover:shadow-xl text-sm lg:text-base whitespace-nowrap"
          >
            ➕ New Trial
          </Link>
        </div>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="Search trials by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <Button type="submit">🔍 Search</Button>
            {search && (
              <Button type="button" variant="outline" onClick={() => { setSearch(''); setSearchParams({}); }}>
                Clear
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Trials List */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading trials...</div>
        ) : error ? (
          <div className="p-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>Failed to load trials. {error instanceof Error ? error.message : 'Please try again.'}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => queryClient.invalidateQueries({ queryKey: ['trials'] })}
                  className="ml-4"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          </div>
        ) : trials.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🧪</div>
            <p className="text-gray-500 dark:text-gray-400 mb-4">No trials yet</p>
            <Link
              to="/trials/new"
              className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
            >
              Create your first trial
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-slate-700" style={{ minWidth: '640px' }}>
                <thead className="bg-gray-50 dark:bg-slate-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Trial Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Program
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Start Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      End Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-700">
                  {trials.map((trial: any) => (
                    <tr key={trial.trialDbId} className="hover:bg-gray-50 dark:hover:bg-slate-700">
                      <td className="px-6 py-4">
                        <Link
                          to={`/trials/${trial.trialDbId}`}
                          className="text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 font-medium"
                        >
                          {trial.trialName}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        {trial.programName || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {trial.startDate || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {trial.endDate || '-'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                        <Link
                          to={`/trials/${trial.trialDbId}`}
                          className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300"
                        >
                          View
                        </Link>
                        <Link
                          to={`/trials/${trial.trialDbId}/edit`}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => setDeleteTrialId(trial.trialDbId)}
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 dark:border-slate-700 flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount} trials
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

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={deleteTrialId !== null}
        onClose={() => setDeleteTrialId(null)}
        onConfirm={() => deleteTrialId && deleteMutation.mutate(deleteTrialId)}
        title="Delete Trial"
        message="Are you sure you want to delete this trial? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
