/**
 * Abiotic Stress Tolerance Page
 * 
 * Track drought, heat, salinity, and other abiotic stress tolerance.
 * Connects to /api/v2/abiotic endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
  Droplets,
  Thermometer,
  Snowflake,
  Waves,
  Leaf,
  Sun,
  Dna,
  Calculator,
  TrendingUp,
  Search,
  AlertTriangle,
} from 'lucide-react';
import { abioticStressAPI, type StressType, type ToleranceGene, type StressIndices } from '@/lib/api-client';

const stressIcons: Record<string, React.ReactNode> = {
  'STR-001': <Droplets className="h-5 w-5" />,
  'STR-002': <Thermometer className="h-5 w-5" />,
  'STR-003': <Snowflake className="h-5 w-5" />,
  'STR-004': <Waves className="h-5 w-5" />,
  'STR-005': <Waves className="h-5 w-5" />,
  'STR-006': <Leaf className="h-5 w-5" />,
  'STR-007': <AlertTriangle className="h-5 w-5" />,
  'STR-008': <Sun className="h-5 w-5" />,
};

const categoryColors: Record<string, string> = {
  water: 'bg-blue-100 text-blue-800',
  temperature: 'bg-orange-100 text-orange-800',
  soil: 'bg-amber-100 text-amber-800',
  radiation: 'bg-purple-100 text-purple-800',
};

export function AbioticStress() {
  const [activeTab, setActiveTab] = useState('stresses');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [controlYield, setControlYield] = useState<string>('100');
  const [stressYield, setStressYield] = useState<string>('70');
  const [calculatedIndices, setCalculatedIndices] = useState<StressIndices | null>(null);

  // Fetch stress types
  const { data: stressesData, isLoading: stressesLoading } = useQuery({
    queryKey: ['stress-types', categoryFilter, searchQuery],
    queryFn: () => abioticStressAPI.getStressTypes({
      category: categoryFilter !== 'all' ? categoryFilter : undefined,
      search: searchQuery || undefined,
    }),
  });

  // Fetch tolerance genes
  const { data: genesData, isLoading: genesLoading } = useQuery({
    queryKey: ['tolerance-genes', searchQuery],
    queryFn: () => abioticStressAPI.getGenes({
      search: searchQuery || undefined,
    }),
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['abiotic-stats'],
    queryFn: () => abioticStressAPI.getStatistics(),
  });

  // Calculate indices mutation
  const calculateMutation = useMutation({
    mutationFn: () => abioticStressAPI.calculateIndices(
      parseFloat(controlYield),
      parseFloat(stressYield)
    ),
    onSuccess: (data) => {
      setCalculatedIndices(data.data.indices);
    },
  });

  const stresses = stressesData?.data || [];
  const genes = genesData?.data || [];

  // Get unique categories from data
  const categories = [...new Set(stresses.map(s => s.category))];

  // Filter genes by search (stresses already filtered by API)
  const filteredGenes = genes.filter(g => {
    if (!searchQuery) return true;
    const matchesSearch = g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.mechanism.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const isLoading = stressesLoading || genesLoading;

  const getStressName = (stressId: string) => {
    const stress = stresses.find(s => s.stress_id === stressId);
    return stress?.name || stressId;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Thermometer className="h-6 w-6" />
          Abiotic Stress Tolerance
        </h1>
        <p className="text-muted-foreground">
          Track drought, heat, salinity, and other environmental stress tolerance
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Droplets className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.totalStressTypes || stresses.length}</p>
                <p className="text-xs text-muted-foreground">Stress Types</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Dna className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.totalGenes || genes.length}</p>
                <p className="text-xs text-muted-foreground">Tolerance Genes</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Calculator className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">7</p>
                <p className="text-xs text-muted-foreground">Stress Indices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.masReadyGenes || genes.filter(g => g.markers && g.markers.length > 0).length}</p>
                <p className="text-xs text-muted-foreground">MAS Ready</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>


      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search stresses or genes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(cat => (
              <SelectItem key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="stresses">
            <Thermometer className="h-4 w-4 mr-2" />
            Stress Types ({stresses.length})
          </TabsTrigger>
          <TabsTrigger value="genes">
            <Dna className="h-4 w-4 mr-2" />
            Tolerance Genes ({filteredGenes.length})
          </TabsTrigger>
          <TabsTrigger value="calculator">
            <Calculator className="h-4 w-4 mr-2" />
            Index Calculator
          </TabsTrigger>
        </TabsList>

        {/* Stress Types Tab */}
        <TabsContent value="stresses">
          {isLoading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stresses.map(stress => {
              const stressGenes = genes.filter(g => g.stress_id === stress.stress_id);
              return (
                <Card key={stress.stress_id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-2">
                      <div className={`p-2 rounded-lg ${categoryColors[stress.category] || 'bg-gray-100'}`}>
                        {stressIcons[stress.stress_id] || <AlertTriangle className="h-5 w-5" />}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{stress.name}</CardTitle>
                        <Badge variant="outline" className="text-xs">
                          {stress.category}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-3">{stress.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        {stressGenes.length} tolerance gene{stressGenes.length !== 1 ? 's' : ''}
                      </span>
                      {stressGenes.length > 0 && (
                        <div className="flex gap-1">
                          {stressGenes.slice(0, 2).map(g => (
                            <Badge key={g.gene_id} variant="secondary" className="text-xs">
                              {g.name}
                            </Badge>
                          ))}
                          {stressGenes.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{stressGenes.length - 2}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          )}
        </TabsContent>

        {/* Genes Tab */}
        <TabsContent value="genes">
          <Card>
            <CardHeader>
              <CardTitle>Tolerance Gene Catalog</CardTitle>
              <CardDescription>Genes conferring abiotic stress tolerance</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Gene</TableHead>
                    <TableHead>Stress</TableHead>
                    <TableHead>Mechanism</TableHead>
                    <TableHead>Crop</TableHead>
                    <TableHead>Markers</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredGenes.map(gene => (
                    <TableRow key={gene.gene_id}>
                      <TableCell className="font-mono font-bold">{gene.name}</TableCell>
                      <TableCell>
                        <Badge className={categoryColors[stresses.find(s => s.stress_id === gene.stress_id)?.category || ''] || 'bg-gray-100'}>
                          {getStressName(gene.stress_id)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm">{gene.mechanism}</TableCell>
                      <TableCell>{gene.crop}</TableCell>
                      <TableCell>
                        {gene.markers && gene.markers.length > 0 ? (
                          <div className="flex gap-1 flex-wrap">
                            {gene.markers.map(m => (
                              <Badge key={m} variant="outline" className="text-xs">{m}</Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Calculator Tab */}
        <TabsContent value="calculator">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Stress Tolerance Index Calculator</CardTitle>
                <CardDescription>Calculate various indices from yield data</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Control Yield (Yp)</Label>
                    <Input
                      type="number"
                      value={controlYield}
                      onChange={(e) => setControlYield(e.target.value)}
                      placeholder="e.g., 100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Stress Yield (Ys)</Label>
                    <Input
                      type="number"
                      value={stressYield}
                      onChange={(e) => setStressYield(e.target.value)}
                      placeholder="e.g., 70"
                    />
                  </div>
                </div>
                <Button onClick={() => calculateMutation.mutate()} className="w-full" disabled={calculateMutation.isPending}>
                  <Calculator className="h-4 w-4 mr-2" />
                  {calculateMutation.isPending ? 'Calculating...' : 'Calculate Indices'}
                </Button>

                {calculatedIndices && (
                  <div className="mt-4 space-y-3">
                    <h4 className="font-medium">Results</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(calculatedIndices).map(([key, value]) => (
                        <div key={key} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-bold">{key}</span>
                            <span className="text-lg">{value}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Index Reference</CardTitle>
                <CardDescription>Understanding stress tolerance indices</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold">SSI</span>
                      <span className="text-sm text-muted-foreground">Stress Susceptibility Index</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Lower is better (less susceptible)</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold">STI</span>
                      <span className="text-sm text-muted-foreground">Stress Tolerance Index</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Higher is better (more tolerant)</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold">YSI</span>
                      <span className="text-sm text-muted-foreground">Yield Stability Index</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Higher is better (more stable)</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold">GMP</span>
                      <span className="text-sm text-muted-foreground">Geometric Mean Productivity</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Higher is better</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono font-bold">TOL</span>
                      <span className="text-sm text-muted-foreground">Tolerance Index</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Lower is better (less yield loss)</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AbioticStress;
