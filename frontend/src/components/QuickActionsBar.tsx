import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Download, Upload, Filter, RefreshCw, 
  Camera, Mic, Scan, BarChart3, FileText, Share2,
  Printer, Copy, Trash2, Archive, Star, Bell
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface QuickAction {
  id: string;
  icon: React.ReactNode;
  label: string;
  shortcut?: string;
  onClick: () => void;
  variant?: 'default' | 'primary' | 'destructive';
}

interface QuickActionsBarProps {
  className?: string;
  onSearch?: () => void;
  onAdd?: () => void;
  onExport?: () => void;
  onImport?: () => void;
  onFilter?: () => void;
  onRefresh?: () => void;
  customActions?: QuickAction[];
}

// Page-specific action configurations
const PAGE_ACTIONS: Record<string, QuickAction[]> = {
  '/germplasm': [
    { id: 'add', icon: <Plus className="h-4 w-4" />, label: 'Add Germplasm', shortcut: '⌘N', onClick: () => {}, variant: 'primary' },
    { id: 'scan', icon: <Scan className="h-4 w-4" />, label: 'Scan Barcode', shortcut: '⌘B', onClick: () => {} },
    { id: 'import', icon: <Upload className="h-4 w-4" />, label: 'Import', shortcut: '⌘I', onClick: () => {} },
  ],
  '/trials': [
    { id: 'add', icon: <Plus className="h-4 w-4" />, label: 'New Trial', shortcut: '⌘N', onClick: () => {}, variant: 'primary' },
    { id: 'design', icon: <BarChart3 className="h-4 w-4" />, label: 'Design Trial', onClick: () => {} },
    { id: 'report', icon: <FileText className="h-4 w-4" />, label: 'Generate Report', onClick: () => {} },
  ],
  '/observations': [
    { id: 'collect', icon: <Plus className="h-4 w-4" />, label: 'Collect Data', shortcut: '⌘N', onClick: () => {}, variant: 'primary' },
    { id: 'camera', icon: <Camera className="h-4 w-4" />, label: 'Capture Image', shortcut: '⌘P', onClick: () => {} },
    { id: 'voice', icon: <Mic className="h-4 w-4" />, label: 'Voice Entry', shortcut: '⌘M', onClick: () => {} },
  ],
  '/plant-vision': [
    { id: 'capture', icon: <Camera className="h-4 w-4" />, label: 'Capture', shortcut: '⌘P', onClick: () => {}, variant: 'primary' },
    { id: 'upload', icon: <Upload className="h-4 w-4" />, label: 'Upload Image', onClick: () => {} },
    { id: 'history', icon: <RefreshCw className="h-4 w-4" />, label: 'View History', onClick: () => {} },
  ],
  '/seed-operations': [
    { id: 'sample', icon: <Plus className="h-4 w-4" />, label: 'Register Sample', onClick: () => {}, variant: 'primary' },
    { id: 'scan', icon: <Scan className="h-4 w-4" />, label: 'Quality Gate', onClick: () => {} },
    { id: 'dispatch', icon: <Share2 className="h-4 w-4" />, label: 'Create Dispatch', onClick: () => {} },
  ],
};

// Default actions available on all pages
const DEFAULT_ACTIONS: QuickAction[] = [
  { id: 'search', icon: <Search className="h-4 w-4" />, label: 'Search', shortcut: '⌘K', onClick: () => {} },
  { id: 'filter', icon: <Filter className="h-4 w-4" />, label: 'Filter', shortcut: '⌘F', onClick: () => {} },
  { id: 'refresh', icon: <RefreshCw className="h-4 w-4" />, label: 'Refresh', shortcut: '⌘R', onClick: () => {} },
  { id: 'export', icon: <Download className="h-4 w-4" />, label: 'Export', shortcut: '⌘E', onClick: () => {} },
];

