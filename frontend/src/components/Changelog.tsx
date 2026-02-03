/**
 * Changelog Component
 * 
 * Displays version history and release notes.
 * Can be used in About page or as a standalone dialog.
 */

import { useState } from 'react';
import { 
  History, Tag, Bug, Sparkles, Wrench, AlertTriangle,
  ChevronDown, ChevronRight, ExternalLink, Calendar
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

type ChangeType = 'feature' | 'fix' | 'improvement' | 'breaking' | 'security';

interface ChangeItem {
  type: ChangeType;
  description: string;
  issue?: string;
}

interface Release {
  version: string;
  date: string;
  title?: string;
  changes: ChangeItem[];
  isLatest?: boolean;
}

const CHANGE_CONFIG: Record<ChangeType, { icon: React.ReactNode; label: string; color: string }> = {
  feature: { icon: <Sparkles className="h-3 w-3" />, label: 'New', color: 'bg-green-100 text-green-700' },
  fix: { icon: <Bug className="h-3 w-3" />, label: 'Fix', color: 'bg-red-100 text-red-700' },
  improvement: { icon: <Wrench className="h-3 w-3" />, label: 'Improved', color: 'bg-blue-100 text-blue-700' },
  breaking: { icon: <AlertTriangle className="h-3 w-3" />, label: 'Breaking', color: 'bg-orange-100 text-orange-700' },
  security: { icon: <AlertTriangle className="h-3 w-3" />, label: 'Security', color: 'bg-purple-100 text-purple-700' },
};

// Sample changelog data - in production, this would come from an API or file
const CHANGELOG: Release[] = [
  {
    version: 'preview-1',
    date: '2026-01-09',
    title: 'CALF Assessment & Version Update',
    isLatest: true,
    changes: [
      { type: 'feature', description: 'Comprehensive CALF (Computational Analysis and Functionality Level) assessment' },
      { type: 'improvement', description: 'Version updated to preview-1 reflecting actual development state' },
      { type: 'improvement', description: 'Documentation reorganized (docs/gupt, docs/standards, docs/operations)' },
      { type: 'feature', description: 'MAHASARTHI navigation system with dock, browser, and search' },
      { type: 'feature', description: 'Future workspaces roadmap (11 modules, ~304 pages planned)' },
      { type: 'fix', description: 'Zero Demo Data Policy enforcement in progress' },
    ],
  },
  {
    version: '1.5.0',
    date: '2025-12-11',
    title: 'UX Components & Help System',
    changes: [
      { type: 'feature', description: 'Added Onboarding Wizard for new users' },
      { type: 'feature', description: 'Added Help Center with contextual help' },
      { type: 'feature', description: 'Added Notification Preferences with quiet hours' },
      { type: 'feature', description: 'Enhanced Profile page with i18n, density, field mode settings' },
      { type: 'feature', description: 'Added Search Results component with filters and view modes' },
      { type: 'feature', description: 'Added Entity Preview Card with hover preview' },
      { type: 'improvement', description: 'Improved accessibility with WCAG AAA contrast in field mode' },
    ],
  },
  {
    version: '1.4.0',
    date: '2025-12-11',
    title: 'Camera Integration & i18n',
    changes: [
      { type: 'feature', description: 'Added Camera Capture component with overlays' },
      { type: 'feature', description: 'Added Plant Vision Analyzer for disease detection' },
      { type: 'feature', description: 'Added i18n system with 7 languages' },
      { type: 'feature', description: 'Added RTL support for Arabic' },
      { type: 'feature', description: 'Added Keyboard Shortcuts Manager' },
      { type: 'feature', description: 'Added Data Export/Import managers' },
      { type: 'feature', description: 'Added Form Wizard for multi-step forms' },
      { type: 'feature', description: 'Added Activity Logger with timeline' },
    ],
  },
  {
    version: '1.3.0',
    date: '2025-12-10',
    title: 'Sun-Earth & Space Research',
    changes: [
      { type: 'feature', description: 'Added Sun-Earth Systems division with solar activity tracking' },
      { type: 'feature', description: 'Added Space Research division with crop catalog' },
      { type: 'feature', description: 'Added Sensor Networks with live data charts' },
      { type: 'feature', description: 'Added Field Mode for outdoor data collection' },
      { type: 'feature', description: 'Added Virtual scrolling for 100K+ rows' },
      { type: 'improvement', description: 'Added ECharts for high-performance visualizations' },
    ],
  },
  {
    version: '1.2.0',
    date: '2025-12-10',
    title: 'Commercial Division',
    changes: [
      { type: 'feature', description: 'Added DUS Testing with 10 crop templates' },
      { type: 'feature', description: 'Added MCPD v2.1 import/export' },
      { type: 'feature', description: 'Added Variety Licensing module' },
      { type: 'feature', description: 'Added Processing Stages workflow' },
      { type: 'feature', description: 'Added Disease Resistance and Abiotic Stress pages' },
    ],
  },
  {
    version: '1.1.0',
    date: '2025-12-06',
    title: 'Seed Operations',
    changes: [
      { type: 'feature', description: 'Added Seed Operations division with 18 pages' },
      { type: 'feature', description: 'Added Quality Gate Scanner' },
      { type: 'feature', description: 'Added Dispatch Management' },
      { type: 'feature', description: 'Added Processing Batches' },
      { type: 'feature', description: 'Added Traceability module' },
    ],
  },
  {
    version: '1.0.0',
    date: '2025-12-01',
    title: 'Initial Release',
    changes: [
      { type: 'feature', description: 'BrAPI v2.1 compliant API (34 endpoints)' },
      { type: 'feature', description: 'Plant Sciences division with breeding tools' },
      { type: 'feature', description: 'Seed Bank division with germplasm management' },
      { type: 'feature', description: 'Earth Systems with weather and GIS' },
      { type: 'feature', description: 'Veena AI assistant with RAG' },
      { type: 'feature', description: 'PWA with offline data collection' },
    ],
  },
];

interface ChangelogProps {
  trigger?: React.ReactNode;
  maxReleases?: number;
}

export function Changelog({ trigger, maxReleases }: ChangelogProps) {
  const [open, setOpen] = useState(false);
  const releases = maxReleases ? CHANGELOG.slice(0, maxReleases) : CHANGELOG;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <History className="h-4 w-4 mr-2" />
            Changelog
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Changelog
          </DialogTitle>
          <DialogDescription>
            Version history and release notes
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[60vh] pr-4">
          <div className="space-y-6">
            {releases.map((release, index) => (
              <ReleaseCard key={release.version} release={release} defaultOpen={index === 0} />
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

function ReleaseCard({ release, defaultOpen = false }: { release: Release; defaultOpen?: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger asChild>
          <button className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <span className="font-mono font-bold">v{release.version}</span>
                {release.isLatest && (
                  <Badge variant="default" className="text-xs">Latest</Badge>
                )}
              </div>
              {release.title && (
                <span className="text-muted-foreground">— {release.title}</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {release.date}
              </span>
              {isOpen ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 space-y-2">
            {release.changes.map((change, i) => (
              <div key={i} className="flex items-start gap-2">
                <Badge 
                  variant="secondary" 
                  className={cn('text-xs shrink-0', CHANGE_CONFIG[change.type].color)}
                >
                  {CHANGE_CONFIG[change.type].icon}
                  <span className="ml-1">{CHANGE_CONFIG[change.type].label}</span>
                </Badge>
                <span className="text-sm">{change.description}</span>
                {change.issue && (
                  <a 
                    href={`#${change.issue}`}
                    className="text-xs text-muted-foreground hover:text-primary"
                  >
                    #{change.issue}
                  </a>
                )}
              </div>
            ))}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

// Inline changelog for embedding in pages
export function ChangelogInline({ maxReleases = 3 }: { maxReleases?: number }) {
  const releases = CHANGELOG.slice(0, maxReleases);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <History className="h-4 w-4" />
          Recent Updates
        </h3>
        <Changelog trigger={
          <Button variant="ghost" size="sm">
            View All
            <ExternalLink className="h-3 w-3 ml-1" />
          </Button>
        } />
      </div>
      
      <div className="space-y-3">
        {releases.map((release) => (
          <div key={release.version} className="p-3 border rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium">v{release.version}</span>
                {release.isLatest && (
                  <Badge variant="default" className="text-xs">Latest</Badge>
                )}
              </div>
              <span className="text-xs text-muted-foreground">{release.date}</span>
            </div>
            {release.title && (
              <p className="text-sm text-muted-foreground">{release.title}</p>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              {release.changes.length} changes
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Get current version
export function useCurrentVersion() {
  const latest = CHANGELOG.find(r => r.isLatest) || CHANGELOG[0];
  return {
    version: latest?.version || 'preview-1',
    date: latest?.date || '',
    title: latest?.title || '',
  };
}
