import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { WeatherStation, WeatherStationCreate, WeatherStationUpdate } from '@/types/weather';
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
import { toast } from 'sonner';

const formSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
  elevation: z.coerce.number().optional(),
  provider: z.string().optional(),
  status: z.string().optional(),
});

interface WeatherStationFormProps {
  station?: WeatherStation;
  onSuccess?: () => void;
}

export function WeatherStationForm({ station, onSuccess }: WeatherStationFormProps) {
  const queryClient = useQueryClient();
  const isEditing = !!station;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: station?.name || "",
      latitude: station?.latitude || 0,
      longitude: station?.longitude || 0,
      elevation: station?.elevation || 0,
      provider: station?.provider || "OpenWeatherMap",
      status: station?.status || "active",
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: WeatherStationCreate) => apiClient.weatherService.createWeatherStation(data),
    onSuccess: () => {
      toast.success('Station created successfully');
      queryClient.invalidateQueries({ queryKey: ['weather-stations'] });
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Failed to create station: ${error}`);
    }
  });

  const updateMutation = useMutation({
    mutationFn: (data: WeatherStationUpdate) => apiClient.weatherService.updateWeatherStation(station!.id, data),
    onSuccess: () => {
      toast.success('Station updated successfully');
      queryClient.invalidateQueries({ queryKey: ['weather-stations'] });
      queryClient.invalidateQueries({ queryKey: ['weather-station', station!.id] });
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Failed to update station: ${error}`);
    }
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    if (isEditing) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input id="name" placeholder="Station Name" {...register("name")} />
        {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="latitude">Latitude</Label>
          <Input id="latitude" type="number" step="any" {...register("latitude")} />
          {errors.latitude && <p className="text-sm text-red-500">{errors.latitude.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="longitude">Longitude</Label>
          <Input id="longitude" type="number" step="any" {...register("longitude")} />
          {errors.longitude && <p className="text-sm text-red-500">{errors.longitude.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="elevation">Elevation (m)</Label>
          <Input id="elevation" type="number" step="any" {...register("elevation")} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="provider">Provider</Label>
          <Input id="provider" placeholder="e.g. OpenWeatherMap" {...register("provider")} />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select
          onValueChange={(val) => setValue("status", val)}
          defaultValue={watch("status")}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="maintenance">Maintenance</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
        {isEditing ? 'Update' : 'Create'} Station
      </Button>
    </form>
  );
}
