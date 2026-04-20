/**
 * Sync Status Badge Component
 *
 * Offline-aware entity status indicator.
 * Shows sync state for individual records.
 */

import { cn } from '@/lib/utils';
import { Cloud, CloudOff, RefreshCw, AlertTriangle, Check } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

type SyncStatus = 'synced' | 'pending' | 'syncing' | 'conflict' | 'offline' | 'error';

interface SyncStatusBadgeProps {
  status: SyncStatus;
  lastSynced?: string;
  pendingChanges?: number;
  className?: string;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig: Record<SyncStatus, {
  icon: React.ElementType;
  label: string;
  color: string;
  bgColor: string;
  animate?: boolean;
}> = {
  synced: {
    icon: Check,
    label: 'Synced',
    color: 'text-green-600',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
  },
  pending: {
    icon: Cloud,
    label: 'Pending',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
  },
  syncing: {
    icon: RefreshCw,
    label: 'Syncing',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    animate: true,
  },
  conflict: {
    icon: AlertTriangle,
    label: 'Conflict',
    color: 'text-red-600',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
  },
  offline: {
    icon: CloudOff,
    label: 'Offline',
    color: 'text-gray-500',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
  },
  error: {
    icon: AlertTriangle,
    label: 'Error',
    color: 'text-red-600',
    bgColor: 'bg-red-100 dark:bg-red-900/30',
  },
};

const sizeConfig: Record<'sm' | 'md' | 'lg', { icon: number; padding: string; text: string }> = {
  sm: { icon: 12, padding: 'px-1.5 py-0.5', text: 'text-xs' },
  md: { icon: 14, padding: 'px-2 py-1', text: 'text-sm' },
  lg: { icon: 16, padding: 'px-2.5 py-1.5', text: 'text-sm' },
};

export function SyncStatusBadge({
  status,
  lastSynced,
  pendingChanges,
  className,
  showLabel = false,
  size = 'md',
}: SyncStatusBadgeProps) {
  const config = statusConfig[status];
  const sizeKey = size as 'sm' | 'md' | 'lg';
  const sizeConf = sizeConfig[sizeKey];
  const Icon = config.icon as React.ComponentType<{ size?: number; className?: string }>;

  const formatLastSynced = (ts: string) => {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const tooltipContent = () => {
    let content = config.label;
    if (lastSynced && status === 'synced') {
      content += ` • ${formatLastSynced(lastSynced)}`;
    }
    if (pendingChanges && status === 'pending') {
      content += ` • ${pendingChanges} change${pendingChanges > 1 ? 's' : ''}`;
    }
    if (status === 'conflict') {
      content += ' • Requires resolution';
    }
    return content;
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              'inline-flex items-center gap-1 rounded-full',
              config.bgColor,
              sizeConf.padding,
              className
            )}
          >
            <Icon
              size={sizeConf.icon}
              className={cn(config.color, config.animate && 'animate-spin')}
            />
            {showLabel && (
              <span className={cn(config.color, sizeConf.text, 'font-medium')}>
                {config.label}
                {pendingChanges && status === 'pending' && ` (${pendingChanges})`}
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipContent()}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default SyncStatusBadge;
