import { useState, useMemo, useEffect, useCallback, type ChangeEvent, type ReactNode } from 'react';
import { Keyboard, Search } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  APP_SHORTCUTS,
  formatShortcutKeyForPlatform,
  groupShortcutsByCategory,
  isEditableShortcutTarget,
  isKeyboardShortcutHelpEvent,
  SHORTCUT_CATEGORY_ORDER,
  type AppShortcut,
} from '@/lib/keyboardShortcuts';

interface KeyboardShortcutsManagerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Key component
function Key({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <kbd className={cn(
      'inline-flex items-center justify-center min-w-[24px] h-6 px-1.5',
      'bg-muted border border-border rounded text-xs font-mono',
      'shadow-sm',
      className
    )}>
      {children}
    </kbd>
  );
}

export function KeyboardShortcutsManager({ open, onOpenChange }: KeyboardShortcutsManagerProps) {
  const [search, setSearch] = useState('');
  const filteredShortcuts = useMemo<AppShortcut[]>(() => {
    if (!search.trim()) {
      return APP_SHORTCUTS;
    }

    const query = search.toLowerCase();
    return APP_SHORTCUTS.filter(
      (shortcut) =>
        shortcut.description.toLowerCase().includes(query) ||
        shortcut.category.toLowerCase().includes(query) ||
        shortcut.keys.join(' ').toLowerCase().includes(query)
    );
  }, [search]);

  const groupedShortcuts = groupShortcutsByCategory(filteredShortcuts);
  const categories = SHORTCUT_CATEGORY_ORDER.filter((category) => (groupedShortcuts[category]?.length ?? 0) > 0);
  const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.userAgent);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Quick reference for the shortcuts currently wired into the active UI. Press ? to open this dialog anytime.
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search shortcuts..."
            value={search}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Shortcuts List */}
        <ScrollArea className="h-[400px] pr-4">
          {categories.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No shortcuts found for "{search}"
            </div>
          ) : (
            <div className="space-y-6">
              {categories.map((category) => (
                <div key={category}>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                    {category}
                  </h3>
                  <div className="space-y-2">
                    {groupedShortcuts[category].map((shortcut) => (
                      <div
                        key={shortcut.id}
                        className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <span className="text-sm">{shortcut.description}</span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, i) => (
                            <Key key={i}>{formatShortcutKeyForPlatform(key, isMac)}</Key>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t text-xs text-muted-foreground">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <Key>⌘</Key> = Command (Mac) / Ctrl (Windows)
            </span>
            <span className="flex items-center gap-1">
              <Key>⇧</Key> = Shift
            </span>
          </div>
          <Badge variant="outline">{APP_SHORTCUTS.length} shortcuts</Badge>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Hook to register global keyboard shortcuts
export function useKeyboardShortcuts() {
  const [showShortcuts, setShowShortcuts] = useState(false);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (isKeyboardShortcutHelpEvent(e)) {
      if (isEditableShortcutTarget(e.target)) {
        return;
      }

      e.preventDefault();
      setShowShortcuts(true);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    showShortcuts,
    setShowShortcuts,
  };
}
