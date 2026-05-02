import { useState } from 'react';
import { Sprout } from 'lucide-react';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CrossPlanForm } from './CrossPlanForm';
import { CrossPlanListPage } from './CrossPlanListPage';
import { PedigreeTree } from './PedigreeTree';
import type { CrossPlan } from './types';

interface PedigreeFocus {
  germplasmId: string;
  name: string;
}

export function CrossPlanningWorkspace() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [pedigreeFocus, setPedigreeFocus] = useState<PedigreeFocus | null>(null);

  const handleCreated = (plan: CrossPlan) => {
    setShowCreateForm(false);

    const focusId = plan.femaleParentId ?? plan.maleParentId;
    const focusName = plan.femaleParentName ?? plan.maleParentName ?? 'Selected parent';

    if (focusId) {
      setPedigreeFocus({
        germplasmId: focusId,
        name: focusName,
      });
    }
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <CrossPlanListPage onCreateRequested={() => setShowCreateForm(true)} />

      <div className="space-y-6">
        {showCreateForm ? (
          <CrossPlanForm
            onCancel={() => setShowCreateForm(false)}
            onCreated={handleCreated}
          />
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sprout className="h-5 w-5" />
                <CardTitle>Create or Inspect Pedigree</CardTitle>
              </div>
              <CardDescription>
                Start a new cross plan to focus the pedigree panel on the selected female parent.
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        <PedigreeTree
          germplasmId={pedigreeFocus?.germplasmId ?? null}
          title={
            pedigreeFocus
              ? `Pedigree for ${pedigreeFocus.name}`
              : 'Pedigree Tree'
          }
        />
      </div>
    </div>
  );
}
