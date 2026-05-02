/**
 * Conservation Page
 *
 * Monitor live diversity coverage and conservation signals from seed-bank accessions.
 */

import { useMemo, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import type { SeedBankAccession, SeedBankAccessionListResponse } from '@/lib/api/seed-bank/accessions';
import { TrendingDown } from 'lucide-react';

interface ConservationMetric {
  label: string;
  value: number;
  icon: ReactNode;
  tone?: 'default' | 'warning' | 'danger';
}

interface PriorityAccession {
  accession: SeedBankAccession;
  signal: string;
  recommendedAction: string;
  score: number;
}

interface DistributionItem {
  label: string;
  count: number;
}

export function Conservation() {
  const { data: accessionResponse, isLoading } = useQuery<SeedBankAccessionListResponse>({
    queryKey: ['seed-bank', 'accessions', 'conservation'],
    queryFn: () => apiClient.accessionService.getAccessions(0, 100),
  });

  const accessions = accessionResponse?.data || [];

  const metrics = useMemo<ConservationMetric[]>(() => {
    const uniqueGenera = new Set(accessions.map(accession => accession.genus).filter(Boolean));
    const uniqueSpecies = new Set(
      accessions.map(accession => `${accession.genus} ${accession.species}`.trim()).filter(Boolean),
    );
    const uniqueOrigins = new Set(accessions.map(accession => accession.origin).filter(Boolean));
    const lowViabilityCount = accessions.filter(accession => accession.viability < 70).length;
    const depletedCount = accessions.filter(accession => accession.status === 'depleted' || accession.seed_count <= 0).length;
    const regeneratingCount = accessions.filter(accession => accession.status === 'regenerating').length;

    return [
      { icon: '🌿', label: 'Genera', value: uniqueGenera.size },
      { icon: '🌱', label: 'Species', value: uniqueSpecies.size },
      { icon: '🌍', label: 'Origins', value: uniqueOrigins.size },
      { icon: '⚠️', label: 'Low Viability', value: lowViabilityCount, tone: lowViabilityCount > 0 ? 'warning' : 'default' },
      { icon: <TrendingDown className="h-6 w-6 text-red-500" />, label: 'Depleted', value: depletedCount, tone: depletedCount > 0 ? 'danger' : 'default' },
      { icon: '🔄', label: 'Regenerating', value: regeneratingCount },
    ];
  }, [accessions]);

  const priorityAccessions = useMemo<PriorityAccession[]>(() => accessions
    .map(accession => {
      const issues: string[] = [];
      let score = 0;

      if (accession.status === 'depleted' || accession.seed_count <= 0) {
        issues.push('Depleted inventory');
        score += 5;
      }

      if (accession.viability < 50) {
        issues.push('Critical viability');
        score += 4;
      } else if (accession.viability < 70) {
        issues.push('Low viability');
        score += 3;
      }

      if (accession.seed_count > 0 && accession.seed_count < 500) {
        issues.push('Low seed count');
        score += 2;
      }

      if (accession.status === 'regenerating') {
        issues.push('Regeneration in progress');
        score += 1;
      }

      if (issues.length === 0) {
        return null;
      }

      let recommendedAction = 'Monitor accession';
      if (accession.status === 'depleted' || accession.seed_count <= 0) {
        recommendedAction = 'Replenish or recollect stock';
      } else if (accession.viability < 70) {
        recommendedAction = 'Schedule regeneration';
      } else if (accession.seed_count < 500) {
        recommendedAction = 'Plan inventory increase';
      }

      return {
        accession,
        signal: issues.join(' • '),
        recommendedAction,
        score,
      };
    })
    .filter((item): item is PriorityAccession => item !== null)
    .sort((left, right) => right.score - left.score || left.accession.accession_number.localeCompare(right.accession.accession_number))
    .slice(0, 8), [accessions]);

  const originDistribution = useMemo<DistributionItem[]>(() => {
    const counts = new Map<string, number>();
    for (const accession of accessions) {
      const label = accession.origin || 'Unknown';
      counts.set(label, (counts.get(label) || 0) + 1);
    }

    return [...counts.entries()]
      .map(([label, count]) => ({ label, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 5);
  }, [accessions]);

  const statusDistribution = useMemo<DistributionItem[]>(() => {
    const counts = new Map<string, number>();
    for (const accession of accessions) {
      const label = accession.status;
      counts.set(label, (counts.get(label) || 0) + 1);
    }

    return [...counts.entries()]
      .map(([label, count]) => ({ label, count }))
      .sort((left, right) => right.count - left.count);
  }, [accessions]);

  const lowViabilityCount = accessions.filter(accession => accession.viability < 70).length;
  const lowInventoryCount = accessions.filter(accession => accession.seed_count > 0 && accession.seed_count < 500).length;
  const averageViability = accessions.length > 0
    ? Math.round(accessions.reduce((sum, accession) => sum + accession.viability, 0) / accessions.length)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Conservation</h1>
        <p className="text-gray-600 mt-1">Monitor live diversity coverage and conservation signals from seed-bank accessions</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {metrics.map(metric => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conservation Priorities</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading conservation signals...</div>
          ) : priorityAccessions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No accessions currently require conservation action based on live viability, inventory, or status thresholds.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Accession</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Viability</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Seed Count</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Signal</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {priorityAccessions.map(({ accession, signal, recommendedAction }) => (
                    <tr key={accession.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-sm text-green-600">{accession.accession_number}</td>
                      <td className="px-4 py-3 italic text-gray-700">{accession.genus} {accession.species}</td>
                      <td className="px-4 py-3 text-right font-medium">{accession.viability}%</td>
                      <td className="px-4 py-3 text-right font-mono text-sm">{accession.seed_count}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{signal}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{recommendedAction}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Origins</CardTitle>
          </CardHeader>
          <CardContent>
            {originDistribution.length === 0 ? (
              <div className="text-sm text-gray-500">No origin data is available yet.</div>
            ) : (
              <div className="space-y-3">
                {originDistribution.map(item => (
                  <DistributionBar key={item.label} label={item.label} count={item.count} total={accessions.length} color="green" />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Accession Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {statusDistribution.length === 0 ? (
              <div className="text-sm text-gray-500">No accession status data is available yet.</div>
            ) : (
              <div className="space-y-3">
                {statusDistribution.map(item => (
                  <DistributionBar key={item.label} label={item.label} count={item.count} total={accessions.length} color={getStatusColor(item.label)} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conservation Signals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <SignalCard
              title="Average Viability"
              value={`${averageViability}%`}
              description="Mean viability across live accessions in this organization"
              tone="green"
            />
            <SignalCard
              title="Low Inventory"
              value={lowInventoryCount.toString()}
              description="Accessions below 500 seeds and still holding stock"
              tone="amber"
            />
            <SignalCard
              title="Priority Viability"
              value={lowViabilityCount.toString()}
              description="Accessions below 70% viability needing closer review"
              tone="red"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ icon, label, value, tone = 'default' }: ConservationMetric) {
  const toneClasses: Record<NonNullable<ConservationMetric['tone']>, string> = {
    default: '',
    warning: 'border-amber-200 bg-amber-50',
    danger: 'border-red-200 bg-red-50',
  };

  const valueClasses: Record<NonNullable<ConservationMetric['tone']>, string> = {
    default: '',
    warning: 'text-amber-700',
    danger: 'text-red-600',
  };

  return (
    <Card className={toneClasses[tone]}>
      <CardContent className="p-4 text-center">
        <span className="text-2xl inline-flex justify-center items-center">{icon}</span>
        <div className={`mt-1 text-2xl font-bold ${valueClasses[tone]}`}>{value.toLocaleString()}</div>
        <div className="text-xs text-gray-500">{label}</div>
      </CardContent>
    </Card>
  );
}

function DistributionBar({ label, count, total, color }: { label: string; count: number; total: number; color: 'green' | 'amber' | 'blue' | 'gray' }) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
  const colors: Record<'green' | 'amber' | 'blue' | 'gray', string> = {
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
    gray: 'bg-gray-500',
  };

  return (
    <div>
      <div className="mb-1 flex justify-between gap-4 text-sm">
        <span className="truncate font-medium">{label}</span>
        <span className="shrink-0 text-gray-500">{count.toLocaleString()} ({percentage}%)</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${colors[color]}`} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

function SignalCard({ title, value, description, tone }: { title: string; value: string; description: string; tone: 'green' | 'amber' | 'red' }) {
  const toneClasses: Record<'green' | 'amber' | 'red', string> = {
    green: 'bg-green-50 text-green-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-700',
  };

  return (
    <div className={`rounded-lg p-4 text-center ${toneClasses[tone]}`}>
      <div className="text-3xl font-bold">{value}</div>
      <div className="mt-1 text-sm font-medium">{title}</div>
      <div className="mt-2 text-xs text-gray-600">{description}</div>
    </div>
  );
}

function getStatusColor(status: string): 'green' | 'amber' | 'blue' | 'gray' {
  switch (status) {
    case 'active':
      return 'green';
    case 'regenerating':
      return 'blue';
    case 'depleted':
      return 'amber';
    default:
      return 'gray';
  }
}

export default Conservation;
