/**
 * Innovation Lab Dashboard
 * 
 * Workspace-specific dashboard for Innovation Lab workspace.
 * Shows experiments, AI models, compute jobs, and datasets.
 */

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { 
  Microscope, Brain, Cpu, Database,
  ArrowRight, Plus, Play, Sparkles,
  LineChart, Rocket, Eye, Beaker
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

export function ResearchDashboard() {
  // TODO: Connect to real APIs when available
  const activeExperiments = 0;
  const trainedModels = 0;
  const runningJobs = 0;
  const datasetCount = 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Microscope className="h-6 w-6 text-purple-600" />
            Innovation Lab Dashboard
          </h1>
          <p className="text-muted-foreground">
            Space, AI, analytics, and experimental tools
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/experiment-designer">
              <Beaker className="h-4 w-4 mr-2" />
              New Experiment
            </Link>
          </Button>
          <Button asChild>
            <Link to="/ai-vision/training">
              <Brain className="h-4 w-4 mr-2" />
              Train Model
            </Link>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Experiments</CardTitle>
            <Beaker className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeExperiments}</div>
            <p className="text-xs text-muted-foreground">Research projects running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">AI Models</CardTitle>
            <Brain className="h-4 w-4 text-pink-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{trainedModels}</div>
            <p className="text-xs text-muted-foreground">Trained and deployed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Compute Jobs</CardTitle>
            <Cpu className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runningJobs}</div>
            <p className="text-xs text-muted-foreground">Currently running</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Datasets</CardTitle>
            <Database className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{datasetCount}</div>
            <p className="text-xs text-muted-foreground">Images and annotations</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Models */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">AI Models</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/ai-vision/registry">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Plant disease detection models</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                    <Eye className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <div className="font-medium">Rice Blast Detector v2.1</div>
                    <div className="text-sm text-muted-foreground">Accuracy: 94.2%</div>
                  </div>
                </div>
                <Badge className="bg-green-100 text-green-800">Deployed</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                    <Eye className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-medium">Wheat Rust Classifier</div>
                    <div className="text-sm text-muted-foreground">Accuracy: 91.8%</div>
                  </div>
                </div>
                <Badge className="bg-green-100 text-green-800">Deployed</Badge>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                    <Brain className="h-4 w-4 text-amber-600" />
                  </div>
                  <div>
                    <div className="font-medium">Multi-Crop Disease v1.0</div>
                    <div className="text-sm text-muted-foreground">Training: 78%</div>
                  </div>
                </div>
                <Badge variant="secondary">Training</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Compute Jobs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Compute Jobs</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/wasm-genomics">
                  View All <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </Button>
            </div>
            <CardDescription>Running and queued jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="p-3 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">GBLUP Analysis - Rice Panel</div>
                  <Badge className="bg-blue-100 text-blue-800">Running</Badge>
                </div>
                <Progress value={67} className="h-2" />
                <div className="text-xs text-muted-foreground mt-1">67% complete • ETA: 12 min</div>
              </div>
              <div className="p-3 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">LD Decay Calculation</div>
                  <Badge className="bg-blue-100 text-blue-800">Running</Badge>
                </div>
                <Progress value={34} className="h-2" />
                <div className="text-xs text-muted-foreground mt-1">34% complete • ETA: 25 min</div>
              </div>
              <div className="p-3 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">Population Structure PCA</div>
                  <Badge variant="secondary">Queued</Badge>
                </div>
                <div className="text-xs text-muted-foreground">Waiting for resources</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Common research tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/wasm-gblup">
                <Cpu className="h-5 w-5 mb-2" />
                <span>Run GBLUP</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/ai-vision/datasets">
                <Database className="h-5 w-5 mb-2" />
                <span>Upload Dataset</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/space-research">
                <Rocket className="h-5 w-5 mb-2" />
                <span>Space Research</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" asChild>
              <Link to="/analytics">
                <LineChart className="h-5 w-5 mb-2" />
                <span>Analytics</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ResearchDashboard;
