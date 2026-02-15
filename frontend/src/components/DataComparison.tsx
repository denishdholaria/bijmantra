import { useState, useMemo } from 'react';
import { ArrowLeftRight, Check, X, Minus, ChevronDown, ChevronUp, Copy, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';

interface ComparisonItem {
  id: string;
  name: string;
  data: Record<string, unknown>;
}

interface FieldConfig {
  key: string;
  label: string;
  type?: 'text' | 'number' | 'date' | 'boolean' | 'array';
  format?: (value: unknown) => string;
  category?: string;
}

interface DataComparisonProps {
  items: ComparisonItem[];
  fields: FieldConfig[];
  title?: string;
  description?: string;
  showOnlyDifferences?: boolean;
  highlightBest?: Record<string, 'highest' | 'lowest'>;
  onExport?: (data: ComparisonResult[]) => void;
  className?: string;
}

interface ComparisonResult {
  field: string;
  label: string;
  values: { itemId: string; value: unknown; formatted: string }[];
  isDifferent: boolean;
  bestItemId?: string;
}

export function DataComparison({
  items,
  fields,
  title = 'Compare',
  description,
  showOnlyDifferences: initialShowDiff = false,
  highlightBest = {},
  onExport,
  className,
}: DataComparisonProps) {
  const [showOnlyDifferences, setShowOnlyDifferences] = useState(initialShowDiff);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['default']));
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set(fields.map(f => f.key)));

  // Group fields by category
  const fieldsByCategory = useMemo(() => {
    const grouped: Record<string, FieldConfig[]> = { default: [] };
    fields.forEach(field => {
      const category = field.category || 'default';
      if (!grouped[category]) grouped[category] = [];
      grouped[category].push(field);
    });
    return grouped;
  }, [fields]);

  // Compare values
  const comparisons = useMemo((): ComparisonResult[] => {
    return fields
      .filter(field => selectedFields.has(field.key))
      .map(field => {
        const values = items.map(item => {
          const value = item.data[field.key];
          const formatted = field.format 
            ? field.format(value) 
            : formatValue(value, field.type);
          return { itemId: item.id, value, formatted };
        });

        // Check if values are different
        const uniqueValues = new Set(values.map(v => JSON.stringify(v.value)));
        const isDifferent = uniqueValues.size > 1;

        // Find best value if configured
        let bestItemId: string | undefined;
        if (highlightBest[field.key] && field.type === 'number') {
          const numericValues = values
            .filter(v => typeof v.value === 'number')
            .map(v => ({ id: v.itemId, value: v.value as number }));
          
          if (numericValues.length > 0) {
            const sorted = [...numericValues].sort((a, b) => 
              highlightBest[field.key] === 'highest' ? b.value - a.value : a.value - b.value
            );
            bestItemId = sorted[0].id;
          }
        }

        return {
          field: field.key,
          label: field.label,
          values,
          isDifferent,
          bestItemId,
        };
      });
  }, [items, fields, selectedFields, highlightBest]);

  // Filter comparisons
  const filteredComparisons = showOnlyDifferences 
    ? comparisons.filter(c => c.isDifferent)
    : comparisons;

  // Stats
  const totalFields = comparisons.length;
  const differentFields = comparisons.filter(c => c.isDifferent).length;
  const sameFields = totalFields - differentFields;

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const toggleField = (key: string) => {
    setSelectedFields(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const handleExport = () => {
    if (onExport) {
      onExport(filteredComparisons);
    }
  };

  if (items.length < 2) {
    return (
      <Card className={className}>
        <CardContent className="p-8 text-center text-muted-foreground">
          <ArrowLeftRight className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select at least 2 items to compare</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ArrowLeftRight className="h-5 w-5" />
              {title}
            </CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              <Check className="h-3 w-3 text-green-500" />
              {sameFields} same
            </Badge>
            <Badge variant="outline" className="gap-1">
              <X className="h-3 w-3 text-amber-500" />
              {differentFields} different
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox
              checked={showOnlyDifferences}
              onCheckedChange={(checked) => setShowOnlyDifferences(!!checked)}
            />
            Show only differences
          </label>
          {onExport && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
        </div>

        {/* Comparison Table */}
        <ScrollArea className="h-[500px]">
          <div className="min-w-[600px]">
            {/* Header Row - Item Names */}
            <div className="flex border-b sticky top-0 bg-background z-10">
              <div className="w-48 flex-shrink-0 p-3 font-medium text-sm">
                Field
              </div>
              {items.map(item => (
                <div key={item.id} className="flex-1 p-3 font-medium text-sm text-center border-l">
                  {item.name}
                </div>
              ))}
            </div>

            {/* Comparison Rows */}
            {Object.entries(fieldsByCategory).map(([category, categoryFields]) => {
              const visibleFields = categoryFields.filter(f => selectedFields.has(f.key));
              const categoryComparisons = filteredComparisons.filter(c => 
                visibleFields.some(f => f.key === c.field)
              );

              if (categoryComparisons.length === 0 && showOnlyDifferences) return null;

              return (
                <div key={category}>
                  {/* Category Header */}
                  {category !== 'default' && (
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full flex items-center gap-2 p-2 bg-muted/50 hover:bg-muted text-sm font-medium"
                    >
                      {expandedCategories.has(category) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronUp className="h-4 w-4" />
                      )}
                      {category}
                      <Badge variant="secondary" className="ml-auto">
                        {categoryComparisons.length}
                      </Badge>
                    </button>
                  )}

                  {/* Category Fields */}
                  {(category === 'default' || expandedCategories.has(category)) && (
                    categoryComparisons.map(comparison => (
                      <div
                        key={comparison.field}
                        className={cn(
                          'flex border-b hover:bg-muted/30',
                          comparison.isDifferent && 'bg-amber-50/50 dark:bg-amber-950/20'
                        )}
                      >
                        <div className="w-48 flex-shrink-0 p-3 text-sm flex items-center gap-2">
                          {comparison.isDifferent ? (
                            <X className="h-3 w-3 text-amber-500" />
                          ) : (
                            <Check className="h-3 w-3 text-green-500" />
                          )}
                          {comparison.label}
                        </div>
                        {comparison.values.map(({ itemId, formatted }) => (
                          <div
                            key={itemId}
                            className={cn(
                              'flex-1 p-3 text-sm text-center border-l',
                              comparison.bestItemId === itemId && 'bg-green-50 dark:bg-green-950/30 font-medium'
                            )}
                          >
                            {formatted || <span className="text-muted-foreground">—</span>}
                            {comparison.bestItemId === itemId && (
                              <Badge variant="secondary" className="ml-2 text-[10px]">Best</Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    ))
                  )}
                </div>
              );
            })}

            {filteredComparisons.length === 0 && (
              <div className="p-8 text-center text-muted-foreground">
                {showOnlyDifferences 
                  ? 'All selected fields have identical values'
                  : 'No fields to compare'}
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Format value based on type
function formatValue(value: unknown, type?: string): string {
  if (value === null || value === undefined) return '';
  
  switch (type) {
    case 'number':
      return typeof value === 'number' ? value.toLocaleString() : String(value);
    case 'date':
      return value instanceof Date 
        ? value.toLocaleDateString() 
        : new Date(String(value)).toLocaleDateString();
    case 'boolean':
      return value ? 'Yes' : 'No';
    case 'array':
      return Array.isArray(value) ? value.join(', ') : String(value);
    default:
      return String(value);
  }
}

// Hook for managing comparison selection
export function useComparison<T extends { id: string }>(maxItems = 4) {
  const [selectedItems, setSelectedItems] = useState<T[]>([]);

  const addItem = (item: T) => {
    if (selectedItems.length >= maxItems) return false;
    if (selectedItems.some(i => i.id === item.id)) return false;
    setSelectedItems(prev => [...prev, item]);
    return true;
  };

  const removeItem = (id: string) => {
    setSelectedItems(prev => prev.filter(i => i.id !== id));
  };

  const clearItems = () => {
    setSelectedItems([]);
  };

  const isSelected = (id: string) => selectedItems.some(i => i.id === id);
  const canAdd = selectedItems.length < maxItems;

  return {
    selectedItems,
    addItem,
    removeItem,
    clearItems,
    isSelected,
    canAdd,
    count: selectedItems.length,
  };
}
