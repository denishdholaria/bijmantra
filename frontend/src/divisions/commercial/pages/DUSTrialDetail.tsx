/**
 * DUS Trial Detail Page
 * 
 * View trial details, manage entries, score characters, and run DUS analysis.
 */

import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
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
import { toast } from 'sonner';
import {
  ArrowLeft,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileText,
  Leaf,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TrialEntry {
  entry_id: string;
  variety_name: string;
  is_candidate: boolean;
  is_reference: boolean;
  breeder?: string;
  origin?: string;
  scores: Array<{
    character_id: string;
    value: number | string;
    scored_at: string;
  }>;
}

interface DUSCharacter {
  id: string;
  name: string;
  type: string;
  states: Array<{ code: number; description: string }>;
  is_grouping: boolean;
  is_asterisk: boolean;
}

interface DUSTrial {
  trial_id: string;
  crop_code: string;
  trial_name: string;
  year: number;
  location: string;
  status: string;
  sample_size: number;
  entries: TrialEntry[];
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-500',
  active: 'bg-blue-500',
  scoring: 'bg-amber-500',
  analysis: 'bg-purple-500',
  completed: 'bg-green-500',
};

export default function DUSTrialDetail() {
  const { trialId } = useParams<{ trialId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('entries');
  const [isAddEntryOpen, setIsAddEntryOpen] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<string | null>(null);
  const [newEntry, setNewEntry] = useState({
    variety_name: '',
    is_candidate: false,
    is_reference: false,
    breeder: '',
    origin: '',
  });

  // Fetch trial
  const { data: trial, isLoading } = useQuery<DUSTrial>({
    queryKey: ['dus-trial', trialId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/dus/trials/${trialId}`);
      if (!res.ok) throw new Error('Failed to fetch trial');
      return res.json();
    },
  });

  // Fetch crop characters
  const { data: cropData } = useQuery({
    queryKey: ['dus-crop', trial?.crop_code],
    queryFn: async () => {
      if (!trial?.crop_code) return null;
      const res = await fetch(`${API_BASE}/api/v2/dus/crops/${trial.crop_code}`);
      if (!res.ok) throw new Error('Failed to fetch crop');
      return res.json();
    },
    enabled: !!trial?.crop_code,
  });

  // Add entry mutation
  const addEntryMutation = useMutation({
    mutationFn: async (data: typeof newEntry) => {
      const res = await fetch(`${API_BASE}/api/v2/dus/trials/${trialId}/entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to add entry');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dus-trial', trialId] });
      setIsAddEntryOpen(false);
      setNewEntry({
        variety_name: '',
        is_candidate: false,
        is_reference: false,
        breeder: '',
        origin: '',
      });
      toast.success('Entry added successfully');
    },
  });

  // Score mutation
  const scoreMutation = useMutation({
    mutationFn: async ({
      entryId,
      characterId,
      value,
    }: {
      entryId: string;
      characterId: string;
      value: number | string;
    }) => {
      const res = await fetch(
        `${API_BASE}/api/v2/dus/trials/${trialId}/entries/${entryId}/scores`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ character_id: characterId, value }),
        }
      );
      if (!res.ok) throw new Error('Failed to record score');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dus-trial', trialId] });
      toast.success('Score recorded');
    },
  });

  // Distinctness analysis
  const { data: distinctnessResult, refetch: analyzeDistinctness } = useQuery({
    queryKey: ['dus-distinctness', trialId, selectedEntry],
    queryFn: async () => {
      if (!selectedEntry) return null;
      const res = await fetch(
        `${API_BASE}/api/v2/dus/trials/${trialId}/distinctness/${selectedEntry}`
      );
      if (!res.ok) return null;
      return res.json();
    },
    enabled: false,
  });

  // DUS Report
  const { data: reportResult, refetch: generateReport } = useQuery({
    queryKey: ['dus-report', trialId, selectedEntry],
    queryFn: async () => {
      if (!selectedEntry) return null;
      const res = await fetch(
        `${API_BASE}/api/v2/dus/trials/${trialId}/report/${selectedEntry}`
      );
      if (!res.ok) return null;
      return res.json();
    },
    enabled: false,
  });

  const characters: DUSCharacter[] = cropData?.characters || [];
  const entries = trial?.entries || [];
  const candidates = entries.filter((e) => e.is_candidate);
  const references = entries.filter((e) => e.is_reference);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="h-32 bg-muted rounded" />
        </div>
      </div>
    );
  }

  if (!trial) {
    return (
      <div className="p-6 text-center">
        <p className="text-muted-foreground">Trial not found</p>
        <Link to="/commercial/dus">
          <Button variant="link">← Back to trials</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/commercial/dus">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Leaf className="h-6 w-6" />
              {trial.trial_name}
            </h1>
            <p className="text-muted-foreground">
              {trial.crop_code.toUpperCase()} • {trial.year} • {trial.location}
            </p>
          </div>
        </div>
        <Badge className={STATUS_COLORS[trial.status]}>{trial.status}</Badge>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{entries.length}</p>
            <p className="text-sm text-muted-foreground">Total Entries</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold text-blue-600">{candidates.length}</p>
            <p className="text-sm text-muted-foreground">Candidates</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold text-green-600">{references.length}</p>
            <p className="text-sm text-muted-foreground">References</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-2xl font-bold">{characters.length}</p>
            <p className="text-sm text-muted-foreground">Characters</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="entries">Entries</TabsTrigger>
          <TabsTrigger value="scoring">Scoring</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        {/* Entries Tab */}
        <TabsContent value="entries" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={isAddEntryOpen} onOpenChange={setIsAddEntryOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Entry
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Variety Entry</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Variety Name</Label>
                    <Input
                      value={newEntry.variety_name}
                      onChange={(e) =>
                        setNewEntry({ ...newEntry, variety_name: e.target.value })
                      }
                      placeholder="e.g., IR64"
                    />
                  </div>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="is_candidate"
                        checked={newEntry.is_candidate}
                        onCheckedChange={(c) =>
                          setNewEntry({ ...newEntry, is_candidate: !!c, is_reference: false })
                        }
                      />
                      <Label htmlFor="is_candidate">Candidate</Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox
                        id="is_reference"
                        checked={newEntry.is_reference}
                        onCheckedChange={(c) =>
                          setNewEntry({ ...newEntry, is_reference: !!c, is_candidate: false })
                        }
                      />
                      <Label htmlFor="is_reference">Reference</Label>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Breeder</Label>
                      <Input
                        value={newEntry.breeder}
                        onChange={(e) => setNewEntry({ ...newEntry, breeder: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Origin</Label>
                      <Input
                        value={newEntry.origin}
                        onChange={(e) => setNewEntry({ ...newEntry, origin: e.target.value })}
                      />
                    </div>
                  </div>
                  <Button
                    className="w-full"
                    onClick={() => addEntryMutation.mutate(newEntry)}
                    disabled={!newEntry.variety_name || addEntryMutation.isPending}
                  >
                    Add Entry
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Variety</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Breeder</TableHead>
                    <TableHead>Origin</TableHead>
                    <TableHead>Scores</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.entry_id}>
                      <TableCell className="font-medium">{entry.variety_name}</TableCell>
                      <TableCell>
                        {entry.is_candidate && (
                          <Badge className="bg-blue-500">Candidate</Badge>
                        )}
                        {entry.is_reference && (
                          <Badge className="bg-green-500">Reference</Badge>
                        )}
                      </TableCell>
                      <TableCell>{entry.breeder || '-'}</TableCell>
                      <TableCell>{entry.origin || '-'}</TableCell>
                      <TableCell>
                        {entry.scores?.length || 0} / {characters.length}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scoring Tab */}
        <TabsContent value="scoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Select Entry to Score</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedEntry || ''} onValueChange={setSelectedEntry}>
                <SelectTrigger>
                  <SelectValue placeholder="Select variety" />
                </SelectTrigger>
                <SelectContent>
                  {entries.map((entry) => (
                    <SelectItem key={entry.entry_id} value={entry.entry_id}>
                      {entry.variety_name}{' '}
                      {entry.is_candidate ? '(Candidate)' : entry.is_reference ? '(Reference)' : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {selectedEntry && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Character Scores</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {characters.map((char) => {
                    const entry = entries.find((e) => e.entry_id === selectedEntry);
                    const existingScore = entry?.scores?.find(
                      (s) => s.character_id === char.id
                    );
                    return (
                      <div
                        key={char.id}
                        className="flex items-center gap-4 p-3 border rounded-lg"
                      >
                        <div className="flex-1">
                          <p className="font-medium text-sm">{char.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {char.is_asterisk && '⭐ '}
                            {char.is_grouping && '👥 '}
                            {char.type}
                          </p>
                        </div>
                        <Select
                          value={existingScore?.value?.toString() || ''}
                          onValueChange={(v) =>
                            scoreMutation.mutate({
                              entryId: selectedEntry,
                              characterId: char.id,
                              value: parseInt(v),
                            })
                          }
                        >
                          <SelectTrigger className="w-[200px]">
                            <SelectValue placeholder="Select state" />
                          </SelectTrigger>
                          <SelectContent>
                            {char.states.map((state) => (
                              <SelectItem key={state.code} value={state.code.toString()}>
                                {state.code} - {state.description}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Select Candidate for Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedEntry || ''} onValueChange={setSelectedEntry}>
                <SelectTrigger>
                  <SelectValue placeholder="Select candidate variety" />
                </SelectTrigger>
                <SelectContent>
                  {candidates.map((entry) => (
                    <SelectItem key={entry.entry_id} value={entry.entry_id}>
                      {entry.variety_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => analyzeDistinctness()}
                  disabled={!selectedEntry}
                >
                  Analyze Distinctness
                </Button>
                <Button onClick={() => generateReport()} disabled={!selectedEntry}>
                  <FileText className="h-4 w-4 mr-2" />
                  Generate Report
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Distinctness Result */}
          {distinctnessResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {distinctnessResult.is_distinct ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  Distinctness Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="mb-4">
                  {distinctnessResult.is_distinct
                    ? '✅ Variety is DISTINCT from all reference varieties'
                    : '❌ Variety is NOT distinct from some references'}
                </p>
                <div className="space-y-2">
                  {distinctnessResult.comparisons?.map((comp: any) => (
                    <div
                      key={comp.reference_variety}
                      className="flex items-center justify-between p-2 bg-muted rounded"
                    >
                      <span>{comp.reference_variety}</span>
                      <Badge variant={comp.is_distinct ? 'default' : 'destructive'}>
                        {comp.differing_characters} differences
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Report Result */}
          {reportResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">DUS Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-lg font-bold">
                        {reportResult.distinctness?.is_distinct ? '✅' : '❌'}
                      </p>
                      <p className="text-sm">Distinctness</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-lg font-bold">
                        {reportResult.uniformity?.passed ? '✅' : '⏳'}
                      </p>
                      <p className="text-sm">Uniformity</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-lg font-bold">
                        {reportResult.stability?.is_stable ? '✅' : '⏳'}
                      </p>
                      <p className="text-sm">Stability</p>
                    </div>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="font-medium">Overall Result</p>
                    <p className="text-2xl font-bold mt-2">
                      {reportResult.overall_result === 'PASS' ? (
                        <span className="text-green-600">✅ PASS</span>
                      ) : reportResult.overall_result === 'FAIL' ? (
                        <span className="text-red-600">❌ FAIL</span>
                      ) : (
                        <span className="text-amber-600">⏳ PENDING</span>
                      )}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
