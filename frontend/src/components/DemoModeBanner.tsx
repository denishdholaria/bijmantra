/**
 * Demo Mode Banner
 * 
 * Shows a banner when demo mode is active, allowing users to:
 * - See they're viewing demo data
 * - Switch to production mode
 * - Dismiss the banner
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertTriangle,
  X,
  Database,
  FlaskConical,
  Settings,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useDemoMode } from '@/hooks/useDemoMode';

export function DemoModeBanner() {
  const { isDemoMode, showDemoBanner, toggleDemoMode, toggleDemoBanner } = useDemoMode();
  const [showSettings, setShowSettings] = useState(false);

  if (!isDemoMode || !showDemoBanner) return null;

  return (
    <>
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-2">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <FlaskConical className="h-4 w-4 text-amber-600" />
            <span className="text-sm text-amber-800">
              <strong>Demo Mode Active</strong> — You're viewing sample data for learning purposes.
            </span>
            <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">
              Not Real Data
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-amber-700 hover:text-amber-900 hover:bg-amber-100"
              onClick={() => setShowSettings(true)}
            >
              <Settings className="h-4 w-4 mr-1" />
              Settings
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-amber-700 hover:text-amber-900 hover:bg-amber-100"
              onClick={toggleDemoBanner}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <Dialog open={showSettings} onOpenChange={setShowSettings}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5" />
              Demo Mode Settings
            </DialogTitle>
            <DialogDescription>
              Demo mode shows sample data for learning. Switch to production mode to use real data.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label htmlFor="demo-mode" className="text-base font-medium">
                  Demo Mode
                </Label>
                <p className="text-sm text-muted-foreground">
                  Show sample/mock data instead of real data
                </p>
              </div>
              <Switch
                id="demo-mode"
                checked={isDemoMode}
                onCheckedChange={toggleDemoMode}
              />
            </div>

            <div className="border-t pt-4">
              <h4 className="text-sm font-medium mb-3">What Demo Mode Does:</h4>
              <ul className="text-sm text-muted-foreground space-y-2">
                <li className="flex items-start gap-2">
                  <Database className="h-4 w-4 mt-0.5 text-blue-500" />
                  <span>Shows pre-loaded sample germplasm, trials, and observations</span>
                </li>
                <li className="flex items-start gap-2">
                  <FlaskConical className="h-4 w-4 mt-0.5 text-green-500" />
                  <span>Simulates sensor readings and IoT data</span>
                </li>
                <li className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-500" />
                  <span>Changes are not saved to the database</span>
                </li>
              </ul>
            </div>

            <div className="bg-blue-50 p-3 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Tip:</strong> Use demo mode to explore features and train new users.
                Switch to production mode when ready to work with real data.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSettings(false)}>
              Close
            </Button>
            <Button onClick={() => { toggleDemoMode(); setShowSettings(false); }}>
              {isDemoMode ? 'Switch to Production' : 'Switch to Demo'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default DemoModeBanner;
