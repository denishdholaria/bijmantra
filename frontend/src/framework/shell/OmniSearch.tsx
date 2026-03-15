import { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import { Search, Calculator, Calendar, CreditCard, Settings, User, Smile, Map, Sprout, FlaskConical, FileText } from 'lucide-react';
import { useOSStore } from './store';
import { DISCOVERED_ROUTES } from '../registry/routeDiscovery';
import { REGISTERED_APPS } from '../registry/moduleRegistry';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function OmniSearch() {
  const { mode, toggleSearch, openApp } = useOSStore();
  const isSearchOpen = mode === 'search';
  const navigate = useNavigate();

  // Toggle on Cmd+K or Escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        toggleSearch();
      }
      if (e.key === 'Escape') {
        toggleSearch(false);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [toggleSearch]);

  if (!isSearchOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh] bg-black/40 backdrop-blur-sm transition-all duration-200">
       <div className="w-full max-w-2xl px-4">
        <Command
          className="relative w-full overflow-hidden rounded-xl border border-border/40 bg-background/95 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100"
          loop
          shouldFilter={true}
        >
          <div className="flex items-center border-b border-border/10 px-4">
            <Search className="mr-2 h-5 w-5 shrink-0 opacity-50" />
            <Command.Input
              placeholder="Search apps, pages, or commands..."
              className="flex h-14 w-full rounded-md bg-transparent py-3 text-lg outline-none placeholder:text-muted-foreground/50 disabled:cursor-not-allowed disabled:opacity-50"
              autoFocus
            />
            <div className="ml-2 flex items-center gap-1">
                <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                    <span className="text-xs">ESC</span>
                </kbd>
            </div>
          </div>

          <Command.List className="max-h-[60vh] overflow-y-auto p-2 scroll-py-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            <Command.Group heading="Applications">
              {REGISTERED_APPS.map((app) => (
                <Command.Item
                  key={app.id}
                  onSelect={() => {
                    openApp(app.id);
                    toggleSearch(false);
                  }}
                  className="relative flex cursor-default select-none items-center rounded-lg px-3 py-3 text-sm outline-none aria-selected:bg-primary/10 aria-selected:text-primary data-[disabled]:opacity-50 transition-colors duration-100"
                >
                  <app.icon className="mr-3 h-5 w-5 opacity-70" />
                  <div className="flex flex-col">
                     <span className="font-medium">{app.title}</span>
                     <span className="text-xs text-muted-foreground font-normal">{app.subtitle}</span>
                  </div>
                </Command.Item>
              ))}
            </Command.Group>

            <Command.Group heading="Pages & Actions">
              {DISCOVERED_ROUTES.map((item) => (
                <Command.Item
                  key={item.path}
                  onSelect={() => {
                    // Navigate using React Router for pages, bypassing OS window logic for now
                    // OR: In a real "OS", we might want to open these in a "Browser" app window.
                    // For now, let's just navigate which might "exit" the desktop mode if not careful.
                    // But since we are INSIDE desktop route, navigating away exits desktop.
                    // Ideally, we launch a "Browser" window.
                    // Let's stick to "Navigate" for simplicity in Phase 2.
                    navigate(item.path);
                    toggleSearch(false);
                  }}
                   className="relative flex cursor-default select-none items-center rounded-lg px-3 py-2 text-sm outline-none aria-selected:bg-primary/10 aria-selected:text-primary data-[disabled]:opacity-50 transition-colors duration-100"
                >
                  <FileText className="mr-3 h-4 w-4 opacity-50" />
                  <span>{item.title}</span>
                  <span className="ml-auto text-xs text-muted-foreground opacity-50">{item.subtitle}</span>
                </Command.Item>
              ))}
            </Command.Group>

          </Command.List>
        </Command>

        {/* Backdrop click to close */}
        <div
            className="absolute inset-0 -z-10 h-full w-full"
            onClick={() => toggleSearch(false)}
        />
       </div>
    </div>
  );
}
