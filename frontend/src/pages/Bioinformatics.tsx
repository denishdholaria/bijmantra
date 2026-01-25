/**
 * Bioinformatics Tools Page
 * 
 * Sequence analysis, primer design, restriction sites, and translation tools.
 * Connects to /api/v2/bioinformatics endpoints.
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dna,
  Scissors,
  FlaskConical,
  Thermometer,
  RotateCcw,
  Play,
  Copy,
  Check,
  AlertCircle,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SequenceStats {
  length: number;
  gc_content: number;
  at_content: number;
  a_count: number;
  t_count: number;
  g_count: number;
  c_count: number;
  molecular_weight: number;
}

interface Primer {
  sequence: string;
  position: number;
  length: number;
  tm: number;
  gc_content: number;
  score: number;
}

interface RestrictionSite {
  enzyme: string;
  position: number;
  recognition_sequence: string;
  cut_site: number;
  overhang: string;
}

interface Enzyme {
  name: string;
  recognition_sequence: string;
  cut_position: number;
  overhang: string;
}

export function Bioinformatics() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [sequence, setSequence] = useState('');
  const [copied, setCopied] = useState(false);
  
  // Primer design state
  const [targetStart, setTargetStart] = useState('30');
  const [targetEnd, setTargetEnd] = useState('70');
  const [minLength, setMinLength] = useState('18');
  const [maxLength, setMaxLength] = useState('25');
  const [minTm, setMinTm] = useState('55');
  const [maxTm, setMaxTm] = useState('65');
  
  // Translation state
  const [frame, setFrame] = useState('0');
  
  // Results state
  const [analysisResult, setAnalysisResult] = useState<SequenceStats | null>(null);
  const [primerResult, setPrimerResult] = useState<{ forward: Primer[]; reverse: Primer[] } | null>(null);
  const [restrictionResult, setRestrictionResult] = useState<RestrictionSite[] | null>(null);
  const [translationResult, setTranslationResult] = useState<{ protein: string; orfs: string[] } | null>(null);
  const [reverseCompResult, setReverseCompResult] = useState<string | null>(null);
  const [tmResult, setTmResult] = useState<{ tm: number; gc_content: number } | null>(null);

  // Fetch enzymes list
  const { data: enzymes = [] } = useQuery<Enzyme[]>({
    queryKey: ['restriction-enzymes'],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v2/bioinformatics/enzymes`);
        if (!res.ok) return [];
        const json = await res.json();
        return json.enzymes || [];
      } catch {
        return [];
      }
    },
  });

  // Analyze sequence mutation
  const analyzeMutation = useMutation({
    mutationFn: async (seq: string) => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: seq }),
      });
      if (!res.ok) throw new Error('Analysis failed');
      return res.json();
    },
    onSuccess: (data) => {
      setAnalysisResult({
        length: data.cleaned_length,
        gc_content: data.gc_content,
        at_content: data.at_content,
        a_count: data.a_count,
        t_count: data.t_count,
        g_count: data.g_count,
        c_count: data.c_count,
        molecular_weight: data.molecular_weight,
      });
    },
  });

  // Design primers mutation
  const primerMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/primers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sequence,
          target_start: parseInt(targetStart),
          target_end: parseInt(targetEnd),
          min_length: parseInt(minLength),
          max_length: parseInt(maxLength),
          min_tm: parseFloat(minTm),
          max_tm: parseFloat(maxTm),
        }),
      });
      if (!res.ok) throw new Error('Primer design failed');
      return res.json();
    },
    onSuccess: (data) => {
      setPrimerResult({
        forward: data.forward_primers || [],
        reverse: data.reverse_primers || [],
      });
    },
  });

  // Find restriction sites mutation
  const restrictionMutation = useMutation({
    mutationFn: async (seq: string) => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/restriction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: seq }),
      });
      if (!res.ok) throw new Error('Restriction analysis failed');
      return res.json();
    },
    onSuccess: (data) => {
      setRestrictionResult(data.sites || []);
    },
  });

  // Translate mutation
  const translateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence, frame: parseInt(frame) }),
      });
      if (!res.ok) throw new Error('Translation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setTranslationResult({
        protein: data.protein || '',
        orfs: data.orfs || [],
      });
    },
  });

  // Reverse complement mutation
  const reverseCompMutation = useMutation({
    mutationFn: async (seq: string) => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/reverse-complement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: seq }),
      });
      if (!res.ok) throw new Error('Reverse complement failed');
      return res.json();
    },
    onSuccess: (data) => {
      setReverseCompResult(data.reverse_complement || '');
    },
  });

  // Tm calculation mutation
  const tmMutation = useMutation({
    mutationFn: async (seq: string) => {
      const res = await fetch(`${API_BASE}/api/v2/bioinformatics/tm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: seq, method: 'nearest_neighbor' }),
      });
      if (!res.ok) throw new Error('Tm calculation failed');
      return res.json();
    },
    onSuccess: (data) => {
      setTmResult({
        tm: data.tm,
        gc_content: data.gc_content,
      });
    },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const cleanSequence = (seq: string) => seq.replace(/[^ATGCatgc]/g, '').toUpperCase();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Dna className="h-6 w-6" />
          Bioinformatics Tools
        </h1>
        <p className="text-muted-foreground">
          Sequence analysis, primer design, restriction sites, and translation
        </p>
      </div>


      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Dna className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">7</p>
                <p className="text-xs text-muted-foreground">Analysis Tools</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Scissors className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{enzymes.length || 15}</p>
                <p className="text-xs text-muted-foreground">Restriction Enzymes</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <FlaskConical className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">3</p>
                <p className="text-xs text-muted-foreground">Tm Methods</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Thermometer className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">3</p>
                <p className="text-xs text-muted-foreground">Reading Frames</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sequence Input */}
      <Card>
        <CardHeader>
          <CardTitle>DNA Sequence Input</CardTitle>
          <CardDescription>Enter or paste your DNA sequence (A, T, G, C only)</CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG..."
            value={sequence}
            onChange={(e) => setSequence(e.target.value)}
            className="font-mono h-32"
          />
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm text-muted-foreground">
              {cleanSequence(sequence).length} bp
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setSequence('')}>
                Clear
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(cleanSequence(sequence))}
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full">
          <TabsTrigger value="analyze">
            <Dna className="h-4 w-4 mr-2" />
            Analyze
          </TabsTrigger>
          <TabsTrigger value="primers">
            <FlaskConical className="h-4 w-4 mr-2" />
            Primers
          </TabsTrigger>
          <TabsTrigger value="restriction">
            <Scissors className="h-4 w-4 mr-2" />
            Restriction
          </TabsTrigger>
          <TabsTrigger value="translate">
            <Play className="h-4 w-4 mr-2" />
            Translate
          </TabsTrigger>
          <TabsTrigger value="tools">
            <RotateCcw className="h-4 w-4 mr-2" />
            Tools
          </TabsTrigger>
        </TabsList>

        {/* Analyze Tab */}
        <TabsContent value="analyze">
          <Card>
            <CardHeader>
              <CardTitle>Sequence Analysis</CardTitle>
              <CardDescription>Analyze composition, GC content, and molecular weight</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                onClick={() => analyzeMutation.mutate(sequence)}
                disabled={!sequence || analyzeMutation.isPending}
              >
                {analyzeMutation.isPending ? 'Analyzing...' : 'Analyze Sequence'}
              </Button>

              {analysisResult && (
                <div className="grid grid-cols-4 gap-4 mt-4">
                  <div className="p-4 border rounded-lg text-center">
                    <p className="text-2xl font-bold">{analysisResult.length}</p>
                    <p className="text-xs text-muted-foreground">Length (bp)</p>
                  </div>
                  <div className="p-4 border rounded-lg text-center">
                    <p className="text-2xl font-bold">{analysisResult.gc_content.toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">GC Content</p>
                  </div>
                  <div className="p-4 border rounded-lg text-center">
                    <p className="text-2xl font-bold">{analysisResult.at_content.toFixed(1)}%</p>
                    <p className="text-xs text-muted-foreground">AT Content</p>
                  </div>
                  <div className="p-4 border rounded-lg text-center">
                    <p className="text-2xl font-bold">{(analysisResult.molecular_weight / 1000).toFixed(1)}k</p>
                    <p className="text-xs text-muted-foreground">MW (Da)</p>
                  </div>
                </div>
              )}

              {analysisResult && (
                <div className="grid grid-cols-4 gap-4">
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-green-600 font-bold">A</span>
                      <span>{analysisResult.a_count}</span>
                    </div>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-red-600 font-bold">T</span>
                      <span>{analysisResult.t_count}</span>
                    </div>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-blue-600 font-bold">G</span>
                      <span>{analysisResult.g_count}</span>
                    </div>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-yellow-600 font-bold">C</span>
                      <span>{analysisResult.c_count}</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Primers Tab */}
        <TabsContent value="primers">
          <Card>
            <CardHeader>
              <CardTitle>Primer Design</CardTitle>
              <CardDescription>Design PCR primers for a target region</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Target Start</Label>
                  <Input
                    type="number"
                    value={targetStart}
                    onChange={(e) => setTargetStart(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Target End</Label>
                  <Input
                    type="number"
                    value={targetEnd}
                    onChange={(e) => setTargetEnd(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Primer Length</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={minLength}
                      onChange={(e) => setMinLength(e.target.value)}
                      placeholder="Min"
                    />
                    <Input
                      type="number"
                      value={maxLength}
                      onChange={(e) => setMaxLength(e.target.value)}
                      placeholder="Max"
                    />
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Tm Range (°C)</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={minTm}
                      onChange={(e) => setMinTm(e.target.value)}
                      placeholder="Min"
                    />
                    <Input
                      type="number"
                      value={maxTm}
                      onChange={(e) => setMaxTm(e.target.value)}
                      placeholder="Max"
                    />
                  </div>
                </div>
              </div>
              <Button
                onClick={() => primerMutation.mutate()}
                disabled={!sequence || sequence.length < 50 || primerMutation.isPending}
              >
                {primerMutation.isPending ? 'Designing...' : 'Design Primers'}
              </Button>

              {primerResult && (
                <div className="grid md:grid-cols-2 gap-4 mt-4">
                  <div>
                    <h4 className="font-medium mb-2">Forward Primers ({primerResult.forward.length})</h4>
                    <div className="space-y-2">
                      {primerResult.forward.slice(0, 5).map((p, i) => (
                        <div key={i} className="p-2 border rounded text-sm">
                          <code className="font-mono text-xs">{p.sequence}</code>
                          <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                            <span>Tm: {p.tm.toFixed(1)}°C</span>
                            <span>GC: {p.gc_content.toFixed(1)}%</span>
                            <span>Pos: {p.position}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Reverse Primers ({primerResult.reverse.length})</h4>
                    <div className="space-y-2">
                      {primerResult.reverse.slice(0, 5).map((p, i) => (
                        <div key={i} className="p-2 border rounded text-sm">
                          <code className="font-mono text-xs">{p.sequence}</code>
                          <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                            <span>Tm: {p.tm.toFixed(1)}°C</span>
                            <span>GC: {p.gc_content.toFixed(1)}%</span>
                            <span>Pos: {p.position}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>


        {/* Restriction Tab */}
        <TabsContent value="restriction">
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Restriction Site Analysis</CardTitle>
                <CardDescription>Find enzyme cut sites in your sequence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => restrictionMutation.mutate(sequence)}
                  disabled={!sequence || restrictionMutation.isPending}
                >
                  {restrictionMutation.isPending ? 'Searching...' : 'Find Restriction Sites'}
                </Button>

                {restrictionResult && restrictionResult.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Enzyme</TableHead>
                        <TableHead>Position</TableHead>
                        <TableHead>Recognition</TableHead>
                        <TableHead>Overhang</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {restrictionResult.map((site, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">{site.enzyme}</TableCell>
                          <TableCell>{site.position}</TableCell>
                          <TableCell className="font-mono text-sm">{site.recognition_sequence}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{site.overhang}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}

                {restrictionResult && restrictionResult.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                    <p>No restriction sites found</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Available Enzymes</CardTitle>
                <CardDescription>{enzymes.length} enzymes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {enzymes.map((enzyme) => (
                    <div key={enzyme.name} className="p-2 border rounded text-sm">
                      <div className="font-medium">{enzyme.name}</div>
                      <div className="font-mono text-xs text-muted-foreground">
                        {enzyme.recognition_sequence}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Translate Tab */}
        <TabsContent value="translate">
          <Card>
            <CardHeader>
              <CardTitle>DNA Translation</CardTitle>
              <CardDescription>Translate DNA to protein sequence</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="space-y-2">
                  <Label>Reading Frame</Label>
                  <Select value={frame} onValueChange={setFrame}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Frame 0</SelectItem>
                      <SelectItem value="1">Frame 1</SelectItem>
                      <SelectItem value="2">Frame 2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={() => translateMutation.mutate()}
                  disabled={!sequence || sequence.length < 3 || translateMutation.isPending}
                >
                  {translateMutation.isPending ? 'Translating...' : 'Translate'}
                </Button>
              </div>

              {translationResult && (
                <div className="space-y-4 mt-4">
                  <div>
                    <Label>Protein Sequence</Label>
                    <div className="p-3 border rounded-lg bg-muted/50 font-mono text-sm break-all mt-2">
                      {translationResult.protein}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {translationResult.protein.length} amino acids • 
                      {translationResult.protein.split('*').length - 1} stop codons
                    </p>
                  </div>

                  {translationResult.orfs.length > 0 && (
                    <div>
                      <Label>Open Reading Frames (ORFs)</Label>
                      <div className="space-y-2 mt-2">
                        {translationResult.orfs.map((orf, i) => (
                          <div key={i} className="p-2 border rounded text-sm">
                            <div className="flex items-center justify-between mb-1">
                              <Badge variant="secondary">ORF {i + 1}</Badge>
                              <span className="text-xs text-muted-foreground">{orf.length} aa</span>
                            </div>
                            <code className="font-mono text-xs break-all">{orf}</code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Reverse Complement</CardTitle>
                <CardDescription>Get the reverse complement of your sequence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => reverseCompMutation.mutate(sequence)}
                  disabled={!sequence || reverseCompMutation.isPending}
                >
                  {reverseCompMutation.isPending ? 'Computing...' : 'Get Reverse Complement'}
                </Button>

                {reverseCompResult && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Result</Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(reverseCompResult)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="p-3 border rounded-lg bg-muted/50 font-mono text-sm break-all">
                      {reverseCompResult}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Melting Temperature (Tm)</CardTitle>
                <CardDescription>Calculate primer Tm using nearest-neighbor method</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => tmMutation.mutate(sequence)}
                  disabled={!sequence || sequence.length < 10 || sequence.length > 50 || tmMutation.isPending}
                >
                  {tmMutation.isPending ? 'Calculating...' : 'Calculate Tm'}
                </Button>
                {sequence.length > 50 && (
                  <p className="text-xs text-yellow-600">Sequence too long for Tm (max 50 bp)</p>
                )}

                {tmResult && (
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-3xl font-bold">{tmResult.tm}°C</p>
                      <p className="text-xs text-muted-foreground">Melting Temperature</p>
                    </div>
                    <div className="p-4 border rounded-lg text-center">
                      <p className="text-3xl font-bold">{tmResult.gc_content}%</p>
                      <p className="text-xs text-muted-foreground">GC Content</p>
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

export default Bioinformatics;
