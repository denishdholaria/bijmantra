import { useState } from 'react';
import { 
  CheckSquare, X, Trash2, Archive, Tag, Download, 
  Share2, Copy, Edit, MoreHorizontal, AlertTriangle,
  Loader2, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator,
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface BulkAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  variant?: 'default' | 'destructive';
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
}

interface BulkOperationsPanelProps {
  selectedCount: number;
  totalCount: number;
  entityName: string;
  onClearSelection: () => void;
  onSelectAll: () => void;
  onAction: (actionId: string) => Promise<void>;
  actions?: BulkAction[];
  className?: string;
}

const DEFAULT_ACTIONS: BulkAction[] = [
  { id: 'export', label: 'Export', icon: <Download className="h-4 w-4" /> },
  { id: 'tag', label: 'Add Tag', icon: <Tag className="h-4 w-4" /> },
  { id: 'share', label: 'Share', icon: <Share2 className="h-4 w-4" /> },
  { id: 'duplicate', label: 'Duplicate', icon: <Copy className="h-4 w-4" /> },
  { id: 'archive', label: 'Archive', icon: <Archive className="h-4 w-4" />, requiresConfirmation: true, confirmationMessage: 'Are you sure you want to archive the selected items?' },
  { id: 'delete', label: 'Delete', icon: <Trash2 className="h-4 w-4" />, variant: 'destructive', requiresConfirmation: true, confirmationMessage: 'This action cannot be undone. Are you sure you want to delete the selected items?' },
];

export function BulkOperationsPanel({
  selectedCount,
  totalCount,
  entityName,
  onClearSelection,
  onSelectAll,
  onAction,
  actions = DEFAULT_ACTIONS,
  className,
}: BulkOperationsPanelProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [confirmAction, setConfirmAction] = useState<BulkAction | null>(null);

  if (selectedCount === 0) return null;

  const handleAction = async (action: BulkAction) => {
    if (action.requiresConfirmation) {
      setConfirmAction(action);
      return;
    }
    await executeAction(action.id);
  };

  const executeAction = async (actionId: string) => {
    setIsProcessing(true);
    setProcessingAction(actionId);
    setProgress(0);

    // Simulate progress
    const interval = setInterval(() => {
      setProgress(p => Math.min(p + 10, 90));
    }, 100);

    try {
      await onAction(actionId);
      setProgress(100);
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingAction(null);
        setProgress(0);
      }, 500);
    } catch (error) {
      console.error('Bulk action failed:', error);
      setIsProcessing(false);
      setProcessingAction(null);
      setProgress(0);
    } finally {
      clearInterval(interval);
    }
  };

  const primaryActions = actions.slice(0, 3);
  const moreActions = actions.slice(3);

  return (
    <>
      <div className={cn(
        'fixed bottom-4 left-1/2 -translate-x-1/2 z-50',
        'flex items-center gap-3 px-4 py-3 rounded-xl',
        'bg-background border shadow-lg',
        'animate-in slide-in-from-bottom-4 duration-200',
        className
      )}>
        {/* Selection Info */}
        <div className="flex items-center gap-2">
          <CheckSquare className="h-5 w-5 text-primary" />
          <span className="font-medium">
            {selectedCount} {entityName}{selectedCount !== 1 ? 's' : ''} selected
          </span>
          <Badge variant="secondary" className="text-xs">
            of {totalCount}
          </Badge>
        </div>

        <div className="w-px h-6 bg-border" />

        {/* Quick Actions */}
        {isProcessing ? (
          <div className="flex items-center gap-3 min-w-[200px]">
            <Loader2 className="h-4 w-4 animate-spin" />
            <div className="flex-1">
              <Progress value={progress} className="h-2" />
            </div>
            <span className="text-sm text-muted-foreground">{progress}%</span>
          </div>
        ) : (
          <>
            {primaryActions.map((action) => (
              <Button
                key={action.id}
                variant={action.variant === 'destructive' ? 'destructive' : 'outline'}
                size="sm"
                onClick={() => handleAction(action)}
                className="gap-2"
              >
                {action.icon}
                <span className="hidden sm:inline">{action.label}</span>
              </Button>
            ))}

            {moreActions.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {moreActions.map((action, index) => (
                    <div key={action.id}>
                      {action.variant === 'destructive' && index > 0 && <DropdownMenuSeparator />}
                      <DropdownMenuItem
                        onClick={() => handleAction(action)}
                        className={cn(
                          'gap-2',
                          action.variant === 'destructive' && 'text-destructive focus:text-destructive'
                        )}
                      >
                        {action.icon}
                        {action.label}
                      </DropdownMenuItem>
                    </div>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </>
        )}

        <div className="w-px h-6 bg-border" />

        {/* Selection Controls */}
        <Button variant="ghost" size="sm" onClick={onSelectAll}>
          Select All
        </Button>
        <Button variant="ghost" size="icon" onClick={onClearSelection} aria-label="Clear selection">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!confirmAction} onOpenChange={() => setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Confirm {confirmAction?.label}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmAction?.confirmationMessage || `Are you sure you want to ${confirmAction?.label.toLowerCase()} ${selectedCount} ${entityName}${selectedCount !== 1 ? 's' : ''}?`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (confirmAction) {
                  executeAction(confirmAction.id);
                }
                setConfirmAction(null);
              }}
              className={cn(
                confirmAction?.variant === 'destructive' && 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
              )}
            >
              {confirmAction?.label}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

// Hook for managing bulk selection
export function useBulkSelection<T extends { id: string }>(items: T[]) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const isSelected = (id: string) => selectedIds.has(id);
  const selectedCount = selectedIds.size;
  const isAllSelected = items.length > 0 && selectedIds.size === items.length;
  const isSomeSelected = selectedIds.size > 0 && selectedIds.size < items.length;

  const toggle = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(items.map(item => item.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const selectRange = (startId: string, endId: string) => {
    const startIndex = items.findIndex(item => item.id === startId);
    const endIndex = items.findIndex(item => item.id === endId);
    if (startIndex === -1 || endIndex === -1) return;

    const [from, to] = startIndex < endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
    const rangeIds = items.slice(from, to + 1).map(item => item.id);
    
    setSelectedIds(prev => {
      const next = new Set(prev);
      rangeIds.forEach(id => next.add(id));
      return next;
    });
  };

  const getSelectedItems = () => items.filter(item => selectedIds.has(item.id));

  return {
    selectedIds,
    selectedCount,
    isSelected,
    isAllSelected,
    isSomeSelected,
    toggle,
    selectAll,
    clearSelection,
    selectRange,
    getSelectedItems,
  };
}
