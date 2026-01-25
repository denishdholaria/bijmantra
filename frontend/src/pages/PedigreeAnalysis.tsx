/**
 * Pedigree Analysis Page
 * 
 * Relationship matrices, inbreeding coefficients, and pedigree visualization.
 * Connects to /api/v2/pedigree endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
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
import {
  GitBranch,
  Users,
  Calculator,
  Upload,
  Search,
  TreeDeciduous,
  ArrowUp,
  ArrowDown,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import { pedigreeAnalysisAPI, PedigreeIndividual, PedigreeStats, PedigreeRecord } from '@/lib/api-client';

// Default pedigree example for loading
const EXAMPLE_PEDIGREE = `F1,,
F2,,
F3,,
G1,F1,F2
G2,F1,F3
G3,G1,G2
H1,G1,G3
H2,G2,G3`;

export function PedigreeAnalysis() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('individuals');
  const [pedigreeText, setPedigreeText] = useState(EXAMPLE_PEDIGREE);
  const [generationFilter, setGenerationFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndividual, setSelectedIndividual] = useState<string>('');
  const [coancestryId1, setCoancestryId1] = useState('');
  const [coancestryId2, setCoancestryId2] = useState('');

  // Fetch pedigree stats
  const { data: statsData, isLoading: isLoadingStats } = useQuery({
    queryKey: ['pedigree-stats'],
    queryFn: () => pedigreeAnalysisAPI.getStats(),
  });

  // Fetch individuals
  const { data: individualsData, isLoading: isLoadingIndividuals } = useQuery({
    queryKey: ['pedigree-individuals', generationFilter],
    queryFn: () => pedigreeAnalysisAPI.getIndividuals(
      generationFilter !== 'all' ? parseInt(generationFilter) : undefined
    ),
  });

  // Load pedigree mutation
  const loadPedigreeMutation = useMutation({
    mutationFn: async () => {
      const lines = pedigreeText.trim().split('\n');
      const pedigree: PedigreeRecord[] = lines.map(line => {
        const [id, sire_id, dam_id] = line.split(',').map(s => s.trim());
        return {
          id,
          sire_id: sire_id || null,
          dam_id: dam_id || null,
        };
      });
      return pedigreeAnalysisAPI.loadPedigree(pedigree);
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Pedigree loaded successfully');
      queryClient.invalidateQueries({ queryKey: ['pedigree-stats'] });
      queryClient.invalidateQueries({ queryKey: ['pedigree-individuals'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to load pedigree: ${error.message}`);
    },
  });

  // Calculate coancestry mutation
  const coancestryMutation = useMutation({
    mutationFn: () => pedigreeAnalysisAPI.calculateCoancestry(coancestryId1, coancestryId2),
    onError: (error: Error) => {
      toast.error(`Failed to calculate coancestry: ${error.message}`);
    },
  });

  // Get ancestors mutation
  const ancestorsMutation = useMutation({
    mutationFn: (id: string) => pedigreeAnalysisAPI.getAncestors(id, 4),
    onError: (error: Error) => {
      toast.error(`Failed to get ancestors: ${error.message}`);
    },
  });

  // Get descendants mutation
  const descendantsMutation = useMutation({
    mutationFn: (id: string) => pedigreeAnalysisAPI.getDescendants(id, 3),
    onError: (error: Error) => {
      toast.error(`Failed to get descendants: ${error.message}`);
    },
  });

  const getRelationshipLabel = (coancestry: number): string => {
    if (coancestry >= 0.5) return 'Same individual';
    if (coancestry >= 0.25) return 'Full siblings / Parent-offspring';
    if (coancestry >= 0.125) return 'Half siblings / Grandparent';
    if (coancestry >= 0.0625) return 'First cousins';
    if (coancestry >= 0.03125) return 'Second cousins';
    if (coancestry > 0) return 'Distant relatives';
    return 'Unrelated';
  };

  const getInbreedingColor = (f: number): string => {
    if (f >= 0.25) return 'text-red-600';
    if (f >= 0.125) return 'text-orange-600';
    if (f >= 0.0625) return 'text-yellow-600';
    return 'text-green-600';
  };

  const stats: PedigreeStats = statsData?.success ? statsData : {
    n_individuals: 0,
    n_founders: 0,
    n_generations: 0,
    avg_inbreeding: 0,
    max_inbreeding: 0,
    completeness_index: 0,
  };

  const individuals: PedigreeIndividual[] = individualsData?.individuals || [];

  // Filter individuals by search
  const filteredIndividuals = individuals.filter(ind =>
    ind.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const generations = [...new Set(individuals.map(i => i.generation))].sort();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <GitBranch className="h-6 w-6" />
          Pedigree Analysis
        </h1>
        <p className="text-muted-foreground">
          Relationship matrices, inbreeding coefficients, and ancestry tracing
        </p>
      </div>

      {/* Stats */}
      {isLoadingStats ? (
        <div className="grid grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{stats.n_individuals}</p>
                <p className="text-xs text-muted-foreground">Individuals</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{stats.n_founders}</p>
                <p className="text-xs text-muted-foreground">Founders</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{stats.n_generations}</p>
                <p className="text-xs text-muted-foreground">Generations</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className={`text-2xl font-bold ${getInbreedingColor(stats.avg_inbreeding)}`}>
                  {(stats.avg_inbreeding * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-muted-foreground">Avg Inbreeding</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className={`text-2xl font-bold ${getInbreedingColor(stats.max_inbreeding)}`}>
                  {(stats.max_inbreeding * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-muted-foreground">Max Inbreeding</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{(stats.completeness_index * 100).toFixed(0)}%</p>
                <p className="text-xs text-muted-foreground">Completeness</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="individuals">
            <Users className="h-4 w-4 mr-2" />
            Individuals ({filteredIndividuals.length})
          </TabsTrigger>
          <TabsTrigger value="load">
            <Upload className="h-4 w-4 mr-2" />
            Load Pedigree
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <Calculator className="h-4 w-4 mr-2" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="trace">
            <TreeDeciduous className="h-4 w-4 mr-2" />
            Trace Ancestry
          </TabsTrigger>
        </TabsList>

        {/* Individuals Tab */}
        <TabsContent value="individuals">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pedigree Records</CardTitle>
                  <CardDescription>All individuals in the pedigree</CardDescription>
                </div>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-[200px]"
                    />
                  </div>
                  <Select value={generationFilter} onValueChange={setGenerationFilter}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="Generation" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Generations</SelectItem>
                      {generations.map(gen => (
                        <SelectItem key={gen} value={gen.toString()}>
                          Generation {gen}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingIndividuals ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map(i => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : filteredIndividuals.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No pedigree data loaded. Use the "Load Pedigree" tab to add data.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Sire</TableHead>
                      <TableHead>Dam</TableHead>
                      <TableHead>Generation</TableHead>
                      <TableHead>Inbreeding (F)</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredIndividuals.map(ind => (
                      <TableRow key={ind.id}>
                        <TableCell className="font-medium">{ind.id}</TableCell>
                        <TableCell>{ind.sire_id || <span className="text-muted-foreground">-</span>}</TableCell>
                        <TableCell>{ind.dam_id || <span className="text-muted-foreground">-</span>}</TableCell>
                        <TableCell>
                          <Badge variant="outline">Gen {ind.generation}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className={getInbreedingColor(ind.inbreeding)}>
                            {(ind.inbreeding * 100).toFixed(2)}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setSelectedIndividual(ind.id);
                                ancestorsMutation.mutate(ind.id);
                                setActiveTab('trace');
                              }}
                            >
                              <ArrowUp className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setSelectedIndividual(ind.id);
                                descendantsMutation.mutate(ind.id);
                                setActiveTab('trace');
                              }}
                            >
                              <ArrowDown className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Load Tab */}
        <TabsContent value="load">
          <Card>
            <CardHeader>
              <CardTitle>Load Pedigree Data</CardTitle>
              <CardDescription>
                Enter pedigree in CSV format: ID, Sire, Dam (one per line). Leave parent blank for founders.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={pedigreeText}
                onChange={(e) => setPedigreeText(e.target.value)}
                placeholder="F1,,&#10;F2,,&#10;G1,F1,F2"
                className="font-mono h-64"
              />
              <div className="flex gap-2">
                <Button
                  onClick={() => loadPedigreeMutation.mutate()}
                  disabled={!pedigreeText || loadPedigreeMutation.isPending}
                >
                  {loadPedigreeMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    'Load Pedigree'
                  )}
                </Button>
                <Button variant="outline" onClick={() => setPedigreeText(EXAMPLE_PEDIGREE)}>
                  Load Example
                </Button>
              </div>
              <div className="text-sm text-muted-foreground">
                <p className="font-medium mb-2">Format Guide:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Each line: ID,Sire,Dam</li>
                  <li>Founders: leave Sire and Dam empty (e.g., "F1,,")</li>
                  <li>Parents must be defined before offspring</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Coancestry Calculator</CardTitle>
                <CardDescription>Calculate coefficient of coancestry between two individuals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Individual 1</Label>
                    <Select value={coancestryId1} onValueChange={setCoancestryId1}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {individuals.map(ind => (
                          <SelectItem key={ind.id} value={ind.id}>{ind.id}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Individual 2</Label>
                    <Select value={coancestryId2} onValueChange={setCoancestryId2}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        {individuals.map(ind => (
                          <SelectItem key={ind.id} value={ind.id}>{ind.id}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  onClick={() => coancestryMutation.mutate()}
                  disabled={!coancestryId1 || !coancestryId2 || coancestryMutation.isPending}
                  className="w-full"
                >
                  {coancestryMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Calculating...
                    </>
                  ) : (
                    'Calculate Coancestry'
                  )}
                </Button>
                {coancestryMutation.data?.success && (
                  <div className="p-4 border rounded-lg bg-muted/50">
                    <div className="text-center">
                      <p className="text-3xl font-bold">{(coancestryMutation.data.coancestry * 100).toFixed(2)}%</p>
                      <p className="text-sm text-muted-foreground">Coefficient of Coancestry (θ)</p>
                      <Badge className="mt-2">
                        {coancestryMutation.data.relationship || getRelationshipLabel(coancestryMutation.data.coancestry)}
                      </Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Relationship Reference</CardTitle>
                <CardDescription>Expected coancestry values</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between p-2 border rounded">
                    <span>Same individual</span>
                    <span className="font-mono">θ = 0.50</span>
                  </div>
                  <div className="flex justify-between p-2 border rounded">
                    <span>Full siblings / Parent-offspring</span>
                    <span className="font-mono">θ = 0.25</span>
                  </div>
                  <div className="flex justify-between p-2 border rounded">
                    <span>Half siblings / Grandparent</span>
                    <span className="font-mono">θ = 0.125</span>
                  </div>
                  <div className="flex justify-between p-2 border rounded">
                    <span>First cousins</span>
                    <span className="font-mono">θ = 0.0625</span>
                  </div>
                  <div className="flex justify-between p-2 border rounded">
                    <span>Second cousins</span>
                    <span className="font-mono">θ = 0.03125</span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  Coancestry (θ) equals the expected inbreeding coefficient of offspring.
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Trace Tab */}
        <TabsContent value="trace">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowUp className="h-5 w-5" />
                  Ancestors
                </CardTitle>
                <CardDescription>Trace ancestry of an individual</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={selectedIndividual} onValueChange={setSelectedIndividual}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select individual" />
                    </SelectTrigger>
                    <SelectContent>
                      {individuals.map(ind => (
                        <SelectItem key={ind.id} value={ind.id}>{ind.id}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={() => selectedIndividual && ancestorsMutation.mutate(selectedIndividual)}
                    disabled={!selectedIndividual || ancestorsMutation.isPending}
                  >
                    {ancestorsMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Trace'}
                  </Button>
                </div>
                {ancestorsMutation.data?.success && (
                  <div className="p-4 border rounded-lg">
                    <p className="font-medium mb-2">Ancestors of {ancestorsMutation.data.individual_id}</p>
                    <div className="text-sm space-y-1">
                      <p>Sire: {ancestorsMutation.data.sire_id || 'Unknown'}</p>
                      <p>Dam: {ancestorsMutation.data.dam_id || 'Unknown'}</p>
                      <p>Total ancestors found: {ancestorsMutation.data.n_ancestors || 0}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowDown className="h-5 w-5" />
                  Descendants
                </CardTitle>
                <CardDescription>Find descendants of an individual</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={selectedIndividual} onValueChange={setSelectedIndividual}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select individual" />
                    </SelectTrigger>
                    <SelectContent>
                      {individuals.map(ind => (
                        <SelectItem key={ind.id} value={ind.id}>{ind.id}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={() => selectedIndividual && descendantsMutation.mutate(selectedIndividual)}
                    disabled={!selectedIndividual || descendantsMutation.isPending}
                  >
                    {descendantsMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Find'}
                  </Button>
                </div>
                {descendantsMutation.data?.success && (
                  <div className="p-4 border rounded-lg">
                    <p className="font-medium mb-2">Descendants of {descendantsMutation.data.individual_id}</p>
                    <div className="text-sm">
                      <p>Total descendants: {descendantsMutation.data.n_descendants || 0}</p>
                      {descendantsMutation.data.descendants && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {descendantsMutation.data.descendants.slice(0, 10).map((d: string) => (
                            <Badge key={d} variant="outline">{d}</Badge>
                          ))}
                          {descendantsMutation.data.descendants.length > 10 && (
                            <Badge variant="secondary">+{descendantsMutation.data.descendants.length - 10} more</Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default PedigreeAnalysis;
