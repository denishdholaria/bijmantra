/**
 * Recent Activity Widget
 * Shows recent actions and changes across the platform
 */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  Plus,
  Pencil,
  Trash2,
  Eye,
  Upload,
  Download,
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Leaf,
  FlaskConical,
  FileText,
  Database,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ActivityItem {
  id: string;
  type: 'create' | 'update' | 'delete' | 'view' | 'import' | 'export' | 'approve' | 'reject';
  entityType: string;
  entityName: string;
  entityId: string;
  user: string;
  timestamp: string;
  details?: string;
}

interface RecentActivityWidgetProps {
  title?: string;
  maxItems?: number;
  showViewAll?: boolean;
  entityFilter?: string;
}

// Demo activity data
const DEMO_ACTIVITIES: ActivityItem[] = [
  {
    id: '1',
    type: 'create',
    entityType: 'germplasm',
    entityName: 'IR64-Sub1',
    entityId: 'G001',
    user: 'Dr. Singh',
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    details: 'New submergence tolerant variety registered',
  },
  {
    id: '2',
    type: 'update',
    entityType: 'trial',
    entityName: 'Rice Yield Trial 2024',
    entityId: 'T001',
    user: 'Dr. Patel',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    details: 'Added 50 new observations',
  },
  {
    id: '3',
    type: 'approve',
    entityType: 'seedlot',
    entityName: 'SL-2024-001',
    entityId: 'SL001',
    user: 'Quality Team',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    details: 'Passed quality gate (98% germination)',
  },
  {
    id: '4',
    type: 'import',
    entityType: 'observations',
    entityName: 'Field Data Import',
    entityId: 'IMP001',
    user: 'Field Team',
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    details: '1,250 observations imported from FieldBook',
  },
  {
    id: '5',
    type: 'create',
    entityType: 'cross',
    entityName: 'IR64 × Swarna',
    entityId: 'C001',
    user: 'Dr. Kumar',
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
    details: 'New cross planned for drought tolerance',
  },
  {
    id: '6',
    type: 'export',
    entityType: 'report',
    entityName: 'Q3 Progress Report',
    entityId: 'R001',
    user: 'Admin',
    timestamp: new Date(Date.now() - 90 * 60000).toISOString(),
    details: 'PDF report generated',
  },
  {
    id: '7',
    type: 'update',
    entityType: 'study',
    entityName: 'Multi-Location Wheat Trial',
    entityId: 'S001',
    user: 'Dr. Sharma',
    timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
    details: 'Status changed to Completed',
  },
  {
    id: '8',
    type: 'reject',
    entityType: 'seedlot',
    entityName: 'SL-2024-002',
    entityId: 'SL002',
    user: 'Quality Team',
    timestamp: new Date(Date.now() - 180 * 60000).toISOString(),
    details: 'Failed moisture test (15.2%)',
  },
];

export function RecentActivityWidget({
  title = 'Recent Activity',
  maxItems = 5,
  showViewAll = true,
  entityFilter,
}: RecentActivityWidgetProps) {
  const { data: activities = DEMO_ACTIVITIES, isLoading } = useQuery({
    queryKey: ['recent-activity', entityFilter],
    queryFn: async () => {
      try {
        const url = entityFilter
          ? `${API_BASE}/api/v2/audit?entityType=${entityFilter}&limit=${maxItems}`
          : `${API_BASE}/api/v2/audit?limit=${maxItems}`;
        const res = await fetch(url);
        if (!res.ok) return DEMO_ACTIVITIES;
        const data = await res.json();
        return Array.isArray(data) ? data : (data.activities || DEMO_ACTIVITIES);
      } catch {
        return DEMO_ACTIVITIES;
      }
    },
    refetchInterval: 30000,
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'create':
        return <Plus className="h-4 w-4 text-green-500" />;
      case 'update':
        return <Pencil className="h-4 w-4 text-blue-500" />;
      case 'delete':
        return <Trash2 className="h-4 w-4 text-red-500" />;
      case 'view':
        return <Eye className="h-4 w-4 text-gray-500" />;
      case 'import':
        return <Upload className="h-4 w-4 text-purple-500" />;
      case 'export':
        return <Download className="h-4 w-4 text-orange-500" />;
      case 'approve':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'reject':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getEntityIcon = (entityType: string) => {
    switch (entityType) {
      case 'germplasm':
        return <Leaf className="h-4 w-4" />;
      case 'trial':
      case 'study':
        return <FlaskConical className="h-4 w-4" />;
      case 'report':
        return <FileText className="h-4 w-4" />;
      case 'observations':
        return <Database className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      create: 'bg-green-100 text-green-800',
      update: 'bg-blue-100 text-blue-800',
      delete: 'bg-red-100 text-red-800',
      import: 'bg-purple-100 text-purple-800',
      export: 'bg-orange-100 text-orange-800',
      approve: 'bg-green-100 text-green-800',
      reject: 'bg-red-100 text-red-800',
    };
    return (
      <Badge className={`${colors[type] || 'bg-gray-100 text-gray-800'} text-xs`}>
        {type}
      </Badge>
    );
  };

  const displayActivities = activities.slice(0, maxItems);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            {title}
          </CardTitle>
          {showViewAll && (
            <Button variant="ghost" size="sm" asChild>
              <a href="/activity">View All</a>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array(maxItems).fill(0).map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : displayActivities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3">
            {displayActivities.map((activity: ActivityItem) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="p-2 bg-muted rounded-lg">
                  {getTypeIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium truncate">{activity.entityName}</span>
                    {getTypeBadge(activity.type)}
                  </div>
                  {activity.details && (
                    <p className="text-sm text-muted-foreground truncate">{activity.details}</p>
                  )}
                  <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    <span>{activity.user}</span>
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}</span>
                  </div>
                </div>
                <div className="text-muted-foreground">
                  {getEntityIcon(activity.entityType)}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RecentActivityWidget;
