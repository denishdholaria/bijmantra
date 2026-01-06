/**
 * Location Form - Create new location
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function LocationForm() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    locationName: '',
    locationType: '',
    countryName: '',
    countryCode: '',
    latitude: '',
    longitude: '',
    altitude: '',
  })

  const mutation = useMutation({
    mutationFn: (data: any) => apiClient.createLocation(data),
    onSuccess: (response) => {
      const locationDbId = response.result?.data?.[0]?.locationDbId
      if (locationDbId) {
        navigate(`/locations/${locationDbId}`)
      } else {
        navigate('/locations')
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const locationData: any = {
      locationName: formData.locationName,
      locationType: formData.locationType || undefined,
      countryName: formData.countryName || undefined,
      countryCode: formData.countryCode || undefined,
    }

    if (formData.latitude && formData.longitude) {
      locationData.coordinates = {
        geometry: {
          type: 'Point',
          coordinates: [parseFloat(formData.longitude), parseFloat(formData.latitude)]
        },
        type: 'Feature'
      }
    }

    if (formData.altitude) {
      locationData.altitude = parseFloat(formData.altitude)
    }

    mutation.mutate([locationData])
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div className="bg-gradient-to-r from-orange-600 to-red-600 rounded-2xl shadow-xl p-8 text-white">
        <h1 className="text-4xl font-bold mb-2">Create New Location</h1>
        <p className="text-orange-100 text-lg">Add a new field location</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        <div>
          <label htmlFor="locationName" className="block text-sm font-medium text-gray-700 mb-2">
            Location Name *
          </label>
          <input
            type="text"
            id="locationName"
            name="locationName"
            required
            value={formData.locationName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
            placeholder="Enter location name"
          />
        </div>

        <div>
          <label htmlFor="locationType" className="block text-sm font-medium text-gray-700 mb-2">
            Location Type
          </label>
          <select
            id="locationType"
            name="locationType"
            value={formData.locationType}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
          >
            <option value="">Select type</option>
            <option value="Field">Field</option>
            <option value="Greenhouse">Greenhouse</option>
            <option value="Laboratory">Laboratory</option>
            <option value="Storage">Storage</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="countryName" className="block text-sm font-medium text-gray-700 mb-2">
              Country Name
            </label>
            <input
              type="text"
              id="countryName"
              name="countryName"
              value={formData.countryName}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
              placeholder="e.g., United States"
            />
          </div>

          <div>
            <label htmlFor="countryCode" className="block text-sm font-medium text-gray-700 mb-2">
              Country Code
            </label>
            <input
              type="text"
              id="countryCode"
              name="countryCode"
              value={formData.countryCode}
              onChange={handleChange}
              maxLength={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
              placeholder="e.g., USA"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label htmlFor="latitude" className="block text-sm font-medium text-gray-700 mb-2">
              Latitude
            </label>
            <input
              type="number"
              step="any"
              id="latitude"
              name="latitude"
              value={formData.latitude}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
              placeholder="e.g., 40.7128"
            />
          </div>

          <div>
            <label htmlFor="longitude" className="block text-sm font-medium text-gray-700 mb-2">
              Longitude
            </label>
            <input
              type="number"
              step="any"
              id="longitude"
              name="longitude"
              value={formData.longitude}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
              placeholder="e.g., -74.0060"
            />
          </div>

          <div>
            <label htmlFor="altitude" className="block text-sm font-medium text-gray-700 mb-2">
              Altitude (m)
            </label>
            <input
              type="number"
              step="any"
              id="altitude"
              name="altitude"
              value={formData.altitude}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white text-gray-900"
              placeholder="e.g., 10"
            />
          </div>
        </div>

        {mutation.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">Error creating location. Please try again.</p>
          </div>
        )}

        <div className="flex gap-4">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 px-6 py-3 bg-orange-600 text-white rounded-lg font-semibold hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {mutation.isPending ? 'Creating...' : 'Create Location'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/locations')}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
