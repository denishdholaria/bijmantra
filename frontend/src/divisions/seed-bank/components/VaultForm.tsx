/**
 * Vault Form Component
 *
 * Form for creating and editing storage vaults.
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';

const vaultSchema = z.object({
  name: z.string().min(1, 'Vault name is required'),
  type: z.enum(['base', 'active', 'cryo']),
  temperature: z.number(),
  humidity: z.number().min(0).max(100),
  capacity: z.number().min(1, 'Capacity must be at least 1'),
  used: z.number().min(0).default(0),
});

type VaultFormData = z.infer<typeof vaultSchema>;

interface VaultFormProps {
  initialData?: Partial<VaultFormData>;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function VaultForm({ initialData, onSuccess, onCancel }: VaultFormProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<VaultFormData>({
    resolver: zodResolver(vaultSchema),
    defaultValues: {
      type: 'base',
      temperature: -18,
      humidity: 15,
      capacity: 10000,
      used: 0,
      ...initialData,
    },
  });

  const vaultType = watch('type');

  const mutation = useMutation({
    mutationFn: (data: VaultFormData) => apiClient.vaultService.createVault(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-bank', 'vaults'] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: VaultFormData) => mutation.mutate(data);

  // Set default temperature based on vault type
  const handleTypeChange = (type: 'base' | 'active' | 'cryo') => {
    setValue('type', type);
    if (type === 'base') {
      setValue('temperature', -18);
      setValue('humidity', 15);
    } else if (type === 'active') {
      setValue('temperature', 4);
      setValue('humidity', 25);
    } else if (type === 'cryo') {
      setValue('temperature', -196);
      setValue('humidity', 0);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>🏛️ Vault Details</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <Label htmlFor="name">Vault Name *</Label>
            <Input id="name" {...register('name')} placeholder="Base Collection A" />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
          </div>
          <div>
            <Label htmlFor="type">Vault Type *</Label>
            <Select onValueChange={handleTypeChange} defaultValue={vaultType}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="base">🏛️ Base Collection (-18°C)</SelectItem>
                <SelectItem value="active">📦 Active Collection (4°C)</SelectItem>
                <SelectItem value="cryo">❄️ Cryo Storage (-196°C)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="capacity">Capacity (accessions) *</Label>
            <Input id="capacity" type="number" {...register('capacity', { valueAsNumber: true })} />
            {errors.capacity && <p className="text-red-500 text-sm mt-1">{errors.capacity.message}</p>}
          </div>
          <div>
            <Label htmlFor="temperature">Temperature (°C)</Label>
            <Input id="temperature" type="number" {...register('temperature', { valueAsNumber: true })} />
          </div>
          <div>
            <Label htmlFor="humidity">Humidity (%)</Label>
            <Input id="humidity" type="number" min="0" max="100" {...register('humidity', { valueAsNumber: true })} />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        {onCancel && <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>}
        <Button type="submit" disabled={isSubmitting || mutation.isPending}>
          {mutation.isPending ? 'Creating...' : 'Create Vault'}
        </Button>
      </div>

      {mutation.isError && (
        <p className="text-red-500 text-sm">Error: {(mutation.error as Error).message}</p>
      )}
    </form>
  );
}

export default VaultForm;
