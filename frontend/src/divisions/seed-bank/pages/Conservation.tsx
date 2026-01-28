/**
 * Conservation Page
 * 
 * Monitor conservation status and manage preservation activities.
 */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ConservationMetrics {
  totalGenera: number;
  totalSpecies: number;
  endangeredSpecies: number;
  uniqueOrigins: number;
  duplicatedAccessions: number;
  safetyDuplicates: number;
}

export function Conservation() {
  const { data: metrics } = useQuery<ConservationMetrics>({
    queryKey: ['seed-bank', 'conservation-metrics'],
    queryFn: async () => ({
      totalGenera: 156,
      totalSpecies: 892,
      endangeredSpecies: 45,
      uniqueOrigins: 78,
      duplicatedAccessions: 8500,
      safetyDuplicates: 3200,
    }),
  });

  const conservationPriorities = [
    { species: 'Oryza rufipogon', status: 'Endangered', accessions: 12, action: 'Regeneration needed' },
    { species: 'Triticum dicoccoides', status: 'Vulnerable', accessions: 28, action: 'Safety duplication' },
    { species: 'Zea diploperennis', status: 'Endangered', accessions: 5, action: 'Collection expansion' },
    { species: 'Solanum phureja', status: 'Near Threatened', accessions: 34, action: 'Viability testing' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Conservation</h1>
        <p className="text-gray-600 mt-1">Monitor genetic diversity and conservation priorities</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard icon="🌿" label="Genera" value={metrics?.totalGenera || 0} />
        <MetricCard icon="🌱" label="Species" value={metrics?.totalSpecies || 0} />
        <MetricCard icon="⚠️" label="Endangered" value={metrics?.endangeredSpecies || 0} alert />
        <MetricCard icon="🌍" label="Origins" value={metrics?.uniqueOrigins || 0} />
        <MetricCard icon="📦" label="Duplicated" value={metrics?.duplicatedAccessions || 0} />
        <MetricCard icon="🔒" label="Safety Copies" value={metrics?.safetyDuplicates || 0} />
      </div>

      {/* Conservation Priorities */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>🎯 Conservation Priorities</CardTitle>
          <Button variant="outline" size="sm">View All</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">IUCN Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Accessions</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommended Action</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {conservationPriorities.map((item, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-3 italic text-gray-700">{item.species}</td>
                    <td className="px-4 py-3 text-center">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono">{item.accessions}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{item.action}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="outline" size="sm">Plan</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Diversity Analysis */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>🌍 Geographic Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <CoverageBar region="Asia" percentage={35} count={4350} />
              <CoverageBar region="Africa" percentage={22} count={2740} />
              <CoverageBar region="Americas" percentage={20} count={2490} />
              <CoverageBar region="Europe" percentage={15} count={1870} />
              <CoverageBar region="Oceania" percentage={8} count={1000} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>🧬 Crop Group Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <CoverageBar region="Cereals" percentage={40} count={4980} color="amber" />
              <CoverageBar region="Legumes" percentage={25} count={3110} color="green" />
              <CoverageBar region="Vegetables" percentage={18} count={2240} color="emerald" />
              <CoverageBar region="Fruits" percentage={10} count={1245} color="orange" />
              <CoverageBar region="Others" percentage={7} count={875} color="gray" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Safety Duplication */}
      <Card>
        <CardHeader>
          <CardTitle>🔒 Safety Duplication Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">68%</div>
              <div className="text-sm text-gray-600 mt-1">Duplicated at Partner Sites</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">3,200</div>
              <div className="text-sm text-gray-600 mt-1">Samples at Svalbard</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl font-bold text-yellow-600">4,050</div>
              <div className="text-sm text-gray-600 mt-1">Pending Duplication</div>
            </div>
          </div>
          <Button className="w-full mt-4">📋 Generate Duplication Plan</Button>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ icon, label, value, alert }: { icon: string; label: string; value: number; alert?: boolean }) {
  return (
    <Card className={alert && value > 0 ? 'border-red-200 bg-red-50' : ''}>
      <CardContent className="p-4 text-center">
        <span className="text-2xl">{icon}</span>
        <div className={`text-2xl font-bold mt-1 ${alert && value > 0 ? 'text-red-600' : ''}`}>
          {value.toLocaleString()}
        </div>
        <div className="text-xs text-gray-500">{label}</div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    'Endangered': 'bg-red-100 text-red-800',
    'Vulnerable': 'bg-orange-100 text-orange-800',
    'Near Threatened': 'bg-yellow-100 text-yellow-800',
    'Least Concern': 'bg-green-100 text-green-800',
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
}

function CoverageBar({ region, percentage, count, color = 'green' }: { region: string; percentage: number; count: number; color?: string }) {
  const colors: Record<string, string> = {
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    emerald: 'bg-emerald-500',
    orange: 'bg-orange-500',
    gray: 'bg-gray-500',
  };
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{region}</span>
        <span className="text-gray-500">{count.toLocaleString()} ({percentage}%)</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${colors[color]} rounded-full`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

export default Conservation;
