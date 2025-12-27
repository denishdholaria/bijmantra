/**
 * Commercial Seed Lot Management Module
 * For Seed Companies to manage commercial lot testing data
 * 
 * Features:
 * - Lot tracking and traceability
 * - Quality testing data management
 * - Certification workflow
 * - Inventory management
 * - Customizable fields per company
 * 
 * Tech Stack: React + TypeScript + Tailwind
 * Data Source: PostgreSQL + Meilisearch
 * Compute Engine: Browser JS (lightweight operations)
 */

import { useState } from 'react'
import { PageInfoWrapper } from '@/components/ModuleInfoMark'
import { cn } from '@/lib/utils'

interface SeedLot {
  id: string
  lotNumber: string
  variety: string
  crop: string
  productionYear: number
  quantity: number
  unit: 'kg' | 'bags' | 'units'
  status: 'pending' | 'testing' | 'certified' | 'rejected' | 'released'
  location: string
  harvestDate: string
  qualityTests: QualityTest[]
  certifications: Certification[]
}

interface QualityTest {
  id: string
  testType: string
  result: number
  unit: string
  standard: number
  passed: boolean
  testDate: string
  technician: string
}

interface Certification {
  id: string
  type: string
  status: 'pending' | 'approved' | 'rejected'
  issuedDate?: string
  expiryDate?: string
  certificateNumber?: string
}

// Module info for i-mark
const moduleInfo = {
  title: 'Commercial Seed Lot Management',
  description: 'Comprehensive module for seed companies to track commercial seed lots, manage quality testing data, handle certification workflows, and maintain inventory.',
  techStack: ['React', 'TypeScript', 'PostgreSQL', 'Meilisearch', 'IndexedDB'],
  dataSource: 'PostgreSQL with offline sync via IndexedDB',
  computeEngine: 'browser',
  apiEndpoint: '/api/v2/commercial/seedlots',
  architectureNotes: 'Designed for seed company operations with full traceability. Supports offline data entry with automatic sync.'
}

