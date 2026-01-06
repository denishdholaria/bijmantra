/**
 * Conflict Resolution Dialog
 * 
 * UI for manually resolving sync conflicts between local and server data.
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  GitMerge,
  Server,
  Smartphone,
} from 'lucide-react';

export interface ConflictData {
  id: string;
  entityType: string;
  entityId: string;
  localData: Record<string, unknown>;
  serverData: Record<string, unknown>;
  localTimestamp: string;
  serverTimestamp: string;
  conflictFields: string[];
}

interface ConflictResolutionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conflict: ConflictData | null;
  onResolve: (resolution: 'local' | 'server' | 'merge', mergedData?: Record<string, unknown>) => void;
}

export function ConflictResolutionDialog({
  open,
  onOpenChange,
  conflict,
  onResolve,
}: ConflictResolutionDialogProps) {
  const [selectedTab, setSelectedTab] = useState<'compare' | 'merge'>('compare');
  const [mergedData, setMergedData] = useState<Record<string, unknown>>({});
  const [fieldSelections, setFieldSelections] = useState<Record<string, 'local' | 'server'>>({});

  if (!conflict) return null;

  const initializeMerge = () => {
    const merged: Record<string, unknown> = { ...conflict.serverData };
    const selections: Record<string, 'local' | 'server'> = {};
    
    conflict.conflictFields.forEach(field => {
      selections[field] = 'server'; // Default to server
    });
    
    setMergedData(merged);
    setFieldSelections(selections);
    setSelectedTab('merge');
  };

  const selectFieldSource = (field: string, source: 'local' | 'server') => {
    setFieldSelections(prev => ({ ...prev, [field]: source }));
    setMergedData(prev => ({
      ...prev,
      [field]: source === 'local' ? conflict.localData[field] : conflict.serverData[field],
    }));
  };

  const handleResolve = (resolution: 'local' | 'server' | 'merge') => {
    if (resolution === 'merge') {
      // Build final merged data
      const finalMerged = { ...conflict.serverData };
      Object.entries(fieldSelections).forEach(([field, source]) => {
        finalMerged[field] = source === 'local' ? conflict.localData[field] : conflict.serverData[field];
      });
      onResolve('merge', finalMerged);
    } else {
      onResolve(resolution);
    }
  };

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return '(empty)';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            Sync Conflict Detected
          </DialogTitle>
          <DialogDescription>
            Changes were made both locally and on the server. Choose how to resolve this conflict.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Conflict Info */}
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <span className="text-sm text-muted-foreground">Entity: </span>
              <Badge variant="outline">{conflict.entityType}</Badge>
              <span className="ml-2 text-sm font-mono">{conflict.entityId}</span>
            </div>
            <div className="text-sm text-muted-foreground">
              {conflict.conflictFields.length} conflicting field(s)
            </div>
          </div>

          <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as 'compare' | 'merge')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="compare">Compare Versions</TabsTrigger>
              <TabsTrigger value="merge">Manual Merge</TabsTrigger>
            </TabsList>

            <TabsContent value="compare" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* Local Version */}
                <div className="border rounded-lg">
                  <div className="flex items-center gap-2 p-3 border-b bg-blue-50 dark:bg-blue-950">
                    <Smartphone className="h-4 w-4 text-blue-500" />
                    <span className="font-medium">Local Version</span>
                  </div>
                  <div className="p-2 text-xs text-muted-foreground border-b">
                    Modified: {formatDate(conflict.localTimestamp)}
                  </div>
                  <ScrollArea className="h-[300px]">
                    <div className="p-3 space-y-2">
                      {Object.entries(conflict.localData).map(([key, value]) => (
                        <div
                          key={key}
                          className={`p-2 rounded ${
                            conflict.conflictFields.includes(key)
                              ? 'bg-yellow-50 dark:bg-yellow-950 border border-yellow-200'
                              : ''
                          }`}
                        >
                          <div className="text-xs font-medium text-muted-foreground">{key}</div>
                          <div className="text-sm font-mono break-all">{formatValue(value)}</div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>

                {/* Server Version */}
                <div className="border rounded-lg">
                  <div className="flex items-center gap-2 p-3 border-b bg-green-50 dark:bg-green-950">
                    <Server className="h-4 w-4 text-green-500" />
                    <span className="font-medium">Server Version</span>
                  </div>
                  <div className="p-2 text-xs text-muted-foreground border-b">
                    Modified: {formatDate(conflict.serverTimestamp)}
                  </div>
                  <ScrollArea className="h-[300px]">
                    <div className="p-3 space-y-2">
                      {Object.entries(conflict.serverData).map(([key, value]) => (
                        <div
                          key={key}
                          className={`p-2 rounded ${
                            conflict.conflictFields.includes(key)
                              ? 'bg-yellow-50 dark:bg-yellow-950 border border-yellow-200'
                              : ''
                          }`}
                        >
                          <div className="text-xs font-medium text-muted-foreground">{key}</div>
                          <div className="text-sm font-mono break-all">{formatValue(value)}</div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex justify-center gap-4 pt-4">
                <Button
                  variant="outline"
                  onClick={() => handleResolve('local')}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Keep Local
                </Button>
                <Button
                  variant="outline"
                  onClick={initializeMerge}
                  className="flex items-center gap-2"
                >
                  <GitMerge className="h-4 w-4" />
                  Merge Manually
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleResolve('server')}
                  className="flex items-center gap-2"
                >
                  Keep Server
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="merge" className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Select which version to use for each conflicting field:
              </p>
              
              <ScrollArea className="h-[350px] border rounded-lg">
                <div className="p-4 space-y-4">
                  {conflict.conflictFields.map(field => (
                    <div key={field} className="border rounded-lg p-3 space-y-2">
                      <div className="font-medium">{field}</div>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => selectFieldSource(field, 'local')}
                          className={`p-2 rounded border text-left transition-colors ${
                            fieldSelections[field] === 'local'
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                              : 'hover:bg-muted'
                          }`}
                        >
                          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
                            <Smartphone className="h-3 w-3" />
                            Local
                            {fieldSelections[field] === 'local' && (
                              <Check className="h-3 w-3 text-blue-500 ml-auto" />
                            )}
                          </div>
                          <div className="text-sm font-mono break-all">
                            {formatValue(conflict.localData[field])}
                          </div>
                        </button>
                        <button
                          onClick={() => selectFieldSource(field, 'server')}
                          className={`p-2 rounded border text-left transition-colors ${
                            fieldSelections[field] === 'server'
                              ? 'border-green-500 bg-green-50 dark:bg-green-950'
                              : 'hover:bg-muted'
                          }`}
                        >
                          <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
                            <Server className="h-3 w-3" />
                            Server
                            {fieldSelections[field] === 'server' && (
                              <Check className="h-3 w-3 text-green-500 ml-auto" />
                            )}
                          </div>
                          <div className="text-sm font-mono break-all">
                            {formatValue(conflict.serverData[field])}
                          </div>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          {selectedTab === 'merge' && (
            <Button onClick={() => handleResolve('merge')}>
              <Check className="h-4 w-4 mr-2" />
              Apply Merge
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
