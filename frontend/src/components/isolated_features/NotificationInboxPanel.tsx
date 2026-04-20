import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  CheckCheck,
  Trash2,
  X,
  Info,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Search,
  MoreVertical,
  Clock,
  ExternalLink
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  useNotifications,
  Notification,
  NotificationType
} from '@/components/notifications/NotificationSystem';
import { LEGACY_REEVU_NOTIFICATION_TYPE } from '@/lib/legacyReevu';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface NotificationInboxPanelProps {
  className?: string;
  onClose?: () => void;
}

export const NotificationInboxPanel: React.FC<NotificationInboxPanelProps> = ({
  className,
  onClose
}) => {
  const {
    notifications,
    markAsRead,
    markAllAsRead,
    clearNotification,
    unreadCount
  } = useNotifications();

  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Filtering logic
  const filteredNotifications = useMemo(() => {
    return notifications.filter(n => {
      // Tab filtering
      if (activeTab === 'unread' && n.read) return false;
      if (activeTab === 'reevu' && n.type !== LEGACY_REEVU_NOTIFICATION_TYPE) return false;

      // Search filtering
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          n.title.toLowerCase().includes(query) ||
          n.message.toLowerCase().includes(query) ||
          n.source?.toLowerCase().includes(query)
        );
      }

      return true;
    });
  }, [notifications, activeTab, searchQuery]);

  return (
    <Card className={cn("flex flex-col h-full w-full max-w-md shadow-xl border-border", className)}>
      <CardHeader className="px-4 py-3 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <CardTitle className="text-lg font-bold">Notifications</CardTitle>
          {unreadCount > 0 && (
            <Badge variant="destructive" className="rounded-full px-2 py-0.5 text-[10px]">
              {unreadCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={markAllAsRead}
                  aria-label="Mark all as read"
                >
                  <CheckCheck className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Mark all as read</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <div className="px-4 pb-2">
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search notifications..."
            className="pl-8 h-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 h-8">
            <TabsTrigger value="all" className="text-xs">All</TabsTrigger>
            <TabsTrigger value="unread" className="text-xs">Unread</TabsTrigger>
            <TabsTrigger value="reevu" className="text-xs">REEVU</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <Separator />

      <CardContent className="p-0 flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <AnimatePresence mode="popLayout" initial={false}>
            {filteredNotifications.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-col items-center justify-center h-64 text-muted-foreground p-8 text-center"
              >
                <div className="bg-muted rounded-full p-4 mb-4">
                  <Bell className="h-8 w-8 opacity-20" />
                </div>
                <p className="font-medium">No notifications found</p>
                <p className="text-sm">When you have alerts, they'll appear here.</p>
              </motion.div>
            ) : (
              <div className="flex flex-col">
                {filteredNotifications.map((notification) => (
                  <motion.div
                    key={notification.id}
                    layout
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <NotificationItem
                      notification={notification}
                      onMarkAsRead={() => markAsRead(notification.id)}
                      onDelete={() => clearNotification(notification.id)}
                    />
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>
        </ScrollArea>
      </CardContent>

      <CardFooter className="px-4 py-3 border-t bg-muted/30">
        <Button variant="link" className="w-full text-xs text-muted-foreground hover:text-primary" asChild>
          <a href="/settings/notifications">Notification Settings</a>
        </Button>
      </CardFooter>
    </Card>
  );
};

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: () => void;
  onDelete: () => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete
}) => {
  const config = getTypeConfig(notification.type);

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "group relative flex gap-3 p-4 border-b border-border/50 hover:bg-muted/50 transition-colors cursor-pointer focus-visible:outline-none focus-visible:bg-muted",
        !notification.read && "bg-primary/5 dark:bg-primary/10 border-l-2 border-l-primary",
        !notification.read && notification.type === LEGACY_REEVU_NOTIFICATION_TYPE && "bg-amber-50/50 dark:bg-amber-900/10 border-l-amber-500"
      )}
      onClick={onMarkAsRead}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onMarkAsRead();
        }
      }}
    >
      <div className={cn("mt-0.5 rounded-full p-1.5 shrink-0", config.bgClass)}>
        <config.icon className={cn("h-4 w-4", config.iconClass)} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h4 className={cn(
            "text-sm font-medium leading-none mb-1",
            !notification.read && "font-bold text-foreground"
          )}>
            {notification.title}
          </h4>
          <span className="text-[10px] text-muted-foreground whitespace-nowrap mt-0.5 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {formatTimeAgo(notification.timestamp)}
          </span>
        </div>

        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
          {notification.message}
        </p>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {notification.source && (
              <Badge variant="outline" className="text-[10px] font-normal py-0 px-1.5 h-4">
                {notification.source}
              </Badge>
            )}
            {notification.type === LEGACY_REEVU_NOTIFICATION_TYPE && (
              <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800 text-[10px] font-bold py-0 px-1.5 h-4">
                REEVU INSIGHT
              </Badge>
            )}
          </div>

          {notification.actionUrl && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-[10px] text-primary hover:text-primary-foreground hover:bg-primary"
              asChild
              onClick={(e) => e.stopPropagation()}
            >
              <a href={notification.actionUrl}>
                View <ExternalLink className="ml-1 h-3 w-3" />
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" className="h-7 w-7 rounded-full bg-background/80 backdrop-blur shadow-sm border">
              <MoreVertical className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            {!notification.read && (
              <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onMarkAsRead(); }}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                <span>Read</span>
              </DropdownMenuItem>
            )}
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

// ============================================
// HELPERS
// ============================================

function getTypeConfig(type: NotificationType) {
  switch (type) {
    case 'success':
      return {
        icon: CheckCircle2,
        bgClass: 'bg-green-100 dark:bg-green-900/30',
        iconClass: 'text-green-600 dark:text-green-400'
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        bgClass: 'bg-amber-100 dark:bg-amber-900/30',
        iconClass: 'text-amber-600 dark:text-amber-400'
      };
    case 'error':
      return {
        icon: AlertCircle,
        bgClass: 'bg-red-100 dark:bg-red-900/30',
        iconClass: 'text-red-600 dark:text-red-400'
      };
    case LEGACY_REEVU_NOTIFICATION_TYPE:
      return {
        icon: Sparkles,
        bgClass: 'bg-amber-100 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-700',
        iconClass: 'text-amber-600 dark:text-amber-400 animate-pulse'
      };
    case 'collaboration':
      return {
        icon: Info,
        bgClass: 'bg-purple-100 dark:bg-purple-900/30',
        iconClass: 'text-purple-600 dark:text-purple-400'
      };
    case 'data':
      return {
        icon: Info,
        bgClass: 'bg-blue-100 dark:bg-blue-900/30',
        iconClass: 'text-blue-600 dark:text-blue-400'
      };
    case 'weather':
      return {
        icon: Info,
        bgClass: 'bg-cyan-100 dark:bg-cyan-900/30',
        iconClass: 'text-cyan-600 dark:text-cyan-400'
      };
    default:
      return {
        icon: Info,
        bgClass: 'bg-blue-100 dark:bg-blue-900/30',
        iconClass: 'text-blue-600 dark:text-blue-400'
      };
  }
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return 'now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d`;
  return date.toLocaleDateString();
}
