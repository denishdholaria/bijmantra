/**
 * Locations Page - List all locations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'

export function Locations() {
  const [page, setPage] = useState(0)
  const [deleteLocationId, setDeleteLocationId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['locations', page],
    queryFn: () => apiClient.getLocations(page, pageSize),
  })

  const deleteMutation = useMutation({
    mutationFn: (locationDbId: string) => apiClient.deleteLocation(locationDbId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      setDeleteLocationId(null)
    },
  })

  const locations = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="bg-gradient-to-r from-orange-600 to-red-600 rounded-xl lg:rounded-2xl shadow-xl p-4 lg:p-8 text-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-4xl font-bold mb-1 lg:mb-2">Locations</h1>
            <p className="text-orange-100 text-sm lg:text-lg">Manage your field locations</p>
          </div>
          <Link
            to="/locations/new"
            className="px-4 lg:px-6 py-2 lg:py-3 bg-white text-orange-600 rounded-lg font-semibold hover:bg-orange-50 transition-colors shadow-lg hover:shadow-xl text-sm lg:text-base whitespace-nowrap"
          >
            ➕ New Location
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading locations...</div>
        ) : error ? (
          <div className="text-center py-12 text-red-500">Error loading locations</div>
        ) : locations.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📍</div>
            <p className="text-gray-500 mb-4">No locations yet</p>
            <Link
              to="/locations/new"
              className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
            >
              Create your first location
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '640px' }}>
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Country
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Coordinates
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {locations.map((location: any) => (
                    <tr key={location.locationDbId} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <Link
                          to={`/locations/${location.locationDbId}`}
                          className="text-orange-600 hover:text-orange-800 font-medium"
                        >
                          {location.locationName}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {location.locationType || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {location.countryName || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {location.coordinates?.geometry?.coordinates ? 
                          `${location.coordinates.geometry.coordinates[1]}, ${location.coordinates.geometry.coordinates[0]}` : '-'}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                        <Link
                          to={`/locations/${location.locationDbId}`}
                          className="text-orange-600 hover:text-orange-900"
                        >
                          View
                        </Link>
                        <Link
                          to={`/locations/${location.locationDbId}/edit`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => setDeleteLocationId(location.locationDbId)}
                          className="text-red-600 hover:text-red-900"
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
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount} locations
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
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
        isOpen={deleteLocationId !== null}
        onClose={() => setDeleteLocationId(null)}
        onConfirm={() => deleteLocationId && deleteMutation.mutate(deleteLocationId)}
        title="Delete Location"
        message="Are you sure you want to delete this location? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
