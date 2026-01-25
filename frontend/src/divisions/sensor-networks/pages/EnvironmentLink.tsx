/**
 * Environment Link Page
 *
 * Link IoT devices to BrAPI environments for automatic aggregation.
 * This enables sensor data to be used in breeding workflows.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Link2, Plus, Radio, Trash2, MapPin, Beaker, Calendar } from 'lucide-react';

interface Device {
  deviceDbId: string;
  deviceName: string;
  deviceType: string;
  status: string;
  environmentDbId?: string;
  location?: { lat: number; lon: number };
}

interface EnvironmentLink {
  id: string;
  environmentDbId: string;
  deviceDbId: string;
  deviceName: string;
  studyName?: string;
  trialName?: string;
  isPrimary: boolean;
  isActive: boolean;
  startDate?: string;
  endDate?: string;
}

export function EnvironmentLink() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [links, setLinks] = useState<EnvironmentLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  // New link form
  const [newLink, setNewLink] = useState({
    environmentDbId: '',
    deviceDbId: '',
    studyName: '',
    isPrimary: false,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/brapi/v2/extensions/iot/devices');
        if (res.ok) {
          const data = await res.json();
          setDevices(data.result?.data || []);
        }
      } catch (error) {
        console.error('Failed to fetch devices:', error);
        // No data available - show empty state
        setDevices([]);
      }
      
      // Fetch links from API (would be a real endpoint in production)
      try {
        const linksRes = await fetch('/brapi/v2/extensions/iot/environment-links');
        if (linksRes.ok) {
          const linksData = await linksRes.json();
          setLinks(linksData.result?.data || []);
        }
      } catch {
        // No links available
        setLinks([]);
      }
      
      setLoading(false);
    };
    
    fetchData();
  }, []);

  const handleCreateLink = () => {
    const device = devices.find(d => d.deviceDbId === newLink.deviceDbId);
    if (!device) return;
    
    const link: EnvironmentLink = {
      id: `link-${Date.now()}`,
      environmentDbId: newLink.environmentDbId,
      deviceDbId: newLink.deviceDbId,
      deviceName: device.deviceName,
      studyName: newLink.studyName,
      isPrimary: newLink.isPrimary,
      isActive: true,
      startDate: new Date().toISOString().split('T')[0],
    };
    
    setLinks([...links, link]);
    setDialogOpen(false);
    setNewLink({ environmentDbId: '', deviceDbId: '', studyName: '', isPrimary: false });
  };

  const handleDeleteLink = (id: string) => {
    setLinks(links.filter(l => l.id !== id));
  };

  const unlinkedDevices = devices.filter(d => !d.environmentDbId);
  const linkedDevices = devices.filter(d => d.environmentDbId);

  // Group links by environment
  const linksByEnvironment = links.reduce((acc, link) => {
    if (!acc[link.environmentDbId]) {
      acc[link.environmentDbId] = [];
    }
    acc[link.environmentDbId].push(link);
    return acc;
  }, {} as Record<string, EnvironmentLink[]>);

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <div className="grid md:grid-cols-2 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold flex items-center gap-2">
            <Link2 className="h-8 w-8" />
            Environment Links
          </h1>
          <p className="text-muted-foreground mt-1">
            Connect IoT devices to BrAPI environments for automatic data aggregation
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Link
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Link Device to Environment</DialogTitle>
              <DialogDescription>
                Connect a sensor device to a BrAPI environment for automatic data aggregation.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Environment ID</label>
                <Input
                  value={newLink.environmentDbId}
                  onChange={(e) => setNewLink({ ...newLink, environmentDbId: e.target.value })}
                  placeholder="e.g., env-kharif-2025-field-c"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Device</label>
                <Select value={newLink.deviceDbId} onValueChange={(v) => setNewLink({ ...newLink, deviceDbId: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select device" />
                  </SelectTrigger>
                  <SelectContent>
                    {devices.map(device => (
                      <SelectItem key={device.deviceDbId} value={device.deviceDbId}>
                        {device.deviceName} ({device.deviceType})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Study Name (optional)</label>
                <Input
                  value={newLink.studyName}
                  onChange={(e) => setNewLink({ ...newLink, studyName: e.target.value })}
                  placeholder="e.g., Rice Yield Trial 2025"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isPrimary"
                  checked={newLink.isPrimary}
                  onChange={(e) => setNewLink({ ...newLink, isPrimary: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="isPrimary" className="text-sm">Primary device for this environment</label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleCreateLink} disabled={!newLink.environmentDbId || !newLink.deviceDbId}>
                Create Link
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Radio className="h-6 w-6 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{devices.length}</p>
                <p className="text-xs text-muted-foreground">Total Devices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Link2 className="h-6 w-6 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{linkedDevices.length}</p>
                <p className="text-xs text-muted-foreground">Linked Devices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <MapPin className="h-6 w-6 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{Object.keys(linksByEnvironment).length}</p>
                <p className="text-xs text-muted-foreground">Environments</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Beaker className="h-6 w-6 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{links.length}</p>
                <p className="text-xs text-muted-foreground">Active Links</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Unlinked Devices Warning */}
      {unlinkedDevices.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50 dark:bg-yellow-950 dark:border-yellow-800">
          <CardHeader>
            <CardTitle className="text-yellow-700 dark:text-yellow-300 flex items-center gap-2">
              <Radio className="h-5 w-5" />
              Unlinked Devices ({unlinkedDevices.length})
            </CardTitle>
            <CardDescription className="text-yellow-600 dark:text-yellow-400">
              These devices are not linked to any environment. Their data won't be aggregated for breeding analysis.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {unlinkedDevices.map(device => (
                <Badge key={device.deviceDbId} variant="outline" className="border-yellow-300">
                  {device.deviceName}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Links by Environment */}
      {Object.entries(linksByEnvironment).map(([envId, envLinks]) => (
        <Card key={envId}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-primary" />
              {envId}
            </CardTitle>
            <CardDescription>
              {envLinks[0]?.studyName && `Study: ${envLinks[0].studyName}`}
              {envLinks[0]?.trialName && ` • Trial: ${envLinks[0].trialName}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Device</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Primary</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {envLinks.map(link => {
                  const device = devices.find(d => d.deviceDbId === link.deviceDbId);
                  return (
                    <TableRow key={link.id}>
                      <TableCell className="font-medium">{link.deviceName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{device?.deviceType || 'unknown'}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={
                          device?.status === 'online' ? 'bg-green-100 text-green-700' :
                          device?.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }>
                          {device?.status || 'unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {link.isPrimary && <Badge className="bg-blue-100 text-blue-700">Primary</Badge>}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {link.startDate}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteLink(link.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}

      {/* Info Card */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="text-blue-700 dark:text-blue-300 flex items-center gap-2">
            <Link2 className="h-5 w-5" />
            How Environment Links Work
          </CardTitle>
        </CardHeader>
        <CardContent className="text-blue-700 dark:text-blue-300 text-sm space-y-2">
          <p>
            <strong>Environment Links</strong> connect IoT devices to BrAPI environments, enabling automatic aggregation of sensor data for breeding analysis.
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li><strong>Primary Device</strong>: The main data source for an environment (e.g., weather station)</li>
            <li><strong>Secondary Devices</strong>: Additional sensors that contribute to aggregates (e.g., soil probes)</li>
            <li><strong>Aggregation</strong>: Daily/weekly/seasonal summaries are calculated automatically</li>
            <li><strong>G×E Analysis</strong>: Aggregates become environmental covariates for breeding analysis</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default EnvironmentLink;
