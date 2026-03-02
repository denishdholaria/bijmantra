import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { WeatherStation } from '@/types/weather';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Trash2, Edit } from 'lucide-react';
import { WeatherStationForm } from './WeatherStationForm';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';

export function WeatherStationList() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingStation, setEditingStation] = useState<WeatherStation | null>(null);
  const queryClient = useQueryClient();

  const { data: stations, isLoading } = useQuery({
    queryKey: ['weather-stations'],
    queryFn: () => apiClient.weatherService.listWeatherStations(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.weatherService.deleteWeatherStation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weather-stations'] });
      toast.success('Station deleted');
    },
    onError: () => toast.error('Failed to delete station'),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Weather Stations</CardTitle>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Add Station
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Weather Station</DialogTitle>
            </DialogHeader>
            <WeatherStationForm
              onSuccess={() => {
                setIsCreateOpen(false);
                queryClient.invalidateQueries({ queryKey: ['weather-stations'] });
              }}
            />
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Coordinates</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {stations?.map((station) => (
              <TableRow key={station.id}>
                <TableCell className="font-medium">{station.name}</TableCell>
                <TableCell>{station.latitude}, {station.longitude}</TableCell>
                <TableCell>{station.provider || '-'}</TableCell>
                <TableCell>{station.status}</TableCell>
                <TableCell className="text-right flex items-center justify-end gap-2">
                  <Dialog open={editingStation?.id === station.id} onOpenChange={(open) => !open && setEditingStation(null)}>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="icon" onClick={() => setEditingStation(station)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Weather Station</DialogTitle>
                      </DialogHeader>
                      <WeatherStationForm
                        station={station}
                        onSuccess={() => {
                          setEditingStation(null);
                          queryClient.invalidateQueries({ queryKey: ['weather-stations'] });
                        }}
                      />
                    </DialogContent>
                  </Dialog>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      if (confirm('Delete station?')) deleteMutation.mutate(station.id);
                    }}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {stations?.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center h-24 text-muted-foreground">
                  No weather stations found. Add one to get started.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
