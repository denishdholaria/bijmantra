/**
 * Demo Mode Banner
 *
 * Shown when the user is in the curated preview environment.
 * Tone: confident and inviting — positions the preview as intentional,
 * not a limitation. Does not alarm investors or collaborators.
 */

import { Button } from '@/components/ui/button';
import { X, Sprout } from 'lucide-react';
import { useDemoMode } from '@/hooks/useDemoMode';

export function DemoModeBanner() {
  const { isDemoMode, showDemoBanner, toggleDemoBanner } = useDemoMode();

  if (!isDemoMode || !showDemoBanner) return null;

  return (
    <div className="border-b border-slate-200/70 bg-slate-50/95 px-4 py-2 dark:border-white/10 dark:bg-slate-950/60">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300">
            <Sprout className="h-3 w-3" />
          </div>
          <span className="text-sm text-slate-700 dark:text-slate-300">
            <span className="font-semibold">UI Preview</span>
            {' — '}BijMantra is under active development. Not all features are connected to a live backend.
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-7 shrink-0 p-0 text-slate-500 hover:bg-slate-200 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
          onClick={toggleDemoBanner}
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

export default DemoModeBanner;
