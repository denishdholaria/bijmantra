/**
 * Timeline Activity Component
 *
 * Displays breeding program milestones and activity history.
 */

import { cn } from '@/lib/utils';

interface TimelineEvent {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  type?: 'success' | 'warning' | 'error' | 'info' | 'default';
  icon?: React.ReactNode;
  user?: string;
}

interface TimelineActivityProps {
  events: TimelineEvent[];
  className?: string;
  showConnector?: boolean;
  compact?: boolean;
}

const typeStyles = {
  success: 'bg-green-500 border-green-500',
  warning: 'bg-yellow-500 border-yellow-500',
  error: 'bg-red-500 border-red-500',
  info: 'bg-blue-500 border-blue-500',
  default: 'bg-gray-400 border-gray-400',
};

const typeBgStyles = {
  success: 'bg-green-50 dark:bg-green-950',
  warning: 'bg-yellow-50 dark:bg-yellow-950',
  error: 'bg-red-50 dark:bg-red-950',
  info: 'bg-blue-50 dark:bg-blue-950',
  default: 'bg-gray-50 dark:bg-gray-900',
};

export function TimelineActivity({
  events,
  className,
  showConnector = true,
  compact = false,
}: TimelineActivityProps) {
  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={cn('relative', className)}>
      {events.map((event, index) => {
        const type = event.type || 'default';
        const isLast = index === events.length - 1;

        return (
          <div key={event.id} className={cn('relative flex gap-4', compact ? 'pb-3' : 'pb-6')}>
            {/* Connector Line */}
            {showConnector && !isLast && (
              <div
                className="absolute left-[11px] top-6 w-0.5 bg-border"
                style={{ height: 'calc(100% - 12px)' }}
              />
            )}

            {/* Dot/Icon */}
            <div className="relative z-10 flex-shrink-0">
              {event.icon ? (
                <div
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full border-2',
                    typeStyles[type]
                  )}
                >
                  {event.icon}
                </div>
              ) : (
                <div
                  className={cn(
                    'h-6 w-6 rounded-full border-2',
                    typeStyles[type]
                  )}
                />
              )}
            </div>

            {/* Content */}
            <div className={cn('flex-1 min-w-0', compact ? 'pt-0.5' : '')}>
              <div
                className={cn(
                  'rounded-lg p-3',
                  typeBgStyles[type]
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className={cn('font-medium', compact ? 'text-sm' : 'text-base')}>
                    {event.title}
                  </h4>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
                {event.description && (
                  <p className={cn('text-muted-foreground mt-1', compact ? 'text-xs' : 'text-sm')}>
                    {event.description}
                  </p>
                )}
                {event.user && (
                  <p className="text-xs text-muted-foreground mt-2">
                    by {event.user}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default TimelineActivity;
