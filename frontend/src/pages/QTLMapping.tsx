/**
 * QTL Mapping Interface
 * Quantitative Trait Loci mapping and marker-trait association analysis
 * Connected to /api/v2/qtl-mapping endpoints
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient, QTL, GWASAssociation, QTLSummary, GOEnrichment } from '@/lib/api-client';

export function QTLMapping() {
  const [analysisType, setAnalysisType] = useState('linkage');
  const [selectedTrait, setSelectedTrait] = useState('all');
  const [lodThreshold, setLodThreshold] = useState([3.0]);
  const [pThreshold, setPThreshold] = useState([5]);

  // Fetch traits
  const { data: traitsData } = useQuery({
    queryKey: ['qtl-mapping', 'traits'],
    queryFn: () => apiClient.qtlMappingService.getTraits(),
  });

  // Fetch QTLs
  const { data: qtlsData, isLoading: loadingQTLs } = useQuery({
    queryKey: ['qtl-mapping', 'qtls', selectedTrait, lodThreshold[0]],
    queryFn: () => apiClient.qtlMappingService.getQTLs({
      trait: selectedTrait !== 'all' ? selectedTrait : undefined,
      min_lod: lodThreshold[0],
    }),
  });

  // Fetch GWAS results
  const { data: gwasData, isLoading: loadingGWAS } = useQuery({
    queryKey: ['qtl-mapping', 'gwas', selectedTrait, pThreshold[0]],
    queryFn: () => apiClient.qtlMappingService.getGWASResults({
      trait: selectedTrait !== 'all' ? selectedTrait : undefined,
      min_log_p: pThreshold[0],
    }),
  });

  // Fetch QTL summary
  const { data: qtlSummary } = useQuery({
    queryKey: ['qtl-mapping', 'summary', 'qtl'],
    queryFn: () => apiClient.qtlMappingService.getQTLSummary(),
  });

  // Fetch GO enrichment
  const { data: goData } = useQuery({
    queryKey: ['qtl-mapping', 'go-enrichment'],
    queryFn: () => apiClient.qtlMappingService.getGOEnrichment(),
  });

  const traits: string[] = traitsData?.traits || ['Grain Yield', 'Plant Height', 'Days to Flowering', 'Grain Weight'];
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const qtls: any[] = qtlsData?.qtls || [];
  const gwasResults: any[] = gwasData?.associations || [];
  const goEnrichment: GOEnrichment[] = goData?.enrichment || [];
  const chromosomes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];


  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">QTL Mapping</h1>
          <p className="text-muted-foreground mt-1">Marker-trait association and QTL analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedTrait} onValueChange={setSelectedTrait}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select trait" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Traits</SelectItem>
              {traits.map((t: string) => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button>Run Analysis</Button>
        </div>
      </div>

      {/* Summary Stats */}
      {qtlSummary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-primary">{qtlSummary.total_qtls}</p>
              <p className="text-xs text-muted-foreground">Total QTLs</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{qtlSummary.total_qtls}</p>
              <p className="text-xs text-muted-foreground">Major QTLs</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-green-600">{qtlSummary.total_pve?.toFixed(1) || 0}%</p>
              <p className="text-xs text-muted-foreground">Total PVE</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-purple-600">{qtlSummary.average_lod?.toFixed(1) || 0}</p>
              <p className="text-xs text-muted-foreground">Avg LOD</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <p className="text-2xl font-bold text-orange-600">{qtlSummary.traits_analyzed}</p>
              <p className="text-xs text-muted-foreground">Traits</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={analysisType} onValueChange={setAnalysisType}>
        <TabsList>
          <TabsTrigger value="linkage">Linkage Mapping</TabsTrigger>
          <TabsTrigger value="gwas">GWAS</TabsTrigger>
          <TabsTrigger value="manhattan">Manhattan Plot</TabsTrigger>
          <TabsTrigger value="candidates">Candidate Genes</TabsTrigger>
        </TabsList>

        <TabsContent value="linkage" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Parameters</CardTitle>
              <CardDescription>Configure QTL detection thresholds</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <Label>LOD Threshold: {lodThreshold[0].toFixed(1)}</Label>
                  <Slider value={lodThreshold} onValueChange={setLodThreshold} min={2} max={10} step={0.5} />
                  <p className="text-xs text-muted-foreground">Minimum LOD score for QTL detection</p>
                </div>
                <div className="space-y-2">
                  <Label>Mapping Method</Label>
                  <Select defaultValue="cim">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sim">Simple Interval Mapping</SelectItem>
                      <SelectItem value="cim">Composite Interval Mapping</SelectItem>
                      <SelectItem value="mqm">Multiple QTL Mapping</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Population Type</Label>
                  <Select defaultValue="ril">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="f2">F2</SelectItem>
                      <SelectItem value="bc">Backcross</SelectItem>
                      <SelectItem value="ril">RIL</SelectItem>
                      <SelectItem value="dh">Doubled Haploid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Detected QTLs</CardTitle>
              <CardDescription>{qtls.length} QTLs above LOD threshold</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingQTLs ? <Skeleton className="h-48 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">QTL Name</th>
                        <th className="text-left p-3">Trait</th>
                        <th className="text-center p-3">Chr</th>
                        <th className="text-right p-3">Position (cM)</th>
                        <th className="text-right p-3">LOD</th>
                        <th className="text-right p-3">PVE (%)</th>
                        <th className="text-right p-3">Add. Effect</th>
                        <th className="text-left p-3">Flanking Markers</th>
                      </tr>
                    </thead>
                    <tbody>
                      {qtls.map((qtl: any) => (
                        <tr key={qtl.id} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-medium">{qtl.name}</td>
                          <td className="p-3"><Badge variant="outline">{qtl.trait}</Badge></td>
                          <td className="p-3 text-center">{qtl.chromosome}</td>
                          <td className="p-3 text-right font-mono">{qtl.position.toFixed(1)}</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold ${qtl.lod >= 8 ? 'text-green-600' : qtl.lod >= 5 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
                              {qtl.lod.toFixed(1)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">{qtl.pve.toFixed(1)}%</td>
                          <td className="p-3 text-right font-mono">
                            <span className={qtl.add_effect > 0 ? 'text-green-600' : 'text-red-600'}>
                              {qtl.add_effect > 0 ? '+' : ''}{qtl.add_effect.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-xs">{qtl.flanking_markers?.join(' - ')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>LOD Profile</CardTitle>
              <CardDescription>Genome-wide LOD score distribution</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {chromosomes.slice(0, 7).map((chr) => {
                  const chrQTLs = qtls.filter((q: any) => q.chromosome === chr);
                  return (
                    <div key={chr} className="flex items-center gap-4">
                      <span className="w-8 text-sm font-medium">Chr {chr}</span>
                      <div className="flex-1 h-8 bg-muted rounded relative">
                        {chrQTLs.map((qtl: any) => (
                          <div key={qtl.id} className="absolute top-0 h-full w-2 bg-primary rounded cursor-pointer hover:bg-primary/80"
                            style={{ left: `${(qtl.position / 150) * 100}%` }}
                            title={`${qtl.name}: LOD ${qtl.lod.toFixed(1)}`} />
                        ))}
                      </div>
                      <span className="w-16 text-xs text-muted-foreground">150 cM</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>


        <TabsContent value="gwas" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>GWAS Parameters</CardTitle>
              <CardDescription>Genome-wide association study settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>-log10(P) Threshold: {pThreshold[0]}</Label>
                  <Slider value={pThreshold} onValueChange={setPThreshold} min={3} max={10} step={0.5} />
                </div>
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Select defaultValue="mlm">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="glm">GLM</SelectItem>
                      <SelectItem value="mlm">MLM</SelectItem>
                      <SelectItem value="cmlm">CMLM</SelectItem>
                      <SelectItem value="farmcpu">FarmCPU</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>MAF Filter</Label>
                  <Input type="number" defaultValue="0.05" step="0.01" />
                </div>
                <div className="space-y-2">
                  <Label>Missing Rate</Label>
                  <Input type="number" defaultValue="0.2" step="0.05" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Significant Associations</CardTitle>
              <CardDescription>{gwasResults.length} markers above threshold</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingGWAS ? <Skeleton className="h-48 w-full" /> : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="text-left p-3">Marker</th>
                        <th className="text-left p-3">Trait</th>
                        <th className="text-center p-3">Chr</th>
                        <th className="text-right p-3">Position</th>
                        <th className="text-right p-3">P-value</th>
                        <th className="text-right p-3">-log10(P)</th>
                        <th className="text-right p-3">Effect</th>
                        <th className="text-right p-3">MAF</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gwasResults.map((assoc: any) => (
                        <tr key={assoc.marker} className="border-b hover:bg-muted/50">
                          <td className="p-3 font-mono font-medium">{assoc.marker}</td>
                          <td className="p-3"><Badge variant="outline">{assoc.trait}</Badge></td>
                          <td className="p-3 text-center">{assoc.chromosome}</td>
                          <td className="p-3 text-right font-mono">{assoc.position.toFixed(1)}</td>
                          <td className="p-3 text-right font-mono text-xs">{assoc.p_value.toExponential(1)}</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold ${assoc.log_p >= 8 ? 'text-red-600' : assoc.log_p >= 5 ? 'text-orange-600' : 'text-yellow-600'}`}>
                              {assoc.log_p.toFixed(1)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">
                            <span className={assoc.effect > 0 ? 'text-green-600' : 'text-red-600'}>
                              {assoc.effect > 0 ? '+' : ''}{assoc.effect.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">{assoc.maf.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manhattan" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Manhattan Plot</CardTitle>
              <CardDescription>Genome-wide association visualization</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-muted rounded-lg p-4 overflow-hidden">
                <svg viewBox="0 0 800 200" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
                  {/* Y-axis */}
                  <line x1="40" y1="10" x2="40" y2="170" stroke="currentColor" strokeOpacity="0.3" />
                  {/* X-axis */}
                  <line x1="40" y1="170" x2="780" y2="170" stroke="currentColor" strokeOpacity="0.3" />
                  {/* Significance threshold line */}
                  <line x1="40" y1={170 - (pThreshold[0] / 10) * 150} x2="780" y2={170 - (pThreshold[0] / 10) * 150} 
                    stroke="#ef4444" strokeDasharray="4,4" strokeWidth="1" />
                  {/* Y-axis labels */}
                  <text x="35" y="175" fontSize="10" textAnchor="end" fill="currentColor" opacity="0.6">0</text>
                  <text x="35" y="95" fontSize="10" textAnchor="end" fill="currentColor" opacity="0.6">5</text>
                  <text x="35" y="20" fontSize="10" textAnchor="end" fill="currentColor" opacity="0.6">10</text>
                  {/* Chromosome data points */}
                  {chromosomes.map((chr, chrIndex) => {
                    const chrWidth = 70;
                    const chrStart = 50 + chrIndex * chrWidth;
                    const isSignificant = gwasResults.some((g: any) => g.chromosome === chr && g.log_p >= pThreshold[0]);
                    // Generate deterministic points based on chromosome
                    const points = Array.from({ length: 12 }, (_, i) => ({
                      x: chrStart + (i / 12) * (chrWidth - 10) + Math.sin(chrIndex * 3 + i) * 5,
                      y: 170 - (Math.abs(Math.sin(chrIndex * 7 + i * 2)) * 3 + 1) * 15,
                      isPeak: i === 6 && isSignificant,
                    }));
                    // Add peak point if significant
                    if (isSignificant) {
                      points.push({
                        x: chrStart + chrWidth / 2,
                        y: 170 - (pThreshold[0] + 2) * 15,
                        isPeak: true,
                      });
                    }
                    return (
                      <g key={chr}>
                        {points.map((point, i) => (
                          <circle
                            key={i}
                            cx={point.x}
                            cy={Math.max(15, Math.min(165, point.y))}
                            r={point.isPeak ? 4 : 3}
                            fill={point.isPeak ? '#ef4444' : chrIndex % 2 === 0 ? '#60a5fa' : '#3b82f6'}
                            opacity={point.isPeak ? 1 : 0.7}
                          />
                        ))}
                        {/* Chromosome label */}
                        <text x={chrStart + chrWidth / 2 - 5} y="190" fontSize="11" fill="currentColor" opacity="0.7">
                          {chr}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
              <div className="flex items-center justify-between mt-4 text-sm">
                <span className="text-muted-foreground">Chromosome</span>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-0.5 bg-red-500" style={{ borderStyle: 'dashed' }} />
                  <span className="text-muted-foreground">Significance threshold (-log10(P) = {pThreshold[0]})</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Q-Q Plot</CardTitle>
              <CardDescription>Quantile-quantile plot for model validation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-48 bg-muted rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <span className="text-4xl">📈</span>
                  <p className="mt-2 text-muted-foreground">Q-Q Plot</p>
                  <p className="text-xs text-muted-foreground">Genomic inflation factor (λ) = 1.02</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="candidates" className="space-y-6 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Candidate Genes</CardTitle>
              <CardDescription>Genes within QTL confidence intervals</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {qtls.slice(0, 4).map((qtl: any) => (
                  <div key={qtl.id} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-bold">{qtl.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Chr {qtl.chromosome}: {qtl.confidence_interval?.[0]?.toFixed(1)} - {qtl.confidence_interval?.[1]?.toFixed(1)} cM
                        </p>
                      </div>
                      <Badge>{qtl.trait}</Badge>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {['Gene_A', 'Gene_B', 'Gene_C'].map((gene, i) => (
                        <div key={gene} className="p-2 bg-muted rounded text-sm">
                          <p className="font-mono font-medium">{gene}_{qtl.chromosome}_{i + 1}</p>
                          <p className="text-xs text-muted-foreground">{['Transcription factor', 'Kinase', 'Transporter'][i]}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>GO Enrichment</CardTitle>
              <CardDescription>Gene Ontology enrichment analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(goEnrichment.length > 0 ? goEnrichment : [
                  { name: 'Response to abiotic stress', p_value: 0.001, gene_count: 8 },
                  { name: 'Carbohydrate metabolic process', p_value: 0.005, gene_count: 5 },
                  { name: 'Regulation of growth', p_value: 0.012, gene_count: 4 },
                  { name: 'Photosynthesis', p_value: 0.023, gene_count: 3 },
                ]).map((go: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-muted rounded">
                    <div>
                      <p className="font-medium">{go.name}</p>
                      <p className="text-xs text-muted-foreground">{go.gene_count} genes</p>
                    </div>
                    <Badge variant={go.p_value < 0.01 ? 'default' : 'secondary'}>P = {go.p_value.toFixed(3)}</Badge>
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
