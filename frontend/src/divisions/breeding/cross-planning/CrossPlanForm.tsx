import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Check, Search } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useDebounce } from '@/hooks/useDebounce';
import { crossPlanningService } from './services/crossPlanningService';
import { useCreateCrossPlan } from './hooks/useCreateCrossPlan';
import type { CrossPlan, CrossPlanCandidate } from './types';

interface CrossPlanFormProps {
  onCancel?: () => void;
  onCreated?: (plan: CrossPlan) => void;
}

function ParentSelector({
  label,
  search,
  onSearchChange,
  selectedParent,
  candidates,
  onSelect,
}: {
  label: string;
  search: string;
  onSearchChange: (value: string) => void;
  selectedParent: CrossPlanCandidate | null;
  candidates: CrossPlanCandidate[];
  onSelect: (candidate: CrossPlanCandidate) => void;
}) {
  return (
    <div className="space-y-3">
      <Label>{label}</Label>
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          aria-label={label}
          className="pl-9"
          placeholder="Search germplasm"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </div>
      {selectedParent ? (
        <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
          <div className="font-medium">{selectedParent.name}</div>
          <div className="text-muted-foreground">
            {selectedParent.accessionNumber ?? selectedParent.germplasmDbId ?? selectedParent.id}
          </div>
        </div>
      ) : null}
      <div className="max-h-48 space-y-2 overflow-auto">
        {candidates.map((candidate) => (
          <button
            key={candidate.id}
            type="button"
            onClick={() => onSelect(candidate)}
            aria-label={`${label} candidate ${candidate.name}`}
            className="flex w-full items-center justify-between rounded-lg border p-3 text-left hover:bg-muted/40"
          >
            <div>
              <div className="font-medium">{candidate.name}</div>
              <div className="text-sm text-muted-foreground">
                {candidate.accessionNumber ?? candidate.germplasmDbId ?? candidate.id}
              </div>
            </div>
            {selectedParent?.id === candidate.id ? <Check className="h-4 w-4 text-primary" /> : null}
          </button>
        ))}
      </div>
    </div>
  );
}

export function CrossPlanForm({ onCancel, onCreated }: CrossPlanFormProps) {
  const createMutation = useCreateCrossPlan();
  const [femaleSearch, setFemaleSearch] = useState('');
  const [maleSearch, setMaleSearch] = useState('');
  const [selectedFemaleParent, setSelectedFemaleParent] = useState<CrossPlanCandidate | null>(null);
  const [selectedMaleParent, setSelectedMaleParent] = useState<CrossPlanCandidate | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [plannedDate, setPlannedDate] = useState('');
  const [objective, setObjective] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const debouncedFemaleSearch = useDebounce(femaleSearch, 250);
  const debouncedMaleSearch = useDebounce(maleSearch, 250);

  const femaleCandidatesQuery = useQuery({
    queryKey: ['breeding', 'cross-planning', 'female-candidates', debouncedFemaleSearch],
    queryFn: () => crossPlanningService.searchParentCandidates(debouncedFemaleSearch || undefined),
  });

  const maleCandidatesQuery = useQuery({
    queryKey: ['breeding', 'cross-planning', 'male-candidates', debouncedMaleSearch],
    queryFn: () => crossPlanningService.searchParentCandidates(debouncedMaleSearch || undefined),
  });

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setValidationError(null);

    if (!selectedFemaleParent || !selectedMaleParent || !name.trim() || !plannedDate || !objective.trim()) {
      setValidationError('Female parent, male parent, plan name, planned date, and objective are required.');
      return;
    }

    if (selectedFemaleParent.id === selectedMaleParent.id) {
      setValidationError('Female and male parents must be different germplasm entries.');
      return;
    }

    try {
      const createdPlan = await createMutation.mutateAsync({
        femaleParentId: selectedFemaleParent.id,
        maleParentId: selectedMaleParent.id,
        name: name.trim(),
        description: description.trim(),
        plannedDate,
        objective: objective.trim(),
      });

      toast.success('Cross plan created');
      onCreated?.(createdPlan);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to create cross plan');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Cross Plan</CardTitle>
        <CardDescription>
          Select female and male parents, record the objective, and save the planned date.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-6 lg:grid-cols-2">
            <ParentSelector
              label="Female Parent"
              search={femaleSearch}
              onSearchChange={setFemaleSearch}
              selectedParent={selectedFemaleParent}
              candidates={femaleCandidatesQuery.data ?? []}
              onSelect={setSelectedFemaleParent}
            />
            <ParentSelector
              label="Male Parent"
              search={maleSearch}
              onSearchChange={setMaleSearch}
              selectedParent={selectedMaleParent}
              candidates={maleCandidatesQuery.data ?? []}
              onSelect={setSelectedMaleParent}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="cross-plan-name">Plan Name</Label>
              <Input
                id="cross-plan-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="2026 drought resilience cross"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cross-plan-date">Planned Date</Label>
              <Input
                id="cross-plan-date"
                type="date"
                value={plannedDate}
                onChange={(event) => setPlannedDate(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="cross-plan-objective">Objective</Label>
            <Textarea
              id="cross-plan-objective"
              value={objective}
              onChange={(event) => setObjective(event.target.value)}
              placeholder="State the breeding objective for the selected parents"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="cross-plan-description">Description</Label>
            <Textarea
              id="cross-plan-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional context for field team execution, provenance, or notes"
              rows={4}
            />
          </div>

          {validationError ? (
            <p className="text-sm text-destructive">{validationError}</p>
          ) : null}

          <div className="flex justify-end gap-2">
            {onCancel ? (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            ) : null}
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Saving Plan...' : 'Save Cross Plan'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
