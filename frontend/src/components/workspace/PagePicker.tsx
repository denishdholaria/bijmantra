/**
 * Page Picker Component
 * 
 * Allows users to select pages for their custom workspace.
 * Pages are grouped by module with search and bulk selection.
 */

import { useState, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Search, ChevronRight, ChevronDown, Check, X } from 'lucide-react';
import { useSelectablePages, useModuleSelectionCounts } from '@/hooks/useCustomWorkspace';
import { CUSTOM_WORKSPACE_LIMITS } from '@/types/customWorkspace';
import type { SelectablePage } from '@/types/customWorkspace';

interface PagePickerProps {
  selectedPageIds: string[];
  onSelectionChange: (pageIds: string[]) => void;
  maxHeight?: string;
}

export function PagePicker({ 
  selectedPageIds, 
  onSelectionChange,
  maxHeight = '400px',
}: PagePickerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  
  const modules = useSelectablePages();
  const selectionCounts = useModuleSelectionCounts(selectedPageIds);
  const selectedSet = useMemo(() => new Set(selectedPageIds), [selectedPageIds]);
  
  // Filter modules and pages by search query
  const filteredModules = useMemo(() => {
    if (!searchQuery.trim()) return modules;
    
    const lowerQuery = searchQuery.toLowerCase();
    
    return modules
      .map(module => ({
        ...module,
        pages: module.pages.filter(page =>
          page.name.toLowerCase().includes(lowerQuery) ||
          module.name.toLowerCase().includes(lowerQuery)
        ),
      }))
      .filter(module => module.pages.length > 0);
  }, [modules, searchQuery]);
  
  // Toggle module expansion
  const toggleModule = (moduleId: string) => {
    setExpandedModules(prev => {
      const next = new Set(prev);
      if (next.has(moduleId)) {
        next.delete(moduleId);
      } else {
        next.add(moduleId);
      }
      return next;
    });
  };
  
  // Expand all modules when searching
  useMemo(() => {
    if (searchQuery.trim()) {
      setExpandedModules(new Set(filteredModules.map(m => m.id)));
    }
  }, [searchQuery, filteredModules]);
  
  // Toggle page selection
  const togglePage = (pageId: string) => {
    if (selectedSet.has(pageId)) {
      onSelectionChange(selectedPageIds.filter(id => id !== pageId));
    } else {
      if (selectedPageIds.length >= CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) {
        return; // At limit
      }
      onSelectionChange([...selectedPageIds, pageId]);
    }
  };
  
  // Select all pages in a module
  const selectAllInModule = (moduleId: string) => {
    const module = modules.find(m => m.id === moduleId);
    if (!module) return;
    
    const modulePageIds = module.pages.map(p => p.id);
    const newSelection = new Set(selectedPageIds);
    
    for (const pageId of modulePageIds) {
      if (newSelection.size >= CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) break;
      newSelection.add(pageId);
    }
    
    onSelectionChange([...newSelection]);
  };
  
  // Deselect all pages in a module
  const deselectAllInModule = (moduleId: string) => {
    const module = modules.find(m => m.id === moduleId);
    if (!module) return;
    
    const modulePageIds = new Set(module.pages.map(p => p.id));
    onSelectionChange(selectedPageIds.filter(id => !modulePageIds.has(id)));
  };
  
  // Check if all pages in module are selected
  const isModuleFullySelected = (moduleId: string) => {
    const module = modules.find(m => m.id === moduleId);
    if (!module) return false;
    return module.pages.every(p => selectedSet.has(p.id));
  };
  
  // Check if some pages in module are selected
  const isModulePartiallySelected = (moduleId: string) => {
    const count = selectionCounts[moduleId] || 0;
    const module = modules.find(m => m.id === moduleId);
    if (!module) return false;
    return count > 0 && count < module.pages.length;
  };
  
  const atLimit = selectedPageIds.length >= CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace;
  
  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search pages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
            onClick={() => setSearchQuery('')}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      
      {/* Selection count */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {selectedPageIds.length} of {CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace} pages selected
        </span>
        {selectedPageIds.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSelectionChange([])}
            className="h-7 text-xs"
          >
            Clear all
          </Button>
        )}
      </div>
      
      {/* Progress bar */}
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all ${atLimit ? 'bg-amber-500' : 'bg-primary'}`}
          style={{ width: `${(selectedPageIds.length / CUSTOM_WORKSPACE_LIMITS.maxPagesPerWorkspace) * 100}%` }}
        />
      </div>
      
      {/* Module list */}
      <ScrollArea style={{ height: maxHeight }}>
        <div className="space-y-1 pr-4">
          {filteredModules.map(module => (
            <Collapsible
              key={module.id}
              open={expandedModules.has(module.id)}
              onOpenChange={() => toggleModule(module.id)}
            >
              <div className="flex items-center gap-2 py-1">
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    {expandedModules.has(module.id) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                </CollapsibleTrigger>
                
                <CollapsibleTrigger asChild>
                  <button className="flex-1 flex items-center gap-2 text-left hover:bg-muted/50 rounded px-2 py-1">
                    <span className="font-medium text-sm">{module.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {selectionCounts[module.id] || 0}/{module.pages.length}
                    </Badge>
                  </button>
                </CollapsibleTrigger>
                
                {/* Module bulk actions */}
                <div className="flex items-center gap-1">
                  {isModuleFullySelected(module.id) ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        deselectAllInModule(module.id);
                      }}
                    >
                      Deselect all
                    </Button>
                  ) : (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        selectAllInModule(module.id);
                      }}
                      disabled={atLimit && !isModulePartiallySelected(module.id)}
                    >
                      Select all
                    </Button>
                  )}
                </div>
              </div>
              
              <CollapsibleContent>
                <div className="ml-10 space-y-1 pb-2">
                  {module.pages.map(page => (
                    <PageItem
                      key={page.id}
                      page={page}
                      isSelected={selectedSet.has(page.id)}
                      onToggle={() => togglePage(page.id)}
                      disabled={atLimit && !selectedSet.has(page.id)}
                    />
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          ))}
          
          {filteredModules.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No pages found matching "{searchQuery}"
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

// Individual page item
interface PageItemProps {
  page: SelectablePage;
  isSelected: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

function PageItem({ page, isSelected, onToggle, disabled }: PageItemProps) {
  return (
    <label
      className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors
        ${isSelected ? 'bg-primary/10' : 'hover:bg-muted/50'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <Checkbox
        checked={isSelected}
        onCheckedChange={onToggle}
        disabled={disabled}
      />
      <span className="text-sm flex-1">{page.name}</span>
      {isSelected && (
        <Check className="h-4 w-4 text-primary" />
      )}
    </label>
  );
}

export default PagePicker;
