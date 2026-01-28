/**
 * Disease Resistance Page
 * 
 * Manage disease screening, resistance genes, and gene pyramiding strategies.
 * Connects to /api/v2/disease endpoints.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
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
  Bug,
  Shield,
  Search,
  Dna,
  Target,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { apiClient, type Disease, type ResistanceGene } from '@/lib/api-client';

export function DiseaseResistance() {
  const [activeTab, setActiveTab] = useState('diseases');
  const [searchQuery, setSearchQuery] = useState('');
  const [cropFilter, setCropFilter] = useState<string>('all');
  const [pathogenFilter, setPathogenFilter] = useState<string>('all');

  // Fetch diseases
  const { data: diseasesData, isLoading: diseasesLoading } = useQuery({
    queryKey: ['diseases', cropFilter, pathogenFilter, searchQuery],
    queryFn: () => apiClient.diseaseResistanceService.getDiseases({
      crop: cropFilter !== 'all' ? cropFilter : undefined,
      pathogen_type: pathogenFilter !== 'all' ? pathogenFilter : undefined,
      search: searchQuery || undefined,
    }),
  });

  // Fetch resistance genes
  const { data: genesData, isLoading: genesLoading } = useQuery({
    queryKey: ['resistance-genes', searchQuery],
    queryFn: () => apiClient.diseaseResistanceService.getGenes({
      search: searchQuery || undefined,
    }),
  });

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['disease-stats'],
    queryFn: () => apiClient.diseaseResistanceService.getStatistics(),
  });

  // Fetch pyramiding strategies
  const { data: pyramidingData } = useQuery({
    queryKey: ['pyramiding-strategies'],
    queryFn: () => apiClient.diseaseResistanceService.getPyramidingStrategies(),
  });

  const diseases = diseasesData?.diseases || [];
  const genes = genesData?.genes || [];

  // Get unique crops and pathogen types from data
  const crops = [...new Set(diseases.map(d => d.crop))];
  const pathogenTypes = [...new Set(diseases.map(d => d.pathogen_type))];

  // Filter genes by search (diseases already filtered by API)
  const filteredGenes = genes.filter(g => {
    if (!searchQuery) return true;
    const matchesSearch = g.gene_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.disease_name?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    return matchesSearch;
  });

  const pyramidingStrategies = pyramidingData?.strategies || [];

  const isLoading = diseasesLoading || genesLoading;

  const pathogenIcons: Record<string, string> = {
    bacteria: '🦠',
    fungus: '🍄',
    virus: '🧬',
    insect: '🐛',
    nematode: '🪱',
  };

  const resistanceColors: Record<string, string> = {
    complete: 'bg-green-100 text-green-800',
    partial: 'bg-yellow-100 text-yellow-800',
    recessive: 'bg-blue-100 text-blue-800',
    dominant: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="h-6 w-6" />
          Disease Resistance
        </h1>
        <p className="text-muted-foreground">
          Manage disease screening, resistance genes, and gene pyramiding strategies
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Bug className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.totalDiseases || diseases.length}</p>
                <p className="text-xs text-muted-foreground">Diseases</p>
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
                <p className="text-xs text-muted-foreground">R-Genes</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats?.totalCrops || crops.length}</p>
                <p className="text-xs text-muted-foreground">Crops</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Shield className="h-5 w-5 text-purple-600" />
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
            placeholder="Search diseases or genes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={cropFilter} onValueChange={setCropFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Crop" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Crops</SelectItem>
            {crops.map(crop => (
              <SelectItem key={crop} value={crop}>{crop}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={pathogenFilter} onValueChange={setPathogenFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Pathogen" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {pathogenTypes.map(type => (
              <SelectItem key={type} value={type}>
                {pathogenIcons[type]} {type.charAt(0).toUpperCase() + type.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="diseases">
            <Bug className="h-4 w-4 mr-2" />
            Diseases ({diseases.length})
          </TabsTrigger>
          <TabsTrigger value="genes">
            <Dna className="h-4 w-4 mr-2" />
            Resistance Genes ({filteredGenes.length})
          </TabsTrigger>
          <TabsTrigger value="pyramiding">
            <Target className="h-4 w-4 mr-2" />
            Gene Pyramiding
          </TabsTrigger>
        </TabsList>

        {/* Diseases Tab */}
        <TabsContent value="diseases">
          <Card>
            <CardHeader>
              <CardTitle>Disease Database</CardTitle>
              <CardDescription>Common diseases affecting breeding programs</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Disease</TableHead>
                    <TableHead>Pathogen</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Crop</TableHead>
                    <TableHead>Symptoms</TableHead>
                    <TableHead>R-Genes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {diseases.map(disease => {
                    const diseaseGenes = genes.filter(g => g.disease_id === disease.id);
                    return (
                      <TableRow key={disease.id}>
                        <TableCell className="font-medium">{disease.name}</TableCell>
                        <TableCell className="italic text-sm">{disease.pathogen}</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {pathogenIcons[disease.pathogen_type]} {disease.pathogen_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{disease.crop}</TableCell>
                        <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">
                          {disease.symptoms}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{diseaseGenes.length} genes</Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Genes Tab */}
        <TabsContent value="genes">
          <Card>
            <CardHeader>
              <CardTitle>Resistance Gene Catalog</CardTitle>
              <CardDescription>Known resistance genes with molecular markers</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Gene</TableHead>
                    <TableHead>Disease</TableHead>
                    <TableHead>Chromosome</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Markers</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredGenes.map(gene => (
                    <TableRow key={gene.id}>
                      <TableCell className="font-mono font-bold">{gene.gene_name}</TableCell>
                      <TableCell>{gene.disease_name}</TableCell>
                      <TableCell>{gene.chromosome || '-'}</TableCell>
                      <TableCell>
                        <Badge className={resistanceColors[gene.resistance_type]}>
                          {gene.resistance_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="italic text-sm">{gene.source_germplasm || '-'}</TableCell>
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

        {/* Pyramiding Tab */}
        <TabsContent value="pyramiding">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Gene Pyramiding Strategies</CardTitle>
                <CardDescription>Combine multiple R-genes for durable resistance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {pyramidingStrategies.map(strategy => (
                  <div key={strategy.id} className={`p-4 border rounded-lg ${strategy.status === 'warning' ? 'border-yellow-200 bg-yellow-50' : ''}`}>
                    <div className="flex items-center gap-2 mb-2">
                      {strategy.status === 'warning' ? (
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                      <span className="font-medium">{strategy.name}</span>
                    </div>
                    <p className={`text-sm mb-3 ${strategy.status === 'warning' ? 'text-yellow-700' : 'text-muted-foreground'}`}>
                      {strategy.description}
                    </p>
                    {strategy.warning && (
                      <p className="text-xs text-yellow-600 mb-2">{strategy.warning}</p>
                    )}
                    <div className="flex gap-2 flex-wrap">
                      {strategy.genes.map((gene, idx) => (
                        <span key={gene} className="flex items-center gap-1">
                          <Badge className={strategy.status === 'warning' && idx === 0 ? 'bg-red-100 text-red-800 line-through' : 'bg-green-100 text-green-800'}>
                            {gene}
                          </Badge>
                          {idx < strategy.genes.length - 1 && <span>+</span>}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>MAS Workflow</CardTitle>
                <CardDescription>Marker-assisted selection for R-genes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">1</div>
                    <div>
                      <p className="font-medium">Select Target Genes</p>
                      <p className="text-sm text-muted-foreground">Choose R-genes based on prevalent races</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">2</div>
                    <div>
                      <p className="font-medium">Identify Donor Parents</p>
                      <p className="text-sm text-muted-foreground">Source germplasm with confirmed genes</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">3</div>
                    <div>
                      <p className="font-medium">Foreground Selection</p>
                      <p className="text-sm text-muted-foreground">Screen F2/BC1 with gene-linked markers</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">4</div>
                    <div>
                      <p className="font-medium">Background Selection</p>
                      <p className="text-sm text-muted-foreground">Recover recurrent parent genome</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold">5</div>
                    <div>
                      <p className="font-medium">Phenotypic Validation</p>
                      <p className="text-sm text-muted-foreground">Confirm resistance in disease nursery</p>
                    </div>
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

export default DiseaseResistance;
