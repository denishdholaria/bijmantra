/**
 * Label Printing Page
 * Generate and print labels for samples, plots, and seed packets
 * Connected to /api/v2/labels endpoints
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';

interface LabelTemplate {
  id: string;
  name: string;
  type: string;
  size: string;
  fields: string[];
  barcode_type: string;
  is_default?: boolean;
}

interface LabelData {
  id: string;
  [key: string]: any;
}

export function LabelPrinting() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('plot-standard');
  const [sourceType, setSourceType] = useState<string>('plots');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [copies, setCopies] = useState(1);
  const [activeTab, setActiveTab] = useState('print');
  const queryClient = useQueryClient();

  // Fetch templates
  const { data: templatesData, isLoading: loadingTemplates } = useQuery({
    queryKey: ['label-templates'],
    queryFn: () => apiClient.getLabelTemplates(),
  });

  // Fetch label data based on source type
  const { data: labelData, isLoading: loadingData } = useQuery({
    queryKey: ['label-data', sourceType],
    queryFn: () => apiClient.getLabelData(sourceType),
  });

  // Fetch print job history
  const { data: jobsData } = useQuery({
    queryKey: ['label-jobs'],
    queryFn: () => apiClient.getLabelPrintJobs(undefined, 20),
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['label-stats'],
    queryFn: () => apiClient.getLabelPrintingStats(),
  });

  // Create print job mutation
  const createJob = useMutation({
    mutationFn: (data: { template_id: string; items: any[]; copies: number }) =>
      apiClient.createLabelPrintJob(data),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: ['label-jobs'] });
      queryClient.invalidateQueries({ queryKey: ['label-stats'] });
      toast.success(`Print job created: ${job.label_count * job.copies} labels`);
      // Simulate completion
      setTimeout(() => {
        apiClient.updateLabelPrintJobStatus(job.id, 'completed');
        queryClient.invalidateQueries({ queryKey: ['label-jobs'] });
        queryClient.invalidateQueries({ queryKey: ['label-stats'] });
      }, 2000);
    },
    onError: () => {
      toast.error('Failed to create print job');
    },
  });

  const templates: LabelTemplate[] = templatesData?.templates || [];
  const data: LabelData[] = labelData?.data || [];
  const jobs = jobsData?.jobs || [];
  const template = templates.find(t => t.id === selectedTemplate);
  const selectedCount = selectedItems.size;

  const toggleSelection = (id: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedItems(new Set(data.map(d => d.id)));
  };

  const deselectAll = () => {
    setSelectedItems(new Set());
  };

  const handlePrint = () => {
    if (selectedCount === 0) {
      toast.error('Please select items to print');
      return;
    }
    const items = data.filter(d => selectedItems.has(d.id));
    createJob.mutate({
      template_id: selectedTemplate,
      items,
      copies,
    });
  };

  const handleExport = () => {
    if (selectedCount === 0) {
      toast.error('Please select items to export');
      return;
    }
    const items = data.filter(d => selectedItems.has(d.id));
    const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `labels-${sourceType}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exported ${selectedCount} labels`);
  };

  const getFieldValue = (item: LabelData, field: string): string => {
    const fieldMap: Record<string, string> = {
      plot_id: item.plot_id || item.plotId || '',
      germplasm: item.germplasm || '',
      rep: item.rep || '',
      lot_number: item.lot_number || item.lotNumber || '',
      harvest_date: item.harvest_date || item.harvestDate || '',
      weight: item.weight || '',
      sample_id: item.sample_id || item.sampleId || '',
      date: item.date || '',
      entry: item.entry || '',
      row: item.row?.toString() || '',
      column: item.column?.toString() || '',
      accession_id: item.accession_id || '',
      species: item.species || '',
      origin: item.origin || '',
      collection_date: item.collection_date || '',
    };
    return fieldMap[field] || item[field] || '';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Label Printing</h1>
          <p className="text-muted-foreground mt-1">Generate labels for plots, seeds, and samples</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>Export</Button>
          <Button onClick={handlePrint} disabled={createJob.isPending}>
            {createJob.isPending ? 'Creating...' : 'Print Labels'}
          </Button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-primary">{stats.total_labels_printed}</p>
              <p className="text-xs text-muted-foreground">Labels Printed</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-green-600">{stats.completed_jobs}</p>
              <p className="text-xs text-muted-foreground">Completed Jobs</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.templates_count}</p>
              <p className="text-xs text-muted-foreground">Templates</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-orange-600">{stats.pending_jobs}</p>
              <p className="text-xs text-muted-foreground">Pending Jobs</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="print">Print Labels</TabsTrigger>
          <TabsTrigger value="history">Print History ({jobs.length})</TabsTrigger>
          <TabsTrigger value="templates">Templates ({templates.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="print" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Template Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Label Template</CardTitle>
                <CardDescription>Choose a label format</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Data Source</Label>
                  <Select value={sourceType} onValueChange={setSourceType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="plots">Plots</SelectItem>
                      <SelectItem value="seedlots">Seed Lots</SelectItem>
                      <SelectItem value="samples">Samples</SelectItem>
                      <SelectItem value="accessions">Accessions</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Template</Label>
                  {loadingTemplates ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.map(t => (
                          <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                {template && (
                  <div className="p-4 bg-muted rounded-lg space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Size:</span>
                      <span className="font-medium">{template.size}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Type:</span>
                      <Badge variant="outline" className="capitalize">{template.type}</Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Barcode:</span>
                      <Badge variant="secondary">{template.barcode_type.toUpperCase()}</Badge>
                    </div>
                    <div className="text-sm">
                      <span>Fields:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {template.fields.map(f => (
                          <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Copies per label</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={copies}
                    onChange={(e) => setCopies(parseInt(e.target.value) || 1)}
                  />
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg">
                  <p className="text-sm font-medium text-green-700 dark:text-green-300">
                    {selectedCount} items selected
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400">
                    Total labels: {selectedCount * copies}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Data Selection */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Select Items</CardTitle>
                    <CardDescription>Choose items to print labels for</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={selectAll}>Select All</Button>
                    <Button size="sm" variant="outline" onClick={deselectAll}>Clear</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loadingData ? (
                  <div className="space-y-2">
                    {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 w-full" />)}
                  </div>
                ) : data.length > 0 ? (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {data.map((item) => (
                      <div
                        key={item.id}
                        className={`flex items-center gap-4 p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedItems.has(item.id) ? 'bg-green-50 dark:bg-green-950/20 border-green-200' : 'hover:bg-muted/50'
                        }`}
                        onClick={() => toggleSelection(item.id)}
                      >
                        <Checkbox checked={selectedItems.has(item.id)} />
                        <div className="flex-1 grid grid-cols-3 gap-4 text-sm">
                          {template?.fields.slice(0, 3).map(field => (
                            <div key={field}>
                              <p className="font-medium truncate">{getFieldValue(item, field) || '-'}</p>
                              <p className="text-xs text-muted-foreground capitalize">{field.replace('_', ' ')}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>No data available for {sourceType}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Label Preview</CardTitle>
              <CardDescription>Preview of selected label template</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 overflow-x-auto pb-4">
                {data.filter(d => selectedItems.has(d.id)).slice(0, 4).map((item) => (
                  <div
                    key={item.id}
                    className="flex-shrink-0 w-48 h-24 border-2 border-dashed border-gray-300 rounded-lg p-3 bg-white dark:bg-gray-900"
                  >
                    <div className="text-xs space-y-1">
                      {template?.fields.slice(0, 3).map(field => (
                        <p key={field} className="truncate">
                          <span className="text-muted-foreground">{field}: </span>
                          <span className="font-medium">{getFieldValue(item, field)}</span>
                        </p>
                      ))}
                      {template?.fields.includes('barcode') && (
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mt-1" title="Barcode placeholder"></div>
                      )}
                    </div>
                  </div>
                ))}
                {selectedCount > 4 && (
                  <div className="flex-shrink-0 w-48 h-24 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-muted-foreground">
                    +{selectedCount - 4} more
                  </div>
                )}
                {selectedCount === 0 && (
                  <div className="w-full text-center py-4 text-muted-foreground">
                    Select items to preview labels
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Print History</CardTitle>
              <CardDescription>Recent print jobs</CardDescription>
            </CardHeader>
            <CardContent>
              {jobs.length > 0 ? (
                <div className="space-y-3">
                  {jobs.map((job: any) => (
                    <div key={job.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{job.template_id}</p>
                        <p className="text-sm text-muted-foreground">
                          {job.label_count} labels × {job.copies} copies
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant={job.status === 'completed' ? 'default' : 'secondary'}>
                          {job.status}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(job.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No print jobs yet
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Available Templates</CardTitle>
              <CardDescription>Label templates for different use cases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((t) => (
                  <div key={t.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{t.name}</h4>
                      {t.is_default && <Badge variant="secondary">Default</Badge>}
                    </div>
                    <div className="space-y-1 text-sm text-muted-foreground">
                      <p>Size: {t.size}</p>
                      <p>Type: {t.type}</p>
                      <p>Barcode: {t.barcode_type}</p>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {t.fields.map(f => (
                        <Badge key={f} variant="outline" className="text-xs">{f}</Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
