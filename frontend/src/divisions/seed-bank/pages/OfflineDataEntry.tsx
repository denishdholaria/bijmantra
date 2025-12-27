/**
 * Offline Data Entry for Seed Bank
 * 
 * Allows field workers to collect accession data without internet connectivity.
 * Data is stored locally in IndexedDB and synced when back online.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  WifiOff,
  Wifi,
  Plus,
  Save,
  Upload,
  Trash2,
  MapPin,
  Camera,
  CheckCircle,
  AlertCircle,
  Clock,
  Leaf,
  RefreshCw,
} from 'lucide-react';

interface OfflineAccession {
  id: string;
  accessionNumber: string;
  genus: string;
  species: string;
  commonName: string;
  collectionDate: string;
  collectorName: string;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  habitat: string;
  sampleType: string;
  seedCount: number | null;
  notes: string;
  status: 'draft' | 'pending' | 'synced' | 'error';
  createdAt: string;
  syncedAt: string | null;
  errorMessage: string | null;
}


const STORAGE_KEY = 'bijmantra_offline_accessions';

export function OfflineDataEntry() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [entries, setEntries] = useState<OfflineAccession[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [currentEntry, setCurrentEntry] = useState<Partial<OfflineAccession>>({
    genus: '',
    species: '',
    commonName: '',
    collectionDate: new Date().toISOString().split('T')[0],
    collectorName: '',
    latitude: null,
    longitude: null,
    altitude: null,
    habitat: '',
    sampleType: 'seed',
    seedCount: null,
    notes: '',
  });

  // Monitor online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load entries from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setEntries(JSON.parse(stored));
    }
  }, []);

  // Save entries to localStorage
  const saveEntries = (newEntries: OfflineAccession[]) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newEntries));
    setEntries(newEntries);
  };

  // Generate accession number
  const generateAccessionNumber = () => {
    const date = new Date();
    const year = date.getFullYear();
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    return `OFF-${year}-${random}`;
  };


  // Get current GPS location
  const getCurrentLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentEntry(prev => ({
            ...prev,
            latitude: Math.round(position.coords.latitude * 1000000) / 1000000,
            longitude: Math.round(position.coords.longitude * 1000000) / 1000000,
            altitude: position.coords.altitude ? Math.round(position.coords.altitude) : null,
          }));
        },
        (error) => {
          console.error('GPS error:', error);
          alert('Unable to get GPS location. Please enter coordinates manually.');
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      alert('GPS not available on this device.');
    }
  };

  // Save new entry
  const handleSaveEntry = () => {
    const newEntry: OfflineAccession = {
      id: crypto.randomUUID(),
      accessionNumber: generateAccessionNumber(),
      genus: currentEntry.genus || '',
      species: currentEntry.species || '',
      commonName: currentEntry.commonName || '',
      collectionDate: currentEntry.collectionDate || new Date().toISOString().split('T')[0],
      collectorName: currentEntry.collectorName || '',
      latitude: currentEntry.latitude || null,
      longitude: currentEntry.longitude || null,
      altitude: currentEntry.altitude || null,
      habitat: currentEntry.habitat || '',
      sampleType: currentEntry.sampleType || 'seed',
      seedCount: currentEntry.seedCount || null,
      notes: currentEntry.notes || '',
      status: 'draft',
      createdAt: new Date().toISOString(),
      syncedAt: null,
      errorMessage: null,
    };

    saveEntries([newEntry, ...entries]);
    setShowForm(false);
    resetForm();
  };

  const resetForm = () => {
    setCurrentEntry({
      genus: '',
      species: '',
      commonName: '',
      collectionDate: new Date().toISOString().split('T')[0],
      collectorName: '',
      latitude: null,
      longitude: null,
      altitude: null,
      habitat: '',
      sampleType: 'seed',
      seedCount: null,
      notes: '',
    });
  };


  // Delete entry
  const handleDeleteEntry = (id: string) => {
    const updated = entries.filter(e => e.id !== id);
    saveEntries(updated);
  };

  // Mark entry as pending sync
  const markForSync = (id: string) => {
    const updated = entries.map(e => 
      e.id === id ? { ...e, status: 'pending' as const } : e
    );
    saveEntries(updated);
  };

  // Sync all pending entries
  const syncEntries = async () => {
    if (!isOnline) {
      alert('You are offline. Please connect to the internet to sync.');
      return;
    }

    setSyncing(true);
    const pendingEntries = entries.filter(e => e.status === 'pending');
    
    for (const entry of pendingEntries) {
      try {
        const response = await fetch('/api/v2/seed-bank/accessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            accession_number: entry.accessionNumber,
            genus: entry.genus,
            species: entry.species,
            common_name: entry.commonName,
            collection_date: entry.collectionDate,
            collector_name: entry.collectorName,
            latitude: entry.latitude,
            longitude: entry.longitude,
            altitude: entry.altitude,
            habitat: entry.habitat,
            sample_type: entry.sampleType,
            seed_count: entry.seedCount,
            notes: entry.notes,
            source: 'offline_collection',
          }),
        });

        if (response.ok) {
          const updated = entries.map(e =>
            e.id === entry.id
              ? { ...e, status: 'synced' as const, syncedAt: new Date().toISOString(), errorMessage: null }
              : e
          );
          saveEntries(updated);
        } else {
          const error = await response.text();
          const updated = entries.map(e =>
            e.id === entry.id
              ? { ...e, status: 'error' as const, errorMessage: error }
              : e
          );
          saveEntries(updated);
        }
      } catch (err) {
        const updated = entries.map(e =>
          e.id === entry.id
            ? { ...e, status: 'error' as const, errorMessage: String(err) }
            : e
        );
        saveEntries(updated);
      }
    }

    setSyncing(false);
  };

  const getStatusBadge = (status: OfflineAccession['status']) => {
    switch (status) {
      case 'draft': return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Draft</Badge>;
      case 'pending': return <Badge className="bg-blue-100 text-blue-800"><Upload className="h-3 w-3 mr-1" />Pending</Badge>;
      case 'synced': return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Synced</Badge>;
      case 'error': return <Badge className="bg-red-100 text-red-800"><AlertCircle className="h-3 w-3 mr-1" />Error</Badge>;
    }
  };

  const draftCount = entries.filter(e => e.status === 'draft').length;
  const pendingCount = entries.filter(e => e.status === 'pending').length;
  const syncedCount = entries.filter(e => e.status === 'synced').length;
  const errorCount = entries.filter(e => e.status === 'error').length;


  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Leaf className="h-6 w-6" />
            Offline Data Entry
          </h1>
          <p className="text-muted-foreground">
            Collect accession data in the field without internet
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isOnline ? 'default' : 'secondary'} className="gap-1">
            {isOnline ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {isOnline ? 'Online' : 'Offline'}
          </Badge>
          <Dialog open={showForm} onOpenChange={setShowForm}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Collection
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>New Accession Collection</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* Taxonomy */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="genus">Genus *</Label>
                    <Input
                      id="genus"
                      value={currentEntry.genus}
                      onChange={(e) => setCurrentEntry(prev => ({ ...prev, genus: e.target.value }))}
                      placeholder="e.g., Oryza"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="species">Species *</Label>
                    <Input
                      id="species"
                      value={currentEntry.species}
                      onChange={(e) => setCurrentEntry(prev => ({ ...prev, species: e.target.value }))}
                      placeholder="e.g., sativa"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="commonName">Common Name</Label>
                  <Input
                    id="commonName"
                    value={currentEntry.commonName}
                    onChange={(e) => setCurrentEntry(prev => ({ ...prev, commonName: e.target.value }))}
                    placeholder="e.g., Rice"
                  />
                </div>

                {/* Collection Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="collectionDate">Collection Date *</Label>
                    <Input
                      id="collectionDate"
                      type="date"
                      value={currentEntry.collectionDate}
                      onChange={(e) => setCurrentEntry(prev => ({ ...prev, collectionDate: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="collectorName">Collector Name *</Label>
                    <Input
                      id="collectorName"
                      value={currentEntry.collectorName}
                      onChange={(e) => setCurrentEntry(prev => ({ ...prev, collectorName: e.target.value }))}
                      placeholder="Your name"
                    />
                  </div>
                </div>


                {/* GPS Location */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>GPS Location</Label>
                    <Button type="button" variant="outline" size="sm" onClick={getCurrentLocation}>
                      <MapPin className="h-4 w-4 mr-1" />
                      Get Current Location
                    </Button>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <Label className="text-xs">Latitude</Label>
                      <Input
                        type="number"
                        step="0.000001"
                        value={currentEntry.latitude || ''}
                        onChange={(e) => setCurrentEntry(prev => ({ ...prev, latitude: parseFloat(e.target.value) || null }))}
                        placeholder="0.000000"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Longitude</Label>
                      <Input
                        type="number"
                        step="0.000001"
                        value={currentEntry.longitude || ''}
                        onChange={(e) => setCurrentEntry(prev => ({ ...prev, longitude: parseFloat(e.target.value) || null }))}
                        placeholder="0.000000"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Altitude (m)</Label>
                      <Input
                        type="number"
                        value={currentEntry.altitude || ''}
                        onChange={(e) => setCurrentEntry(prev => ({ ...prev, altitude: parseInt(e.target.value) || null }))}
                        placeholder="0"
                      />
                    </div>
                  </div>
                </div>

                {/* Sample Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="sampleType">Sample Type</Label>
                    <Select
                      value={currentEntry.sampleType}
                      onValueChange={(value) => setCurrentEntry(prev => ({ ...prev, sampleType: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="seed">Seed</SelectItem>
                        <SelectItem value="cutting">Cutting</SelectItem>
                        <SelectItem value="tissue">Tissue</SelectItem>
                        <SelectItem value="pollen">Pollen</SelectItem>
                        <SelectItem value="dna">DNA</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="seedCount">Seed/Sample Count</Label>
                    <Input
                      id="seedCount"
                      type="number"
                      value={currentEntry.seedCount || ''}
                      onChange={(e) => setCurrentEntry(prev => ({ ...prev, seedCount: parseInt(e.target.value) || null }))}
                      placeholder="Number of seeds"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="habitat">Habitat Description</Label>
                  <Textarea
                    id="habitat"
                    value={currentEntry.habitat}
                    onChange={(e) => setCurrentEntry(prev => ({ ...prev, habitat: e.target.value }))}
                    placeholder="Describe the collection site..."
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Additional Notes</Label>
                  <Textarea
                    id="notes"
                    value={currentEntry.notes}
                    onChange={(e) => setCurrentEntry(prev => ({ ...prev, notes: e.target.value }))}
                    placeholder="Any other observations..."
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
                <Button onClick={handleSaveEntry} disabled={!currentEntry.genus || !currentEntry.species}>
                  <Save className="h-4 w-4 mr-2" />
                  Save Locally
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>


      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{entries.length}</p>
            <p className="text-sm text-muted-foreground">Total Entries</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-gray-600">{draftCount}</p>
            <p className="text-sm text-muted-foreground">Drafts</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{pendingCount}</p>
            <p className="text-sm text-muted-foreground">Pending Sync</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-green-600">{syncedCount}</p>
            <p className="text-sm text-muted-foreground">Synced</p>
          </CardContent>
        </Card>
      </div>

      {/* Sync Button */}
      {pendingCount > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="font-medium">{pendingCount} entries ready to sync</p>
              <p className="text-sm text-muted-foreground">
                {isOnline ? 'Click sync to upload to server' : 'Connect to internet to sync'}
              </p>
            </div>
            <Button onClick={syncEntries} disabled={!isOnline || syncing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Entries List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All ({entries.length})</TabsTrigger>
          <TabsTrigger value="draft">Drafts ({draftCount})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({pendingCount})</TabsTrigger>
          <TabsTrigger value="synced">Synced ({syncedCount})</TabsTrigger>
          {errorCount > 0 && <TabsTrigger value="error">Errors ({errorCount})</TabsTrigger>}
        </TabsList>

        {['all', 'draft', 'pending', 'synced', 'error'].map(tab => (
          <TabsContent key={tab} value={tab}>
            <Card>
              <CardHeader>
                <CardTitle>Collected Accessions</CardTitle>
                <CardDescription>
                  {tab === 'all' && 'All offline collected accessions'}
                  {tab === 'draft' && 'Entries saved locally, not yet marked for sync'}
                  {tab === 'pending' && 'Entries waiting to be synced'}
                  {tab === 'synced' && 'Successfully synced to server'}
                  {tab === 'error' && 'Entries that failed to sync'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {entries.filter(e => tab === 'all' || e.status === tab).length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Leaf className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No entries in this category</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {entries
                      .filter(e => tab === 'all' || e.status === tab)
                      .map(entry => (
                        <div key={entry.id} className="p-4 border rounded-lg">
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-mono text-sm">{entry.accessionNumber}</span>
                                {getStatusBadge(entry.status)}
                              </div>
                              <p className="font-medium italic">
                                {entry.genus} {entry.species}
                                {entry.commonName && <span className="not-italic text-muted-foreground"> ({entry.commonName})</span>}
                              </p>
                              <div className="text-sm text-muted-foreground mt-1">
                                <span>Collected: {entry.collectionDate}</span>
                                {entry.latitude && entry.longitude && (
                                  <span className="ml-3">
                                    <MapPin className="h-3 w-3 inline mr-1" />
                                    {entry.latitude.toFixed(4)}, {entry.longitude.toFixed(4)}
                                  </span>
                                )}
                              </div>
                              {entry.errorMessage && (
                                <p className="text-sm text-red-600 mt-1">{entry.errorMessage}</p>
                              )}
                            </div>
                            <div className="flex gap-2">
                              {entry.status === 'draft' && (
                                <Button size="sm" variant="outline" onClick={() => markForSync(entry.id)}>
                                  <Upload className="h-4 w-4 mr-1" />
                                  Mark for Sync
                                </Button>
                              )}
                              {entry.status !== 'synced' && (
                                <Button size="sm" variant="ghost" onClick={() => handleDeleteEntry(entry.id)}>
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

export default OfflineDataEntry;
