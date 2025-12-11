/**
 * Disease Resistance Page
 * 
 * Manage disease screening, resistance genes, and gene pyramiding strategies.
 * Connects to /api/v2/disease endpoints.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
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
  Bug,
  Shield,
  Search,
  Dna,
  Target,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Disease {
  id: string;
  name: string;
  pathogen: string;
  pathogen_type: string;
  crop: string;
  symptoms: string;
  severity_scale: string[];
}

interface ResistanceGene {
  id: string;
  gene_name: string;
  disease_id: string;
  disease_name?: string;
  chromosome?: string;
  resistance_type: string;
  source_germplasm?: string;
  markers?: string[];
}

// Demo data for when API is unavailable
const DEMO_DISEASES: Disease[] = [
  { id: 'd1', name: 'Bacterial Blight', pathogen: 'Xanthomonas oryzae pv. oryzae', pathogen_type: 'bacteria', crop: 'Rice', symptoms: 'Water-soaked lesions, wilting', severity_scale: ['0', '1', '3', '5', '7', '9'] },
  { id: 'd2', name: 'Blast', pathogen: 'Magnaporthe oryzae', pathogen_type: 'fungus', crop: 'Rice', symptoms: 'Diamond-shaped lesions', severity_scale: ['0', '1', '3', '5', '7', '9'] },
  { id: 'd3', name: 'Brown Planthopper', pathogen: 'Nilaparvata lugens', pathogen_type: 'insect', crop: 'Rice', symptoms: 'Hopper burn, stunting', severity_scale: ['0', '1', '3', '5', '7', '9'] },
  { id: 'd4', name: 'Stem Rust', pathogen: 'Puccinia graminis', pathogen_type: 'fungus', crop: 'Wheat', symptoms: 'Reddish-brown pustules on stems', severity_scale: ['0', '5', '10', '20', '40', '60', '100'] },
  { id: 'd5', name: 'Yellow Rust', pathogen: 'Puccinia striiformis', pathogen_type: 'fungus', crop: 'Wheat', symptoms: 'Yellow stripes on leaves', severity_scale: ['0', '5', '10', '20', '40', '60', '100'] },
  { id: 'd6', name: 'Northern Corn Leaf Blight', pathogen: 'Exserohilum turcicum', pathogen_type: 'fungus', crop: 'Maize', symptoms: 'Cigar-shaped lesions', severity_scale: ['1', '2', '3', '4', '5'] },
  { id: 'd7', name: 'Gray Leaf Spot', pathogen: 'Cercospora zeae-maydis', pathogen_type: 'fungus', crop: 'Maize', symptoms: 'Rectangular gray lesions', severity_scale: ['1', '2', '3', '4', '5'] },
  { id: 'd8', name: 'Sheath Blight', pathogen: 'Rhizoctonia solani', pathogen_type: 'fungus', crop: 'Rice', symptoms: 'Oval lesions on sheath', severity_scale: ['0', '1', '3', '5', '7', '9'] },
];

const DEMO_GENES: ResistanceGene[] = [
  { id: 'g1', gene_name: 'Xa21', disease_id: 'd1', disease_name: 'Bacterial Blight', chromosome: '11', resistance_type: 'complete', source_germplasm: 'O. longistaminata', markers: ['pTA248', 'Xa21-STS'] },
  { id: 'g2', gene_name: 'xa13', disease_id: 'd1', disease_name: 'Bacterial Blight', chromosome: '8', resistance_type: 'recessive', source_germplasm: 'BJ1', markers: ['xa13-prom'] },
  { id: 'g3', gene_name: 'xa5', disease_id: 'd1', disease_name: 'Bacterial Blight', chromosome: '5', resistance_type: 'recessive', source_germplasm: 'DZ192', markers: ['RM122', 'xa5-1'] },
  { id: 'g4', gene_name: 'Pi-ta', disease_id: 'd2', disease_name: 'Blast', chromosome: '12', resistance_type: 'complete', source_germplasm: 'Tetep', markers: ['YL155/YL87'] },
  { id: 'g5', gene_name: 'Pi9', disease_id: 'd2', disease_name: 'Blast', chromosome: '6', resistance_type: 'complete', source_germplasm: 'O. minuta', markers: ['Pi9-STS'] },
  { id: 'g6', gene_name: 'Bph3', disease_id: 'd3', disease_name: 'Brown Planthopper', chromosome: '6', resistance_type: 'complete', source_germplasm: 'Rathu Heenati', markers: ['RM589', 'RM586'] },
  { id: 'g7', gene_name: 'Sr31', disease_id: 'd4', disease_name: 'Stem Rust', chromosome: '1BL/1RS', resistance_type: 'complete', source_germplasm: 'Petkus rye', markers: ['iag95'] },
  { id: 'g8', gene_name: 'Yr15', disease_id: 'd5', disease_name: 'Yellow Rust', chromosome: '1BS', resistance_type: 'complete', source_germplasm: 'T. dicoccoides', markers: ['Xbarc8'] },
  { id: 'g9', gene_name: 'Ht1', disease_id: 'd6', disease_name: 'Northern Corn Leaf Blight', chromosome: '2', resistance_type: 'partial', source_germplasm: 'Ladyfinger popcorn', markers: ['umc1065'] },
];

export function DiseaseResistance() {
  const [activeTab, setActiveTab] = useState('diseases');
  const [searchQuery, setSearchQuery] = useState('');
  const [cropFilter, setCropFilter] = useState<string>('all');
  const [pathogenFilter, setPathogenFilter] = useState<string>('all');

  // Fetch diseases
  const { data: diseases = DEMO_DISEASES } = useQuery<Disease[]>({
    queryKey: ['diseases'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/disease/diseases`);
        if (!res.ok) return DEMO_DISEASES;
        const data = await res.json();
        // Handle both array and object with diseases property
        return Array.isArray(data) ? data : (data.diseases || DEMO_DISEASES);
      } catch {
        return DEMO_DISEASES;
      }
    },
  });

  // Fetch resistance genes
  const { data: genes = DEMO_GENES } = useQuery<ResistanceGene[]>({
    queryKey: ['resistance-genes'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/disease/genes`);
        if (!res.ok) return DEMO_GENES;
        const data = await res.json();
        // Handle both array and object with genes property
        return Array.isArray(data) ? data : (data.genes || DEMO_GENES);
      } catch {
        return DEMO_GENES;
      }
    },
  });

  // Get unique crops and pathogen types
  const crops = [...new Set(diseases.map(d => d.crop))];
  const pathogenTypes = [...new Set(diseases.map(d => d.pathogen_type))];

  // Filter diseases
  const filteredDiseases = diseases.filter(d => {
    const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.pathogen.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCrop = cropFilter === 'all' || d.crop === cropFilter;
    const matchesPathogen = pathogenFilter === 'all' || d.pathogen_type === pathogenFilter;
    return matchesSearch && matchesCrop && matchesPathogen;
  });

  // Filter genes
  const filteredGenes = genes.filter(g => {
    const matchesSearch = g.gene_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.disease_name?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    return matchesSearch;
  });

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
                <p className="text-2xl font-bold">{diseases.length}</p>
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
                <p className="text-2xl font-bold">{genes.length}</p>
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
                <p className="text-2xl font-bold">{crops.length}</p>
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
                <p className="text-2xl font-bold">{genes.filter(g => g.markers && g.markers.length > 0).length}</p>
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
            Diseases ({filteredDiseases.length})
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
                  {filteredDiseases.map(disease => {
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
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <span className="font-medium">Bacterial Blight Pyramid</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Combine Xa21 + xa13 + xa5 for broad-spectrum resistance
                  </p>
                  <div className="flex gap-2">
                    <Badge className="bg-green-100 text-green-800">Xa21</Badge>
                    <span>+</span>
                    <Badge className="bg-blue-100 text-blue-800">xa13</Badge>
                    <span>+</span>
                    <Badge className="bg-blue-100 text-blue-800">xa5</Badge>
                  </div>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <span className="font-medium">Blast Resistance Pyramid</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Stack Pi-ta + Pi9 for multiple race resistance
                  </p>
                  <div className="flex gap-2">
                    <Badge className="bg-green-100 text-green-800">Pi-ta</Badge>
                    <span>+</span>
                    <Badge className="bg-green-100 text-green-800">Pi9</Badge>
                  </div>
                </div>

                <div className="p-4 border rounded-lg border-yellow-200 bg-yellow-50">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-yellow-600" />
                    <span className="font-medium">Rust Resistance (Wheat)</span>
                  </div>
                  <p className="text-sm text-yellow-700 mb-3">
                    Sr31 breakdown reported - consider adding Sr38 or Sr2
                  </p>
                  <div className="flex gap-2">
                    <Badge className="bg-red-100 text-red-800 line-through">Sr31</Badge>
                    <span>→</span>
                    <Badge className="bg-green-100 text-green-800">Sr38</Badge>
                    <span>+</span>
                    <Badge className="bg-green-100 text-green-800">Sr2</Badge>
                  </div>
                </div>
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
