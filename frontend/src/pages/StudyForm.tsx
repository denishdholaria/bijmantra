/**
 * Study Form - Create new study
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function StudyForm() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    studyName: '',
    studyDescription: '',
    trialDbId: '',
    locationDbId: '',
    startDate: '',
    endDate: '',
    active: true,
  })

  const { data: trialsData } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.trialService.getTrials(0, 100),
  })

  const { data: locationsData } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.locationService.getLocations(0, 100),
  })

  const trials = trialsData?.result?.data || []
  const locations = locationsData?.result?.data || []

  const mutation = useMutation({
    mutationFn: (data: any) => apiClient.studyService.createStudy(data),
    onSuccess: (response) => {
      // Response is single object, not array
      const studyDbId = response.result?.studyDbId || response.result?.data?.[0]?.studyDbId
      if (studyDbId) {
        navigate(`/studies/${studyDbId}`)
      } else {
        navigate('/studies')
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
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl shadow-xl p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Create New Study</h1>
        <p className="text-blue-100 text-lg">Add a new study to your trial</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 space-y-6">
        <div>
          <label htmlFor="studyName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Study Name *
          </label>
          <input
            type="text"
            id="studyName"
            name="studyName"
            required
            value={formData.studyName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            placeholder="Enter study name"
          />
        </div>

        <div>
          <label htmlFor="studyDescription" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description
          </label>
          <textarea
            id="studyDescription"
            name="studyDescription"
            value={formData.studyDescription}
            onChange={handleChange}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
            placeholder="Enter study description"
          />
        </div>

        <div>
          <label htmlFor="trialDbId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Trial
          </label>
          <select
            id="trialDbId"
            name="trialDbId"
            value={formData.trialDbId}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">Select a trial</option>
            {trials.map((trial: any) => (
              <option key={trial.trialDbId} value={trial.trialDbId}>
                {trial.trialName}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="locationDbId" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Location
          </label>
          <select
            id="locationDbId"
            name="locationDbId"
            value={formData.locationDbId}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
          >
            <option value="">Select a location</option>
            {locations.map((location: any) => (
              <option key={location.locationDbId} value={location.locationDbId}>
                {location.locationName}
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100"
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
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-slate-600 rounded"
          />
          <label htmlFor="active" className="ml-2 block text-sm text-gray-900 dark:text-gray-100">
            Active
          </label>
        </div>

        {mutation.isError && (
          <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-sm text-red-600 dark:text-red-400">Error creating study. Please try again.</p>
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {mutation.isPending ? 'Creating...' : 'Create Study'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/studies')}
            className="px-6 py-3 border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
