/**
 * Entity Context Menu Component
 * Provides common actions for breeding entities (germplasm, trials, studies, etc.)
 * Supports right-click and long-press on mobile
 */

import { ReactNode, useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuShortcut,
  ContextMenuLabel,
} from '@/components/ui/context-menu';
import {
  Eye,
  Pencil,
  Copy,
  Trash2,
  Star,
  StarOff,
  Share2,
  Download,
  ExternalLink,
  FolderPlus,
  Tag,
  History,
  MoreHorizontal,
  Clipboard,
  QrCode,
  FileText,
  GitBranch,
  Beaker,
  Leaf,
} from 'lucide-react';

type EntityType = 
  | 'germplasm' 
  | 'trial' 
  | 'study' 
  | 'program' 
  | 'location' 
  | 'seedlot' 
  | 'cross' 
  | 'observation'
  | 'sample'
  | 'accession';

interface EntityAction {
  id: string;
  label: string;
  icon: ReactNode;
  shortcut?: string;
  onClick: () => void;
  disabled?: boolean;
  destructive?: boolean;
}

interface EntityContextMenuProps {
  children: ReactNode;
  entityType: EntityType;
  entityId: string;
  entityName?: string;
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onClone?: () => void;
  onFavorite?: (isFavorite: boolean) => void;
  onExport?: (format: 'json' | 'csv' | 'pdf') => void;
  onAddToList?: (listId: string) => void;
  onShare?: () => void;
  isFavorite?: boolean;
  customActions?: EntityAction[];
  disabled?: boolean;
}

