/**
 * GRIN-Global / Genesys Search
 * 
 * Search and import germplasm from global databases:
 * - GRIN-Global (USDA)
 * - Genesys (Global portal)
 */

import React, { useState } from 'react';
import { Search, Download, Database, Globe, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/store/auth';

interface GRINAccession {
  accession_number: string;
  genus: string;
  species: string;
  subspecies?: string;
  variety?: string;
  common_name?: string;
  origin_country?: string;
  collection_date?: string;
  biological_status?: string;
  storage_type?: string;
  notes?: string;
}

interface GenesysAccession {
  accession_id: string;
  institute_code: string;
  accession_number: string;
  genus: string;
  species: string;
  country_of_origin?: string;
  available: boolean;
  mlsStatus?: string;
}

export default function GRINSearch() {
  const { toast } = useToast();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('grin');
  
  // Search state
  const [genus, setGenus] = useState('');
  const [species, setSpecies] = useState('');
  const [country, setCountry] = useState('');
  const [searching, setSearching] = useState(false);
  
  // Results
  const [grinResults, setGrinResults] = useState<GRINAccession[]>([]);
  const [genesysResults, setGenesysResults] = useState<GenesysAccession[]>([]);
  
  // Selection
  const [selectedGrin, setSelectedGrin] = useState<Set<string>>(new Set());
  const [selectedGenesys, setSelectedGenesys] = useState<Set<string>>(new Set());
  
  // Import dialog
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [importing, setImporting] = useState(false);

  const searchGRIN = async () => {
    setSearching(true);
    try {
      const params = new URLSearchParams();
      if (genus) params.append('genus', genus);
      if (species) params.append('species', species);
      if (country) params.append('country', country);
      params.append('use_demo', 'true');
      
      const response = await fetch(`/api/v2/grin/grin-global/search?${params}`);
      const data = await response.json();
      setGrinResults(data);
      
      toast({
        title: "Search Complete",
        description: `Found ${data.length} accessions in GRIN-Global`,
      });
    } catch (error) {
      toast({
        title: "Search Failed",
        description: "Could not search GRIN-Global",
        variant: "destructive",
      });
    } finally {
      setSearching(false);
    }
  };

  const searchGenesys = async () => {
    setSearching(true);
    try {
      const params = new URLSearchParams();
      if (genus) params.append('genus', genus);
      if (species) params.append('species', species);
      if (country) params.append('country', country);
      params.append('use_demo', 'true');
      
      const response = await fetch(`/api/v2/grin/genesys/search?${params}`);
      const data = await response.json();
      setGenesysResults(data);
      
      toast({
        title: "Search Complete",
        description: `Found ${data.length} accessions in Genesys`,
      });
    } catch (error) {
      toast({
        title: "Search Failed",
        description: "Could not search Genesys",
        variant: "destructive",
      });
    } finally {
      setSearching(false);
    }
  };

  const handleSearch = () => {
    if (activeTab === 'grin') {
      searchGRIN();
    } else {
      searchGenesys();
    }
  };

  const toggleGrinSelection = (accessionNumber: string) => {
    const newSelection = new Set(selectedGrin);
    if (newSelection.has(accessionNumber)) {
      newSelection.delete(accessionNumber);
    } else {
      newSelection.add(accessionNumber);
    }
    setSelectedGrin(newSelection);
  };

  const toggleGenesysSelection = (accessionId: string) => {
    const newSelection = new Set(selectedGenesys);
    if (newSelection.has(accessionId)) {
      newSelection.delete(accessionId);
    } else {
      newSelection.add(accessionId);
    }
    setSelectedGenesys(newSelection);
  };

  const handleImport = async () => {
    setImporting(true);

    if (!user?.organization_id) {
      toast({
        title: "Authentication Error",
        description: "User organization not found. Please log in again.",
        variant: "destructive",
      });
      setImporting(false);
      return;
    }

    try {
      if (activeTab === 'grin') {
        const response = await fetch('/api/v2/grin/import/grin-global', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            accession_numbers: Array.from(selectedGrin),
            organization_id: user.organization_id,
          }),
        });
        
        const result = await response.json();
        
        toast({
          title: "Import Complete",
          description: `Imported ${result.imported_count} accessions from GRIN-Global`,
        });
      } else {
        const accessions = Array.from(selectedGenesys).map(id => {
          const acc = genesysResults.find(a => a.accession_id === id);
          return {
            institute_code: acc?.institute_code,
            accession_number: acc?.accession_number,
          };
        });
        
        const response = await fetch('/api/v2/grin/import/genesys', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            accessions,
            organization_id: user.organization_id,
          }),
        });
        
        const result = await response.json();
        
        toast({
          title: "Import Complete",
          description: `Imported ${result.imported_count} accessions from Genesys`,
        });
      }
      
      setImportDialogOpen(false);
      setSelectedGrin(new Set());
      setSelectedGenesys(new Set());
    } catch (error) {
      toast({
        title: "Import Failed",
        description: "Could not import accessions",
        variant: "destructive",
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">GRIN-Global / Genesys Search</h1>
        <p className="text-muted-foreground mt-2">
          Search and import germplasm from global databases
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle>Search Parameters</CardTitle>
          <CardDescription>
            Search by genus, species, or country of origin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="genus">Genus</Label>
              <Input
                id="genus"
                placeholder="e.g., Oryza"
                value={genus}
                onChange={(e) => setGenus(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="species">Species</Label>
              <Input
                id="species"
                placeholder="e.g., sativa"
                value={species}
                onChange={(e) => setSpecies(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                placeholder="e.g., IND"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              />
            </div>
            
            <div className="flex items-end">
              <Button 
                onClick={handleSearch} 
                disabled={searching}
                className="w-full"
              >
                {searching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="grin">
              <Database className="mr-2 h-4 w-4" />
              GRIN-Global ({grinResults.length})
            </TabsTrigger>
            <TabsTrigger value="genesys">
              <Globe className="mr-2 h-4 w-4" />
              Genesys ({genesysResults.length})
            </TabsTrigger>
          </TabsList>
          
          {((activeTab === 'grin' && selectedGrin.size > 0) || 
            (activeTab === 'genesys' && selectedGenesys.size > 0)) && (
            <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Download className="mr-2 h-4 w-4" />
                  Import Selected ({activeTab === 'grin' ? selectedGrin.size : selectedGenesys.size})
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Import Accessions</DialogTitle>
                  <DialogDescription>
                    Import {activeTab === 'grin' ? selectedGrin.size : selectedGenesys.size} accessions 
                    from {activeTab === 'grin' ? 'GRIN-Global' : 'Genesys'} into your Seed Bank?
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    This will create new accession records in your Seed Bank with passport data 
                    from the selected accessions.
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setImportDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleImport} disabled={importing}>
                      {importing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Importing...
                        </>
                      ) : (
                        <>
                          <Download className="mr-2 h-4 w-4" />
                          Import
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <TabsContent value="grin" className="space-y-4">
          {grinResults.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Database className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No results yet. Try searching above.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {grinResults.map((acc) => (
                <Card key={acc.accession_number} className="hover:border-primary transition-colors">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <Checkbox
                        checked={selectedGrin.has(acc.accession_number)}
                        onCheckedChange={() => toggleGrinSelection(acc.accession_number)}
                      />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold text-lg">{acc.accession_number}</h3>
                            <p className="text-sm text-muted-foreground italic">
                              {acc.genus} {acc.species} {acc.subspecies}
                            </p>
                          </div>
                          {acc.common_name && (
                            <Badge variant="secondary">{acc.common_name}</Badge>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          {acc.origin_country && (
                            <div>
                              <span className="text-muted-foreground">Origin:</span>
                              <span className="ml-2 font-medium">{acc.origin_country}</span>
                            </div>
                          )}
                          {acc.biological_status && (
                            <div>
                              <span className="text-muted-foreground">Status:</span>
                              <span className="ml-2 font-medium">{acc.biological_status}</span>
                            </div>
                          )}
                          {acc.storage_type && (
                            <div>
                              <span className="text-muted-foreground">Storage:</span>
                              <span className="ml-2 font-medium">{acc.storage_type}</span>
                            </div>
                          )}
                          {acc.collection_date && (
                            <div>
                              <span className="text-muted-foreground">Collected:</span>
                              <span className="ml-2 font-medium">{acc.collection_date}</span>
                            </div>
                          )}
                        </div>
                        
                        {acc.notes && (
                          <p className="text-sm text-muted-foreground">{acc.notes}</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="genesys" className="space-y-4">
          {genesysResults.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Globe className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No results yet. Try searching above.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {genesysResults.map((acc) => (
                <Card key={acc.accession_id} className="hover:border-primary transition-colors">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <Checkbox
                        checked={selectedGenesys.has(acc.accession_id)}
                        onCheckedChange={() => toggleGenesysSelection(acc.accession_id)}
                      />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-semibold text-lg">
                              {acc.institute_code} / {acc.accession_number}
                            </h3>
                            <p className="text-sm text-muted-foreground italic">
                              {acc.genus} {acc.species}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {acc.available && (
                              <Badge variant="default">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Available
                              </Badge>
                            )}
                            {acc.mlsStatus === 'INCLUDED' && (
                              <Badge variant="secondary">MLS</Badge>
                            )}
                          </div>
                        </div>
                        
                        {acc.country_of_origin && (
                          <div className="text-sm">
                            <span className="text-muted-foreground">Origin:</span>
                            <span className="ml-2 font-medium">{acc.country_of_origin}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
