import * as React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TrendIndicatorProps {
  value: number;
  previousValue: number;
  format?: 'percent' | 'absolute' | 'both';
  positiveIsGood?: boolean;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function TrendIndicator({
  value,
  previousValue,
  format = 'percent',
  positiveIsGood = true,
  showIcon = true,
  size = 'md',
  className,
}: TrendIndicatorProps) {
  const diff = value - previousValue;
  const percentChange = previousValue !== 0 ? (diff / previousValue) * 100 : 0;
  const isPositive = diff > 0;
  const isNeutral = diff === 0;
  const isGood = positiveIsGood ? isPositive : !isPositive;

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  const formatValue = () => {
    const sign = isPositive ? '+' : '';
    switch (format) {
      case 'absolute':
        return `${sign}${diff.toLocaleString()}`;
      case 'both':
        return `${sign}${diff.toLocaleString()} (${sign}${percentChange.toFixed(1)}%)`;
      default:
        return `${sign}${percentChange.toFixed(1)}%`;
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 font-medium',
        sizeClasses[size],
        isNeutral && 'text-muted-foreground',
        !isNeutral && isGood && 'text-green-600',
        !isNeutral && !isGood && 'text-red-600',
        className
      )}
    >
      {showIcon && (
        <>
          {isPositive && <TrendingUp className={iconSizes[size]} />}
          {!isPositive && !isNeutral && <TrendingDown className={iconSizes[size]} />}
          {isNeutral && <Minus className={iconSizes[size]} />}
        </>
      )}
      {formatValue()}
    </span>
  );
}

export default TrendIndicator;
