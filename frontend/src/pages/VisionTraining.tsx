import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Brain, Play, Pause, Clock, CheckCircle2, XCircle, 
  ArrowLeft, Plus, Settings, TrendingUp, BarChart3,
  Loader2, AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface TrainingJob {
  id: string;
  name: string;
  dataset_id: string;
  base_model: string;
  backend: string;
  status: string;
  hyperparameters: Record<string, unknown>;
  metrics: Record<string, number>;
  progress: number;
  current_epoch: number;
  total_epochs: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  model_id: string | null;
}

interface Dataset {
  id: string;
  name: string;
  image_count: number;
}

const BASE_MODELS = [
  { id: 'mobilenetv2', name: 'MobileNetV2', size: '14 MB', recommended: 'Mobile/Edge' },
  { id: 'efficientnetb0', name: 'EfficientNetB0', size: '29 MB', recommended: 'Balanced' },
  { id: 'resnet50', name: 'ResNet50', size: '98 MB', recommended: 'Accuracy' },
];

export function VisionTraining() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedJob, setSelectedJob] = useState<TrainingJob | null>(null);
  
  const [newJob, setNewJob] = useState({
    name: '',
    dataset_id: '',
    base_model: 'mobilenetv2',
    backend: 'server',
    learning_rate: '0.001',
    batch_size: '32',
    epochs: '50',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [jobsRes, datasetsRes] = await Promise.all([
        fetch('/api/v2/vision/training/jobs'),
        fetch('/api/v2/vision/datasets'),
      ]);
      
      if (jobsRes.ok) {
        const data = await jobsRes.json();
        setJobs(data.jobs || []);
      }
      if (datasetsRes.ok) {
        const data = await datasetsRes.json();
        setDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async () => {
    try {
      const res = await fetch('/api/v2/vision/training/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newJob.name,
          dataset_id: newJob.dataset_id,
          base_model: newJob.base_model,
          backend: newJob.backend,
          hyperparameters: {
            learning_rate: parseFloat(newJob.learning_rate),
            batch_size: parseInt(newJob.batch_size),
            epochs: parseInt(newJob.epochs),
          },
        }),
      });

      if (res.ok) {
        setShowCreateDialog(false);
        setNewJob({ name: '', dataset_id: '', base_model: 'mobilenetv2', backend: 'server', learning_rate: '0.001', batch_size: '32', epochs: '50' });
        fetchData();
      }
    } catch (error) {
      console.error('Failed to create job:', error);
    }
  };

  const handleStartJob = async (jobId: string) => {
    try {
      await fetch(`/api/v2/vision/training/jobs/${jobId}/start`, { method: 'POST' });
      fetchData();
    } catch (error) {
      console.error('Failed to start job:', error);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await fetch(`/api/v2/vision/training/jobs/${jobId}/cancel`, { method: 'POST' });
      fetchData();
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle2 className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'training':
        return <Badge className="bg-blue-100 text-blue-800"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Training</Badge>;
      case 'queued':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Queued</Badge>;
      case 'failed':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      case 'cancelled':
        return <Badge variant="outline"><XCircle className="h-3 w-3 mr-1" />Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const activeJobs = jobs.filter(j => j.status === 'training' || j.status === 'queued');
  const completedJobs = jobs.filter(j => j.status === 'completed');

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
              <Brain className="h-6 w-6" />
              Model Training
            </h1>
            <p className="text-muted-foreground">
              Train custom models on your datasets
            </p>
          </div>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Training Job
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Loader2 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeJobs.length}</p>
                <p className="text-xs text-muted-foreground">Active Jobs</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{completedJobs.length}</p>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <TrendingUp className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {completedJobs.length > 0 
                    ? `${Math.round(Math.max(...completedJobs.map(j => (j.metrics?.val_accuracy || 0) * 100)))}%`
                    : '-'}
                </p>
                <p className="text-xs text-muted-foreground">Best Accuracy</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <BarChart3 className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{jobs.length}</p>
                <p className="text-xs text-muted-foreground">Total Jobs</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Jobs List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Jobs ({jobs.length})</TabsTrigger>
          <TabsTrigger value="active">Active ({activeJobs.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedJobs.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4 mt-4">
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : jobs.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No training jobs</h3>
                <p className="text-muted-foreground mb-4">Create your first training job to get started</p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Training Job
                </Button>
              </CardContent>
            </Card>
          ) : (
            jobs.map((job) => (
              <JobCard 
                key={job.id} 
                job={job} 
                onStart={handleStartJob}
                onCancel={handleCancelJob}
                onSelect={setSelectedJob}
                getStatusBadge={getStatusBadge}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="active" className="space-y-4 mt-4">
          {activeJobs.map((job) => (
            <JobCard 
              key={job.id} 
              job={job} 
              onStart={handleStartJob}
              onCancel={handleCancelJob}
              onSelect={setSelectedJob}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4 mt-4">
          {completedJobs.map((job) => (
            <JobCard 
              key={job.id} 
              job={job} 
              onStart={handleStartJob}
              onCancel={handleCancelJob}
              onSelect={setSelectedJob}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </TabsContent>
      </Tabs>

      {/* Create Job Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Training Job</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Job Name</Label>
              <Input
                placeholder="e.g., Rice Blast Classifier v4"
                value={newJob.name}
                onChange={(e) => setNewJob({ ...newJob, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Dataset</Label>
              <Select value={newJob.dataset_id} onValueChange={(v) => setNewJob({ ...newJob, dataset_id: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets.map(ds => (
                    <SelectItem key={ds.id} value={ds.id}>
                      {ds.name} ({ds.image_count} images)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Base Model</Label>
                <Select value={newJob.base_model} onValueChange={(v) => setNewJob({ ...newJob, base_model: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BASE_MODELS.map(m => (
                      <SelectItem key={m.id} value={m.id}>
                        {m.name} ({m.size})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Backend</Label>
                <Select value={newJob.backend} onValueChange={(v) => setNewJob({ ...newJob, backend: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="browser">Browser (TensorFlow.js)</SelectItem>
                    <SelectItem value="server">Server (GPU)</SelectItem>
                    <SelectItem value="cloud">Cloud (AWS/GCP)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Learning Rate</Label>
                <Input
                  type="number"
                  step="0.0001"
                  value={newJob.learning_rate}
                  onChange={(e) => setNewJob({ ...newJob, learning_rate: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Batch Size</Label>
                <Input
                  type="number"
                  value={newJob.batch_size}
                  onChange={(e) => setNewJob({ ...newJob, batch_size: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Epochs</Label>
                <Input
                  type="number"
                  value={newJob.epochs}
                  onChange={(e) => setNewJob({ ...newJob, epochs: e.target.value })}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateJob} disabled={!newJob.name || !newJob.dataset_id}>
              Create Job
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Job Detail Dialog */}
      {selectedJob && (
        <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedJob.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  {getStatusBadge(selectedJob.status)}
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Progress</p>
                  <p className="font-medium">{selectedJob.current_epoch} / {selectedJob.total_epochs} epochs</p>
                </div>
              </div>
              <Progress value={selectedJob.progress} />
              {selectedJob.metrics && Object.keys(selectedJob.metrics).length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {selectedJob.metrics.train_loss !== undefined && (
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Train Loss</p>
                      <p className="text-lg font-bold">{selectedJob.metrics.train_loss.toFixed(4)}</p>
                    </div>
                  )}
                  {selectedJob.metrics.val_loss !== undefined && (
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Val Loss</p>
                      <p className="text-lg font-bold">{selectedJob.metrics.val_loss.toFixed(4)}</p>
                    </div>
                  )}
                  {selectedJob.metrics.train_accuracy !== undefined && (
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Train Acc</p>
                      <p className="text-lg font-bold">{(selectedJob.metrics.train_accuracy * 100).toFixed(1)}%</p>
                    </div>
                  )}
                  {selectedJob.metrics.val_accuracy !== undefined && (
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Val Acc</p>
                      <p className="text-lg font-bold">{(selectedJob.metrics.val_accuracy * 100).toFixed(1)}%</p>
                    </div>
                  )}
                </div>
              )}
              <div className="text-sm text-muted-foreground">
                <p>Base Model: {selectedJob.base_model}</p>
                <p>Backend: {selectedJob.backend}</p>
                <p>Created: {new Date(selectedJob.created_at).toLocaleString()}</p>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function JobCard({ 
  job, 
  onStart, 
  onCancel, 
  onSelect,
  getStatusBadge 
}: { 
  job: TrainingJob; 
  onStart: (id: string) => void;
  onCancel: (id: string) => void;
  onSelect: (job: TrainingJob) => void;
  getStatusBadge: (status: string) => React.ReactNode;
}) {
  return (
    <Card className="hover:border-primary/50 transition-colors cursor-pointer" onClick={() => onSelect(job)}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-medium">{job.name}</h3>
              {getStatusBadge(job.status)}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
              <span>Base: {job.base_model}</span>
              <span>Backend: {job.backend}</span>
              <span>Epochs: {job.current_epoch}/{job.total_epochs}</span>
            </div>
            <Progress value={job.progress} className="h-2" />
            {job.metrics && job.metrics.val_accuracy !== undefined && (
              <p className="text-sm mt-2">
                Accuracy: <span className="font-medium">{(job.metrics.val_accuracy * 100).toFixed(1)}%</span>
              </p>
            )}
          </div>
          <div className="flex gap-2 ml-4" onClick={(e) => e.stopPropagation()}>
            {job.status === 'queued' && (
              <Button size="sm" onClick={() => onStart(job.id)}>
                <Play className="h-4 w-4 mr-1" />
                Start
              </Button>
            )}
            {(job.status === 'training' || job.status === 'queued') && (
              <Button size="sm" variant="outline" onClick={() => onCancel(job.id)}>
                <Pause className="h-4 w-4 mr-1" />
                Cancel
              </Button>
            )}
            {job.status === 'completed' && job.model_id && (
              <Button size="sm" variant="outline" asChild>
                <Link to={`/vision/models/${job.model_id}`}>
                  View Model
                </Link>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
