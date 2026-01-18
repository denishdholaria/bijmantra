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
  viabilityHistory: { date: string; germination: number }[];
  seedLots: { id: string; lotNumber: string; quantity: number; date: string }[];
}

export function AccessionDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: accession, isLoading } = useQuery<AccessionDetail>({
    queryKey: ['seed-bank', 'accession', id],
    queryFn: async () => ({
      id: id!,
      accessionNumber: 'ACC-2024-0001',
      genus: 'Triticum',
      species: 'aestivum',
      subspecies: 'aestivum',
      commonName: 'Bread Wheat',
      origin: 'India',
      collectionDate: '2024-03-15',
      collectionSite: 'Punjab Agricultural University, Ludhiana',
      latitude: 30.9010,
      longitude: 75.8573,
      altitude: 247,
      vault: 'Base Collection A',
      seedCount: 5000,
      viability: 98,
      status: 'active',
      acquisitionType: 'Collection',
      donorInstitution: 'PAU Ludhiana',
      mls: true,
      pedigree: 'HD2967 / PBW343',
      notes: 'High yielding variety with good disease resistance',
      viabilityHistory: [
        { date: '2024-03-20', germination: 98 },
        { date: '2023-09-15', germination: 99 },
        { date: '2023-03-10', germination: 99 },
      ],
      seedLots: [
        { id: 'SL001', lotNumber: 'SL-2024-0001', quantity: 3000, date: '2024-03-15' },
        { id: 'SL002', lotNumber: 'SL-2023-0456', quantity: 2000, date: '2023-09-01' },
      ],
    }),
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
        <h2 className="text-xl font-bold">Accession Not Found</h2>
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
            <CardTitle>🏛️ Storage & Status</CardTitle>
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
            <div className="space-y-2">
              {accession.viabilityHistory.map((test, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-600">{new Date(test.date).toLocaleDateString()}</span>
                  <span className={`font-medium ${test.germination >= 85 ? 'text-green-600' : test.germination >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {test.germination}% germination
                  </span>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              🔬 Schedule Viability Test
            </Button>
          </CardContent>
        </Card>

        {/* Seed Lots */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>📦 Seed Lots</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Lot Number</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date Added</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {accession.seedLots.map((lot) => (
                  <tr key={lot.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{lot.lotNumber}</td>
                    <td className="px-4 py-3 text-right font-mono">{lot.quantity.toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600">{new Date(lot.date).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
