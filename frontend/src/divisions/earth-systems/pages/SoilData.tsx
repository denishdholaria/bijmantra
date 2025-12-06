/**
 * Soil Data Page
 *
 * Soil analysis, nutrient management, and fertilizer recommendations.
 * Connected to backend: /api/v2/field-environment
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SoilProfile {
  id: string;
  field_id: string;
  sample_date: string;
  depth_cm: number;
  texture: string;
  ph: number;
  organic_matter: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  calcium: number | null;
  magnesium: number | null;
  notes: string;
}

interface Recommendation {
  nutrient: string;
  current: number;
  target: number;
  product: string;
  quantity: number;
  unit: string;
  timing: string;
}

export function SoilData() {
  const [profiles, setProfiles] = useState<SoilProfile[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [textures, setTextures] = useState<{value: string; name: string}[]>([]);
  const { toast } = useToast();

  const [formData, setFormData] = useState({
    field_id: 'field-001',
    depth_cm: 30,
    texture: 'loam',
    ph: 7.0,
    organic_matter: 2.0,
    nitrogen: 40,
    phosphorus: 30,
    potassium: 150,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [profilesRes, texturesRes] = await Promise.all([
        fetch(`${API_BASE}/api/v2/field-environment/soil-profiles`),
        fetch(`${API_BASE}/api/v2/field-environment/soil-textures`),
      ]);
      if (profilesRes.ok) {
        const data = await profilesRes.json();
        setProfiles(data);
        if (data.length > 0 && !selectedProfile) {
          setSelectedProfile(data[0].id);
          fetchRecommendations(data[0].id);
        }
      }
      if (texturesRes.ok) {
        const data = await texturesRes.json();
        setTextures(data.soil_textures || []);
      }
    } catch (error) {
      console.error('Failed to fetch soil data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async (profileId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/field-environment/soil-profiles/${profileId}/recommendations`);
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const handleProfileSelect = (profileId: string) => {
    setSelectedProfile(profileId);
    fetchRecommendations(profileId);
  };

  const handleAddProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/field-environment/soil-profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        toast({ title: 'Success', description: 'Soil profile added' });
        setDialogOpen(false);
        fetchData();
      } else {
        toast({ title: 'Error', description: 'Failed to add profile', variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Error', description: 'Failed to connect', variant: 'destructive' });
    }
  };

  const getNutrientStatus = (value: number, type: string) => {
    const thresholds: Record<string, [number, number]> = {
      nitrogen: [40, 60], phosphorus: [25, 40], potassium: [150, 200],
    };
    const [low, high] = thresholds[type] || [0, 100];
    if (value < low) return 'bg-red-100 text-red-700';
    if (value > high) return 'bg-blue-100 text-blue-700';
    return 'bg-green-100 text-green-700';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Soil Data</h1>
          <p className="text-gray-600 mt-1">Soil analysis and nutrient management</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>+ Add Sample</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Add Soil Sample</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Field ID</Label><Input value={formData.field_id} onChange={(e) => setFormData({...formData, field_id: e.target.value})} /></div>
                <div><Label>Depth (cm)</Label><Input type="number" value={formData.depth_cm} onChange={(e) => setFormData({...formData, depth_cm: parseInt(e.target.value)})} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Texture</Label>
                  <Select value={formData.texture} onValueChange={(v) => setFormData({...formData, texture: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{textures.map((t) => (<SelectItem key={t.value} value={t.value}>{t.name}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div><Label>pH</Label><Input type="number" step="0.1" value={formData.ph} onChange={(e) => setFormData({...formData, ph: parseFloat(e.target.value)})} /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><Label>N (kg/ha)</Label><Input type="number" value={formData.nitrogen} onChange={(e) => setFormData({...formData, nitrogen: parseInt(e.target.value)})} /></div>
                <div><Label>P (kg/ha)</Label><Input type="number" value={formData.phosphorus} onChange={(e) => setFormData({...formData, phosphorus: parseInt(e.target.value)})} /></div>
                <div><Label>K (kg/ha)</Label><Input type="number" value={formData.potassium} onChange={(e) => setFormData({...formData, potassium: parseInt(e.target.value)})} /></div>
              </div>
              <Button onClick={handleAddProfile} className="w-full">Add Sample</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="profiles">
        <TabsList><TabsTrigger value="profiles">Soil Profiles</TabsTrigger><TabsTrigger value="recommendations">Recommendations</TabsTrigger></TabsList>
        <TabsContent value="profiles" className="mt-4">
          <Card>
            <CardHeader><CardTitle>📊 Soil Analyses</CardTitle></CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              {loading ? <p className="p-4 text-gray-500">Loading...</p> : profiles.length === 0 ? <p className="p-4 text-gray-500">No profiles yet</p> : (
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Field</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">pH</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">N</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">P</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">K</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {profiles.map((p) => (
                      <tr key={p.id} className={`hover:bg-gray-50 ${selectedProfile === p.id ? 'bg-green-50' : ''}`}>
                        <td className="px-4 py-3 font-medium">{p.field_id}</td>
                        <td className="px-4 py-3 text-gray-600">{p.sample_date}</td>
                        <td className="px-4 py-3 text-center">{p.ph}</td>
                        <td className="px-4 py-3 text-center"><span className={`px-2 py-1 rounded text-sm ${getNutrientStatus(p.nitrogen, 'nitrogen')}`}>{p.nitrogen}</span></td>
                        <td className="px-4 py-3 text-center"><span className={`px-2 py-1 rounded text-sm ${getNutrientStatus(p.phosphorus, 'phosphorus')}`}>{p.phosphorus}</span></td>
                        <td className="px-4 py-3 text-center"><span className={`px-2 py-1 rounded text-sm ${getNutrientStatus(p.potassium, 'potassium')}`}>{p.potassium}</span></td>
                        <td className="px-4 py-3"><Button variant="ghost" size="sm" onClick={() => handleProfileSelect(p.id)}>View</Button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="recommendations" className="mt-4">
          <Card>
            <CardHeader><CardTitle>🌱 Fertilizer Recommendations</CardTitle></CardHeader>
            <CardContent>
              {recommendations.length === 0 ? <p className="text-gray-500">Select a profile or all nutrients optimal</p> : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recommendations.map((r, i) => (
                    <div key={i} className="p-4 border rounded-lg">
                      <div className="font-medium text-lg">{r.nutrient}</div>
                      <div className="flex items-center gap-2 my-2">
                        <span className="text-2xl font-bold">{r.current}</span>
                        <span className="text-gray-400">→</span>
                        <span className="text-green-600 font-medium">{r.target}</span>
                      </div>
                      <p className="text-sm"><span className="font-medium">Product:</span> {r.product}</p>
                      <p className="text-sm"><span className="font-medium">Apply:</span> {r.quantity} {r.unit}</p>
                      <p className="text-sm text-gray-600">{r.timing}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default SoilData;
