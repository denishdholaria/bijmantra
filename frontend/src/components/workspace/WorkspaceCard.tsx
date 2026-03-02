/**
 * Workspace Card Component
 * 
 * Displays a custom workspace in the gateway or workspace list.
 * Supports edit, delete, and activate actions.
 */

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
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
import { MoreVertical, Pencil, Copy, Trash2, Check, File, Plus } from 'lucide-react';
import { getWorkspaceIcon } from '@/lib/workspace-icons';
import { WORKSPACE_COLORS } from '@/types/customWorkspace';
import type { CustomWorkspace } from '@/types/customWorkspace';

interface WorkspaceCardProps {
  workspace: CustomWorkspace;
  isActive?: boolean;
  onActivate?: () => void;
  onEdit?: () => void;
  onDuplicate?: () => void;
  onDelete?: () => void;
  showActions?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function WorkspaceCard({
  workspace,
  isActive = false,
  onActivate,
  onEdit,
  onDuplicate,
  onDelete,
  showActions = true,
  size = 'md',
}: WorkspaceCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  
  const colorConfig = WORKSPACE_COLORS[workspace.color];
  const IconComponent = getWorkspaceIcon(workspace.icon, File);
  
  const sizeClasses = {
    sm: {
      card: 'p-3',
      icon: 'w-10 h-10',
      iconInner: 'h-5 w-5',
      title: 'text-sm',
      desc: 'text-xs',
    },
    md: {
      card: 'p-4',
      icon: 'w-12 h-12',
      iconInner: 'h-6 w-6',
      title: 'text-base',
      desc: 'text-sm',
    },
    lg: {
      card: 'p-6',
      icon: 'w-16 h-16',
      iconInner: 'h-8 w-8',
      title: 'text-lg',
      desc: 'text-base',
    },
  };
  
  const classes = sizeClasses[size];
  
  const handleDelete = () => {
    setShowDeleteDialog(false);
    onDelete?.();
  };
  
  return (
    <>
      <Card 
        className={`relative group cursor-pointer transition-all hover:shadow-md
          ${isActive ? `ring-2 ring-primary ${colorConfig.bg}` : 'hover:bg-muted/50'}
        `}
        onClick={onActivate}
      >
        <CardContent className={classes.card}>
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className={`${classes.icon} rounded-xl bg-gradient-to-br ${colorConfig.gradient} flex items-center justify-center shadow-md flex-shrink-0`}>
              <IconComponent className={`${classes.iconInner} text-white`} />
            </div>
            
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className={`font-semibold truncate ${classes.title}`}>
                  {workspace.name}
                </h3>
                {isActive && (
                  <Badge variant="default" className="text-xs">
                    <Check className="h-3 w-3 mr-1" />
                    Active
                  </Badge>
                )}
              </div>
              
              {workspace.description && (
                <p className={`text-muted-foreground truncate mt-0.5 ${classes.desc}`}>
                  {workspace.description}
                </p>
              )}
              
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="secondary" className="text-xs">
                  {workspace.pageIds.length} pages
                </Badge>
              </div>
            </div>
            
            {/* Actions */}
            {showActions && (onEdit || onDuplicate || onDelete) && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {onEdit && (
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onEdit(); }}>
                      <Pencil className="h-4 w-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                  )}
                  {onDuplicate && (
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onDuplicate(); }}>
                      <Copy className="h-4 w-4 mr-2" />
                      Duplicate
                    </DropdownMenuItem>
                  )}
                  {onDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); setShowDeleteDialog(true); }}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Delete confirmation dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete "{workspace.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your custom workspace.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

/**
 * Create New Workspace Card
 * Placeholder card for creating a new workspace
 */
interface CreateWorkspaceCardProps {
  onClick: () => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function CreateWorkspaceCard({ onClick, disabled, size = 'md' }: CreateWorkspaceCardProps) {
  const sizeClasses = {
    sm: { card: 'p-3', icon: 'w-10 h-10', iconInner: 'h-5 w-5', text: 'text-sm' },
    md: { card: 'p-4', icon: 'w-12 h-12', iconInner: 'h-6 w-6', text: 'text-base' },
    lg: { card: 'p-6', icon: 'w-16 h-16', iconInner: 'h-8 w-8', text: 'text-lg' },
  };
  
  const classes = sizeClasses[size];
  
  return (
    <Card 
      className={`cursor-pointer transition-all border-dashed border-2 hover:border-primary hover:bg-muted/50
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={disabled ? undefined : onClick}
    >
      <CardContent className={classes.card}>
        <div className="flex items-center gap-3">
          <div className={`${classes.icon} rounded-xl bg-muted flex items-center justify-center`}>
            <Plus className={`${classes.iconInner} text-muted-foreground`} />
          </div>
          <div>
            <h3 className={`font-semibold ${classes.text}`}>Create New</h3>
            <p className="text-muted-foreground text-sm">Custom workspace</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default WorkspaceCard;
