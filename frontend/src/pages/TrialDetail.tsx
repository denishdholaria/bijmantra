/**
 * Trial Detail Page
 */

import { useQuery } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'

export function TrialDetail() {
  const { trialDbId } = useParams<{ trialDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['trial', trialDbId],
    queryFn: () => apiClient.getTrial(trialDbId!),
    enabled: !!trialDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteTrial(trialDbId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trials'] })
      navigate('/trials')
    },
  })

  const trial = data?.result

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading trial details...</div>
      </div>
    )
  }

  if (error || !trial) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500">Error loading trial details</div>
        <Link to="/trials" className="text-purple-600 hover:text-purple-800 mt-4 inline-block">
          ← Back to Trials
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl shadow-xl p-8 text-white">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Link to="/trials" className="text-purple-100 hover:text-white mb-2 inline-block">
              ← Back to Trials
            </Link>
            <h1 className="text-4xl font-bold mb-2">{trial.trialName}</h1>
            <p className="text-purple-100 text-lg">Trial Details</p>
          </div>
          <div className="flex gap-3">
            <Link
              to={`/trials/${trialDbId}/edit`}
              className="px-6 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-colors shadow-lg"
            >
              ✏️ Edit
            </Link>
            <button
              onClick={() => setShowDeleteDialog(true)}
              className="px-6 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors shadow-lg"
            >
              🗑️ Delete
            </button>
          </div>
        </div>
      </div>

      {/* Trial Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Trial Information</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <dt className="text-sm font-medium text-gray-500">Trial ID</dt>
            <dd className="mt-1 text-sm text-gray-900">{trial.trialDbId}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Trial Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{trial.trialName}</dd>
          </div>
          {trial.trialDescription && (
            <div className="md:col-span-2">
              <dt className="text-sm font-medium text-gray-500">Description</dt>
              <dd className="mt-1 text-sm text-gray-900">{trial.trialDescription}</dd>
            </div>
          )}
          {trial.programName && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Program</dt>
              <dd className="mt-1 text-sm text-gray-900">{trial.programName}</dd>
            </div>
          )}
          {trial.programDbId && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Program ID</dt>
              <dd className="mt-1 text-sm text-gray-900">
                <Link to={`/programs/${trial.programDbId}`} className="text-purple-600 hover:text-purple-800">
                  {trial.programDbId}
                </Link>
              </dd>
            </div>
          )}
          {trial.startDate && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Start Date</dt>
              <dd className="mt-1 text-sm text-gray-900">{trial.startDate}</dd>
            </div>
          )}
          {trial.endDate && (
            <div>
              <dt className="text-sm font-medium text-gray-500">End Date</dt>
              <dd className="mt-1 text-sm text-gray-900">{trial.endDate}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1">
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                trial.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {trial.active ? 'Active' : 'Inactive'}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      {/* Additional Info */}
      {trial.additionalInfo && Object.keys(trial.additionalInfo).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Additional Information</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(trial.additionalInfo).map(([key, value]) => (
              <div key={key}>
                <dt className="text-sm font-medium text-gray-500">{key}</dt>
                <dd className="mt-1 text-sm text-gray-900">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Trial"
        message="Are you sure you want to delete this trial? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
