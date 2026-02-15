import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, OfflinePlot, OfflineTrait } from '@/lib/db';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { syncService } from '@/services/SyncService';
import { useToast } from '@/hooks/use-toast';
import { Save, AlertTriangle } from 'lucide-react';

interface ObservationEntryFormProps {
  plotId: string;
  onClose: () => void;
}

export function ObservationEntryForm({ plotId, onClose }: ObservationEntryFormProps) {
  const { toast } = useToast();
  
  // 1. Fetch Plot & Traits
  const plot = useLiveQuery(
    () => db.plots.get(plotId),
    [plotId]
  );

  const traits = useLiveQuery(
    async () => {
      if (!plot) return [];
      return await db.traits.where({ trialId: plot.trialId }).toArray();
    },
    [plot]
  );

  // 2. Form State
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  // Initialize values (could load existing observations here too)
  useEffect(() => {
    // Ideally we fetch existing observations for this plot to pre-fill
  }, [plotId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!plot) return;

    setSaving(true);
    try {
      // Loop through values and queue sync items
      for (const [traitId, value] of Object.entries(values)) {
        if (!value) continue; // Skip empty
        
        const trait = traits?.find(t => t.id === traitId);
        
        // Save to offline DB immediately for UI feedback
        // (Skipped for brevity, SyncQueue handles the "real" persistence logic)

        await syncService.queueAction('CREATE', 'OBSERVATION', {
          study_id: plot.trialId,
          plot_id: plot.id,
          trait_id: traitId,
          value: parseFloat(value) || value, // Try parse number
          timestamp: new Date().toISOString(),
          notes: ''
        });
      }

      toast({
        title: 'Saved Successfully',
        description: `Recorded data for ${plot.plotNumber}`,
      });
      onClose();
    } catch (err) {
      console.error(err);
      toast({
        title: 'Error Saving',
        description: 'Could not save observation.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (!plot) return <div>Loading plot...</div>;

  return (
    <Card className="w-full">
      <CardHeader className="pb-2 bg-green-50 border-b">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-lg">Plot {plot.plotNumber}</CardTitle>
            <p className="text-sm text-gray-600 font-mono">{plot.accessionName}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} type="button">Close</Button>
        </div>
      </CardHeader>
      
      <CardContent className="pt-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          {!traits || traits.length === 0 ? (
            <div className="text-center p-4 text-gray-500">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
              <p>No traits defined for this trial.</p>
              <p className="text-xs">Try syncing study metadata.</p>
            </div>
          ) : (
            traits.map(trait => (
              <div key={trait.id} className="space-y-1">
                <label className="text-sm font-medium flex justify-between">
                  {trait.name}
                  {trait.unit && <span className="text-gray-400 font-normal">({trait.unit})</span>}
                </label>
                <Input
                  type={trait.dataType === 'Numeric' ? 'number' : 'text'}
                  placeholder={trait.min && trait.max ? `${trait.min} - ${trait.max}` : 'Enter value'}
                  value={values[trait.id] || ''}
                  onChange={(e) => setValues(prev => ({ ...prev, [trait.id]: e.target.value }))}
                  className="text-lg"
                />
              </div>
            ))
          )}

          <div className="pt-4">
            <Button type="submit" className="w-full h-12 text-lg gap-2" disabled={saving || !traits?.length}>
              <Save className="w-5 h-5" />
              {saving ? 'Saving...' : 'Save Observations'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
