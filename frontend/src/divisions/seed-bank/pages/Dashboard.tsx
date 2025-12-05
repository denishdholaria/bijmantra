/**
 * Seed Bank Dashboard
 * 
 * Overview of germplasm conservation activities, vault status, and key metrics.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface DashboardStats {
  totalAccessions: number;
  activeVaults: number;
  pendingViability: number;
  scheduledRegeneration: number;
  recentExchanges: number;
  criticalAlerts: number;
}

export function Dashboard() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['seed-bank', 'dashboard-stats'],
    queryFn: async () => ({
      totalAccessions: 12450,
      activeVaults: 8,
      pendingViability: 234,
      scheduledRegeneration: 45,
      recentExchanges: 12,
      criticalAlerts: 3,
    }),
  });

  const quickActions = [
    { label: 'Register Accession', path: '/seed-bank/accessions', icon: '🌱' },
    { label: 'Viability Test', path: '/seed-bank/viability', icon: '🔬' },
    { label: 'Plan Regeneration', path: '/seed-bank/regeneration', icon: '🔄' },
    { label: 'Germplasm Exchange', path: '/seed-bank/exchange', icon: '🤝' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Seed Bank</h1>
        <p className="text-gray-600 mt-1">Genetic resources preservation and germplasm conservation</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {isLoading ? (
          Array(6).fill(0).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-4 w-24" />
              </CardContent>
            </Card>
          ))
        ) : (
          <>
            <StatCard label="Total Accessions" value={stats?.totalAccessions || 0} icon="🌾" />
            <StatCard label="Active Vaults" value={stats?.activeVaults || 0} icon="🏛️" />
            <StatCard label="Pending Viability" value={stats?.pendingViability || 0} icon="⏳" />
            <StatCard label="Regeneration Queue" value={stats?.scheduledRegeneration || 0} icon="🔄" />
            <StatCard label="Recent Exchanges" value={stats?.recentExchanges || 0} icon="🤝" />
            <StatCard label="Critical Alerts" value={stats?.criticalAlerts || 0} icon="⚠️" alert />
          </>
        )}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {quickActions.map((action) => (
              <Link
                key={action.path}
                to={action.path}
                className="flex flex-col items-center p-4 rounded-lg border border-gray-200 hover:border-green-500 hover:bg-green-50 transition-colors"
              >
                <span className="text-3xl mb-2">{action.icon}</span>
                <span className="text-sm font-medium text-gray-700">{action.label}</span>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity & Alerts */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <ActivityItem
                icon="🌱"
                title="New accession registered"
                description="ACC-2024-1234 - Triticum aestivum"
                time="2 hours ago"
              />
              <ActivityItem
                icon="🔬"
                title="Viability test completed"
                description="Batch VT-2024-089 - 98% germination"
                time="5 hours ago"
              />
              <ActivityItem
                icon="🤝"
                title="Germplasm exchange approved"
                description="EX-2024-045 to CIMMYT"
                time="1 day ago"
              />
              <ActivityItem
                icon="🔄"
                title="Regeneration completed"
                description="REG-2024-012 - 500 seeds harvested"
                time="2 days ago"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Conservation Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <AlertItem
                level="critical"
                title="Low viability detected"
                description="ACC-2019-0456 requires immediate regeneration"
              />
              <AlertItem
                level="warning"
                title="Viability test overdue"
                description="15 accessions past scheduled test date"
              />
              <AlertItem
                level="info"
                title="Storage capacity"
                description="Vault A reaching 85% capacity"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, alert }: { label: string; value: number; icon: string; alert?: boolean }) {
  return (
    <Card className={alert && value > 0 ? 'border-red-300 bg-red-50' : ''}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{icon}</span>
          <span className={`text-2xl font-bold ${alert && value > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {value.toLocaleString()}
          </span>
        </div>
        <p className="text-sm text-gray-600 mt-1">{label}</p>
      </CardContent>
    </Card>
  );
}

function ActivityItem({ icon, title, description, time }: { icon: string; title: string; description: string; time: string }) {
  return (
    <div className="flex items-start gap-3 p-2 rounded hover:bg-gray-50">
      <span className="text-xl">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500 truncate">{description}</p>
      </div>
      <span className="text-xs text-gray-400 whitespace-nowrap">{time}</span>
    </div>
  );
}

function AlertItem({ level, title, description }: { level: 'critical' | 'warning' | 'info'; title: string; description: string }) {
  const styles = {
    critical: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };
  const icons = { critical: '🚨', warning: '⚠️', info: 'ℹ️' };

  return (
    <div className={`p-3 rounded-lg border ${styles[level]}`}>
      <div className="flex items-center gap-2">
        <span>{icons[level]}</span>
        <span className="font-medium">{title}</span>
      </div>
      <p className="text-sm mt-1 opacity-80">{description}</p>
    </div>
  );
}

export default Dashboard;