export function EntityContextMenu({
  children,
  entityType,
  entityId,
  entityName,
  onView,
  onEdit,
  onDelete,
  onClone,
  onFavorite,
  onExport,
  onAddToList,
  onShare,
  isFavorite = false,
  customActions = [],
  disabled = false,
}: EntityContextMenuProps) {
  const navigate = useNavigate();
  const [longPressTimer, setLongPressTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);

  // Get entity-specific route
  const getEntityRoute = (action: 'view' | 'edit') => {
    const routes: Record<EntityType, string> = {
      germplasm: '/germplasm',
      trial: '/trials',
      study: '/studies',
      program: '/programs',
      location: '/locations',
      seedlot: '/seedlots',
      cross: '/crosses',
      observation: '/observations',
      sample: '/samples',
      accession: '/seed-bank/accessions',
    };
    const base = routes[entityType] || '';
    return action === 'edit' ? `${base}/${entityId}/edit` : `${base}/${entityId}`;
  };

  // Default handlers
  const handleView = () => {
    if (onView) {
      onView();
    } else {
      navigate(getEntityRoute('view'));
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit();
    } else {
      navigate(getEntityRoute('edit'));
    }
  };

  const handleCopyId = () => {
    navigator.clipboard.writeText(entityId);
  };

  const handleCopyLink = () => {
    const url = `${window.location.origin}${getEntityRoute('view')}`;
    navigator.clipboard.writeText(url);
  };

  // Long press handling for mobile
  const handleTouchStart = () => {
    const timer = setTimeout(() => {
      setShowMobileMenu(true);
    }, 500);
    setLongPressTimer(timer);
  };

  const handleTouchEnd = () => {
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }
  };

  // Get entity-specific actions
  const getEntitySpecificActions = (): EntityAction[] => {
    const actions: EntityAction[] = [];

    switch (entityType) {
      case 'germplasm':
        actions.push({
          id: 'pedigree',
          label: 'View Pedigree',
          icon: <GitBranch className="h-4 w-4" />,
          onClick: () => navigate(`/pedigree?germplasmId=${entityId}`),
        });
        actions.push({
          id: 'create-cross',
          label: 'Create Cross',
          icon: <Leaf className="h-4 w-4" />,
          onClick: () => navigate(`/crosses/new?parent=${entityId}`),
        });
        break;
      case 'trial':
      case 'study':
        actions.push({
          id: 'collect-data',
          label: 'Collect Data',
          icon: <Beaker className="h-4 w-4" />,
          onClick: () => navigate(`/observations/collect?studyId=${entityId}`),
        });
        break;
      case 'seedlot':
        actions.push({
          id: 'print-label',
          label: 'Print Label',
          icon: <QrCode className="h-4 w-4" />,
          onClick: () => navigate(`/labels?seedlotId=${entityId}`),
        });
        break;
      case 'accession':
        actions.push({
          id: 'viability-test',
          label: 'Schedule Viability Test',
          icon: <Beaker className="h-4 w-4" />,
          onClick: () => navigate(`/seed-bank/viability?accessionId=${entityId}`),
        });
        break;
    }

    return actions;
  };

  const entitySpecificActions = getEntitySpecificActions();

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <ContextMenu>
      <div
        ref={triggerRef}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={handleTouchEnd}
        className="contents"
      >
        <ContextMenu>
          <ContextMenu>
            {children}
          </ContextMenu>
        </ContextMenu>
      </div>
      <ContextMenuContent className="w-56">
        {entityName && (
          <>
            <ContextMenuLabel className="truncate">{entityName}</ContextMenuLabel>
            <ContextMenuSeparator />
          </>
        )}

        {/* Primary Actions */}
        <ContextMenuItem onClick={handleView}>
          <Eye className="h-4 w-4 mr-2" />
          View Details
          <ContextMenuShortcut>⌘O</ContextMenuShortcut>
        </ContextMenuItem>
        
        <ContextMenuItem onClick={handleEdit}>
          <Pencil className="h-4 w-4 mr-2" />
          Edit
          <ContextMenuShortcut>⌘E</ContextMenuShortcut>
        </ContextMenuItem>

        {onClone && (
          <ContextMenuItem onClick={onClone}>
            <Copy className="h-4 w-4 mr-2" />
            Duplicate
            <ContextMenuShortcut>⌘D</ContextMenuShortcut>
          </ContextMenuItem>
        )}

        <ContextMenuSeparator />

        {/* Entity-specific actions */}
        {entitySpecificActions.length > 0 && (
          <>
            {entitySpecificActions.map(action => (
              <ContextMenuItem key={action.id} onClick={action.onClick} disabled={action.disabled}>
                {action.icon}
                <span className="ml-2">{action.label}</span>
                {action.shortcut && <ContextMenuShortcut>{action.shortcut}</ContextMenuShortcut>}
              </ContextMenuItem>
            ))}
            <ContextMenuSeparator />
          </>
        )}

        {/* Custom actions */}
        {customActions.length > 0 && (
          <>
            {customActions.map(action => (
              <ContextMenuItem 
                key={action.id} 
                onClick={action.onClick} 
                disabled={action.disabled}
                className={action.destructive ? 'text-red-600' : ''}
              >
                {action.icon}
                <span className="ml-2">{action.label}</span>
                {action.shortcut && <ContextMenuShortcut>{action.shortcut}</ContextMenuShortcut>}
              </ContextMenuItem>
            ))}
            <ContextMenuSeparator />
          </>
        )}

        {/* Favorite */}
        {onFavorite && (
          <ContextMenuItem onClick={() => onFavorite(!isFavorite)}>
            {isFavorite ? (
              <>
                <StarOff className="h-4 w-4 mr-2" />
                Remove from Favorites
              </>
            ) : (
              <>
                <Star className="h-4 w-4 mr-2" />
                Add to Favorites
              </>
            )}
          </ContextMenuItem>
        )}

        {/* Add to List */}
        {onAddToList && (
          <ContextMenuSub>
            <ContextMenuSubTrigger>
              <FolderPlus className="h-4 w-4 mr-2" />
              Add to List
            </ContextMenuSubTrigger>
            <ContextMenuSubContent>
              <ContextMenuItem onClick={() => onAddToList('new')}>
                <FolderPlus className="h-4 w-4 mr-2" />
                Create New List
              </ContextMenuItem>
              <ContextMenuSeparator />
              <ContextMenuItem onClick={() => onAddToList('favorites')}>
                Favorites
              </ContextMenuItem>
              <ContextMenuItem onClick={() => onAddToList('selection')}>
                Selection Candidates
              </ContextMenuItem>
              <ContextMenuItem onClick={() => onAddToList('review')}>
                For Review
              </ContextMenuItem>
            </ContextMenuSubContent>
          </ContextMenuSub>
        )}

        <ContextMenuSeparator />

        {/* Copy submenu */}
        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <Clipboard className="h-4 w-4 mr-2" />
            Copy
          </ContextMenuSubTrigger>
          <ContextMenuSubContent>
            <ContextMenuItem onClick={handleCopyId}>
              Copy ID
            </ContextMenuItem>
            <ContextMenuItem onClick={handleCopyLink}>
              Copy Link
            </ContextMenuItem>
            {entityName && (
              <ContextMenuItem onClick={() => navigator.clipboard.writeText(entityName)}>
                Copy Name
              </ContextMenuItem>
            )}
          </ContextMenuSubContent>
        </ContextMenuSub>

        {/* Export submenu */}
        {onExport && (
          <ContextMenuSub>
            <ContextMenuSubTrigger>
              <Download className="h-4 w-4 mr-2" />
              Export
            </ContextMenuSubTrigger>
            <ContextMenuSubContent>
              <ContextMenuItem onClick={() => onExport('json')}>
                <FileText className="h-4 w-4 mr-2" />
                JSON
              </ContextMenuItem>
              <ContextMenuItem onClick={() => onExport('csv')}>
                <FileText className="h-4 w-4 mr-2" />
                CSV
              </ContextMenuItem>
              <ContextMenuItem onClick={() => onExport('pdf')}>
                <FileText className="h-4 w-4 mr-2" />
                PDF Report
              </ContextMenuItem>
            </ContextMenuSubContent>
          </ContextMenuSub>
        )}

        {/* Share */}
        {onShare && (
          <ContextMenuItem onClick={onShare}>
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </ContextMenuItem>
        )}

        {/* History */}
        <ContextMenuItem onClick={() => navigate(`/activity?entityId=${entityId}`)}>
          <History className="h-4 w-4 mr-2" />
          View History
        </ContextMenuItem>

        {/* Delete */}
        {onDelete && (
          <>
            <ContextMenuSeparator />
            <ContextMenuItem onClick={onDelete} className="text-red-600">
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
              <ContextMenuShortcut>⌘⌫</ContextMenuShortcut>
            </ContextMenuItem>
          </>
        )}
      </ContextMenuContent>
    </ContextMenu>
  );
}

export default EntityContextMenu;
