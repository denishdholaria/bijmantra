/**
 * DUS Crop Templates Page
 * 
 * Browse UPOV crop templates with DUS characters.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Search, Leaf, Star, Users } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DUSCharacter {
  id: string;
  name: string;
  type: string;
  states: Array<{ code: number; description: string }>;
  is_grouping: boolean;
  is_asterisk: boolean;
}

interface CropTemplate {
  code: string;
  name: string;
  scientific_name: string;
  upov_code: string;
  character_count: number;
  characters?: DUSCharacter[];
}

const TYPE_LABELS: Record<string, string> = {
  VG: 'Visual (Grouping)',
  MG: 'Measurement (Grouping)',
  VS: 'Visual (Single)',
  MS: 'Measurement (Single)',
  PQ: 'Pseudo-qualitative',
  QN: 'Quantitative',
  QL: 'Qualitative',
};

export default function DUSCrops() {
  const [search, setSearch] = useState('');
  const [selectedCrop, setSelectedCrop] = useState<string | null>(null);

  // Fetch crop templates
  const { data: cropsData, isLoading } = useQuery({
    queryKey: ['dus-crops'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v2/dus/crops`);
      if (!res.ok) throw new Error('Failed to fetch crops');
      return res.json();
    },
  });

  // Fetch selected crop characters
  const { data: cropDetail } = useQuery({
    queryKey: ['dus-crop', selectedCrop],
    queryFn: async () => {
      if (!selectedCrop) return null;
      const res = await fetch(`${API_BASE}/api/v2/dus/crops/${selectedCrop}`);
      if (!res.ok) throw new Error('Failed to fetch crop');
      return res.json();
    },
    enabled: !!selectedCrop,
  });

  const crops: CropTemplate[] = cropsData?.crops || [];
  const filteredCrops = crops.filter(
    (c) =>
      (c.name?.toLowerCase() || '').includes(search.toLowerCase()) ||
      (c.scientific_name?.toLowerCase() || '').includes(search.toLowerCase())
  );

  const characters: DUSCharacter[] = cropDetail?.characters || [];
  const groupingChars = characters.filter((c) => c.is_grouping);
  const asteriskChars = characters.filter((c) => c.is_asterisk);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/commercial/dus">
            <Button variant="ghost" size="icon" aria-label="Back to DUS trials">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Leaf className="h-6 w-6" />
              DUS Crop Templates
            </h1>
            <p className="text-muted-foreground">
              UPOV character definitions for variety testing
            </p>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Crop List */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search crops..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Available Crops ({crops.length})</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-4 text-center text-muted-foreground">Loading...</div>
              ) : (
                <div className="divide-y max-h-[500px] overflow-y-auto">
                  {filteredCrops.map((crop) => (
                    <button
                      key={crop.code}
                      onClick={() => setSelectedCrop(crop.code)}
                      className={`w-full p-3 text-left hover:bg-muted transition-colors ${
                        selectedCrop === crop.code ? 'bg-muted' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{crop.name}</p>
                          <p className="text-xs text-muted-foreground italic">
                            {crop.scientific_name}
                          </p>
                        </div>
                        <Badge variant="secondary">{crop.character_count}</Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Character Details */}
        <div className="md:col-span-2 space-y-4">
          {selectedCrop && cropDetail ? (
            <>
              {/* Crop Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{cropDetail.name}</span>
                    <Badge>{cropDetail.upov_code}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-2xl font-bold">{characters.length}</p>
                      <p className="text-xs text-muted-foreground">Total Characters</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-700">{groupingChars.length}</p>
                      <p className="text-xs text-blue-600">Grouping</p>
                    </div>
                    <div className="p-3 bg-amber-50 rounded-lg">
                      <p className="text-2xl font-bold text-amber-700">{asteriskChars.length}</p>
                      <p className="text-xs text-amber-600">Asterisk (*)</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Characters */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">DUS Characters</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <Accordion type="multiple" className="w-full">
                    {characters.map((char, idx) => (
                      <AccordionItem key={char.id} value={char.id}>
                        <AccordionTrigger className="px-4 hover:no-underline">
                          <div className="flex items-center gap-3 text-left">
                            <span className="text-muted-foreground text-sm w-6">
                              {idx + 1}.
                            </span>
                            <span className="flex-1">{char.name}</span>
                            <div className="flex gap-1">
                              {char.is_asterisk && (
                                <Badge variant="outline" className="text-amber-600 border-amber-300">
                                  <Star className="h-3 w-3 mr-1" />*
                                </Badge>
                              )}
                              {char.is_grouping && (
                                <Badge variant="outline" className="text-blue-600 border-blue-300">
                                  <Users className="h-3 w-3 mr-1" />G
                                </Badge>
                              )}
                              <Badge variant="secondary" className="text-xs">
                                {TYPE_LABELS[char.type] || char.type}
                              </Badge>
                            </div>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="px-4 pb-4">
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead className="w-20">Code</TableHead>
                                <TableHead>Description</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {char.states.map((state) => (
                                <TableRow key={state.code}>
                                  <TableCell className="font-mono">{state.code}</TableCell>
                                  <TableCell>{state.description}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="p-12 text-center text-muted-foreground">
                <Leaf className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a crop to view its DUS characters</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
