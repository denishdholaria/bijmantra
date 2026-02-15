import { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, FileText, Loader2, Check, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

type ExportFormat = 'csv' | 'xlsx' | 'json' | 'tsv';

interface Column {
  id: string;
  label: string;
  selected: boolean;
}

interface DataExportManagerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: Record<string, unknown>[];
  columns: Column[];
  filename?: string;
  title?: string;
  onExport?: (format: ExportFormat, selectedColumns: string[], options: ExportOptions) => void;
}

interface ExportOptions {
  includeHeaders: boolean;
  dateFormat: string;
  numberFormat: string;
  nullValue: string;
  encoding: string;
}

const FORMAT_INFO: Record<ExportFormat, { icon: React.ReactNode; label: string; description: string }> = {
  csv: { icon: <FileText className="h-5 w-5" />, label: 'CSV', description: 'Comma-separated values, universal compatibility' },
  xlsx: { icon: <FileSpreadsheet className="h-5 w-5" />, label: 'Excel', description: 'Microsoft Excel format with formatting' },
  json: { icon: <FileJson className="h-5 w-5" />, label: 'JSON', description: 'JavaScript Object Notation for APIs' },
  tsv: { icon: <FileText className="h-5 w-5" />, label: 'TSV', description: 'Tab-separated values for spreadsheets' },
};

