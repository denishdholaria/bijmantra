/**
 * Taxonomy Validator
 * 
 * Validate scientific names against GRIN-Global taxonomy database
 */

import React, { useState } from 'react';
import { CheckCircle, XCircle, Loader2, Search, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

interface ValidationResult {
  valid: boolean;
  accepted_name?: string;
  synonyms?: string[];
  error?: string;
}

export default function TaxonomyValidator() {
  const { toast } = useToast();
  
  const [genus, setGenus] = useState('');
  const [species, setSpecies] = useState('');
  const [subspecies, setSubspecies] = useState('');
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  
  // Common crops for quick testing
  const commonCrops = [
    { genus: 'Oryza', species: 'sativa', common: 'Rice' },
    { genus: 'Triticum', species: 'aestivum', common: 'Wheat' },
    { genus: 'Zea', species: 'mays', common: 'Maize' },
    { genus: 'Glycine', species: 'max', common: 'Soybean' },
    { genus: 'Solanum', species: 'tuberosum', common: 'Potato' },
    { genus: 'Gossypium', species: 'hirsutum', common: 'Cotton' },
  ];

  const handleValidate = async () => {
    if (!genus || !species) {
      toast({
        title: "Missing Information",
        description: "Please enter at least genus and species",
        variant: "destructive",
      });
      return;
    }

    setValidating(true);
    setResult(null);
    
    try {
      const params = new URLSearchParams();
      params.append('genus', genus);
      params.append('species', species);
      if (subspecies) params.append('subspecies', subspecies);
      params.append('use_demo', 'true');
      
      const response = await fetch(`/api/v2/grin/grin-global/validate-taxonomy?${params}`, {
        method: 'POST',
      });
      
      const data = await response.json();
      setResult(data);
      
      if (data.valid) {
        toast({
          title: "Valid Taxonomy",
          description: `Accepted name: ${data.accepted_name}`,
        });
      } else {
        toast({
          title: "Invalid Taxonomy",
          description: data.error || "Taxon not found in database",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Validation Failed",
        description: "Could not validate taxonomy",
        variant: "destructive",
      });
    } finally {
      setValidating(false);
    }
  };

  const loadCommonCrop = (crop: typeof commonCrops[0]) => {
    setGenus(crop.genus);
    setSpecies(crop.species);
    setSubspecies('');
    setResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Taxonomy Validator</h1>
        <p className="text-muted-foreground mt-2">
          Validate scientific names against GRIN-Global taxonomy database
        </p>
      </div>

      {/* Quick Select */}
      <Card>
        <CardHeader>
          <CardTitle>Common Crops</CardTitle>
          <CardDescription>
            Click to quickly test validation with common crops
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {commonCrops.map((crop) => (
              <Button
                key={`${crop.genus}-${crop.species}`}
                variant="outline"
                size="sm"
                onClick={() => loadCommonCrop(crop)}
              >
                <BookOpen className="mr-2 h-4 w-4" />
                {crop.common}
                <span className="ml-2 text-xs text-muted-foreground italic">
                  {crop.genus} {crop.species}
                </span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Validation Form */}
      <Card>
        <CardHeader>
          <CardTitle>Enter Scientific Name</CardTitle>
          <CardDescription>
            Enter the genus, species, and optionally subspecies to validate
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="genus">Genus *</Label>
                <Input
                  id="genus"
                  placeholder="e.g., Oryza"
                  value={genus}
                  onChange={(e) => setGenus(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="species">Species *</Label>
                <Input
                  id="species"
                  placeholder="e.g., sativa"
                  value={species}
                  onChange={(e) => setSpecies(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="subspecies">Subspecies (optional)</Label>
                <Input
                  id="subspecies"
                  placeholder="e.g., indica"
                  value={subspecies}
                  onChange={(e) => setSubspecies(e.target.value)}
                />
              </div>
            </div>
            
            <Button 
              onClick={handleValidate} 
              disabled={validating || !genus || !species}
              className="w-full md:w-auto"
            >
              {validating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Validate Taxonomy
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {result.valid ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  Valid Taxonomy
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  Invalid Taxonomy
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.valid ? (
              <>
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    This scientific name is valid and recognized in the GRIN-Global taxonomy database.
                  </AlertDescription>
                </Alert>
                
                {result.accepted_name && (
                  <div>
                    <Label>Accepted Name</Label>
                    <div className="mt-2 p-4 bg-muted rounded-lg">
                      <p className="text-lg font-semibold italic">{result.accepted_name}</p>
                    </div>
                  </div>
                )}
                
                {result.synonyms && result.synonyms.length > 0 && (
                  <div>
                    <Label>Known Synonyms</Label>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {result.synonyms.map((synonym, index) => (
                        <Badge key={index} variant="secondary">
                          {synonym}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <>
                <Alert variant="destructive">
                  <XCircle className="h-4 w-4" />
                  <AlertDescription>
                    {result.error || 'This scientific name was not found in the GRIN-Global taxonomy database.'}
                  </AlertDescription>
                </Alert>
                
                <div className="text-sm text-muted-foreground space-y-2">
                  <p>Possible reasons:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>The name may be misspelled</li>
                    <li>It may be an outdated synonym</li>
                    <li>The taxon may not be in the GRIN database</li>
                    <li>Check the spelling and try again</li>
                  </ul>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>About Taxonomy Validation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>
            The GRIN-Global taxonomy database contains standardized scientific names for plant species 
            used in germplasm conservation and breeding programs worldwide.
          </p>
          
          <div>
            <p className="font-semibold text-foreground mb-2">Why validate taxonomy?</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Ensures consistency across germplasm collections</li>
              <li>Prevents duplicate entries with different spellings</li>
              <li>Enables accurate data exchange with other genebanks</li>
              <li>Maintains compliance with international standards</li>
            </ul>
          </div>
          
          <div>
            <p className="font-semibold text-foreground mb-2">Naming conventions:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Genus: Capitalized (e.g., Oryza)</li>
              <li>Species: Lowercase (e.g., sativa)</li>
              <li>Subspecies: Lowercase, optional (e.g., indica)</li>
              <li>Full name: <span className="italic">Oryza sativa</span> subsp. <span className="italic">indica</span></li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
