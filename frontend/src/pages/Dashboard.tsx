/**
 * Dashboard Page
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'

export function Dashboard() {
  const { data: programsData, isLoading: programsLoading } = useQuery({
    queryKey: ['programs'],
    queryFn: () => apiClient.getPrograms(0, 10),
  })

  const { data: trialsData, isLoading: trialsLoading } = useQuery({
    queryKey: ['trials'],
    queryFn: () => apiClient.getTrials(0, 10),
  })

  const { data: studiesData, isLoading: studiesLoading } = useQuery({
    queryKey: ['studies'],
    queryFn: () => apiClient.getStudies(0, 10),
  })

  const { data: locationsData, isLoading: locationsLoading } = useQuery({
    queryKey: ['locations'],
    queryFn: () => apiClient.getLocations(0, 10),
  })

  const { data: germplasmData, isLoading: germplasmLoading } = useQuery({
    queryKey: ['germplasm'],
    queryFn: () => apiClient.getGermplasm(0, 10),
  })

  const { data: traitsData, isLoading: traitsLoading } = useQuery({
    queryKey: ['variables'],
    queryFn: () => apiClient.getObservationVariables(0, 10),
  })

  const { data: observationsData, isLoading: observationsLoading } = useQuery({
    queryKey: ['observations'],
    queryFn: () => apiClient.getObservations(undefined, 0, 10),
  })

  const { data: seedlotsData, isLoading: seedlotsLoading } = useQuery({
    queryKey: ['seedlots'],
    queryFn: () => apiClient.getSeedLots(undefined, 0, 10),
  })

  const programs = programsData?.result?.data || []

  return (
    <div className="space-y-4 lg:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl lg:rounded-2xl shadow-xl p-4 lg:p-8 text-white">
        <h1 className="text-2xl lg:text-4xl font-bold mb-1 lg:mb-2">Dashboard</h1>
        <p className="text-green-100 text-sm lg:text-lg">Overview of your breeding programs and activities</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 lg:gap-4">
        <StatCard
          title="Programs"
          count={programsData?.metadata?.pagination?.totalCount || 0}
          icon="🌾"
          link="/programs"
          isLoading={programsLoading}
        />
        <StatCard
          title="Germplasm"
          count={germplasmData?.metadata?.pagination?.totalCount || 0}
          icon="🌱"
          link="/germplasm"
          isLoading={germplasmLoading}
        />
        <StatCard
          title="Trials"
          count={trialsData?.metadata?.pagination?.totalCount || 0}
          icon="🧪"
          link="/trials"
          isLoading={trialsLoading}
        />
        <StatCard
          title="Studies"
          count={studiesData?.metadata?.pagination?.totalCount || 0}
          icon="📊"
          link="/studies"
          isLoading={studiesLoading}
        />
        <StatCard
          title="Traits"
          count={traitsData?.metadata?.pagination?.totalCount || 0}
          icon="🔬"
          link="/traits"
          isLoading={traitsLoading}
        />
        <StatCard
          title="Locations"
          count={locationsData?.metadata?.pagination?.totalCount || 0}
          icon="📍"
          link="/locations"
          isLoading={locationsLoading}
        />
        <StatCard
          title="Observations"
          count={observationsData?.metadata?.pagination?.totalCount || 0}
          icon="📋"
          link="/observations"
          isLoading={observationsLoading}
        />
        <StatCard
          title="Seed Lots"
          count={seedlotsData?.metadata?.pagination?.totalCount || 0}
          icon="📦"
          link="/seedlots"
          isLoading={seedlotsLoading}
        />
      </div>

      {/* Recent Programs */}
      <div className="bg-white rounded-lg shadow p-4 lg:p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Recent Programs</h2>
          <Link
            to="/programs"
            className="text-sm text-green-600 hover:text-green-700 font-medium"
          >
            View all →
          </Link>
        </div>

        {programsLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : programs.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No programs yet</p>
            <Link
              to="/programs/new"
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Create your first program
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {programs.slice(0, 5).map((program: any) => (
              <Link
                key={program.programDbId}
                to={`/programs/${program.programDbId}`}
                className="block p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{program.programName}</h3>
                    {program.abbreviation && (
                      <span className="text-sm text-gray-500">{program.abbreviation}</span>
                    )}
                    {program.objective && (
                      <p className="text-sm text-gray-600 mt-1">{program.objective}</p>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">{program.programDbId}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-4 lg:p-6">
        <h2 className="text-lg lg:text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4">
          <QuickActionButton
            to="/programs/new"
            icon="🌾"
            label="New Program"
          />
          <QuickActionButton
            to="/germplasm/new"
            icon="🌱"
            label="New Germplasm"
          />
          <QuickActionButton
            to="/traits/new"
            icon="🔬"
            label="New Trait"
          />
          <QuickActionButton
            to="/trials/new"
            icon="🧪"
            label="New Trial"
          />
          <QuickActionButton
            to="/studies/new"
            icon="📊"
            label="New Study"
          />
          <QuickActionButton
            to="/locations/new"
            icon="📍"
            label="New Location"
          />
          <QuickActionButton
            to="/observations/collect"
            icon="📝"
            label="Collect Data"
          />
          <QuickActionButton
            to="/seedlots/new"
            icon="📦"
            label="New Seed Lot"
          />
          <QuickActionButton
            to="/crosses/new"
            icon="🧬"
            label="New Cross"
          />
          <QuickActionButton
            to="/search"
            icon="🔍"
            label="Search"
          />
          <QuickActionButton
            to="/import-export"
            icon="🔄"
            label="Import/Export"
          />
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  count,
  icon,
  link,
  isLoading,
}: {
  title: string
  count: number
  icon: string
  link: string
  isLoading: boolean
}) {
  return (
    <Link
      to={link}
      className="group bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-md p-6 hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-green-200 hover:-translate-y-1"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
          <p className="text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
            {isLoading ? (
              <span className="inline-block w-12 h-10 bg-gray-200 rounded animate-pulse"></span>
            ) : (
              count
            )}
          </p>
        </div>
        <div className="text-5xl group-hover:scale-110 transition-transform duration-300">
          {icon}
        </div>
      </div>
      <div className="mt-4 flex items-center text-sm text-green-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
        View all <span className="ml-1">→</span>
      </div>
    </Link>
  )
}

function QuickActionButton({
  to,
  icon,
  label,
}: {
  to: string
  icon: string
  label: string
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all"
    >
      <span className="text-2xl">{icon}</span>
      <span className="font-medium text-gray-700">{label}</span>
    </Link>
  )
}
