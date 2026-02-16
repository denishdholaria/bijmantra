/**
 * Seed Bank Dashboard
 * 
 * Overview of germplasm conservation activities, vault status, and key metrics.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api-client';
import { 
  Sprout, 
  Warehouse, 
  Clock, 
  RefreshCw, 
  FlaskConical, 
  FileText, 
  Handshake,
  AlertTriangle,
  AlertCircle,
  Info,
  Activity
} from 'lucide-react';
import { VaultSensorWidget } from '@/components/VaultSensorWidget';
import { useNavigate } from 'react-router-dom';

interface DashboardStats {
  total_accessions: number;
  active_vaults: number;
  pending_viability: number;
  scheduled_regeneration: number;
}

export function Dashboard() {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['seed-bank', 'dashboard-stats'],
    queryFn: async () => {
      const summary = await apiClient.inventoryService.getSummary();
      return {
        total_accessions: summary.total_lots,
        active_vaults: 4, // Mocked for now
        pending_viability: summary.lots_needing_test,
        scheduled_regeneration: 0 // Mocked for now
      };
    },
  });

  const quickActions = [
    { label: 'Register Accession', path: '/seed-bank/accessions/new', icon: Sprout, color: 'text-green-600 bg-green-100' },
    { label: 'Viability Test', path: '/seed-bank/viability', icon: FlaskConical, color: 'text-purple-600 bg-purple-100' },
    { label: 'MCPD Exchange', path: '/seed-bank/mcpd', icon: FileText, color: 'text-blue-600 bg-blue-100' },
    { label: 'Germplasm Exchange', path: '/seed-bank/exchange', icon: Handshake, color: 'text-amber-600 bg-amber-100' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">Seed Bank</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Genetic resources preservation and germplasm conservation</p>
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
            <StatCard label="Total Accessions" value={stats?.total_accessions || 0} icon={Sprout} color="text-green-600 bg-green-100" />
            <StatCard label="Active Vaults" value={stats?.active_vaults || 0} icon={Warehouse} color="text-blue-600 bg-blue-100" />
            <StatCard label="Pending Viability" value={stats?.pending_viability || 0} icon={Clock} color="text-amber-600 bg-amber-100" />
            <StatCard label="Regeneration Queue" value={stats?.scheduled_regeneration || 0} icon={RefreshCw} color="text-purple-600 bg-purple-100" />
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
                className="flex flex-col items-center p-4 rounded-lg border border-gray-200 dark:border-slate-700 hover:border-green-500 dark:hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
              >
                <div className={`w-12 h-12 rounded-lg ${action.color} flex items-center justify-center mb-2`}>
                  <action.icon className="h-6 w-6" />
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{action.label}</span>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Vault Environmental Monitoring */}
      <VaultSensorWidget onViewDetails={() => navigate('/seed-bank/monitoring')} />

      {/* Recent Activity & Alerts */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <ActivityItem
                icon={Sprout}
                color="text-green-600 bg-green-100"
                title="New accession registered"
                description="ACC-2024-1234 - Triticum aestivum"
                time="2 hours ago"
              />
              <ActivityItem
                icon={FlaskConical}
                color="text-purple-600 bg-purple-100"
                title="Viability test completed"
                description="Batch VT-2024-089 - 98% germination"
                time="5 hours ago"
              />
              <ActivityItem
                icon={Handshake}
                color="text-amber-600 bg-amber-100"
                title="Germplasm exchange approved"
                description="EX-2024-045 to CIMMYT"
                time="1 day ago"
              />
              <ActivityItem
                icon={RefreshCw}
                color="text-blue-600 bg-blue-100"
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

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
  alert?: boolean;
}

function StatCard({ label, value, icon: IconComponent, color, alert }: StatCardProps) {
  const Icon = IconComponent as React.ComponentType<{ className?: string }>;
  return (
    <Card className={alert && value > 0 ? 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20' : ''}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <span className={`text-2xl font-bold ${alert && value > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'}`}>
              {value.toLocaleString()}
            </span>
            <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActivityItemProps {
  icon: React.ElementType;
  title: string;
  description: string;
  time: string;
  color: string;
}

function ActivityItem({ icon: IconComponent, title, description, time, color }: ActivityItemProps) {
  const Icon = IconComponent as React.ComponentType<{ className?: string }>;
  return (
    <div className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 dark:hover:bg-slate-800">
      <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center flex-shrink-0`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{description}</p>
      </div>
      <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">{time}</span>
    </div>
  );
}

function AlertItem({ level, title, description }: { level: 'critical' | 'warning' | 'info'; title: string; description: string }) {
  const styles = {
    critical: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-300',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300',
  };
  const iconMap = { 
    critical: AlertTriangle, 
    warning: AlertCircle, 
    info: Info 
  };
  const IconComponent = iconMap[level];

  return (
    <div className={`p-3 rounded-lg border ${styles[level]}`}>
      <div className="flex items-center gap-2">
        <IconComponent className="h-4 w-4" />
        <span className="font-medium">{title}</span>
      </div>
      <p className="text-sm mt-1 opacity-80">{description}</p>
    </div>
  );
}

export default Dashboard;
