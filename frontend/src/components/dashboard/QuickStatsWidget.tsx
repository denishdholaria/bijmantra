/**
 * Quick Stats Widget
 * Displays key metrics in a compact, real-time updating format
 */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Leaf,
  FlaskConical,
  MapPin,
  Users,
  Calendar,
  Package,
  Activity,
  Target,
  Award,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface StatItem {
  id: string;
  label: string;
  value: number | string;
  previousValue?: number;
  unit?: string;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'stable';
  link?: string;
}

interface QuickStatsWidgetProps {
  title?: string;
  refreshInterval?: number;
  compact?: boolean;
}

export function QuickStatsWidget({
  title = 'Quick Stats',
  refreshInterval = 60000,
  compact = false,
}: QuickStatsWidgetProps) {
  // Fetch stats from multiple endpoints
  const { data: stats, isLoading } = useQuery({
    queryKey: ['quick-stats'],
    queryFn: async () => {
      try {
        // Fetch from multiple endpoints in parallel
        const [programs, germplasm, trials, locations] = await Promise.all([
          fetch(`${API_BASE}/brapi/v2/programs?pageSize=1`).then(r => r.ok ? r.json() : null),
          fetch(`${API_BASE}/brapi/v2/germplasm?pageSize=1`).then(r => r.ok ? r.json() : null),
          fetch(`${API_BASE}/brapi/v2/trials?pageSize=1`).then(r => r.ok ? r.json() : null),
          fetch(`${API_BASE}/brapi/v2/locations?pageSize=1`).then(r => r.ok ? r.json() : null),
        ]);

        return {
          programs: programs?.metadata?.pagination?.totalCount || 0,
          germplasm: germplasm?.metadata?.pagination?.totalCount || 0,
          trials: trials?.metadata?.pagination?.totalCount || 0,
          locations: locations?.metadata?.pagination?.totalCount || 0,
        };
      } catch {
        // Return zeros if API unavailable - Zero Mock Data Policy
        return {
          programs: 0,
          germplasm: 0,
          trials: 0,
          locations: 0,
        };
      }
    },
    refetchInterval: refreshInterval,
  });

  const statItems: StatItem[] = [
    {
      id: 'programs',
      label: 'Programs',
      value: stats?.programs || 0,
      icon: <Target className="h-4 w-4" />,
      color: 'text-blue-600',
      trend: 'stable',
      link: '/programs',
    },
    {
      id: 'germplasm',
      label: 'Germplasm',
      value: stats?.germplasm || 0,
      icon: <Leaf className="h-4 w-4" />,
      color: 'text-green-600',
      trend: 'up',
      link: '/germplasm',
    },
    {
      id: 'trials',
      label: 'Trials',
      value: stats?.trials || 0,
      icon: <FlaskConical className="h-4 w-4" />,
      color: 'text-purple-600',
      trend: 'up',
      link: '/trials',
    },
    {
      id: 'locations',
      label: 'Locations',
      value: stats?.locations || 0,
      icon: <MapPin className="h-4 w-4" />,
      color: 'text-orange-600',
      trend: 'stable',
      link: '/locations',
    },
  ];

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-3 w-3 text-red-500" />;
      default:
        return <Minus className="h-3 w-3 text-gray-400" />;
    }
  };

  if (compact) {
    return (
      <div className="flex gap-4 flex-wrap">
        {isLoading ? (
          Array(4).fill(0).map((_, i) => (
            <Skeleton key={i} className="h-16 w-32" />
          ))
        ) : (
          statItems.map(stat => (
            <a
              key={stat.id}
              href={stat.link}
              className="flex items-center gap-3 p-3 bg-muted rounded-lg hover:bg-muted/80 transition-colors"
            >
              <div className={stat.color}>{stat.icon}</div>
              <div>
                <p className="text-lg font-bold">{stat.value.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </a>
          ))
        )}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="h-5 w-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {isLoading ? (
            Array(4).fill(0).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))
          ) : (
            statItems.map(stat => (
              <a
                key={stat.id}
                href={stat.link}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-2 rounded-lg bg-muted ${stat.color}`}>
                    {stat.icon}
                  </div>
                  {getTrendIcon(stat.trend)}
                </div>
                <p className="text-2xl font-bold group-hover:text-primary transition-colors">
                  {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                  {stat.unit && <span className="text-sm font-normal text-muted-foreground ml-1">{stat.unit}</span>}
                </p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </a>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default QuickStatsWidget;
