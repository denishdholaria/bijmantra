import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Database, Plus, Search, Filter, Upload, MoreVertical,
  Image, CheckCircle2, Clock, Trash2, Edit, Eye,
  FolderOpen, ArrowLeft
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface Dataset {
  id: string;
  name: string;
  description: string;
  dataset_type: string;
  crop: string;
  classes: string[];
  status: string;
  image_count: number;
  annotated_count: number;
  quality_score: number;
  created_at: string;
  updated_at: string;
}

const CROPS = [
  { value: 'rice', label: 'Rice', icon: '🌾' },
  { value: 'wheat', label: 'Wheat', icon: '🌾' },
  { value: 'maize', label: 'Maize', icon: '🌽' },
  { value: 'soybean', label: 'Soybean', icon: '🫘' },
  { value: 'cotton', label: 'Cotton', icon: '☁️' },
  { value: 'tomato', label: 'Tomato', icon: '🍅' },
  { value: 'potato', label: 'Potato', icon: '🥔' },
];

export function VisionDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [cropFilter, setCropFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  
  // Create form state
  const [newDataset, setNewDataset] = useState({
    name: '',
    description: '',
    crop: 'rice',
    dataset_type: 'classification',
    classes: '',
  });

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const res = await fetch('/api/v2/vision/datasets');
      if (res.ok) {
        const data = await res.json();
        setDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error('Failed to fetch datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDataset = async () => {
    try {
      const classes = newDataset.classes.split(',').map(c => c.trim()).filter(Boolean);
      if (classes.length < 2) {
        alert('Please enter at least 2 classes');
        return;
      }

      const res = await fetch('/api/v2/vision/datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newDataset.name,
          description: newDataset.description,
          crop: newDataset.crop,
          dataset_type: newDataset.dataset_type,
          classes,
        }),
      });

      if (res.ok) {
        setShowCreateDialog(false);
        setNewDataset({ name: '', description: '', crop: 'rice', dataset_type: 'classification', classes: '' });
        fetchDatasets();
      }
    } catch (error) {
      console.error('Failed to create dataset:', error);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    if (!confirm('Are you sure you want to delete this dataset?')) return;
    
    try {
      const res = await fetch(`/api/v2/vision/datasets/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchDatasets();
      }
    } catch (error) {
      console.error('Failed to delete dataset:', error);
    }
  };

  const handleUploadImages = async () => {
    if (!selectedDataset) return;
    
    // Simulate upload with demo images
    try {
      const demoImages = Array.from({ length: 5 }, (_, i) => ({
        filename: `image_${Date.now()}_${i}.jpg`,
        width: 640,
        height: 480,
        annotation: { label: selectedDataset.classes[i % selectedDataset.classes.length] },
        split: i < 3 ? 'train' : i < 4 ? 'val' : 'test',
      }));

      const res = await fetch(`/api/v2/vision/datasets/${selectedDataset.id}/images`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: demoImages }),
      });

      if (res.ok) {
        setShowUploadDialog(false);
        setSelectedDataset(null);
        fetchDatasets();
      }
    } catch (error) {
      console.error('Failed to upload images:', error);
    }
  };

  const filteredDatasets = datasets.filter(d => {
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (cropFilter !== 'all' && d.crop !== cropFilter) return false;
    if (statusFilter !== 'all' && d.status !== statusFilter) return false;
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle2 className="h-3 w-3 mr-1" />Ready</Badge>;
      case 'draft':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Draft</Badge>;
      case 'training':
        return <Badge className="bg-blue-100 text-blue-800">Training</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" aria-label="Back to AI Vision" asChild>
            <Link to="/ai-vision"><ArrowLeft className="h-4 w-4" /></Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Database className="h-6 w-6" />
              Vision Datasets
            </h1>
            <p className="text-muted-foreground">
              Manage your plant image datasets for AI training
            </p>
          </div>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Dataset
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={cropFilter} onValueChange={setCropFilter}>
          <SelectTrigger className="w-[150px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Crop" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Crops</SelectItem>
            {CROPS.map(crop => (
              <SelectItem key={crop.value} value={crop.value}>
                {crop.icon} {crop.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="ready">Ready</SelectItem>
            <SelectItem value="training">Training</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Dataset Grid */}
      {loading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading datasets...</p>
        </div>
      ) : filteredDatasets.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No datasets found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery || cropFilter !== 'all' || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first dataset to get started'}
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Dataset
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDatasets.map((dataset) => (
            <Card key={dataset.id} className="hover:border-primary/50 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{dataset.name}</CardTitle>
                    <CardDescription className="line-clamp-2">{dataset.description}</CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Dataset options">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => { setSelectedDataset(dataset); setShowUploadDialog(true); }}>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Images
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-destructive"
                        onClick={() => handleDeleteDataset(dataset.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{CROPS.find(c => c.value === dataset.crop)?.icon} {dataset.crop}</Badge>
                  {getStatusBadge(dataset.status)}
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Images</span>
                    <span>{dataset.annotated_count} / {dataset.image_count}</span>
                  </div>
                  <Progress value={(dataset.annotated_count / Math.max(dataset.image_count, 1)) * 100} className="h-2" />
                </div>

                <div className="flex flex-wrap gap-1">
                  {dataset.classes.slice(0, 4).map((cls, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{cls}</Badge>
                  ))}
                  {dataset.classes.length > 4 && (
                    <Badge variant="secondary" className="text-xs">+{dataset.classes.length - 4}</Badge>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-xs text-muted-foreground">
                    Quality: {dataset.quality_score}%
                  </span>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => { setSelectedDataset(dataset); setShowUploadDialog(true); }}
                  >
                    <Upload className="h-3 w-3 mr-1" />
                    Upload
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dataset Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Dataset</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Dataset Name</Label>
              <Input
                placeholder="e.g., Rice Blast Detection v1"
                value={newDataset.name}
                onChange={(e) => setNewDataset({ ...newDataset, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Describe the purpose of this dataset..."
                value={newDataset.description}
                onChange={(e) => setNewDataset({ ...newDataset, description: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Crop</Label>
                <Select value={newDataset.crop} onValueChange={(v) => setNewDataset({ ...newDataset, crop: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CROPS.map(crop => (
                      <SelectItem key={crop.value} value={crop.value}>
                        {crop.icon} {crop.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={newDataset.dataset_type} onValueChange={(v) => setNewDataset({ ...newDataset, dataset_type: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="classification">Classification</SelectItem>
                    <SelectItem value="object_detection">Object Detection</SelectItem>
                    <SelectItem value="segmentation">Segmentation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Classes (comma-separated)</Label>
              <Input
                placeholder="e.g., healthy, mild, moderate, severe"
                value={newDataset.classes}
                onChange={(e) => setNewDataset({ ...newDataset, classes: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">Enter at least 2 class labels</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateDataset} disabled={!newDataset.name || !newDataset.classes}>
              Create Dataset
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Images Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload Images to {selectedDataset?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <Image className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground mb-2">
                Drag and drop images here, or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supports JPG, PNG, WebP (max 10MB each)
              </p>
              <Button variant="outline" className="mt-4">
                <Upload className="h-4 w-4 mr-2" />
                Browse Files
              </Button>
            </div>
            <div className="text-sm text-muted-foreground">
              <p>Classes: {selectedDataset?.classes.join(', ')}</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadDialog(false)}>Cancel</Button>
            <Button onClick={handleUploadImages}>
              Upload Demo Images
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