export function DataExportManager({
  open,
  onOpenChange,
  data,
  columns: initialColumns,
  filename = 'export',
  title = 'Export Data',
  onExport,
}: DataExportManagerProps) {
  const [format, setFormat] = useState<ExportFormat>('csv');
  const [columns, setColumns] = useState<Column[]>(initialColumns);
  const [isExporting, setIsExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [options, setOptions] = useState<ExportOptions>({
    includeHeaders: true,
    dateFormat: 'YYYY-MM-DD',
    numberFormat: 'decimal',
    nullValue: '',
    encoding: 'utf-8',
  });

  const selectedCount = columns.filter(c => c.selected).length;

  const toggleColumn = (id: string) => {
    setColumns(cols => cols.map(c => c.id === id ? { ...c, selected: !c.selected } : c));
  };

  const selectAll = () => {
    setColumns(cols => cols.map(c => ({ ...c, selected: true })));
  };

  const selectNone = () => {
    setColumns(cols => cols.map(c => ({ ...c, selected: false })));
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportComplete(false);

    const selectedColumns = columns.filter(c => c.selected).map(c => c.id);

    try {
      if (onExport) {
        await onExport(format, selectedColumns, options);
      } else {
        // Default export implementation
        await defaultExport(data, selectedColumns, format, filename, options);
      }
      setExportComplete(true);
      setTimeout(() => {
        onOpenChange(false);
        setExportComplete(false);
      }, 1500);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            {title}
          </DialogTitle>
          <DialogDescription>
            Export {data.length.toLocaleString()} records to your preferred format
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="format" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="format">Format</TabsTrigger>
            <TabsTrigger value="columns">Columns ({selectedCount})</TabsTrigger>
            <TabsTrigger value="options">Options</TabsTrigger>
          </TabsList>

          {/* Format Selection */}
          <TabsContent value="format" className="space-y-4">
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as ExportFormat)}>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(FORMAT_INFO).map(([key, info]) => (
                  <label
                    key={key}
                    className={cn(
                      'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors',
                      format === key ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'
                    )}
                  >
                    <RadioGroupItem value={key} className="mt-1" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {info.icon}
                        <span className="font-medium">{info.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{info.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </RadioGroup>
          </TabsContent>

          {/* Column Selection */}
          <TabsContent value="columns" className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {selectedCount} of {columns.length} columns selected
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={selectAll}>Select All</Button>
                <Button variant="outline" size="sm" onClick={selectNone}>Clear</Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {columns.map((column) => (
                <label
                  key={column.id}
                  className={cn(
                    'flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors',
                    column.selected ? 'bg-primary/10' : 'hover:bg-muted/50'
                  )}
                >
                  <Checkbox
                    checked={column.selected}
                    onCheckedChange={() => toggleColumn(column.id)}
                  />
                  <span className="text-sm truncate">{column.label}</span>
                </label>
              ))}
            </div>
          </TabsContent>

          {/* Export Options */}
          <TabsContent value="options" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="headers">Include column headers</Label>
                <Checkbox
                  id="headers"
                  checked={options.includeHeaders}
                  onCheckedChange={(checked) => setOptions({ ...options, includeHeaders: !!checked })}
                />
              </div>

              <div className="space-y-2">
                <Label>Date format</Label>
                <Select
                  value={options.dateFormat}
                  onValueChange={(v: string) => setOptions({ ...options, dateFormat: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="YYYY-MM-DD">YYYY-MM-DD (ISO)</SelectItem>
                    <SelectItem value="MM/DD/YYYY">MM/DD/YYYY (US)</SelectItem>
                    <SelectItem value="DD/MM/YYYY">DD/MM/YYYY (EU)</SelectItem>
                    <SelectItem value="DD-MMM-YYYY">DD-MMM-YYYY</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Empty values</Label>
                <Select
                  value={options.nullValue || '__empty__'}
                  onValueChange={(v: string) => setOptions({ ...options, nullValue: v === '__empty__' ? '' : v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__empty__">Empty string</SelectItem>
                    <SelectItem value="NA">NA</SelectItem>
                    <SelectItem value="NULL">NULL</SelectItem>
                    <SelectItem value="-">-</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Encoding</Label>
                <Select
                  value={options.encoding}
                  onValueChange={(v: string) => setOptions({ ...options, encoding: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="utf-8">UTF-8 (Recommended)</SelectItem>
                    <SelectItem value="utf-16">UTF-16</SelectItem>
                    <SelectItem value="ascii">ASCII</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-6">
          <div className="flex items-center gap-2 mr-auto">
            <Badge variant="outline">{data.length.toLocaleString()} rows</Badge>
            <Badge variant="outline">{selectedCount} columns</Badge>
            <Badge variant="secondary">{FORMAT_INFO[format].label}</Badge>
          </div>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleExport} disabled={isExporting || selectedCount === 0}>
            {isExporting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : exportComplete ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Done!
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Export
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Default export implementation
async function defaultExport(
  data: Record<string, unknown>[],
  columns: string[],
  format: ExportFormat,
  filename: string,
  options: ExportOptions
) {
  let content: string;
  let mimeType: string;
  let extension: string;

  const filteredData = data.map(row => {
    const filtered: Record<string, unknown> = {};
    columns.forEach(col => {
      let value = row[col];
      if (value === null || value === undefined) {
        value = options.nullValue;
      }
      filtered[col] = value;
    });
    return filtered;
  });

  switch (format) {
    case 'json':
      content = JSON.stringify(filteredData, null, 2);
      mimeType = 'application/json';
      extension = 'json';
      break;

    case 'tsv':
      content = convertToDelimited(filteredData, columns, '\t', options);
      mimeType = 'text/tab-separated-values';
      extension = 'tsv';
      break;

    case 'csv':
    default:
      content = convertToDelimited(filteredData, columns, ',', options);
      mimeType = 'text/csv';
      extension = 'csv';
      break;
  }

  // Create and download file
  const blob = new Blob([content], { type: `${mimeType};charset=${options.encoding}` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.${extension}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function convertToDelimited(
  data: Record<string, unknown>[],
  columns: string[],
  delimiter: string,
  options: ExportOptions
): string {
  const lines: string[] = [];

  if (options.includeHeaders) {
    lines.push(columns.join(delimiter));
  }

  data.forEach(row => {
    const values = columns.map(col => {
      const value = row[col];
      if (value === null || value === undefined) return options.nullValue;
      const str = String(value);
      // Escape quotes and wrap in quotes if contains delimiter or quotes
      if (str.includes(delimiter) || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    });
    lines.push(values.join(delimiter));
  });

  return lines.join('\n');
}

// Hook for easy usage
export function useDataExport() {
  const [isOpen, setIsOpen] = useState(false);
  const [exportData, setExportData] = useState<{
    data: Record<string, unknown>[];
    columns: Column[];
    filename?: string;
    title?: string;
  } | null>(null);

  const openExport = (
    data: Record<string, unknown>[],
    columns: Column[],
    filename?: string,
    title?: string
  ) => {
    setExportData({ data, columns, filename, title });
    setIsOpen(true);
  };

  const closeExport = () => {
    setIsOpen(false);
    setExportData(null);
  };

  return {
    isOpen,
    exportData,
    openExport,
    closeExport,
    setIsOpen,
  };
}
