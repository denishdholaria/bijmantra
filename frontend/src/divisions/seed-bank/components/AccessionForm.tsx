/**
 * Accession Form Component
 *
 * Form for creating and editing germplasm accessions.
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

const accessionSchema = z.object({
  accession_number: z.string().min(1, 'Accession number is required'),
  genus: z.string().min(1, 'Genus is required'),
  species: z.string().min(1, 'Species is required'),
  subspecies: z.string().optional(),
  common_name: z.string().optional(),
  origin: z.string().min(1, 'Country of origin is required'),
  collection_date: z.string().optional(),
  collection_site: z.string().optional(),
  latitude: z.number().optional(),
  longitude: z.number().optional(),
  altitude: z.number().optional(),
  vault_id: z.string().optional(),
  seed_count: z.number().min(0).default(0),
  acquisition_type: z.string().optional(),
  donor_institution: z.string().optional(),
  mls: z.boolean().default(false),
  pedigree: z.string().optional(),
  notes: z.string().optional(),
});

type AccessionFormData = z.infer<typeof accessionSchema>;

interface AccessionFormProps {
  initialData?: Partial<AccessionFormData>;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function AccessionForm({ initialData, onSuccess, onCancel }: AccessionFormProps) {
  const queryClient = useQueryClient();
  const isEditing = !!initialData?.accession_number;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AccessionFormData>({
    resolver: zodResolver(accessionSchema),
    defaultValues: {
      seed_count: 0,
      mls: false,
      ...initialData,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: AccessionFormData) => {
      if (isEditing) {
        return apiClient.accessionService.updateAccession(initialData.accession_number!, data);
      }
      return apiClient.accessionService.createAccession(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seed-bank', 'accessions'] });
      onSuccess?.();
    },
  });

  const onSubmit = (data: AccessionFormData) => {
    mutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>🌿 Taxonomy</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="accession_number">Accession Number *</Label>
            <Input id="accession_number" {...register('accession_number')} placeholder="ACC-2024-0001" />
            {errors.accession_number && <p className="text-red-500 text-sm mt-1">{errors.accession_number.message}</p>}
          </div>
          <div>
            <Label htmlFor="common_name">Common Name</Label>
            <Input id="common_name" {...register('common_name')} placeholder="Bread Wheat" />
          </div>
          <div>
            <Label htmlFor="genus">Genus *</Label>
            <Input id="genus" {...register('genus')} placeholder="Triticum" />
            {errors.genus && <p className="text-red-500 text-sm mt-1">{errors.genus.message}</p>}
          </div>
          <div>
            <Label htmlFor="species">Species *</Label>
            <Input id="species" {...register('species')} placeholder="aestivum" />
            {errors.species && <p className="text-red-500 text-sm mt-1">{errors.species.message}</p>}
          </div>
          <div>
            <Label htmlFor="subspecies">Subspecies</Label>
            <Input id="subspecies" {...register('subspecies')} />
          </div>
          <div>
            <Label htmlFor="pedigree">Pedigree</Label>
            <Input id="pedigree" {...register('pedigree')} placeholder="Parent1 / Parent2" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>📍 Collection Info</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="origin">Country of Origin *</Label>
            <Input id="origin" {...register('origin')} placeholder="India" />
            {errors.origin && <p className="text-red-500 text-sm mt-1">{errors.origin.message}</p>}
          </div>
          <div>
            <Label htmlFor="collection_date">Collection Date</Label>
            <Input id="collection_date" type="date" {...register('collection_date')} />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="collection_site">Collection Site</Label>
            <Input id="collection_site" {...register('collection_site')} placeholder="Location description" />
          </div>
          <div>
            <Label htmlFor="latitude">Latitude</Label>
            <Input id="latitude" type="number" step="0.0001" {...register('latitude', { valueAsNumber: true })} />
          </div>
          <div>
            <Label htmlFor="longitude">Longitude</Label>
            <Input id="longitude" type="number" step="0.0001" {...register('longitude', { valueAsNumber: true })} />
          </div>
          <div>
            <Label htmlFor="altitude">Altitude (m)</Label>
            <Input id="altitude" type="number" {...register('altitude', { valueAsNumber: true })} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>🏛️ Storage & Acquisition</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="seed_count">Seed Count</Label>
            <Input id="seed_count" type="number" {...register('seed_count', { valueAsNumber: true })} />
          </div>
          <div>
            <Label htmlFor="acquisition_type">Acquisition Type</Label>
            <Select onValueChange={(v) => setValue('acquisition_type', v)} defaultValue={watch('acquisition_type')}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="collection">Collection</SelectItem>
                <SelectItem value="donation">Donation</SelectItem>
                <SelectItem value="exchange">Exchange</SelectItem>
                <SelectItem value="purchase">Purchase</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="donor_institution">Donor Institution</Label>
            <Input id="donor_institution" {...register('donor_institution')} />
          </div>
          <div className="flex items-center gap-2 pt-6">
            <input type="checkbox" id="mls" {...register('mls')} className="h-4 w-4" />
            <Label htmlFor="mls">Multilateral System (MLS)</Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3">
        {onCancel && <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>}
        <Button type="submit" disabled={isSubmitting || mutation.isPending}>
          {mutation.isPending ? 'Saving...' : isEditing ? 'Update Accession' : 'Register Accession'}
        </Button>
      </div>

      {mutation.isError && (
        <p className="text-red-500 text-sm">Error: {(mutation.error as Error).message}</p>
      )}
    </form>
  );
}

export default AccessionForm;
