/**
 * Accession Detail Page
 * 
 * View and manage individual germplasm accession details.
 */

import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { SeedBankAccession } from '@/lib/api/seed-bank/accessions';
import { apiClient } from '@/lib/api-client';
import { Landmark, Package } from 'lucide-react';

interface AccessionDetail {
  id: string;
  accessionNumber: string;
  genus: string;
  species: string;
  subspecies?: string;
  commonName: string;
  origin: string;
  collectionDate: string;
  collectionSite: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
  vault: string;
  seedCount: number;
  viability: number;
  status: 'active' | 'depleted' | 'regenerating';
  acquisitionType: string;
  donorInstitution?: string;
  mls: boolean;
  pedigree?: string;
  notes?: string;
}

function toAccessionDetail(accession: SeedBankAccession): AccessionDetail {
  return {
    id: accession.id,
    accessionNumber: accession.accession_number,
    genus: accession.genus,
    species: accession.species,
    subspecies: accession.subspecies || undefined,
    commonName: accession.common_name || '—',
    origin: accession.origin,
    collectionDate: accession.collection_date || accession.created_at,
    collectionSite: accession.collection_site || 'Not recorded',
    latitude: accession.latitude || undefined,
    longitude: accession.longitude || undefined,
    altitude: accession.altitude || undefined,
    vault: accession.vault_id || 'Unassigned',
    seedCount: accession.seed_count,
    viability: accession.viability,
    status: accession.status,
    acquisitionType: accession.acquisition_type || 'Not recorded',
    donorInstitution: accession.donor_institution || undefined,
    mls: accession.mls,
    pedigree: accession.pedigree || undefined,
    notes: accession.notes || undefined,
  };
}

export function AccessionDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: accession, isLoading, error } = useQuery<AccessionDetail>({
    queryKey: ['seed-bank', 'accession', id],
    enabled: Boolean(id),
    queryFn: async () => toAccessionDetail(await apiClient.accessionService.getAccession(id!)),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid md:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (!accession) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-xl font-bold">{error ? 'Unable to Load Accession' : 'Accession Not Found'}</h2>
        {error instanceof Error && <p className="text-gray-600 mt-2">{error.message}</p>}
        <Link to="/seed-bank/accessions" className="text-green-600 hover:underline mt-2 inline-block">
          Back to Accessions
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'depleted': return 'bg-red-100 text-red-800';
      case 'regenerating': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">{accession.accessionNumber}</h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(accession.status)}`}>
              {accession.status}
            </span>
          </div>
          <p className="text-gray-600 mt-1 italic">
            {accession.genus} {accession.species} {accession.subspecies && `subsp. ${accession.subspecies}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/seed-bank/accessions">← Back</Link>
          </Button>
          <Button>Edit Accession</Button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Taxonomy & Origin */}
        <Card>
          <CardHeader>
            <CardTitle>🌿 Taxonomy & Origin</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoRow label="Common Name" value={accession.commonName} />
            <InfoRow label="Genus" value={accession.genus} />
            <InfoRow label="Species" value={accession.species} />
            {accession.subspecies && <InfoRow label="Subspecies" value={accession.subspecies} />}
            <InfoRow label="Country of Origin" value={accession.origin} />
            <InfoRow label="Collection Site" value={accession.collectionSite} />
            <InfoRow label="Collection Date" value={new Date(accession.collectionDate).toLocaleDateString()} />
            {accession.pedigree && <InfoRow label="Pedigree" value={accession.pedigree} />}
          </CardContent>
        </Card>

        {/* Storage & Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Landmark className="h-5 w-5" /> Storage & Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoRow label="Vault" value={accession.vault} />
            <InfoRow label="Seed Count" value={accession.seedCount.toLocaleString()} />
            <InfoRow label="Current Viability" value={`${accession.viability}%`} highlight={accession.viability < 85} />
            <InfoRow label="Acquisition Type" value={accession.acquisitionType} />
            {accession.donorInstitution && <InfoRow label="Donor Institution" value={accession.donorInstitution} />}
            <InfoRow label="MLS Status" value={accession.mls ? 'Yes - Multilateral System' : 'No'} />
          </CardContent>
        </Card>

        {/* Geographic Data */}
        {(accession.latitude || accession.longitude) && (
          <Card>
            <CardHeader>
              <CardTitle>📍 Geographic Data</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-500">Latitude</div>
                  <div className="font-mono font-medium">{accession.latitude?.toFixed(4)}°</div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-500">Longitude</div>
                  <div className="font-mono font-medium">{accession.longitude?.toFixed(4)}°</div>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-sm text-gray-500">Altitude</div>
                  <div className="font-mono font-medium">{accession.altitude}m</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Viability History */}
        <Card>
          <CardHeader>
            <CardTitle>🔬 Viability History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded border border-dashed p-4 text-sm text-gray-600">
              No viability history is available on this route yet.
            </div>
            <Button variant="outline" className="w-full mt-4">
              🔬 Schedule Viability Test
            </Button>
          </CardContent>
        </Card>

        {/* Seed Lots */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Package className="h-5 w-5" /> Seed Lots</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded border border-dashed p-4 text-sm text-gray-600">
              Seed lot details are not exposed by the current accession endpoint.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notes */}
      {accession.notes && (
        <Card>
          <CardHeader>
            <CardTitle>📝 Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700">{accession.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function InfoRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between items-center py-1 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm font-medium ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</span>
    </div>
  );
}

export default AccessionDetail;
