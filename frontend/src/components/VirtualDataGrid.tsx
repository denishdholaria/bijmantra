/**
 * Virtual Data Grid
 * 
 * High-performance table for large datasets (100K+ rows).
 * Uses @tanstack/react-virtual for virtualization.
 */

import { useRef, useState, useMemo, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  id: string;
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
  width?: number;
  minWidth?: number;
  sortable?: boolean;
  sticky?: boolean;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

export interface VirtualDataGridProps<T> {
  data: T[];
  columns: Column<T>[];
  rowHeight?: number;
  headerHeight?: number;
  maxHeight?: number;
  selectable?: boolean;
  onSelectionChange?: (selectedRows: T[]) => void;
  onRowClick?: (row: T, index: number) => void;
  getRowId?: (row: T, index: number) => string | number;
  searchable?: boolean;
  searchPlaceholder?: string;
  exportable?: boolean;
  exportFilename?: string;
  emptyMessage?: string;
  className?: string;
}

type SortDirection = 'asc' | 'desc' | null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function VirtualDataGrid<T extends Record<string, any>>({
  data,
  columns,
  rowHeight = 48,
  headerHeight = 48,
  maxHeight = 600,
  selectable = false,
  onSelectionChange,
  onRowClick,
  getRowId = (_row: T, index: number) => index,
  searchable = false,
  searchPlaceholder = 'Search...',
  exportable = false,
  exportFilename = 'data',
  emptyMessage = 'No data available',
  className,
}: VirtualDataGridProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Filter data based on search
  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data;
    
    const query = searchQuery.toLowerCase();
    return data.filter(row => {
      return columns.some(col => {
        const value = typeof col.accessor === 'function'
          ? col.accessor(row)
          : row[col.accessor];
        return String(value).toLowerCase().includes(query);
      });
    });
  }, [data, columns, searchQuery]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData;
    
    const column = columns.find(c => c.id === sortColumn);
    if (!column) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = typeof column.accessor === 'function'
        ? column.accessor(a)
        : a[column.accessor];
      const bValue = typeof column.accessor === 'function'
        ? column.accessor(b)
        : b[column.accessor];

      if (aValue === bValue) return 0;
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      const comparison = aValue < bValue ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortColumn, sortDirection, columns]);

  // Virtual row renderer
  const rowVirtualizer = useVirtualizer({
    count: sortedData.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan: 10,
  });

  // Calculate total width
  const totalWidth = useMemo(() => {
    return columns.reduce((sum, col) => sum + (col.width || col.minWidth || 150), 0);
  }, [columns]);

  // Handle sort
  const handleSort = useCallback((columnId: string) => {
    const column = columns.find(c => c.id === columnId);
    if (!column?.sortable) return;

    if (sortColumn === columnId) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      }
    } else {
      setSortColumn(columnId);
      setSortDirection('asc');
    }
  }, [sortColumn, sortDirection, columns]);

  // Handle selection
  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === sortedData.length) {
      setSelectedIds(new Set());
      onSelectionChange?.([]);
    } else {
      const allIds = new Set(sortedData.map((row, i) => getRowId(row, i)));
      setSelectedIds(allIds);
      onSelectionChange?.(sortedData);
    }
  }, [sortedData, selectedIds, getRowId, onSelectionChange]);

  const handleSelectRow = useCallback((row: T, index: number) => {
    const id = getRowId(row, index);
    const newSelected = new Set(selectedIds);
    
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    
    setSelectedIds(newSelected);
    onSelectionChange?.(sortedData.filter((r, i) => newSelected.has(getRowId(r, i))));
  }, [selectedIds, sortedData, getRowId, onSelectionChange]);

  // Export to CSV
  const handleExport = useCallback(() => {
    const headers = columns.map(c => c.header).join(',');
    const rows = sortedData.map(row => {
      return columns.map(col => {
        const value = typeof col.accessor === 'function'
          ? col.accessor(row)
          : row[col.accessor];
        const strValue = String(value ?? '');
        // Escape quotes and wrap in quotes if contains comma
        if (strValue.includes(',') || strValue.includes('"')) {
          return `"${strValue.replace(/"/g, '""')}"`;
        }
        return strValue;
      }).join(',');
    }).join('\n');

    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${exportFilename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [columns, sortedData, exportFilename]);

  // Get cell value
  const getCellValue = (row: T, column: Column<T>) => {
    if (typeof column.accessor === 'function') {
      return column.accessor(row);
    }
    return row[column.accessor] as React.ReactNode;
  };

  // Render sort icon
  const renderSortIcon = (columnId: string) => {
    if (sortColumn !== columnId) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" />;
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="h-4 w-4" />
      : <ArrowDown className="h-4 w-4" />;
  };

  const isAllSelected = sortedData.length > 0 && selectedIds.size === sortedData.length;
  const isSomeSelected = selectedIds.size > 0 && selectedIds.size < sortedData.length;

  return (
    <div className={cn('flex flex-col border rounded-lg', className)}>
      {/* Toolbar */}
      {(searchable || exportable) && (
        <div className="flex items-center justify-between gap-4 p-3 border-b bg-muted/30">
          {searchable && (
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          )}
          <div className="flex items-center gap-2">
            {selectable && selectedIds.size > 0 && (
              <span className="text-sm text-muted-foreground">
                {selectedIds.size} selected
              </span>
            )}
            {exportable && (
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Table container */}
      <div className="overflow-auto" style={{ maxHeight }}>
        <div style={{ minWidth: totalWidth }}>
          {/* Header */}
          <div
            className="flex sticky top-0 z-10 bg-muted/50 border-b"
            style={{ height: headerHeight }}
          >
            {selectable && (
              <div className="flex items-center justify-center w-12 border-r">
                <Checkbox
                  checked={isAllSelected || (isSomeSelected ? 'indeterminate' : false)}
                  onCheckedChange={handleSelectAll}
                />
              </div>
            )}
            {columns.map(column => (
              <div
                key={column.id}
                className={cn(
                  'flex items-center px-4 border-r last:border-r-0 font-medium text-sm',
                  column.sortable && 'cursor-pointer hover:bg-muted/80',
                  column.sticky && 'sticky left-0 bg-muted/50 z-20',
                  column.className
                )}
                style={{
                  width: column.width || column.minWidth || 150,
                  minWidth: column.minWidth || 100,
                  justifyContent: column.align === 'center' ? 'center' : column.align === 'right' ? 'flex-end' : 'flex-start',
                }}
                onClick={() => column.sortable && handleSort(column.id)}
              >
                <span className="truncate">{column.header}</span>
                {column.sortable && (
                  <span className="ml-2">{renderSortIcon(column.id)}</span>
                )}
              </div>
            ))}
          </div>

          {/* Virtual rows */}
          <div
            ref={parentRef}
            className="relative"
            style={{ height: Math.min(sortedData.length * rowHeight, maxHeight - headerHeight) }}
          >
            <div
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: '100%',
                position: 'relative',
              }}
            >
              {sortedData.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-muted-foreground">
                  {emptyMessage}
                </div>
              ) : (
                rowVirtualizer.getVirtualItems().map(virtualRow => {
                  const row = sortedData[virtualRow.index];
                  const rowId = getRowId(row, virtualRow.index);
                  const isSelected = selectedIds.has(rowId);

                  return (
                    <div
                      key={virtualRow.key}
                      className={cn(
                        'flex absolute top-0 left-0 w-full border-b hover:bg-muted/30 transition-colors',
                        isSelected && 'bg-primary/10',
                        onRowClick && 'cursor-pointer'
                      )}
                      style={{
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start}px)`,
                      }}
                      onClick={() => onRowClick?.(row, virtualRow.index)}
                    >
                      {selectable && (
                        <div
                          className="flex items-center justify-center w-12 border-r"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectRow(row, virtualRow.index);
                          }}
                        >
                          <Checkbox checked={isSelected} />
                        </div>
                      )}
                      {columns.map(column => (
                        <div
                          key={column.id}
                          className={cn(
                            'flex items-center px-4 border-r last:border-r-0 text-sm',
                            column.sticky && 'sticky left-0 bg-background z-10',
                            column.className
                          )}
                          style={{
                            width: column.width || column.minWidth || 150,
                            minWidth: column.minWidth || 100,
                            justifyContent: column.align === 'center' ? 'center' : column.align === 'right' ? 'flex-end' : 'flex-start',
                          }}
                        >
                          <span className="truncate">{getCellValue(row, column)}</span>
                        </div>
                      ))}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/30 text-sm text-muted-foreground">
        <span>
          {sortedData.length.toLocaleString()} row{sortedData.length !== 1 ? 's' : ''}
          {searchQuery && ` (filtered from ${data.length.toLocaleString()})`}
        </span>
      </div>
    </div>
  );
}

export default VirtualDataGrid;