export function QuickActionsBar({
  className,
  onSearch,
  onAdd,
  onExport,
  onImport,
  onFilter,
  onRefresh,
  customActions = [],
}: QuickActionsBarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [pageActions, setPageActions] = useState<QuickAction[]>([]);

  // Get page-specific actions
  useEffect(() => {
    const path = location.pathname;
    
    // Find matching page actions
    let actions: QuickAction[] = [];
    for (const [pattern, pageActs] of Object.entries(PAGE_ACTIONS)) {
      if (path.startsWith(pattern)) {
        actions = pageActs;
        break;
      }
    }

    // Bind navigation handlers
    actions = actions.map(action => ({
      ...action,
      onClick: () => {
        if (action.id === 'add' && onAdd) {
          onAdd();
        } else if (path === '/germplasm' && action.id === 'add') {
          navigate('/germplasm/new');
        } else if (path === '/trials' && action.id === 'add') {
          navigate('/trials/new');
        } else if (path === '/observations' && action.id === 'collect') {
          navigate('/observations/collect');
        }
      },
    }));

    setPageActions(actions);
  }, [location.pathname, navigate, onAdd]);

  // Combine all actions
  const allActions = [
    ...pageActions,
    ...customActions,
    ...DEFAULT_ACTIONS.map(action => ({
      ...action,
      onClick: () => {
        if (action.id === 'search' && onSearch) onSearch();
        else if (action.id === 'filter' && onFilter) onFilter();
        else if (action.id === 'refresh' && onRefresh) onRefresh();
        else if (action.id === 'export' && onExport) onExport();
      },
    })),
  ];

  // Remove duplicates by id
  const uniqueActions = allActions.filter(
    (action, index, self) => index === self.findIndex(a => a.id === action.id)
  );

  return (
    <TooltipProvider>
      <div className={cn(
        'flex items-center gap-1 p-1 bg-muted/50 rounded-lg border',
        className
      )}>
        {uniqueActions.map((action, index) => (
          <div key={action.id} className="flex items-center">
            {/* Separator between page actions and default actions */}
            {index === pageActions.length && pageActions.length > 0 && (
              <div className="w-px h-6 bg-border mx-1" />
            )}
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={action.variant === 'primary' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={action.onClick}
                  className={cn(
                    'h-8 px-2',
                    action.variant === 'primary' && 'bg-primary text-primary-foreground'
                  )}
                >
                  {action.icon}
                  {action.variant === 'primary' && (
                    <span className="ml-1.5 hidden sm:inline">{action.label}</span>
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <div className="flex items-center gap-2">
                  <span>{action.label}</span>
                  {action.shortcut && (
                    <kbd className="px-1.5 py-0.5 text-xs bg-muted rounded">
                      {action.shortcut}
                    </kbd>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}

// Floating variant for mobile
export function FloatingQuickActions({ className }: { className?: string }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const actions = [
    { id: 'add', icon: <Plus className="h-5 w-5" />, label: 'Add', primary: true },
    { id: 'camera', icon: <Camera className="h-5 w-5" />, label: 'Camera' },
    { id: 'voice', icon: <Mic className="h-5 w-5" />, label: 'Voice' },
    { id: 'scan', icon: <Scan className="h-5 w-5" />, label: 'Scan' },
  ];

  return (
    <div className={cn('fixed bottom-20 right-4 z-50', className)}>
      {/* Expanded actions */}
      {isExpanded && (
        <div className="absolute bottom-16 right-0 flex flex-col gap-2 mb-2">
          {actions.slice(1).map((action) => (
            <Button
              key={action.id}
              size="icon"
              variant="secondary"
              className="h-12 w-12 rounded-full shadow-lg"
              onClick={() => {
                setIsExpanded(false);
                // Handle action
              }}
            >
              {action.icon}
            </Button>
          ))}
        </div>
      )}

      {/* Main FAB */}
      <Button
        size="icon"
        className={cn(
          'h-14 w-14 rounded-full shadow-lg transition-transform',
          isExpanded && 'rotate-45'
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Plus className="h-6 w-6" />
      </Button>
    </div>
  );
}
