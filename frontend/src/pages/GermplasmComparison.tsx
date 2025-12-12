/**
 * Germplasm Comparison Tool
 * 
 * Compare multiple germplasm entries side-by-side for selection decisions.
 * Helps breeders evaluate and select parent material.
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Scale,
  Plus,
  X,
  Search,
  Download,
  Star,
  StarOff,
  ArrowUpDown,
  CheckCircle,
  AlertCircle,
  Leaf,
  Dna,
  Target,
  TrendingUp,
  Loader2,
  Info,
} from 'lucide-react';
import { useDemoMode } from '@/hooks/useDemoMode';

interface GermplasmEntry {
  id: string;
  name: string;
  accession: string;
  species: string;
  origin: string;
  pedigree: string;
  traits: Record<string, number | string>;
  markers: Record<string, string>;
  status: 'active' | 'archived' | 'candidate';
}

interface ComparisonTrait {
  id: string;
  name: string;
  unit: string;
  type: 'numeric' | 'categorical';
  higherIsBetter: boolean;
}

// Demo germplasm data
const DEMO_GERMPLASM: GermplasmEntry[] = [
  {
    id: 'G001',
    name: 'IR64',
    accession: 'IRRI-001',
    species: 'Oryza sativa',
    origin: 'Philippines',
    pedigree: 'IR5657-33-2-1/IR2061-465-1-5-5',
    status: 'active',
    traits: {
      yield: 6.5,
      plant_height: 105,
      days_to_maturity: 115,
      grain_length: 7.2,
      amylose: 23,
      blast_resistance: 'MR',
      drought_tolerance: 'S',
    },
    markers: {
      'Xa21': 'Present',
      'xa13': 'Absent',
      'Pi-ta': 'Present',
      'Sub1A': 'Absent',
    },
  },
  {
    id: 'G002',
    name: 'Swarna',
    accession: 'CRRI-002',
    species: 'Oryza sativa',
    origin: 'India',
    pedigree: 'Vasistha/Mahsuri',
    status: 'active',
    traits: {
      yield: 5.8,
      plant_height: 115,
      days_to_maturity: 140,
      grain_length: 5.5,
      amylose: 25,
      blast_resistance: 'S',
      drought_tolerance: 'MT',
    },
    markers: {
      'Xa21': 'Absent',
      'xa13': 'Present',
      'Pi-ta': 'Absent',
      'Sub1A': 'Present',
    },
  },
  {
    id: 'G003',
    name: 'Sahbhagi Dhan',
    accession: 'IRRI-003',
    species: 'Oryza sativa',
    origin: 'India',
    pedigree: 'IR74371-70-1-1',
    status: 'active',
    traits: {
      yield: 4.5,
      plant_height: 100,
      days_to_maturity: 105,
      grain_length: 6.8,
      amylose: 22,
      blast_resistance: 'MR',
      drought_tolerance: 'T',
    },
    markers: {
      'Xa21': 'Present',
      'xa13': 'Absent',
      'Pi-ta': 'Present',
      'Sub1A': 'Absent',
    },
  },
  {
    id: 'G004',
    name: 'Swarna-Sub1',
    accession: 'IRRI-004',
    species: 'Oryza sativa',
    origin: 'India',
    pedigree: 'Swarna*3/IR49830-7-1-2-2',
    status: 'candidate',
    traits: {
      yield: 5.5,
      plant_height: 112,
      days_to_maturity: 138,
      grain_length: 5.6,
      amylose: 24,
      blast_resistance: 'S',
      drought_tolerance: 'MT',
    },
    markers: {
      'Xa21': 'Absent',
      'xa13': 'Present',
      'Pi-ta': 'Absent',
      'Sub1A': 'Present',
    },
  },
  {
    id: 'G005',
    name: 'DRR Dhan 44',
    accession: 'IIRR-005',
    species: 'Oryza sativa',
    origin: 'India',
    pedigree: 'MTU1010/Swarna',
    status: 'active',
    traits: {
      yield: 6.2,
      plant_height: 95,
      days_to_maturity: 120,
      grain_length: 6.5,
      amylose: 21,
      blast_resistance: 'R',
      drought_tolerance: 'MT',
    },
    markers: {
      'Xa21': 'Present',
      'xa13': 'Present',
      'Pi-ta': 'Present',
      'Sub1A': 'Absent',
    },
  },
];

const COMPARISON_TRAITS: ComparisonTrait[] = [
  { id: 'yield', name: 'Yield', unit: 't/ha', type: 'numeric', higherIsBetter: true },
  { id: 'plant_height', name: 'Plant Height', unit: 'cm', type: 'numeric', higherIsBetter: false },
  { id: 'days_to_maturity', name: 'Days to Maturity', unit: 'days', type: 'numeric', higherIsBetter: false },
  { id: 'grain_length', name: 'Grain Length', unit: 'mm', type: 'numeric', higherIsBetter: true },
  { id: 'amylose', name: 'Amylose Content', unit: '%', type: 'numeric', higherIsBetter: false },
  { id: 'blast_resistance', name: 'Blast Resistance', unit: '', type: 'categorical', higherIsBetter: true },
  { id: 'drought_tolerance', name: 'Drought Tolerance', unit: '', type: 'categorical', higherIsBetter: true },
];

const MARKERS = ['Xa21', 'xa13', 'Pi-ta', 'Sub1A'];

export function GermplasmComparison() {
  const [selectedIds, setSelectedIds] = useState<string[]>(['G001', 'G002', 'G003']);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [highlightBest, setHighlightBest] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [favorites, setFavorites] = useState<string[]>([]);
  const { isDemoMode } = useDemoMode();

  // Fetch germplasm list from API
  const { data: germplasmData, isLoading: isLoadingList } = useQuery({
    queryKey: ['germplasm-comparison-list', searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      params.append('limit', '50');
      const response = await fetch(`/api/v2/germplasm-comparison?${params}`);
      if (!response.ok) throw new Error('Failed to fetch germplasm');
      return response.json();
    },
    enabled: !isDemoMode,
  });

  // Fetch comparison data from API
  const { data: comparisonData, isLoading: isLoadingComparison, refetch: refetchComparison } = useQuery({
    queryKey: ['germplasm-comparison', selectedIds],
    queryFn: async () => {
      if (selectedIds.length < 2) return null;
      const response = await fetch('/api/v2/germplasm-comparison/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: selectedIds }),
      });
      if (!response.ok) throw new Error('Failed to compare germplasm');
      return response.json();
    },
    enabled: !isDemoMode && selectedIds.length >= 2,
  });

  // Use API data or fall back to demo data
  const allGermplasm = isDemoMode ? DEMO_GERMPLASM : (germplasmData?.data || DEMO_GERMPLASM);
  const selectedGermplasm = isDemoMode 
    ? DEMO_GERMPLASM.filter(g => selectedIds.includes(g.id))
    : (comparisonData?.entries || DEMO_GERMPLASM.filter(g => selectedIds.includes(g.id)));
  
  const availableGermplasm = allGermplasm.filter((g: GermplasmEntry) => 
    !selectedIds.includes(g.id) &&
    (g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
     g.accession.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Get comparison traits and markers from API or demo
  interface APITrait {
    id: string;
    name: string;
    unit: string;
    type: 'numeric' | 'categorical';
    higher_is_better: boolean;
    best?: { value: string | number; entry_id: string };
  }
  
  const comparisonTraits = isDemoMode ? COMPARISON_TRAITS : (comparisonData?.traits?.map((t: APITrait) => ({
    id: t.id,
    name: t.name,
    unit: t.unit,
    type: t.type,
    higherIsBetter: t.higher_is_better,
    best: t.best,
  })) || COMPARISON_TRAITS);

  const comparisonMarkers = isDemoMode ? null : comparisonData?.markers;

  const addGermplasm = (id: string) => {
    if (selectedIds.length < 5) {
      const newIds = [...selectedIds, id];
      setSelectedIds(newIds);
    }
  };

  const removeGermplasm = (id: string) => {
    const newIds = selectedIds.filter(i => i !== id);
    setSelectedIds(newIds);
  };

  // Refetch comparison when selectedIds change
  useEffect(() => {
    if (!isDemoMode && selectedIds.length >= 2) {
      refetchComparison();
    }
  }, [selectedIds, isDemoMode]);

  const toggleFavorite = (id: string) => {
    setFavorites(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const getBestValue = (traitId: string, trait: ComparisonTrait): string | number | null => {
    // If we have API comparison data with best values, use it
    if (!isDemoMode && (trait as ComparisonTrait & { best?: { value: string | number } }).best) {
      return (trait as ComparisonTrait & { best: { value: string | number } }).best.value;
    }
    
    const values = selectedGermplasm.map((g: GermplasmEntry) => g.traits[traitId]).filter((v: string | number | undefined): v is string | number => v !== undefined);
    if (values.length === 0) return null;
    
    if (trait.type === 'numeric') {
      const numValues = values as number[];
      return trait.higherIsBetter ? Math.max(...numValues) : Math.min(...numValues);
    } else {
      // For categorical, define order
      const order = trait.higherIsBetter 
        ? ['R', 'T', 'MR', 'MT', 'MS', 'S', 'HS']
        : ['HS', 'S', 'MS', 'MT', 'MR', 'T', 'R'];
      return values.sort((a: string | number, b: string | number) => order.indexOf(String(a)) - order.indexOf(String(b)))[0];
    }
  };

  const isBestValue = (value: string | number, traitId: string, trait: ComparisonTrait): boolean => {
    if (!highlightBest) return false;
    const best = getBestValue(traitId, trait);
    return value === best;
  };

  const getResistanceColor = (value: string): string => {
    switch (value) {
      case 'R': case 'T': return 'bg-green-100 text-green-800';
      case 'MR': case 'MT': return 'bg-blue-100 text-blue-800';
      case 'MS': return 'bg-yellow-100 text-yellow-800';
      case 'S': return 'bg-orange-100 text-orange-800';
      case 'HS': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportComparison = () => {
    const headers = ['Trait', ...selectedGermplasm.map((g: GermplasmEntry) => g.name)];
    const rows = COMPARISON_TRAITS.map(trait => [
      trait.name,
      ...selectedGermplasm.map((g: GermplasmEntry) => `${g.traits[trait.id] || '-'} ${trait.unit}`.trim())
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'germplasm_comparison.csv';
    a.click();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Scale className="h-6 w-6" />
            Germplasm Comparison
            {isDemoMode && (
              <Badge variant="outline" className="ml-2 text-xs">Demo Mode</Badge>
            )}
          </h1>
          <p className="text-muted-foreground">
            Compare germplasm entries side-by-side for selection decisions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportComparison}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button disabled={selectedIds.length >= 5}>
                <Plus className="h-4 w-4 mr-2" />
                Add Germplasm
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Germplasm to Compare</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name or accession..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <div className="max-h-64 overflow-y-auto space-y-2">
                  {availableGermplasm.map((g: GermplasmEntry) => (
                    <div
                      key={g.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted cursor-pointer"
                      onClick={() => {
                        addGermplasm(g.id);
                        setShowAddDialog(false);
                        setSearchQuery('');
                      }}
                    >
                      <div>
                        <p className="font-medium">{g.name}</p>
                        <p className="text-sm text-muted-foreground">{g.accession} • {g.species}</p>
                      </div>
                      <Badge variant={g.status === 'candidate' ? 'default' : 'secondary'}>
                        {g.status}
                      </Badge>
                    </div>
                  ))}
                  {availableGermplasm.length === 0 && (
                    <p className="text-center text-muted-foreground py-4">
                      No germplasm found
                    </p>
                  )}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Options */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Checkbox
                id="highlight"
                checked={highlightBest}
                onCheckedChange={(checked) => setHighlightBest(checked as boolean)}
              />
              <Label htmlFor="highlight" className="text-sm">Highlight best values</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="markers"
                checked={showMarkers}
                onCheckedChange={(checked) => setShowMarkers(checked as boolean)}
              />
              <Label htmlFor="markers" className="text-sm">Show molecular markers</Label>
            </div>
            <div className="text-sm text-muted-foreground ml-auto">
              Comparing {selectedIds.length} of 5 max entries
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Selected Germplasm Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {selectedGermplasm.map((g: GermplasmEntry) => (
          <Card key={g.id} className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 h-6 w-6"
              onClick={() => removeGermplasm(g.id)}
            >
              <X className="h-4 w-4" />
            </Button>
            <CardHeader className="pb-2">
              <div className="flex items-start gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 -ml-1"
                  onClick={() => toggleFavorite(g.id)}
                >
                  {favorites.includes(g.id) ? (
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ) : (
                    <StarOff className="h-4 w-4" />
                  )}
                </Button>
                <div>
                  <CardTitle className="text-base">{g.name}</CardTitle>
                  <CardDescription className="text-xs">{g.accession}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1 text-sm">
                <p className="text-muted-foreground italic">{g.species}</p>
                <p className="text-xs truncate" title={g.pedigree}>
                  {g.pedigree}
                </p>
                <Badge variant={g.status === 'candidate' ? 'default' : 'secondary'} className="text-xs">
                  {g.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        {selectedIds.length < 5 && (
          <Card className="border-dashed flex items-center justify-center min-h-[150px]">
            <Button variant="ghost" onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Entry
            </Button>
          </Card>
        )}
      </div>

      {/* Comparison Table */}
      {selectedGermplasm.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Trait Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">Trait</TableHead>
                  {selectedGermplasm.map((g: GermplasmEntry) => (
                    <TableHead key={g.id} className="text-center">{g.name}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {COMPARISON_TRAITS.map(trait => (
                  <TableRow key={trait.id}>
                    <TableCell className="font-medium">
                      <div>
                        {trait.name}
                        {trait.unit && <span className="text-muted-foreground text-xs ml-1">({trait.unit})</span>}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {trait.higherIsBetter ? '↑ Higher is better' : '↓ Lower is better'}
                      </div>
                    </TableCell>
                    {selectedGermplasm.map((g: GermplasmEntry) => {
                      const value = g.traits[trait.id];
                      const isBest = isBestValue(value, trait.id, trait);
                      
                      return (
                        <TableCell key={g.id} className="text-center">
                          {trait.type === 'categorical' ? (
                            <Badge className={getResistanceColor(String(value))}>
                              {value}
                            </Badge>
                          ) : (
                            <span className={`font-mono ${isBest ? 'font-bold text-green-600' : ''}`}>
                              {value}
                              {isBest && <CheckCircle className="inline h-3 w-3 ml-1" />}
                            </span>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Molecular Markers */}
      {showMarkers && selectedGermplasm.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Dna className="h-5 w-5" />
              Molecular Markers
            </CardTitle>
            <CardDescription>
              Presence/absence of key resistance and tolerance genes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">Marker</TableHead>
                  {selectedGermplasm.map((g: GermplasmEntry) => (
                    <TableHead key={g.id} className="text-center">{g.name}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {MARKERS.map(marker => (
                  <TableRow key={marker}>
                    <TableCell className="font-medium font-mono">{marker}</TableCell>
                    {selectedGermplasm.map((g: GermplasmEntry) => {
                      const value = g.markers[marker];
                      return (
                        <TableCell key={g.id} className="text-center">
                          {value === 'Present' ? (
                            <Badge className="bg-green-100 text-green-800">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Present
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-muted-foreground">
                              <X className="h-3 w-3 mr-1" />
                              Absent
                            </Badge>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Summary & Recommendations */}
      {selectedGermplasm.length >= 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Selection Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Best for Yield */}
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">Best for Yield</h4>
                {(() => {
                  const best = selectedGermplasm.reduce((a: GermplasmEntry, b: GermplasmEntry) => 
                    (a.traits.yield as number) > (b.traits.yield as number) ? a : b
                  );
                  return (
                    <div>
                      <p className="text-lg font-bold text-green-900">{best.name}</p>
                      <p className="text-sm text-green-700">{best.traits.yield} t/ha</p>
                    </div>
                  );
                })()}
              </div>
              
              {/* Best for Disease Resistance */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">Best Disease Resistance</h4>
                {(() => {
                  const order = ['R', 'MR', 'MS', 'S', 'HS'];
                  const best = selectedGermplasm.reduce((a: GermplasmEntry, b: GermplasmEntry) => {
                    const aIdx = order.indexOf(String(a.traits.blast_resistance));
                    const bIdx = order.indexOf(String(b.traits.blast_resistance));
                    return aIdx < bIdx ? a : b;
                  });
                  return (
                    <div>
                      <p className="text-lg font-bold text-blue-900">{best.name}</p>
                      <p className="text-sm text-blue-700">Blast: {best.traits.blast_resistance}</p>
                    </div>
                  );
                })()}
              </div>
              
              {/* Best for Stress Tolerance */}
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-purple-800 mb-2">Best Stress Tolerance</h4>
                {(() => {
                  const order = ['T', 'MT', 'MS', 'S', 'HS'];
                  const best = selectedGermplasm.reduce((a: GermplasmEntry, b: GermplasmEntry) => {
                    const aIdx = order.indexOf(String(a.traits.drought_tolerance));
                    const bIdx = order.indexOf(String(b.traits.drought_tolerance));
                    return aIdx < bIdx ? a : b;
                  });
                  return (
                    <div>
                      <p className="text-lg font-bold text-purple-900">{best.name}</p>
                      <p className="text-sm text-purple-700">Drought: {best.traits.drought_tolerance}</p>
                    </div>
                  );
                })()}
              </div>
            </div>
            
            {/* Marker Summary */}
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Marker-Assisted Selection Notes</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                {selectedGermplasm.some((g: GermplasmEntry) => g.markers['Xa21'] === 'Present' && g.markers['xa13'] === 'Present') && (
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Gene pyramiding possible: Xa21 + xa13 for bacterial blight resistance
                  </li>
                )}
                {selectedGermplasm.some((g: GermplasmEntry) => g.markers['Sub1A'] === 'Present') && (
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-blue-600" />
                    Sub1A available for submergence tolerance introgression
                  </li>
                )}
                {selectedGermplasm.every((g: GermplasmEntry) => g.markers['Pi-ta'] === 'Absent') && (
                  <li className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                    Consider adding Pi-ta donor for blast resistance
                  </li>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {selectedGermplasm.length === 0 && (
        <Card className="p-12">
          <div className="text-center">
            <Leaf className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No Germplasm Selected</h3>
            <p className="text-muted-foreground mb-4">
              Add germplasm entries to compare their traits and markers
            </p>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Germplasm
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export default GermplasmComparison;
