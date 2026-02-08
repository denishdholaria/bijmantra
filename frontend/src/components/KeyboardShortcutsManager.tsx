import { useState, useEffect, useCallback } from 'react';
import { Keyboard, Search, Command, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, CornerDownLeft } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Shortcut {
  id: string;
  keys: string[];
  description: string;
  category: string;
  action?: () => void;
}

interface KeyboardShortcutsManagerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Define all keyboard shortcuts
const SHORTCUTS: Shortcut[] = [
  // Navigation
  { id: 'cmd-k', keys: ['⌘', 'K'], description: 'Open command palette', category: 'Navigation' },
  { id: 'cmd-/', keys: ['⌘', '/'], description: 'Open keyboard shortcuts', category: 'Navigation' },
  { id: 'cmd-b', keys: ['⌘', 'B'], description: 'Toggle sidebar', category: 'Navigation' },
  { id: 'cmd-shift-p', keys: ['⌘', '⇧', 'P'], description: 'Go to programs', category: 'Navigation' },
  { id: 'cmd-shift-t', keys: ['⌘', '⇧', 'T'], description: 'Go to trials', category: 'Navigation' },
  { id: 'cmd-shift-g', keys: ['⌘', '⇧', 'G'], description: 'Go to germplasm', category: 'Navigation' },
  { id: 'cmd-shift-d', keys: ['⌘', '⇧', 'D'], description: 'Go to dashboard', category: 'Navigation' },
  { id: 'esc', keys: ['Esc'], description: 'Close dialog/modal', category: 'Navigation' },
  
  // Data Entry
  { id: 'cmd-s', keys: ['⌘', 'S'], description: 'Save current form', category: 'Data Entry' },
  { id: 'cmd-enter', keys: ['⌘', '↵'], description: 'Submit form', category: 'Data Entry' },
  { id: 'tab', keys: ['Tab'], description: 'Next field', category: 'Data Entry' },
  { id: 'shift-tab', keys: ['⇧', 'Tab'], description: 'Previous field', category: 'Data Entry' },
  { id: 'cmd-z', keys: ['⌘', 'Z'], description: 'Undo', category: 'Data Entry' },
  { id: 'cmd-shift-z', keys: ['⌘', '⇧', 'Z'], description: 'Redo', category: 'Data Entry' },
  
  // Field Book
  { id: 'arrow-up', keys: ['↑'], description: 'Previous plot', category: 'Field Book' },
  { id: 'arrow-down', keys: ['↓'], description: 'Next plot', category: 'Field Book' },
  { id: 'arrow-left', keys: ['←'], description: 'Previous trait', category: 'Field Book' },
  { id: 'arrow-right', keys: ['→'], description: 'Next trait', category: 'Field Book' },
  { id: 'space', keys: ['Space'], description: 'Toggle selection', category: 'Field Book' },
  { id: 'enter', keys: ['↵'], description: 'Confirm value', category: 'Field Book' },
  
  // Tables
  { id: 'cmd-a', keys: ['⌘', 'A'], description: 'Select all rows', category: 'Tables' },
  { id: 'cmd-shift-e', keys: ['⌘', '⇧', 'E'], description: 'Export selected', category: 'Tables' },
  { id: 'cmd-f', keys: ['⌘', 'F'], description: 'Search in table', category: 'Tables' },
  { id: 'delete', keys: ['Del'], description: 'Delete selected', category: 'Tables' },
  
  // AI Assistant
  { id: 'cmd-shift-v', keys: ['⌘', '⇧', 'V'], description: 'Open Veena AI', category: 'AI Assistant' },
  { id: 'cmd-shift-a', keys: ['⌘', '⇧', 'A'], description: 'Ask Veena about selection', category: 'AI Assistant' },
  
  // View
  { id: 'cmd-plus', keys: ['⌘', '+'], description: 'Zoom in', category: 'View' },
  { id: 'cmd-minus', keys: ['⌘', '-'], description: 'Zoom out', category: 'View' },
  { id: 'cmd-0', keys: ['⌘', '0'], description: 'Reset zoom', category: 'View' },
  { id: 'f11', keys: ['F11'], description: 'Toggle fullscreen', category: 'View' },
  { id: 'cmd-shift-l', keys: ['⌘', '⇧', 'L'], description: 'Toggle dark mode', category: 'View' },
];

// Group shortcuts by category
function groupByCategory(shortcuts: Shortcut[]): Record<string, Shortcut[]> {
  return shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, Shortcut[]>);
}

// Key component
function Key({ children, className }: { children: React.ReactNode; className?: string }) {
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
  const [filteredShortcuts, setFilteredShortcuts] = useState(SHORTCUTS);

  // Filter shortcuts based on search
  useEffect(() => {
    if (!search.trim()) {
      setFilteredShortcuts(SHORTCUTS);
      return;
    }

    const query = search.toLowerCase();
    const filtered = SHORTCUTS.filter(
      s => s.description.toLowerCase().includes(query) ||
           s.category.toLowerCase().includes(query) ||
           s.keys.join(' ').toLowerCase().includes(query)
    );
    setFilteredShortcuts(filtered);
  }, [search]);

  const groupedShortcuts = groupByCategory(filteredShortcuts);
  const categories = Object.keys(groupedShortcuts);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
          <DialogDescription>
            Quick reference for all keyboard shortcuts. Press ⌘/ to open this dialog anytime.
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search shortcuts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
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
                            <Key key={i}>{key}</Key>
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
          <Badge variant="outline">{SHORTCUTS.length} shortcuts</Badge>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Hook to register global keyboard shortcuts
export function useKeyboardShortcuts() {
  const [showShortcuts, setShowShortcuts] = useState(false);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // ⌘/ or Ctrl+/ to show shortcuts
    if ((e.metaKey || e.ctrlKey) && e.key === '/') {
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