export function SeedLotManagement() {
  const [selectedLot, setSelectedLot] = useState<SeedLot | null>(null)

  // Sample data
  const seedLots: SeedLot[] = [
    {
      id: '1',
      lotNumber: 'SL-2024-00847',
      variety: 'Pioneer P1234',
      crop: 'Maize',
      productionYear: 2024,
      quantity: 5000,
      unit: 'kg',
      status: 'certified',
      location: 'Warehouse A-12',
      harvestDate: '2024-10-15',
      qualityTests: [
        { id: '1', testType: 'Germination', result: 96.5, unit: '%', standard: 90, passed: true, testDate: '2024-10-20', technician: 'John D.' },
        { id: '2', testType: 'Purity', result: 99.2, unit: '%', standard: 98, passed: true, testDate: '2024-10-20', technician: 'John D.' },
        { id: '3', testType: 'Moisture', result: 12.1, unit: '%', standard: 13, passed: true, testDate: '2024-10-20', technician: 'Sarah M.' },
      ],
      certifications: [
        { id: '1', type: 'ISTA', status: 'approved', issuedDate: '2024-10-25', expiryDate: '2025-10-25', certificateNumber: 'ISTA-2024-8847' }
      ]
    },
    {
      id: '2',
      lotNumber: 'SL-2024-00923',
      variety: 'Syngenta SY-500',
      crop: 'Wheat',
      productionYear: 2024,
      quantity: 3200,
      unit: 'kg',
      status: 'testing',
      location: 'Warehouse B-05',
      harvestDate: '2024-11-01',
      qualityTests: [
        { id: '1', testType: 'Germination', result: 88.0, unit: '%', standard: 85, passed: true, testDate: '2024-11-10', technician: 'Mike R.' },
      ],
      certifications: [
        { id: '1', type: 'ISTA', status: 'pending' }
      ]
    },
    {
      id: '3',
      lotNumber: 'SL-2024-01102',
      variety: 'Bayer CropScience B-750',
      crop: 'Soybean',
      productionYear: 2024,
      quantity: 1800,
      unit: 'kg',
      status: 'pending',
      location: 'Processing Unit C',
      harvestDate: '2024-11-20',
      qualityTests: [],
      certifications: []
    }
  ]

  // Stats
  const stats = {
    totalLots: seedLots.length,
    certified: seedLots.filter(l => l.status === 'certified').length,
    testing: seedLots.filter(l => l.status === 'testing').length,
    pending: seedLots.filter(l => l.status === 'pending').length,
    totalQuantity: seedLots.reduce((sum, l) => sum + l.quantity, 0)
  }

  return (
    <PageInfoWrapper moduleInfo={moduleInfo}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Commercial Seed Lots</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage commercial seed lot inventory and certifications</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
              📤 Export
            </button>
            <button className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700">
              + New Lot
            </button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard label="Total Lots" value={stats.totalLots} />
          <StatCard label="Certified" value={stats.certified} color="green" />
          <StatCard label="In Testing" value={stats.testing} color="blue" />
          <StatCard label="Pending" value={stats.pending} color="orange" />
          <StatCard label="Total Stock" value={`${stats.totalQuantity.toLocaleString()} kg`} />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lot List */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Seed Lot Inventory</h3>
              <div className="space-y-3">
                {seedLots.map((lot) => (
                  <LotCard 
                    key={lot.id} 
                    lot={lot} 
                    selected={selectedLot?.id === lot.id}
                    onClick={() => setSelectedLot(lot)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Detail Panel */}
          <div>
            {selectedLot ? (
              <LotDetailPanel lot={selectedLot} />
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
                <span className="text-4xl mb-4 block">📦</span>
                <p className="text-sm text-gray-500 dark:text-gray-400">Select a lot to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageInfoWrapper>
  )
}

/* ============================================
   STAT CARD COMPONENT
   ============================================ */
function StatCard({ label, value, color }: { label: string; value: string | number; color?: 'green' | 'blue' | 'orange' }) {
  const colorClasses: Record<string, string> = {
    green: 'text-green-600 dark:text-green-400',
    blue: 'text-blue-600 dark:text-blue-400',
    orange: 'text-orange-600 dark:text-orange-400',
    default: 'text-gray-900 dark:text-white'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{label}</p>
      <p className={cn('text-2xl font-bold mt-1', colorClasses[color || 'default'])}>{value}</p>
    </div>
  )
}

/* ============================================
   LOT CARD COMPONENT
   ============================================ */
interface LotCardProps {
  lot: SeedLot
  selected: boolean
  onClick: () => void
}

function LotCard({ lot, selected, onClick }: LotCardProps) {
  const statusColors = {
    pending: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    testing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    certified: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    released: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400'
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-4 rounded-lg border transition-all duration-200',
        selected 
          ? 'bg-green-50 dark:bg-green-900/20 border-green-500' 
          : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-semibold text-gray-900 dark:text-white">
              {lot.lotNumber}
            </span>
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', statusColors[lot.status])}>
              {lot.status}
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{lot.variety}</p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5">{lot.crop} • {lot.productionYear}</p>
        </div>
        <div className="text-right">
          <p className="font-mono text-lg font-bold text-green-600 dark:text-green-400">
            {lot.quantity.toLocaleString()}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500">{lot.unit}</p>
        </div>
      </div>
      
      {/* Quality Progress */}
      {lot.qualityTests.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>Quality Tests</span>
            <span>{lot.qualityTests.filter(t => t.passed).length}/{lot.qualityTests.length} passed</span>
          </div>
          <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={cn(
                'h-full rounded-full transition-all',
                lot.qualityTests.every(t => t.passed) ? 'bg-green-500' : 'bg-orange-500'
              )}
              style={{ width: `${(lot.qualityTests.filter(t => t.passed).length / lot.qualityTests.length) * 100}%` }}
            />
          </div>
        </div>
      )}
    </button>
  )
}

/* ============================================
   LOT DETAIL PANEL
   ============================================ */
interface LotDetailPanelProps {
  lot: SeedLot
}

function LotDetailPanel({ lot }: LotDetailPanelProps) {
  const statusColors = {
    pending: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    testing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    certified: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    released: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
    approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  }

  return (
    <div className="space-y-4">
      {/* Basic Info */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Lot Information</h3>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Lot Number</label>
              <p className="font-mono text-sm text-gray-900 dark:text-white">{lot.lotNumber}</p>
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</label>
              <span className={cn('inline-block px-2 py-0.5 rounded text-xs font-medium mt-1', statusColors[lot.status])}>
                {lot.status}
              </span>
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Variety</label>
            <p className="text-sm text-gray-900 dark:text-white">{lot.variety}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Location</label>
              <p className="text-sm text-gray-600 dark:text-gray-300">{lot.location}</p>
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Harvest Date</label>
              <p className="text-sm text-gray-600 dark:text-gray-300">{lot.harvestDate}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quality Tests */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Quality Tests {lot.qualityTests.length > 0 && `(${lot.qualityTests.length})`}
        </h3>
        {lot.qualityTests.length > 0 ? (
          <div className="space-y-2">
            {lot.qualityTests.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-900 rounded">
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">{test.testType}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Standard: {test.standard}{test.unit}</p>
                </div>
                <div className="text-right">
                  <p className={cn('font-mono text-lg font-bold', test.passed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400')}>
                    {test.result}{test.unit}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{test.passed ? '✓ Passed' : '✗ Failed'}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">No quality tests recorded</p>
            <button className="mt-2 text-sm text-green-600 hover:text-green-700">+ Add Test</button>
          </div>
        )}
      </div>

      {/* Certifications */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Certifications</h3>
        {lot.certifications.length > 0 ? (
          <div className="space-y-2">
            {lot.certifications.map((cert) => (
              <div key={cert.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-900 rounded">
                <div>
                  <p className="text-sm text-gray-900 dark:text-white">{cert.type}</p>
                  {cert.certificateNumber && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">{cert.certificateNumber}</p>
                  )}
                </div>
                <span className={cn('px-2 py-0.5 rounded text-xs font-medium', statusColors[cert.status])}>
                  {cert.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">No certifications</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700">
          Edit Lot
        </button>
        <button className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
          Print Label
        </button>
      </div>
    </div>
  )
}

export default SeedLotManagement
