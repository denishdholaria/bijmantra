import { useState, useCallback, useRef } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, X, FileSpreadsheet, Loader2, Eye, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

type ImportFormat = 'csv' | 'json' | 'xlsx';

interface ValidationError {
  row: number;
  column: string;
  value: string;
  message: string;
}

interface ImportResult {
  success: boolean;
  totalRows: number;
  importedRows: number;
  skippedRows: number;
  errors: ValidationError[];
}

interface ColumnMapping {
  sourceColumn: string;
  targetColumn: string;
  required: boolean;
  mapped: boolean;
}

interface DataImportManagerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  expectedColumns: { name: string; required: boolean; type?: string }[];
  onImport: (data: Record<string, unknown>[], mappings: ColumnMapping[]) => Promise<ImportResult>;
  templateUrl?: string;
  maxFileSize?: number; // in MB
}

export function DataImportManager({
  open,
  onOpenChange,
  title = 'Import Data',
  description = 'Upload a CSV or JSON file to import data',
  expectedColumns,
  onImport,
  templateUrl,
  maxFileSize = 10,
}: DataImportManagerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<ImportFormat | null>(null);
  const [parsedData, setParsedData] = useState<Record<string, unknown>[]>([]);
  const [sourceColumns, setSourceColumns] = useState<string[]>([]);
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [step, setStep] = useState<'upload' | 'preview' | 'mapping' | 'importing' | 'result'>('upload');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setFile(null);
    setFormat(null);
    setParsedData([]);
    setSourceColumns([]);
    setMappings([]);
    setStep('upload');
    setProgress(0);
    setResult(null);
    setError(null);
  };

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setError(null);

    // Check file size
    if (selectedFile.size > maxFileSize * 1024 * 1024) {
      setError(`File size exceeds ${maxFileSize}MB limit`);
      return;
    }

    // Detect format
    const extension = selectedFile.name.split('.').pop()?.toLowerCase();
    let detectedFormat: ImportFormat;
    
    if (extension === 'csv' || extension === 'tsv') {
      detectedFormat = 'csv';
    } else if (extension === 'json') {
      detectedFormat = 'json';
    } else if (extension === 'xlsx' || extension === 'xls') {
      detectedFormat = 'xlsx';
    } else {
      setError('Unsupported file format. Please use CSV, JSON, or Excel files.');
      return;
    }

    setFile(selectedFile);
    setFormat(detectedFormat);

    try {
      const data = await parseFile(selectedFile, detectedFormat);
      setParsedData(data);
      
      // Extract columns from first row
      if (data.length > 0) {
        const cols = Object.keys(data[0]);
        setSourceColumns(cols);
        
        // Auto-map columns
        const autoMappings: ColumnMapping[] = expectedColumns.map(expected => {
          const matchedSource = cols.find(
            col => col.toLowerCase() === expected.name.toLowerCase() ||
                   col.toLowerCase().replace(/[_\s]/g, '') === expected.name.toLowerCase().replace(/[_\s]/g, '')
          );
          return {
            sourceColumn: matchedSource || '',
            targetColumn: expected.name,
            required: expected.required,
            mapped: !!matchedSource,
          };
        });
        setMappings(autoMappings);
      }
      
      setStep('preview');
    } catch (err) {
      setError(`Failed to parse file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [expectedColumns, maxFileSize]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleImport = async () => {
    setStep('importing');
    setProgress(0);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress(p => Math.min(p + 5, 90));
    }, 100);

    try {
      const importResult = await onImport(parsedData, mappings);
      setResult(importResult);
      setProgress(100);
      setStep('result');
    } catch (err) {
      setError(`Import failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setStep('preview');
    } finally {
      clearInterval(interval);
    }
  };

  const updateMapping = (targetColumn: string, sourceColumn: string) => {
    setMappings(prev => prev.map(m => 
      m.targetColumn === targetColumn 
        ? { ...m, sourceColumn, mapped: !!sourceColumn }
        : m
    ));
  };

  const requiredMapped = mappings.filter(m => m.required).every(m => m.mapped);

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) reset();
      onOpenChange(isOpen);
    }}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Step: Upload */}
        {step === 'upload' && (
          <div
            className={cn(
              'flex-1 flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg',
              'hover:border-primary/50 hover:bg-muted/50 transition-colors cursor-pointer'
            )}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">Drop file here or click to browse</p>
            <p className="text-sm text-muted-foreground mb-4">
              Supports CSV, JSON, and Excel files (max {maxFileSize}MB)
            </p>
            <div className="flex gap-2">
              <Badge variant="outline"><FileText className="h-3 w-3 mr-1" />CSV</Badge>
              <Badge variant="outline"><FileText className="h-3 w-3 mr-1" />JSON</Badge>
              <Badge variant="outline"><FileSpreadsheet className="h-3 w-3 mr-1" />Excel</Badge>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.tsv,.json,.xlsx,.xls"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              className="hidden"
            />
          </div>
        )}

        {/* Step: Preview */}
        {step === 'preview' && (
          <Tabs defaultValue="preview" className="flex-1 flex flex-col overflow-hidden">
            <TabsList>
              <TabsTrigger value="preview">
                <Eye className="h-4 w-4 mr-2" />
                Preview ({parsedData.length} rows)
              </TabsTrigger>
              <TabsTrigger value="mapping">
                Column Mapping
              </TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="flex-1 overflow-hidden">
              <ScrollArea className="h-[300px] border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      {sourceColumns.slice(0, 6).map((col) => (
                        <TableHead key={col} className="min-w-[120px]">{col}</TableHead>
                      ))}
                      {sourceColumns.length > 6 && (
                        <TableHead>+{sourceColumns.length - 6} more</TableHead>
                      )}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {parsedData.slice(0, 10).map((row, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-muted-foreground">{i + 1}</TableCell>
                        {sourceColumns.slice(0, 6).map((col) => (
                          <TableCell key={col} className="truncate max-w-[150px]">
                            {String(row[col] ?? '')}
                          </TableCell>
                        ))}
                        {sourceColumns.length > 6 && <TableCell>...</TableCell>}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
              {parsedData.length > 10 && (
                <p className="text-xs text-muted-foreground mt-2">
                  Showing first 10 of {parsedData.length} rows
                </p>
              )}
            </TabsContent>

            <TabsContent value="mapping" className="flex-1 overflow-hidden">
              <ScrollArea className="h-[300px]">
                <div className="space-y-3 p-1">
                  {mappings.map((mapping) => (
                    <div key={mapping.targetColumn} className="flex items-center gap-3">
                      <div className="w-1/3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{mapping.targetColumn}</span>
                          {mapping.required && (
                            <Badge variant="destructive" className="text-[10px] px-1">Required</Badge>
                          )}
                        </div>
                      </div>
                      <span className="text-muted-foreground">→</span>
                      <select
                        value={mapping.sourceColumn}
                        onChange={(e) => updateMapping(mapping.targetColumn, e.target.value)}
                        className={cn(
                          'flex-1 h-9 px-3 rounded-md border bg-background text-sm',
                          !mapping.mapped && mapping.required && 'border-destructive'
                        )}
                      >
                        <option value="">-- Select column --</option>
                        {sourceColumns.map((col) => (
                          <option key={col} value={col}>{col}</option>
                        ))}
                      </select>
                      {mapping.mapped ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <X className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        )}

        {/* Step: Importing */}
        {step === 'importing' && (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <p className="text-lg font-medium mb-4">Importing data...</p>
            <Progress value={progress} className="w-64" />
            <p className="text-sm text-muted-foreground mt-2">{progress}%</p>
          </div>
        )}

        {/* Step: Result */}
        {step === 'result' && result && (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            {result.success ? (
              <>
                <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
                <p className="text-xl font-medium mb-2">Import Complete!</p>
                <div className="flex gap-4 text-sm">
                  <Badge variant="secondary">{result.importedRows} imported</Badge>
                  {result.skippedRows > 0 && (
                    <Badge variant="outline">{result.skippedRows} skipped</Badge>
                  )}
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="h-16 w-16 text-amber-500 mb-4" />
                <p className="text-xl font-medium mb-2">Import Completed with Errors</p>
                <div className="flex gap-4 text-sm mb-4">
                  <Badge variant="secondary">{result.importedRows} imported</Badge>
                  <Badge variant="destructive">{result.errors.length} errors</Badge>
                </div>
                {result.errors.length > 0 && (
                  <ScrollArea className="h-32 w-full border rounded-lg p-2">
                    {result.errors.slice(0, 10).map((err, i) => (
                      <p key={i} className="text-xs text-destructive">
                        Row {err.row}: {err.column} - {err.message}
                      </p>
                    ))}
                  </ScrollArea>
                )}
              </>
            )}
          </div>
        )}

        <DialogFooter className="flex-shrink-0">
          {file && step !== 'result' && (
            <div className="flex items-center gap-2 mr-auto">
              <FileText className="h-4 w-4" />
              <span className="text-sm truncate max-w-[200px]">{file.name}</span>
              <Badge variant="outline">{format?.toUpperCase()}</Badge>
            </div>
          )}
          
          {templateUrl && step === 'upload' && (
            <Button variant="outline" asChild>
              <a href={templateUrl} download>
                <Download className="h-4 w-4 mr-2" />
                Download Template
              </a>
            </Button>
          )}

          {step === 'upload' && (
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          )}

          {step === 'preview' && (
            <>
              <Button variant="outline" onClick={reset}>Back</Button>
              <Button onClick={handleImport} disabled={!requiredMapped}>
                Import {parsedData.length} Rows
              </Button>
            </>
          )}

          {step === 'result' && (
            <>
              <Button variant="outline" onClick={reset}>Import Another</Button>
              <Button onClick={() => onOpenChange(false)}>Done</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Parse file based on format
async function parseFile(file: File, format: ImportFormat): Promise<Record<string, unknown>[]> {
  const text = await file.text();

  if (format === 'json') {
    const parsed = JSON.parse(text);
    return Array.isArray(parsed) ? parsed : [parsed];
  }

  if (format === 'csv') {
    return parseCSV(text);
  }

  // For Excel, we'd need a library like xlsx
  throw new Error('Excel parsing requires additional setup');
}

// Simple CSV parser
function parseCSV(text: string): Record<string, unknown>[] {
  const lines = text.split('\n').filter(line => line.trim());
  if (lines.length < 2) return [];

  const headers = parseCSVLine(lines[0]);
  const data: Record<string, unknown>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    const row: Record<string, unknown> = {};
    headers.forEach((header, j) => {
      row[header] = values[j] ?? '';
    });
    data.push(row);
  }

  return data;
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  result.push(current.trim());
  return result;
}
