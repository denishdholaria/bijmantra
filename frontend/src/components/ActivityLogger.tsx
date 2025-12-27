import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { 
  Activity, Clock, User, FileText, Edit, Trash2, Plus, 
  Eye, Download, Upload, Share2, Settings, Filter,
  ChevronDown, Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

type ActivityType = 
  | 'create' | 'update' | 'delete' | 'view' 
  | 'export' | 'import' | 'share' | 'login' 
  | 'logout' | 'settings' | 'other';

interface ActivityEntry {
  id: string;
  type: ActivityType;
  action: string;
  entityType?: string;
  entityId?: string;
  entityName?: string;
  userId: string;
  userName: string;
  timestamp: Date;
  details?: Record<string, unknown>;
  metadata?: {
    ip?: string;
    userAgent?: string;
    location?: string;
  };
}

interface ActivityLoggerProps {
  activities: ActivityEntry[];
  title?: string;
  showFilters?: boolean;
  showSearch?: boolean;
  maxHeight?: string;
  onActivityClick?: (activity: ActivityEntry) => void;
  className?: string;
}

const ACTIVITY_CONFIG: Record<ActivityType, { icon: React.ReactNode; color: string; label: string }> = {
  create: { icon: <Plus className="h-4 w-4" />, color: 'text-green-500', label: 'Created' },
  update: { icon: <Edit className="h-4 w-4" />, color: 'text-blue-500', label: 'Updated' },
  delete: { icon: <Trash2 className="h-4 w-4" />, color: 'text-red-500', label: 'Deleted' },
  view: { icon: <Eye className="h-4 w-4" />, color: 'text-gray-500', label: 'Viewed' },
  export: { icon: <Download className="h-4 w-4" />, color: 'text-purple-500', label: 'Exported' },
  import: { icon: <Upload className="h-4 w-4" />, color: 'text-orange-500', label: 'Imported' },
  share: { icon: <Share2 className="h-4 w-4" />, color: 'text-cyan-500', label: 'Shared' },
  login: { icon: <User className="h-4 w-4" />, color: 'text-green-500', label: 'Logged in' },
  logout: { icon: <User className="h-4 w-4" />, color: 'text-gray-500', label: 'Logged out' },
  settings: { icon: <Settings className="h-4 w-4" />, color: 'text-gray-500', label: 'Settings' },
  other: { icon: <Activity className="h-4 w-4" />, color: 'text-gray-500', label: 'Activity' },
};

export function ActivityLogger({
  activities,
  title = 'Activity Log',
  showFilters = true,
  showSearch = true,
  maxHeight = '500px',
  onActivityClick,
  className,
}: ActivityLoggerProps) {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<ActivityType | 'all'>('all');
  const [userFilter, setUserFilter] = useState<string>('all');

  // Get unique users
  const users = [...new Set(activities.map(a => a.userName))];

  // Filter activities
  const filteredActivities = activities.filter(activity => {
    if (typeFilter !== 'all' && activity.type !== typeFilter) return false;
    if (userFilter !== 'all' && activity.userName !== userFilter) return false;
    if (search) {
      const searchLower = search.toLowerCase();
      return (
        activity.action.toLowerCase().includes(searchLower) ||
        activity.entityName?.toLowerCase().includes(searchLower) ||
        activity.userName.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  // Group by date
  const groupedActivities = groupByDate(filteredActivities);

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            {title}
          </CardTitle>
          <Badge variant="secondary">{filteredActivities.length} activities</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Filters */}
        {(showFilters || showSearch) && (
          <div className="flex flex-wrap gap-2">
            {showSearch && (
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search activities..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            )}
            {showFilters && (
              <>
                <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as ActivityType | 'all')}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    {Object.entries(ACTIVITY_CONFIG).map(([type, config]) => (
                      <SelectItem key={type} value={type}>
                        <span className="flex items-center gap-2">
                          <span className={config.color}>{config.icon}</span>
                          {config.label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={userFilter} onValueChange={setUserFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="User" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Users</SelectItem>
                    {users.map(user => (
                      <SelectItem key={user} value={user}>{user}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </>
            )}
          </div>
        )}

        {/* Activity List */}
        <ScrollArea style={{ height: maxHeight }}>
          {Object.entries(groupedActivities).length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No activities found</p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedActivities).map(([date, dateActivities]) => (
                <div key={date}>
                  <div className="sticky top-0 bg-background py-2 z-10">
                    <Badge variant="outline" className="text-xs">
                      {date}
                    </Badge>
                  </div>
                  <div className="space-y-2 ml-2 border-l-2 border-muted pl-4">
                    {dateActivities.map((activity) => {
                      const config = ACTIVITY_CONFIG[activity.type];
                      return (
                        <div
                          key={activity.id}
                          onClick={() => onActivityClick?.(activity)}
                          className={cn(
                            'relative flex items-start gap-3 p-3 rounded-lg',
                            'hover:bg-muted/50 transition-colors',
                            onActivityClick && 'cursor-pointer'
                          )}
                        >
                          {/* Timeline dot */}
                          <div className={cn(
                            'absolute -left-[21px] w-3 h-3 rounded-full border-2 border-background',
                            config.color.replace('text-', 'bg-')
                          )} />

                          {/* Icon */}
                          <div className={cn('p-2 rounded-lg bg-muted', config.color)}>
                            {config.icon}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm">
                              <span className="font-medium">{activity.userName}</span>
                              {' '}
                              <span className="text-muted-foreground">{activity.action}</span>
                              {activity.entityName && (
                                <>
                                  {' '}
                                  <span className="font-medium">{activity.entityName}</span>
                                </>
                              )}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {formatTime(activity.timestamp)}
                              </span>
                              {activity.entityType && (
                                <Badge variant="secondary" className="text-[10px]">
                                  {activity.entityType}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Group activities by date
function groupByDate(activities: ActivityEntry[]): Record<string, ActivityEntry[]> {
  const grouped: Record<string, ActivityEntry[]> = {};
  
  activities.forEach(activity => {
    const date = formatDate(activity.timestamp);
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(activity);
  });

  return grouped;
}

// Format date for grouping
function formatDate(date: Date): string {
  const now = new Date();
  const activityDate = new Date(date);
  const diffDays = Math.floor((now.getTime() - activityDate.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return activityDate.toLocaleDateString(undefined, { 
    month: 'short', 
    day: 'numeric',
    year: activityDate.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  });
}

// Format time
function formatTime(date: Date): string {
  return new Date(date).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Activity Logger Context for global logging
interface ActivityLoggerContextValue {
  log: (entry: Omit<ActivityEntry, 'id' | 'timestamp'>) => void;
  activities: ActivityEntry[];
  clearActivities: () => void;
}

const ActivityLoggerContext = createContext<ActivityLoggerContextValue | null>(null);

export function useActivityLogger() {
  const context = useContext(ActivityLoggerContext);
  if (!context) {
    throw new Error('useActivityLogger must be used within ActivityLoggerProvider');
  }
  return context;
}

export function ActivityLoggerProvider({ 
  children,
  maxEntries = 1000,
  persistKey = 'bijmantra-activity-log',
}: { 
  children: React.ReactNode;
  maxEntries?: number;
  persistKey?: string;
}) {
  const [activities, setActivities] = useState<ActivityEntry[]>(() => {
    try {
      const stored = localStorage.getItem(persistKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed.map((a: ActivityEntry) => ({ ...a, timestamp: new Date(a.timestamp) }));
      }
    } catch {}
    return [];
  });

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(persistKey, JSON.stringify(activities.slice(0, maxEntries)));
    } catch {}
  }, [activities, maxEntries, persistKey]);

  const log = useCallback((entry: Omit<ActivityEntry, 'id' | 'timestamp'>) => {
    const newEntry: ActivityEntry = {
      ...entry,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setActivities(prev => [newEntry, ...prev].slice(0, maxEntries));
  }, [maxEntries]);

  const clearActivities = useCallback(() => {
    setActivities([]);
    localStorage.removeItem(persistKey);
  }, [persistKey]);

  return (
    <ActivityLoggerContext.Provider value={{ log, activities, clearActivities }}>
      {children}
    </ActivityLoggerContext.Provider>
  );
}
