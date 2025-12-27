import * as React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Check, X, Minus, Trophy } from 'lucide-react';

export interface ComparisonItem {
  id: string;
  name: string;
  [key: string]: unknown;
}

export interface ComparisonField {
  key: string;
  label: string;
  type?: 'text' | 'number' | 'boolean' | 'badge';
  unit?: string;
  higherIsBetter?: boolean;
  format?: (value: unknown) => string;
}

interface ComparisonTableProps {
  items: ComparisonItem[];
  fields: ComparisonField[];
  highlightBest?: boolean;
  showDifference?: boolean;
  baselineIndex?: number;
  className?: string;
}

export function ComparisonTable({
  items,
  fields,
  highlightBest = true,
  showDifference = false,
  baselineIndex = 0,
  className,
}: ComparisonTableProps) {
  const getBestIndex = (field: ComparisonField): number | null => {
    if (field.type === 'boolean' || field.type === 'badge') return null;

    const values = items.map((item) => {
      const val = item[field.key];
      return typeof val === 'number' ? val : parseFloat(String(val));
    });

    if (values.every((v) => isNaN(v))) return null;

    const validValues = values.filter((v) => !isNaN(v));
    const best = field.higherIsBetter
      ? Math.max(...validValues)
      : Math.min(...validValues);

    return values.findIndex((v) => v === best);
  };

  const formatValue = (value: unknown, field: ComparisonField): string => {
    if (field.format) return field.format(value);
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      const formatted = value.toLocaleString(undefined, {
        maximumFractionDigits: 2,
      });
      return field.unit ? `${formatted} ${field.unit}` : formatted;
    }
    return String(value);
  };

  const getDifference = (
    value: unknown,
    baseValue: unknown,
    field: ComparisonField
  ): { diff: number; percent: number } | null => {
    if (field.type === 'boolean' || field.type === 'badge') return null;

    const val = typeof value === 'number' ? value : parseFloat(String(value));
    const base =
      typeof baseValue === 'number' ? baseValue : parseFloat(String(baseValue));

    if (isNaN(val) || isNaN(base) || base === 0) return null;

    return {
      diff: val - base,
      percent: ((val - base) / base) * 100,
    };
  };

  const renderValue = (
    item: ComparisonItem,
    field: ComparisonField,
    itemIndex: number,
    bestIndex: number | null
  ) => {
    const value = item[field.key];
    const isBest = highlightBest && bestIndex === itemIndex;
    const baseline = items[baselineIndex];
    const diff =
      showDifference && itemIndex !== baselineIndex
        ? getDifference(value, baseline[field.key], field)
        : null;

    if (field.type === 'boolean') {
      return value ? (
        <Check className="h-4 w-4 text-green-600" />
      ) : (
        <X className="h-4 w-4 text-red-600" />
      );
    }

    if (field.type === 'badge') {
      return <Badge variant="secondary">{String(value)}</Badge>;
    }

    return (
      <div className="flex items-center gap-2">
        <span className={cn(isBest && 'font-semibold text-primary')}>
          {formatValue(value, field)}
        </span>
        {isBest && <Trophy className="h-3 w-3 text-yellow-500" />}
        {diff && (
          <span
            className={cn(
              'text-xs',
              diff.diff > 0
                ? field.higherIsBetter
                  ? 'text-green-600'
                  : 'text-red-600'
                : diff.diff < 0
                  ? field.higherIsBetter
                    ? 'text-red-600'
                    : 'text-green-600'
                  : 'text-muted-foreground'
            )}
          >
            ({diff.diff > 0 ? '+' : ''}
            {diff.percent.toFixed(1)}%)
          </span>
        )}
      </div>
    );
  };

  if (items.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No items to compare
      </div>
    );
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 bg-background">
              Attribute
            </TableHead>
            {items.map((item) => (
              <TableHead key={item.id} className="text-center min-w-32">
                {item.name}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {fields.map((field) => {
            const bestIndex = getBestIndex(field);
            return (
              <TableRow key={field.key}>
                <TableCell className="sticky left-0 bg-background font-medium">
                  {field.label}
                </TableCell>
                {items.map((item, index) => (
                  <TableCell key={item.id} className="text-center">
                    {renderValue(item, field, index, bestIndex)}
                  </TableCell>
                ))}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

export default ComparisonTable;
