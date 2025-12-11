/**
 * Pedigree Analysis Page
 * 
 * Relationship matrices, inbreeding coefficients, and pedigree visualization.
 * Connects to /api/v2/pedigree endpoints.
 */

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
import {
  GitBranch,
  Users,
  Calculator,
  Upload,
  Search,
  TreeDeciduous,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Individual {
  id: string;
  sire_id: string | null;
  dam_id: string | null;
  generation: number;
  inbreeding: number;
}

interface PedigreeStats {
  n_individuals: number;
  n_founders: number;
  n_generations: number;
  avg_inbreeding: number;
  max_inbreeding: number;
  completeness_index: number;
}

// Demo pedigree data
const DEMO_PEDIGREE = `F1,,
F2,,
F3,,
G1,F1,F2
G2,F1,F3
G3,G1,G2
H1,G1,G3
H2,G2,G3`;

const DEMO_INDIVIDUALS: Individual[] = [
  { id: 'F1', sire_id: null, dam_id: null, generation: 0, inbreeding: 0 },
  { id: 'F2', sire_id: null, dam_id: null, generation: 0, inbreeding: 0 },
  { id: 'F3', sire_id: null, dam_id: null, generation: 0, inbreeding: 0 },
  { id: 'G1', sire_id: 'F1', dam_id: 'F2', generation: 1, inbreeding: 0 },
  { id: 'G2', sire_id: 'F1', dam_id: 'F3', generation: 1, inbreeding: 0 },
  { id: 'G3', sire_id: 'G1', dam_id: 'G2', generation: 2, inbreeding: 0.25 },
  { id: 'H1', sire_id: 'G1', dam_id: 'G3', generation: 3, inbreeding: 0.25 },
  { id: 'H2', sire_id: 'G2', dam_id: 'G3', generation: 3, inbreeding: 0.25 },
];

const DEMO_STATS: PedigreeStats = {
  n_individuals: 8,
  n_founders: 3,
  n_generations: 4,
  avg_inbreeding: 0.094,
  max_inbreeding: 0.25,
  completeness_index: 0.85,
};

export function PedigreeAnalysis() {
  const [activeTab, setActiveTab] = useState('individuals');
  const [pedigreeText, setPedigreeText] = useState(DEMO_PEDIGREE);
  const [generationFilter, setGenerationFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndividual, setSelectedIndividual] = useState<string>('');
  const [coancestryId1, setCoancestryId1] = useState('');
  const [coancestryId2, setCoancestryId2] = useState('');
  const [coancestryResult, setCoancestryResult] = useState<{ coancestry: number; relationship: string } | null>(null);
  const [ancestorResult, setAncestorResult] = useState<any>(null);
  const [descendantResult, setDescendantResult] = useState<any>(null);
  
  // State for loaded data
  const [individuals, setIndividuals] = useState<Individual[]>(DEMO_INDIVIDUALS);
  const [stats, setStats] = useState<PedigreeStats>(DEMO_STATS);
  const [isLoaded, setIsLoaded] = useState(true);

  // Load pedigree mutation
  const loadPedigreeMutation = useMutation({
    mutationFn: async () => {
      // Parse CSV text to pedigree records
      const lines = pedigreeText.trim().split('\n');
      const pedigree = lines.map(line => {
        const [id, sire_id, dam_id] = line.split(',').map(s => s.trim());
        return {
          id,
          sire_id: sire_id || null,
          dam_id: dam_id || null,
        };
      });

      const res = await fetch(`${API_BASE}/api/v2/pedigree/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pedigree }),
      });
      if (!res.ok) throw new Error('Failed to load pedigree');
      return res.json();
    },
    onSuccess: async () => {
      // Fetch individuals after loading
      try {
        const res = await fetch(`${API_BASE}/api/v2/pedigree/individuals`);
        if (res.ok) {
          const json = await res.json();
          setIndividuals(json.individuals || DEMO_INDIVIDUALS);
        }
        const statsRes = await fetch(`${API_BASE}/api/v2/pedigree/stats`);
        if (statsRes.ok) {
          const statsJson = await statsRes.json();
          setStats(statsJson);
        }
        setIsLoaded(true);
      } catch {
        // Use demo data on error
      }
    },
  });

  // Calculate coancestry mutation
  const coancestryMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/pedigree/coancestry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          individual_1: coancestryId1,
          individual_2: coancestryId2,
        }),
      });
      if (!res.ok) throw new Error('Failed to calculate coancestry');
      return res.json();
    },
    onSuccess: (data) => {
      setCoancestryResult({
        coancestry: data.coancestry,
        relationship: data.relationship || getRelationshipLabel(data.coancestry),
      });
    },
  });

  // Get ancestors mutation
  const ancestorsMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/api/v2/pedigree/ancestors/${id}?max_generations=4`);
      if (!res.ok) throw new Error('Failed to get ancestors');
      return res.json();
    },
    onSuccess: (data) => {
      setAncestorResult(data);
    },
  });

  // Get descendants mutation
  const descendantsMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/api/v2/pedigree/descendants/${id}?max_generations=3`);
      if (!res.ok) throw new Error('Failed to get descendants');
      return res.json();
    },
    onSuccess: (data) => {
      setDescendantResult(data);
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

  // Filter individuals
  const filteredIndividuals = individuals.filter(ind => {
    const matchesSearch = ind.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesGeneration = generationFilter === 'all' || ind.generation === parseInt(generationFilter);
    return matchesSearch && matchesGeneration;
  });

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
                  {loadPedigreeMutation.isPending ? 'Loading...' : 'Load Pedigree'}
                </Button>
                <Button variant="outline" onClick={() => setPedigreeText(DEMO_PEDIGREE)}>
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
                  {coancestryMutation.isPending ? 'Calculating...' : 'Calculate Coancestry'}
                </Button>
                {coancestryResult && (
                  <div className="p-4 border rounded-lg bg-muted/50">
                    <div className="text-center">
                      <p className="text-3xl font-bold">{(coancestryResult.coancestry * 100).toFixed(2)}%</p>
                      <p className="text-sm text-muted-foreground">Coefficient of Coancestry (θ)</p>
                      <Badge className="mt-2">{coancestryResult.relationship}</Badge>
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
                    Trace
                  </Button>
                </div>
                {ancestorResult && (
                  <div className="p-4 border rounded-lg">
                    <p className="font-medium mb-2">Ancestors of {ancestorResult.individual_id}</p>
                    <div className="text-sm space-y-1">
                      <p>Sire: {ancestorResult.sire_id || 'Unknown'}</p>
                      <p>Dam: {ancestorResult.dam_id || 'Unknown'}</p>
                      <p>Total ancestors found: {ancestorResult.n_ancestors || 0}</p>
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
                    Find
                  </Button>
                </div>
                {descendantResult && (
                  <div className="p-4 border rounded-lg">
                    <p className="font-medium mb-2">Descendants of {descendantResult.individual_id}</p>
                    <div className="text-sm">
                      <p>Total descendants: {descendantResult.n_descendants || 0}</p>
                      {descendantResult.descendants && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {descendantResult.descendants.slice(0, 10).map((d: string) => (
                            <Badge key={d} variant="outline">{d}</Badge>
                          ))}
                          {descendantResult.descendants.length > 10 && (
                            <Badge variant="secondary">+{descendantResult.descendants.length - 10} more</Badge>
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
