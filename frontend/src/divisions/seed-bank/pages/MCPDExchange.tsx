/**
 * MCPD Exchange Page
 * 
 * Import and export germplasm passport data using MCPD v2.1 standard.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Download,
  Upload,
  FileSpreadsheet,
  FileJson,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Info,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ValidationError {
  row: number;
  field: string;
  message: string;
}

interface ImportResult {
  success: boolean;
  imported_count: number;
  error_count: number;
  errors: ValidationError[];
}

export default function MCPDExchange() {
  const [activeTab, setActiveTab] = useState('export');
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [previewData, setPreviewData] = useState<any[] | null>(null);

  // Fetch reference codes
  const { data: biologicalStatus } = useQuery({
    queryKey: ['mcpd-biological-status'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/codes/biological-status`);
      if (!res.ok) throw new Error('Failed to fetch codes');
      return res.json();
    },
  });

  const { data: acquisitionSource } = useQuery({
    queryKey: ['mcpd-acquisition-source'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/codes/acquisition-source`);
      if (!res.ok) throw new Error('Failed to fetch codes');
      return res.json();
    },
  });

  const { data: storageType } = useQuery({
    queryKey: ['mcpd-storage-type'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/codes/storage-type`);
      if (!res.ok) throw new Error('Failed to fetch codes');
      return res.json();
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async (format: 'csv' | 'json') => {
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/export/${format}`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mcpd_export_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
    onSuccess: () => {
      toast.success('Export completed successfully');
    },
    onError: () => {
      toast.error('Export failed');
    },
  });

  // Download template
  const downloadTemplate = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/template`);
      if (!res.ok) throw new Error('Failed to download template');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'mcpd_template.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Template downloaded');
    } catch {
      toast.error('Failed to download template');
    }
  };

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/api/v2/seed-bank/mcpd/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Import failed');
      }
      return res.json();
    },
    onSuccess: (data) => {
      setImportResult(data);
      if (data.imported_count > 0) {
        toast.success(`Imported ${data.imported_count} accessions`);
      }
      if (data.error_count > 0) {
        toast.warning(`${data.error_count} rows had errors`);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setImportResult(null);
      setPreviewData(null);

      // Preview CSV
      if (file.name.endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target?.result as string;
          const lines = text.split('\n').slice(0, 6); // Header + 5 rows
          const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));
          const rows = lines.slice(1).map((line) => {
            const values = line.split(',').map((v) => v.trim().replace(/"/g, ''));
            return headers.reduce((obj, header, i) => {
              obj[header] = values[i] || '';
              return obj;
            }, {} as Record<string, string>);
          });
          setPreviewData(rows.filter((r) => Object.values(r).some((v) => v)));
        };
        reader.readAsText(file);
      }
    }
  };

  const biologicalStatusCodes = biologicalStatus?.codes || [];
  const acquisitionSourceCodes = acquisitionSource?.codes || [];
  const storageTypeCodes = storageType?.codes || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileSpreadsheet className="h-6 w-6" />
          MCPD Data Exchange
        </h1>
        <p className="text-muted-foreground">
          Import and export germplasm passport data using FAO/Bioversity MCPD v2.1 standard
        </p>
      </div>

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">Multi-Crop Passport Descriptors (MCPD) v2.1</p>
              <p className="mt-1">
                International standard for germplasm passport data exchange between genebanks.
                Includes 49 standardized fields for accession identification, collection, and
                characterization.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="export">
            <Download className="h-4 w-4 mr-2" />
            Export
          </TabsTrigger>
          <TabsTrigger value="import">
            <Upload className="h-4 w-4 mr-2" />
            Import
          </TabsTrigger>
          <TabsTrigger value="codes">Reference Codes</TabsTrigger>
        </TabsList>

        {/* Export Tab */}
        <TabsContent value="export" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Export Accessions</CardTitle>
              <CardDescription>
                Export all accessions in MCPD v2.1 format
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Export Format</Label>
                <Select
                  value={exportFormat}
                  onValueChange={(v) => setExportFormat(v as 'csv' | 'json')}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">
                      <div className="flex items-center gap-2">
                        <FileSpreadsheet className="h-4 w-4" />
                        CSV (Spreadsheet)
                      </div>
                    </SelectItem>
                    <SelectItem value="json">
                      <div className="flex items-center gap-2">
                        <FileJson className="h-4 w-4" />
                        JSON (API)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={() => exportMutation.mutate(exportFormat)}
                disabled={exportMutation.isPending}
              >
                <Download className="h-4 w-4 mr-2" />
                {exportMutation.isPending ? 'Exporting...' : `Export as ${exportFormat.toUpperCase()}`}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Import Tab */}
        <TabsContent value="import" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Import Accessions</CardTitle>
              <CardDescription>
                Import accessions from MCPD CSV file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Button variant="outline" onClick={downloadTemplate}>
                  <Download className="h-4 w-4 mr-2" />
                  Download Template
                </Button>
              </div>

              <div className="space-y-2">
                <Label>Select CSV File</Label>
                <Input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="cursor-pointer"
                />
              </div>

              {selectedFile && (
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm">
                    <span className="font-medium">Selected:</span> {selectedFile.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              )}

              {/* Preview */}
              {previewData && previewData.length > 0 && (
                <div className="space-y-2">
                  <Label>Preview (first 5 rows)</Label>
                  <div className="border rounded-lg overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {Object.keys(previewData[0]).slice(0, 6).map((key) => (
                            <TableHead key={key} className="text-xs whitespace-nowrap">
                              {key}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {previewData.map((row, i) => (
                          <TableRow key={i}>
                            {Object.values(row).slice(0, 6).map((val, j) => (
                              <TableCell key={j} className="text-xs">
                                {String(val).substring(0, 20)}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              <Button
                onClick={() => selectedFile && importMutation.mutate(selectedFile)}
                disabled={!selectedFile || importMutation.isPending}
              >
                <Upload className="h-4 w-4 mr-2" />
                {importMutation.isPending ? 'Importing...' : 'Import Data'}
              </Button>

              {/* Import Result */}
              {importResult && (
                <Card className={importResult.error_count > 0 ? 'border-amber-200' : 'border-green-200'}>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4 mb-4">
                      {importResult.error_count === 0 ? (
                        <CheckCircle2 className="h-8 w-8 text-green-500" />
                      ) : (
                        <AlertCircle className="h-8 w-8 text-amber-500" />
                      )}
                      <div>
                        <p className="font-medium">Import Complete</p>
                        <p className="text-sm text-muted-foreground">
                          {importResult.imported_count} imported, {importResult.error_count} errors
                        </p>
                      </div>
                    </div>

                    {importResult.errors.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-red-600">Errors:</p>
                        <div className="max-h-[200px] overflow-y-auto space-y-1">
                          {importResult.errors.map((err, i) => (
                            <div key={i} className="text-xs p-2 bg-red-50 rounded flex items-start gap-2">
                              <XCircle className="h-3 w-3 text-red-500 mt-0.5" />
                              <span>
                                Row {err.row}: {err.field} - {err.message}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reference Codes Tab */}
        <TabsContent value="codes" className="space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            {/* Biological Status */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Biological Status (SAMPSTAT)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-[300px] overflow-y-auto space-y-1">
                  {biologicalStatusCodes.map((code: any) => (
                    <div key={code.code} className="flex items-center gap-2 text-sm p-1">
                      <Badge variant="outline" className="w-10 justify-center">
                        {code.code}
                      </Badge>
                      <span className="text-xs">{code.description}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Acquisition Source */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Acquisition Source (COLLSRC)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-[300px] overflow-y-auto space-y-1">
                  {acquisitionSourceCodes.map((code: any) => (
                    <div key={code.code} className="flex items-center gap-2 text-sm p-1">
                      <Badge variant="outline" className="w-10 justify-center">
                        {code.code}
                      </Badge>
                      <span className="text-xs">{code.description}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Storage Type */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Storage Type (STORAGE)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-[300px] overflow-y-auto space-y-1">
                  {storageTypeCodes.map((code: any) => (
                    <div key={code.code} className="flex items-center gap-2 text-sm p-1">
                      <Badge variant="outline" className="w-10 justify-center">
                        {code.code}
                      </Badge>
                      <span className="text-xs">{code.description}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
