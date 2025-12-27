/**
 * Tutorials Page
 *
 * Step-by-step learning tutorials.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Tutorial {
  id: string;
  title: string;
  description: string;
  duration: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  category: string;
}

export function Tutorials() {
  const tutorials: Tutorial[] = [
    { id: '1', title: 'Creating Your First Breeding Program', description: 'Learn how to set up and configure a breeding program', duration: '15 min', level: 'beginner', category: 'Getting Started' },
    { id: '2', title: 'Recording Field Observations', description: 'Collect phenotypic data efficiently in the field', duration: '20 min', level: 'beginner', category: 'Data Collection' },
    { id: '3', title: 'Managing Germplasm Accessions', description: 'Register and track germplasm in the seed bank', duration: '25 min', level: 'intermediate', category: 'Seed Bank' },
    { id: '4', title: 'Using the Field Map', description: 'Visualize and manage your trial locations', duration: '15 min', level: 'beginner', category: 'Earth Systems' },
    { id: '5', title: 'Genomic Selection Workflow', description: 'Implement GS in your breeding program', duration: '45 min', level: 'advanced', category: 'Genomics' },
    { id: '6', title: 'Offline Data Sync', description: 'Work offline and sync when connected', duration: '10 min', level: 'beginner', category: 'Features' },
  ];

  const getLevelBadge = (level: string) => {
    const colors = {
      beginner: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
      intermediate: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300',
      advanced: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
    };
    return colors[level as keyof typeof colors] || 'bg-muted text-muted-foreground';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">Tutorials</h1>
        <p className="text-muted-foreground mt-1">Step-by-step guides to master Bijmantra</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tutorials.map((tutorial) => (
          <Card key={tutorial.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{tutorial.category}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${getLevelBadge(tutorial.level)}`}>
                  {tutorial.level}
                </span>
              </div>
              <CardTitle className="text-lg">{tutorial.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{tutorial.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">⏱️ {tutorial.duration}</span>
                <Button size="sm">Start Tutorial</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default Tutorials;
