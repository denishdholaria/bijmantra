import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus, LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  previousValue?: string | number;
  unit?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendLabel?: string;
  description?: string;
  loading?: boolean;
  className?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export function MetricCard({
  title,
  value,
  previousValue,
  unit,
  icon: Icon,
  trend,
  trendLabel,
  description,
  loading = false,
  className,
  variant = 'default',
}: MetricCardProps) {
  const calculatedTrend = React.useMemo(() => {
    if (trend) return trend;
    if (previousValue === undefined) return 'neutral';

    const curr = typeof value === 'number' ? value : parseFloat(String(value));
    const prev =
      typeof previousValue === 'number'
        ? previousValue
        : parseFloat(String(previousValue));

    if (isNaN(curr) || isNaN(prev)) return 'neutral';
    if (curr > prev) return 'up';
    if (curr < prev) return 'down';
    return 'neutral';
  }, [value, previousValue, trend]);

  const percentChange = React.useMemo(() => {
    if (previousValue === undefined) return null;

    const curr = typeof value === 'number' ? value : parseFloat(String(value));
    const prev =
      typeof previousValue === 'number'
        ? previousValue
        : parseFloat(String(previousValue));

    if (isNaN(curr) || isNaN(prev) || prev === 0) return null;
    return ((curr - prev) / prev) * 100;
  }, [value, previousValue]);

  const variantStyles = {
    default: '',
    success: 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950',
    warning: 'border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950',
    danger: 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950',
  };

  const iconColors = {
    default: 'text-muted-foreground',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
  };

  return (
    <Card className={cn(variantStyles[variant], className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && <Icon className={cn('h-4 w-4', iconColors[variant])} />}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <div className="h-8 w-24 bg-muted animate-pulse rounded" />
            <div className="h-4 w-32 bg-muted animate-pulse rounded" />
          </div>
        ) : (
          <>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold">
                {typeof value === 'number'
                  ? value.toLocaleString()
                  : value}
              </span>
              {unit && (
                <span className="text-sm text-muted-foreground">{unit}</span>
              )}
            </div>

            <div className="flex items-center gap-2 mt-1">
              {percentChange !== null && (
                <div
                  className={cn(
                    'flex items-center gap-0.5 text-xs font-medium',
                    calculatedTrend === 'up' && 'text-green-600',
                    calculatedTrend === 'down' && 'text-red-600',
                    calculatedTrend === 'neutral' && 'text-muted-foreground'
                  )}
                >
                  {calculatedTrend === 'up' && (
                    <TrendingUp className="h-3 w-3" />
                  )}
                  {calculatedTrend === 'down' && (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {calculatedTrend === 'neutral' && (
                    <Minus className="h-3 w-3" />
                  )}
                  <span>
                    {percentChange > 0 ? '+' : ''}
                    {percentChange.toFixed(1)}%
                  </span>
                </div>
              )}
              {trendLabel && (
                <span className="text-xs text-muted-foreground">
                  {trendLabel}
                </span>
              )}
            </div>

            {description && (
              <p className="text-xs text-muted-foreground mt-1">
                {description}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default MetricCard;
