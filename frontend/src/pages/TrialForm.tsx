/**
 * Trial Form - Create new trial
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function TrialForm() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    trialName: '',
    trialDescription: '',
    programDbId: '',
    startDate: '',
    endDate: '',
    active: true,
  })

  const { data: programsData } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.getPrograms(0, 100),
  })

  const programs = programsData?.result?.data || []

  const mutation = useMutation({
    mutationFn: (data: any) => apiClient.createTrial(data),
    onSuccess: (response) => {
      // Response is single object, not array
      const trialDbId = response.result?.trialDbId || response.result?.data?.[0]?.trialDbId
      if (trialDbId) {
        navigate(`/trials/${trialDbId}`)
      } else {
        navigate('/trials')
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }))
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl shadow-xl p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Create New Trial</h1>
        <p className="text-purple-100 text-lg">Add a new breeding trial to your program</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 space-y-6">
        <div>
          <label htmlFor="trialName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Trial Name *
          </label>
          <input
            type="text"
            id="trialName"
            name="trialName"
            required
            value={formData.trialName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            placeholder="Enter trial name"
          />
        </div>

        <div>
          <label htmlFor="trialDescription" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description
          </label>
          <textarea
            id="trialDescription"
            name="trialDescription"
            value={formData.trialDescription}
            onChange={handleChange}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            placeholder="Enter trial description"
          />
        </div>

        <div>
          <label htmlFor="programDbId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Program
          </label>
          <select
            id="programDbId"
            name="programDbId"
            value={formData.programDbId}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">Select a program</option>
            {programs.map((program: any) => (
              <option key={program.programDbId} value={program.programDbId}>
                {program.programName}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Start Date
            </label>
            <input
              type="date"
              id="startDate"
              name="startDate"
              value={formData.startDate}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              End Date
            </label>
            <input
              type="date"
              id="endDate"
              name="endDate"
              value={formData.endDate}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            />
          </div>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="active"
            name="active"
            checked={formData.active}
            onChange={handleChange}
            className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 dark:border-slate-600 rounded"
          />
          <label htmlFor="active" className="ml-2 block text-sm text-gray-900 dark:text-gray-100">
            Active
          </label>
        </div>

        {mutation.isError && (
          <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-sm text-red-600 dark:text-red-400">
              Error creating trial. Please try again.
            </p>
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {mutation.isPending ? 'Creating...' : 'Create Trial'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/trials')}
            className="px-6 py-3 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
