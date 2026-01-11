import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Globe, Search, Download, Heart, Star, Filter,
  ArrowLeft, TrendingUp, Users, Clock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface RegistryModel {
  id: string;
  model_id: string;
  name: string;
  description: string;
  author: string;
  crop: string;
  task: string;
  classes: string[];
  accuracy: number;
  size_mb: number;
  downloads: number;
  likes: number;
  tags: string[];
  published_at: string;
  version: string;
  license: string;
}

const CROPS = [
  { value: 'all', label: 'All Crops' },
  { value: 'rice', label: '🌾 Rice' },
  { value: 'wheat', label: '🌾 Wheat' },
  { value: 'maize', label: '🌽 Maize' },
  { value: 'multi', label: '🌱 Multi-crop' },
];

export function VisionRegistry() {
  const [models, setModels] = useState<RegistryModel[]>([]);
  const [featured, setFeatured] = useState<RegistryModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [cropFilter, setCropFilter] = useState('all');
  const [sortBy, setSortBy] = useState('downloads');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    searchModels();
  }, [searchQuery, cropFilter, sortBy]);

  const fetchData = async () => {
    try {
      const [registryRes, featuredRes] = await Promise.all([
        fetch('/api/v2/vision/registry'),
        fetch('/api/v2/vision/registry/featured?limit=3'),
      ]);
      
      if (registryRes.ok) {
        const data = await registryRes.json();
        setModels(data.models || []);
      }
      if (featuredRes.ok) {
        const data = await featuredRes.json();
        setFeatured(data.models || []);
      }
    } catch (error) {
      console.error('Failed to fetch registry:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchModels = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (cropFilter !== 'all') params.append('crop', cropFilter);
      params.append('sort_by', sortBy);

      const res = await fetch(`/api/v2/vision/registry?${params}`);
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch (error) {
      console.error('Failed to search:', error);
    }
  };

  const handleDownload = async (registryId: string) => {
    try {
      const res = await fetch(`/api/v2/vision/registry/${registryId}/download`, { method: 'POST' });
      if (res.ok) {
        fetchData();
        alert('Download started! Check your downloads folder.');
      }
    } catch (error) {
      console.error('Failed to download:', error);
    }
  };

  const handleLike = async (registryId: string) => {
    try {
      await fetch(`/api/v2/vision/registry/${registryId}/like`, { method: 'POST' });
      fetchData();
    } catch (error) {
      console.error('Failed to like:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to AI Vision">
            <Link to="/ai-vision"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Globe className="h-6 w-6" />
              Model Registry
            </h1>
            <p className="text-muted-foreground">
              Discover and download community-shared plant vision models
            </p>
          </div>
        </div>
      </div>

      {/* Featured Models */}
      {featured.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            Featured Models
          </h2>
          <div className="grid md:grid-cols-3 gap-4">
            {featured.map((model) => (
              <Card key={model.id} className="border-yellow-200 dark:border-yellow-800">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{model.name}</CardTitle>
                      <CardDescription className="line-clamp-2">{model.description}</CardDescription>
                    </div>
                    <Badge variant="secondary">{model.crop}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4" />
                      {(model.accuracy * 100).toFixed(1)}%
                    </span>
                    <span className="flex items-center gap-1">
                      <Download className="h-4 w-4" />
                      {model.downloads}
                    </span>
                    <span className="flex items-center gap-1">
                      <Heart className="h-4 w-4" />
                      {model.likes}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1" onClick={() => handleDownload(model.id)}>
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleLike(model.id)} aria-label="Like model">
                      <Heart className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={cropFilter} onValueChange={setCropFilter}>
          <SelectTrigger className="w-[150px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CROPS.map(crop => (
              <SelectItem key={crop.value} value={crop.value}>{crop.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="downloads">Most Downloads</SelectItem>
            <SelectItem value="accuracy">Highest Accuracy</SelectItem>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="likes">Most Liked</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Models Grid */}
      {loading ? (
        <p className="text-muted-foreground">Loading models...</p>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No models found</h3>
            <p className="text-muted-foreground">Try adjusting your search or filters</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => (
            <Card key={model.id} className="hover:border-primary/50 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">by {model.author}</p>
                  </div>
                  <Badge variant="outline">{model.crop}</Badge>
                </div>
                <CardDescription className="line-clamp-2">{model.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1 text-green-600">
                    <TrendingUp className="h-4 w-4" />
                    {(model.accuracy * 100).toFixed(1)}%
                  </span>
                  <span className="text-muted-foreground">{model.size_mb} MB</span>
                  <span className="text-muted-foreground">v{model.version}</span>
                </div>

                <div className="flex flex-wrap gap-1">
                  {model.tags.slice(0, 4).map((tag, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{tag}</Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Download className="h-4 w-4" />
                    {model.downloads}
                  </span>
                  <span className="flex items-center gap-1">
                    <Heart className="h-4 w-4" />
                    {model.likes}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(model.published_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex gap-2 pt-2 border-t">
                  <Button size="sm" className="flex-1" onClick={() => handleDownload(model.id)}>
                    <Download className="h-4 w-4 mr-1" />
                    Download
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleLike(model.id)} aria-label="Like model">
                    <Heart className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Stats */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-around text-center">
            <div>
              <p className="text-2xl font-bold">{models.length}</p>
              <p className="text-sm text-muted-foreground">Models Available</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{models.reduce((sum, m) => sum + m.downloads, 0)}</p>
              <p className="text-sm text-muted-foreground">Total Downloads</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{new Set(models.map(m => m.author)).size}</p>
              <p className="text-sm text-muted-foreground">Contributors</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
