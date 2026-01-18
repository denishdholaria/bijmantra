/**
 * Germplasm Comparison Tool
 * 
 * Compare multiple germplasm entries side-by-side for selection decisions.
 * Connects to /api/v2/germplasm-comparison endpoints.
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import {
  Scale, Plus, X, Search, Download, Star, StarOff,
  CheckCircle, AlertCircle, Leaf, Dna, Target, TrendingUp,
} from 'lucide-react';
import { germplasmComparisonAPI, ComparisonGermplasm, ComparisonTrait } from '@/lib/api-client';

const MARKERS = ['Xa21', 'xa13', 'Pi-ta', 'Sub1A'];

export function GermplasmComparison() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [highlightBest, setHighlightBest] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [favorites, setFavorites] = useState<string[]>([]);

  // Fetch germplasm list
  const { data: listData, isLoading: isLoadingList } = useQuery({
    queryKey: ['germplasm-comparison-list', searchQuery],
    queryFn: () => germplasmComparisonAPI.listGermplasm({ search: searchQuery || undefined, limit: 50 }),
  });

  // Fetch comparison data when we have selected IDs
  const { data: comparisonData, isLoading: isLoadingComparison, refetch: refetchComparison } = useQuery({
    queryKey: ['germplasm-comparison', selectedIds],
    queryFn: () => germplasmComparisonAPI.compare(selectedIds),
    enabled: selectedIds.length >= 2,
  });

  // Fetch traits
  const { data: traitsData } = useQuery({
    queryKey: ['germplasm-comparison-traits'],
    queryFn: () => germplasmComparisonAPI.getTraits(),
  });

  const allGermplasm: ComparisonGermplasm[] = listData?.data || [];
  const selectedGermplasm: ComparisonGermplasm[] = comparisonData?.entries || allGermplasm.filter(g => selectedIds.includes(g.id));
  const comparisonTraits: ComparisonTrait[] = comparisonData?.traits || traitsData?.traits || [];
  
  const availableGermplasm = allGermplasm.filter(g => 
    !selectedIds.includes(g.id) &&
    (g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
     g.accession.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Initialize with first 3 germplasm if none selected
  useEffect(() => {
    if (selectedIds.length === 0 && allGermplasm.length >= 3) {
      setSelectedIds(allGermplasm.slice(0, 3).map(g => g.id));
    }
  }, [allGermplasm, selectedIds.length]);

  const addGermplasm = (id: string) => {
    if (selectedIds.length < 5) {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const removeGermplasm = (id: string) => {
    setSelectedIds(selectedIds.filter(i => i !== id));
  };

  const toggleFavorite = (id: string) => {
    setFavorites(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const getBestValue = (traitId: string, trait: ComparisonTrait): string | number | null => {
    if ((trait as any).best) return (trait as any).best.value;
    const values = selectedGermplasm.map(g => g.traits[traitId]).filter((v): v is string | number => v !== undefined);
    if (values.length === 0) return null;
    if (trait.type === 'numeric') {
      const numValues = values as number[];
      return trait.higher_is_better ? Math.max(...numValues) : Math.min(...numValues);
    } else {
      const order = trait.higher_is_better ? ['R', 'T', 'MR', 'MT', 'MS', 'S', 'HS'] : ['HS', 'S', 'MS', 'MT', 'MR', 'T', 'R'];
      return values.sort((a, b) => order.indexOf(String(a)) - order.indexOf(String(b)))[0];
    }
  };

  const isBestValue = (value: string | number, traitId: string, trait: ComparisonTrait): boolean => {
    if (!highlightBest) return false;
    return value === getBestValue(traitId, trait);
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
    const headers = ['Trait', ...selectedGermplasm.map(g => g.name)];
    const rows = comparisonTraits.map(trait => [
      trait.name,
      ...selectedGermplasm.map(g => `${g.traits[trait.id] || '-'} ${trait.unit}`.trim())
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'germplasm_comparison.csv';
    a.click();
    toast.success('Comparison exported to CSV');
  };

  const isLoading = isLoadingList || (selectedIds.length >= 2 && isLoadingComparison);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Scale className="h-6 w-6" />
            Germplasm Comparison
          </h1>
          <p className="text-muted-foreground">Compare germplasm entries side-by-side for selection decisions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportComparison} disabled={selectedGermplasm.length === 0}>
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <Button disabled={selectedIds.length >= 5}><Plus className="h-4 w-4 mr-2" />Add Germplasm</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Add Germplasm to Compare</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search by name or accession..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                </div>
                <div className="max-h-64 overflow-y-auto space-y-2">
                  {availableGermplasm.map(g => (
                    <div key={g.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted cursor-pointer" onClick={() => { addGermplasm(g.id); setShowAddDialog(false); setSearchQuery(''); }}>
                      <div><p className="font-medium">{g.name}</p><p className="text-sm text-muted-foreground">{g.accession} • {g.species}</p></div>
                      <Badge variant={g.status === 'candidate' ? 'default' : 'secondary'}>{g.status}</Badge>
                    </div>
                  ))}
                  {availableGermplasm.length === 0 && <p className="text-center text-muted-foreground py-4">No germplasm found</p>}
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Checkbox id="highlight" checked={highlightBest} onCheckedChange={(checked) => setHighlightBest(checked as boolean)} />
              <Label htmlFor="highlight" className="text-sm">Highlight best values</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox id="markers" checked={showMarkers} onCheckedChange={(checked) => setShowMarkers(checked as boolean)} />
              <Label htmlFor="markers" className="text-sm">Show molecular markers</Label>
            </div>
            <div className="text-sm text-muted-foreground ml-auto">Comparing {selectedIds.length} of 5 max entries</div>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">{[1,2,3].map(i => <Skeleton key={i} className="h-40" />)}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {selectedGermplasm.map(g => (
            <Card key={g.id} className="relative">
              <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-6 w-6" aria-label={`Remove ${g.name} from comparison`} onClick={() => removeGermplasm(g.id)}><X className="h-4 w-4" /></Button>
              <CardHeader className="pb-2">
                <div className="flex items-start gap-2">
                  <Button variant="ghost" size="icon" className="h-6 w-6 -ml-1" aria-label={favorites.includes(g.id) ? `Remove ${g.name} from favorites` : `Add ${g.name} to favorites`} onClick={() => toggleFavorite(g.id)}>
                    {favorites.includes(g.id) ? <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" /> : <StarOff className="h-4 w-4" />}
                  </Button>
                  <div><CardTitle className="text-base">{g.name}</CardTitle><CardDescription className="text-xs">{g.accession}</CardDescription></div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-1 text-sm">
                  <p className="text-muted-foreground italic">{g.species}</p>
                  <p className="text-xs truncate" title={g.pedigree}>{g.pedigree}</p>
                  <Badge variant={g.status === 'candidate' ? 'default' : 'secondary'} className="text-xs">{g.status}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
          {selectedIds.length < 5 && (
            <Card className="border-dashed flex items-center justify-center min-h-[150px]">
              <Button variant="ghost" onClick={() => setShowAddDialog(true)}><Plus className="h-4 w-4 mr-2" />Add Entry</Button>
            </Card>
          )}
        </div>
      )}

      {selectedGermplasm.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-5 w-5" />Trait Comparison</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">Trait</TableHead>
                  {selectedGermplasm.map(g => <TableHead key={g.id} className="text-center">{g.name}</TableHead>)}
                </TableRow>
              </TableHeader>
              <TableBody>
                {comparisonTraits.map(trait => (
                  <TableRow key={trait.id}>
                    <TableCell className="font-medium">
                      <div>{trait.name}{trait.unit && <span className="text-muted-foreground text-xs ml-1">({trait.unit})</span>}</div>
                      <div className="text-xs text-muted-foreground">{trait.higher_is_better ? '↑ Higher is better' : '↓ Lower is better'}</div>
                    </TableCell>
                    {selectedGermplasm.map(g => {
                      const value = g.traits[trait.id];
                      const isBest = value !== undefined && isBestValue(value, trait.id, trait);
                      return (
                        <TableCell key={g.id} className="text-center">
                          {trait.type === 'categorical' ? (
                            <Badge className={getResistanceColor(String(value))}>{value}</Badge>
                          ) : (
                            <span className={`font-mono ${isBest ? 'font-bold text-green-600' : ''}`}>
                              {value}{isBest && <CheckCircle className="inline h-3 w-3 ml-1" />}
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

      {showMarkers && selectedGermplasm.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Dna className="h-5 w-5" />Molecular Markers</CardTitle><CardDescription>Presence/absence of key resistance and tolerance genes</CardDescription></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-48">Marker</TableHead>
                  {selectedGermplasm.map(g => <TableHead key={g.id} className="text-center">{g.name}</TableHead>)}
                </TableRow>
              </TableHeader>
              <TableBody>
                {MARKERS.map(marker => (
                  <TableRow key={marker}>
                    <TableCell className="font-medium font-mono">{marker}</TableCell>
                    {selectedGermplasm.map(g => {
                      const value = g.markers?.[marker];
                      return (
                        <TableCell key={g.id} className="text-center">
                          {value === 'Present' ? (
                            <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Present</Badge>
                          ) : (
                            <Badge variant="outline" className="text-muted-foreground"><X className="h-3 w-3 mr-1" />Absent</Badge>
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

      {selectedGermplasm.length >= 2 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5" />Selection Summary</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">Best for Yield</h4>
                {(() => {
                  const best = selectedGermplasm.reduce((a, b) => (a.traits.yield as number) > (b.traits.yield as number) ? a : b);
                  return <div><p className="text-lg font-bold text-green-900">{best.name}</p><p className="text-sm text-green-700">{best.traits.yield} t/ha</p></div>;
                })()}
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">Best Disease Resistance</h4>
                {(() => {
                  const order = ['R', 'MR', 'MS', 'S', 'HS'];
                  const best = selectedGermplasm.reduce((a, b) => order.indexOf(String(a.traits.blast_resistance)) < order.indexOf(String(b.traits.blast_resistance)) ? a : b);
                  return <div><p className="text-lg font-bold text-blue-900">{best.name}</p><p className="text-sm text-blue-700">Blast: {best.traits.blast_resistance}</p></div>;
                })()}
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-purple-800 mb-2">Best Stress Tolerance</h4>
                {(() => {
                  const order = ['T', 'MT', 'MS', 'S', 'HS'];
                  const best = selectedGermplasm.reduce((a, b) => order.indexOf(String(a.traits.drought_tolerance)) < order.indexOf(String(b.traits.drought_tolerance)) ? a : b);
                  return <div><p className="text-lg font-bold text-purple-900">{best.name}</p><p className="text-sm text-purple-700">Drought: {best.traits.drought_tolerance}</p></div>;
                })()}
              </div>
            </div>
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Marker-Assisted Selection Notes</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                {selectedGermplasm.some(g => g.markers?.['Xa21'] === 'Present' && g.markers?.['xa13'] === 'Present') && (
                  <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-600" />Gene pyramiding possible: Xa21 + xa13 for bacterial blight resistance</li>
                )}
                {selectedGermplasm.some(g => g.markers?.['Sub1A'] === 'Present') && (
                  <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-blue-600" />Sub1A available for submergence tolerance introgression</li>
                )}
                {selectedGermplasm.every(g => g.markers?.['Pi-ta'] === 'Absent') && (
                  <li className="flex items-center gap-2"><AlertCircle className="h-4 w-4 text-orange-600" />Consider adding Pi-ta donor for blast resistance</li>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedGermplasm.length === 0 && !isLoading && (
        <Card className="p-12">
          <div className="text-center">
            <Leaf className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No Germplasm Selected</h3>
            <p className="text-muted-foreground mb-4">Add germplasm entries to compare their traits and markers</p>
            <Button onClick={() => setShowAddDialog(true)}><Plus className="h-4 w-4 mr-2" />Add Germplasm</Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export default GermplasmComparison;
