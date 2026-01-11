/**
 * Quick Entry Page
 * Rapid data entry for common breeding tasks
 * Connected to /api/v2/quick-entry endpoints
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import { Zap, Sprout, Eye, GitMerge, FlaskConical, Save, CheckCircle2, Clock, ArrowRight, Trash2 } from 'lucide-react';

export function QuickEntry() {
  const [activeTab, setActiveTab] = useState('germplasm');
  const queryClient = useQueryClient();

  const [germplasmForm, setGermplasmForm] = useState({ germplasm_name: '', accession_number: '', species: '', country_of_origin: '', pedigree: '', notes: '' });
  const [observationForm, setObservationForm] = useState({ study_id: '', observation_unit_id: '', trait: '', value: '', unit: '', notes: '' });
  const [crossForm, setCrossForm] = useState({ female_parent: '', male_parent: '', cross_date: '', seeds_obtained: '', notes: '' });
  const [trialForm, setTrialForm] = useState({ trial_name: '', program_id: '', start_date: '', end_date: '', notes: '' });

  const { data: stats } = useQuery({ queryKey: ['quick-entry', 'stats'], queryFn: () => apiClient.getQuickEntryStats() });
  const { data: recentData } = useQuery({ queryKey: ['quick-entry', 'recent'], queryFn: () => apiClient.getQuickEntryRecent() });
  const { data: speciesOptions } = useQuery({ queryKey: ['quick-entry', 'options', 'species'], queryFn: () => apiClient.getQuickEntryOptions('species') });
  const { data: countryOptions } = useQuery({ queryKey: ['quick-entry', 'options', 'countries'], queryFn: () => apiClient.getQuickEntryOptions('countries') });
  const { data: traitOptions } = useQuery({ queryKey: ['quick-entry', 'options', 'traits'], queryFn: () => apiClient.getQuickEntryOptions('traits') });
  const { data: programOptions } = useQuery({ queryKey: ['quick-entry', 'options', 'programs'], queryFn: () => apiClient.getQuickEntryOptions('programs') });
  const { data: germplasmOptions } = useQuery({ queryKey: ['quick-entry', 'options', 'germplasm'], queryFn: () => apiClient.getQuickEntryOptions('germplasm') });
  const { data: entriesData, isLoading: loadingEntries } = useQuery({ queryKey: ['quick-entry', 'entries'], queryFn: () => apiClient.getQuickEntries({ limit: 10 }) });

  const createGermplasm = useMutation({
    mutationFn: (data: typeof germplasmForm) => apiClient.createQuickGermplasm(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['quick-entry'] }); toast.success('Germplasm saved'); setGermplasmForm({ germplasm_name: '', accession_number: '', species: '', country_of_origin: '', pedigree: '', notes: '' }); },
  });

  const createObservation = useMutation({
    mutationFn: (data: any) => apiClient.createQuickObservation({ ...data, value: parseFloat(data.value) }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['quick-entry'] }); toast.success('Observation saved'); setObservationForm({ study_id: '', observation_unit_id: '', trait: '', value: '', unit: '', notes: '' }); },
  });

  const createCross = useMutation({
    mutationFn: (data: any) => apiClient.createQuickCross({ ...data, seeds_obtained: data.seeds_obtained ? parseInt(data.seeds_obtained) : undefined }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['quick-entry'] }); toast.success('Cross saved'); setCrossForm({ female_parent: '', male_parent: '', cross_date: '', seeds_obtained: '', notes: '' }); },
  });

  const createTrial = useMutation({
    mutationFn: (data: typeof trialForm) => apiClient.createQuickTrial(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['quick-entry'] }); toast.success('Trial created'); setTrialForm({ trial_name: '', program_id: '', start_date: '', end_date: '', notes: '' }); },
  });

  const deleteEntry = useMutation({
    mutationFn: (entryId: string) => apiClient.deleteQuickEntry(entryId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['quick-entry'] }); toast.success('Entry deleted'); },
  });

  const recentActivity = recentData?.activity || [];
  const totalSaved = stats?.total_entries || 0;

  const formatTimeAgo = (isoString: string) => {
    const diffMins = Math.floor((Date.now() - new Date(isoString).getTime()) / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    return diffHours < 24 ? `${diffHours}h ago` : new Date(isoString).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2"><Zap className="h-8 w-8 text-primary" strokeWidth={2} />Quick Entry</h1>
          <p className="text-muted-foreground mt-1">Rapid data entry for common breeding tasks</p>
        </div>
        <Badge variant="secondary" className="text-lg py-1 px-3"><CheckCircle2 className="h-4 w-4 mr-2 text-emerald-500" strokeWidth={2} />{totalSaved} saved</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['germplasm', 'observation', 'cross', 'trial'].map((type) => {
          const activity = recentActivity.find((a: any) => a.type === type);
          const count = stats?.by_type?.[type] || 0;
          const Icon = type === 'germplasm' ? Sprout : type === 'observation' ? Eye : type === 'cross' ? GitMerge : FlaskConical;
          return (
            <Card key={type}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg"><Icon className="h-5 w-5 text-primary" strokeWidth={1.75} /></div>
                    <div><div className="font-medium capitalize">{type}</div><div className="text-sm text-muted-foreground">{count} entries</div></div>
                  </div>
                  {activity?.last_entry && <div className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" strokeWidth={2} />{formatTimeAgo(activity.last_entry)}</div>}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="germplasm"><Sprout className="h-4 w-4 mr-2" strokeWidth={1.75} />Germplasm</TabsTrigger>
          <TabsTrigger value="observation"><Eye className="h-4 w-4 mr-2" strokeWidth={1.75} />Observation</TabsTrigger>
          <TabsTrigger value="cross"><GitMerge className="h-4 w-4 mr-2" strokeWidth={1.75} />Cross</TabsTrigger>
          <TabsTrigger value="trial"><FlaskConical className="h-4 w-4 mr-2" strokeWidth={1.75} />Trial</TabsTrigger>
          <TabsTrigger value="history">History ({entriesData?.total || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="germplasm">
          <Card>
            <CardHeader><CardTitle>Quick Germplasm Entry</CardTitle><CardDescription>Add new germplasm to the database</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Germplasm Name *</Label><Input placeholder="e.g., IR64-Sub1" value={germplasmForm.germplasm_name} onChange={(e) => setGermplasmForm(f => ({ ...f, germplasm_name: e.target.value }))} /></div>
                <div className="space-y-2"><Label>Accession Number</Label><Input placeholder="e.g., ACC-2025-001" value={germplasmForm.accession_number} onChange={(e) => setGermplasmForm(f => ({ ...f, accession_number: e.target.value }))} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Species</Label><Select value={germplasmForm.species} onValueChange={(v) => setGermplasmForm(f => ({ ...f, species: v }))}><SelectTrigger><SelectValue placeholder="Select species" /></SelectTrigger><SelectContent>{speciesOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
                <div className="space-y-2"><Label>Country of Origin</Label><Select value={germplasmForm.country_of_origin} onValueChange={(v) => setGermplasmForm(f => ({ ...f, country_of_origin: v }))}><SelectTrigger><SelectValue placeholder="Select country" /></SelectTrigger><SelectContent>{countryOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
              </div>
              <div className="space-y-2"><Label>Pedigree</Label><Input placeholder="e.g., IR5657-33-2-1/IR2061-465-1-5-5" value={germplasmForm.pedigree} onChange={(e) => setGermplasmForm(f => ({ ...f, pedigree: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Notes</Label><Textarea placeholder="Additional information..." rows={3} value={germplasmForm.notes} onChange={(e) => setGermplasmForm(f => ({ ...f, notes: e.target.value }))} /></div>
              <Button onClick={() => createGermplasm.mutate(germplasmForm)} disabled={!germplasmForm.germplasm_name || createGermplasm.isPending} className="w-full"><Save className="h-4 w-4 mr-2" />{createGermplasm.isPending ? 'Saving...' : 'Save'}</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="observation">
          <Card>
            <CardHeader><CardTitle>Quick Observation Entry</CardTitle><CardDescription>Record phenotypic observations</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Study ID *</Label><Input placeholder="e.g., study-001" value={observationForm.study_id} onChange={(e) => setObservationForm(f => ({ ...f, study_id: e.target.value }))} /></div>
                <div className="space-y-2"><Label>Observation Unit *</Label><Input placeholder="e.g., plot-R1-C1" value={observationForm.observation_unit_id} onChange={(e) => setObservationForm(f => ({ ...f, observation_unit_id: e.target.value }))} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Trait *</Label><Select value={observationForm.trait} onValueChange={(v) => { const t = traitOptions?.options?.find((x: any) => x.value === v); setObservationForm(f => ({ ...f, trait: v, unit: t?.unit || '' })); }}><SelectTrigger><SelectValue placeholder="Select trait" /></SelectTrigger><SelectContent>{traitOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
                <div className="space-y-2"><Label>Value * {observationForm.unit && `(${observationForm.unit})`}</Label><Input type="number" placeholder="Enter value" value={observationForm.value} onChange={(e) => setObservationForm(f => ({ ...f, value: e.target.value }))} /></div>
              </div>
              <div className="flex gap-2">
                <Button onClick={() => createObservation.mutate(observationForm)} disabled={!observationForm.study_id || !observationForm.trait || !observationForm.value || createObservation.isPending} className="flex-1"><Save className="h-4 w-4 mr-2" />{createObservation.isPending ? 'Saving...' : 'Save'}</Button>
                <Button variant="outline"><ArrowRight className="h-4 w-4 mr-2" />Next Plot</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cross">
          <Card>
            <CardHeader><CardTitle>Quick Cross Entry</CardTitle><CardDescription>Record new crosses</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Female Parent *</Label><Select value={crossForm.female_parent} onValueChange={(v) => setCrossForm(f => ({ ...f, female_parent: v }))}><SelectTrigger><SelectValue placeholder="Select female" /></SelectTrigger><SelectContent>{germplasmOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
                <div className="space-y-2"><Label>Male Parent *</Label><Select value={crossForm.male_parent} onValueChange={(v) => setCrossForm(f => ({ ...f, male_parent: v }))}><SelectTrigger><SelectValue placeholder="Select male" /></SelectTrigger><SelectContent>{germplasmOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Cross Date</Label><Input type="date" value={crossForm.cross_date} onChange={(e) => setCrossForm(f => ({ ...f, cross_date: e.target.value }))} /></div>
                <div className="space-y-2"><Label>Seeds Obtained</Label><Input type="number" placeholder="Number of seeds" value={crossForm.seeds_obtained} onChange={(e) => setCrossForm(f => ({ ...f, seeds_obtained: e.target.value }))} /></div>
              </div>
              <Button onClick={() => createCross.mutate(crossForm)} disabled={!crossForm.female_parent || !crossForm.male_parent || createCross.isPending} className="w-full"><Save className="h-4 w-4 mr-2" />{createCross.isPending ? 'Saving...' : 'Save Cross'}</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trial">
          <Card>
            <CardHeader><CardTitle>Quick Trial Entry</CardTitle><CardDescription>Create a new trial</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Trial Name *</Label><Input placeholder="e.g., Yield Trial Spring 2025" value={trialForm.trial_name} onChange={(e) => setTrialForm(f => ({ ...f, trial_name: e.target.value }))} /></div>
                <div className="space-y-2"><Label>Program</Label><Select value={trialForm.program_id} onValueChange={(v) => setTrialForm(f => ({ ...f, program_id: v }))}><SelectTrigger><SelectValue placeholder="Select program" /></SelectTrigger><SelectContent>{programOptions?.options?.map((opt: any) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent></Select></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Start Date</Label><Input type="date" value={trialForm.start_date} onChange={(e) => setTrialForm(f => ({ ...f, start_date: e.target.value }))} /></div>
                <div className="space-y-2"><Label>End Date</Label><Input type="date" value={trialForm.end_date} onChange={(e) => setTrialForm(f => ({ ...f, end_date: e.target.value }))} /></div>
              </div>
              <Button onClick={() => createTrial.mutate(trialForm)} disabled={!trialForm.trial_name || createTrial.isPending} className="w-full"><Save className="h-4 w-4 mr-2" />{createTrial.isPending ? 'Creating...' : 'Create Trial'}</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card>
            <CardHeader><CardTitle>Recent Entries</CardTitle><CardDescription>Your recent quick entries</CardDescription></CardHeader>
            <CardContent>
              {loadingEntries ? <div className="space-y-2">{[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}</div> : entriesData?.entries?.length ? (
                <div className="space-y-2">
                  {entriesData.entries.map((entry: any) => (
                    <div key={entry.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="capitalize">{entry.type}</Badge>
                        <div>
                          <p className="font-medium text-sm">{entry.data?.germplasm_name || entry.data?.trial_name || (entry.data?.female_parent && `${entry.data.female_parent} × ${entry.data.male_parent}`) || `${entry.data?.trait}: ${entry.data?.value}`}</p>
                          <p className="text-xs text-muted-foreground">{formatTimeAgo(entry.created_at)}</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => deleteEntry.mutate(entry.id)} disabled={deleteEntry.isPending}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  ))}
                </div>
              ) : <div className="text-center py-8 text-muted-foreground">No entries yet. Start adding data above!</div>}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
