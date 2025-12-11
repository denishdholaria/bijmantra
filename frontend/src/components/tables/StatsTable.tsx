import * as React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface StatRow {
  label: string;
  value: string | number;
  previousValue?: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  highlight?: boolean;
  description?: string;
}

interface StatsTableProps {
  title?: string;
  stats: StatRow[];
  showTrend?: boolean;
  compact?: boolean;
  className?: string;
}

const formatValue = (value: string | number, unit?: string): string => {
  if (typeof value === 'number') {
    const formatted = value.toLocaleString(undefined, {
      maximumFractionDigits: 2,
    });
    return unit ? `${formatted} ${unit}` : formatted;
  }
  return unit ? `${value} ${unit}` : value;
};

const calculateChange = (
  current: string | number,
  previous: string | number
): { percent: number; direction: 'up' | 'down' | 'neutral' } => {
  const curr = typeof current === 'number' ? current : parseFloat(current);
  const prev = typeof previous === 'number' ? previous : parseFloat(previous);

  if (isNaN(curr) || isNaN(prev) || prev === 0) {
    return { percent: 0, direction: 'neutral' };
  }

  const percent = ((curr - prev) / prev) * 100;
  return {
    percent: Math.abs(percent),
    direction: percent > 0 ? 'up' : percent < 0 ? 'down' : 'neutral',
  };
};

export function StatsTable({
  title,
  stats,
  showTrend = true,
  compact = false,
  className,
}: StatsTableProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {title && <h3 className="font-semibold text-sm">{title}</h3>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Metric</TableHead>
            <TableHead className="text-right">Value</TableHead>
            {showTrend && <TableHead className="text-right w-24">Change</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {stats.map((stat, index) => {
            const change =
              stat.previousValue !== undefined
                ? calculateChange(stat.value, stat.previousValue)
                : null;
            const trend = stat.trend || change?.direction || 'neutral';

            return (
              <TableRow
                key={index}
                className={cn(stat.highlight && 'bg-primary/5')}
              >
                <TableCell className={cn(compact && 'py-2')}>
                  <div>
                    <span className={cn(stat.highlight && 'font-medium')}>
                      {stat.label}
                    </span>
                    {stat.description && (
                      <p className="text-xs text-muted-foreground">
                        {stat.description}
                      </p>
                    )}
                  </div>
                </TableCell>
                <TableCell
                  className={cn(
                    'text-right font-mono',
                    compact && 'py-2',
                    stat.highlight && 'font-semibold'
                  )}
                >
                  {formatValue(stat.value, stat.unit)}
                </TableCell>
                {showTrend && (
                  <TableCell className={cn('text-right', compact && 'py-2')}>
                    {change && (
                      <div
                        className={cn(
                          'flex items-center justify-end gap-1 text-sm',
                          trend === 'up' && 'text-green-600',
                          trend === 'down' && 'text-red-600',
                          trend === 'neutral' && 'text-muted-foreground'
                        )}
                      >
                        {trend === 'up' && <TrendingUp className="h-3 w-3" />}
                        {trend === 'down' && <TrendingDown className="h-3 w-3" />}
                        {trend === 'neutral' && <Minus className="h-3 w-3" />}
                        <span>{change.percent.toFixed(1)}%</span>
                      </div>
                    )}
                  </TableCell>
                )}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

export default StatsTable;
