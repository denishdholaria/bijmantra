/**
 * Favorites Panel Component
 *
 * Displays user's pinned/favorite items for quick access.
 */

import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useFavorites, FavoriteItem } from '@/hooks/useFavorites';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Star,
  StarOff,
  Trash2,
  FlaskConical,
  Microscope,
  FileText,
  Leaf,
  Database,
  LayoutDashboard,
  BarChart3,
} from 'lucide-react';

type FavoriteType = 'program' | 'trial' | 'study' | 'germplasm' | 'accession' | 'page' | 'report' | 'division';

const TYPE_ICONS: Record<FavoriteType, React.ElementType> = {
  program: FlaskConical,
  trial: Microscope,
  study: FileText,
  germplasm: Leaf,
  accession: Database,
  page: LayoutDashboard,
  report: BarChart3,
  division: LayoutDashboard,
};

const TYPE_COLORS: Record<FavoriteType, string> = {
  program: 'text-blue-500',
  trial: 'text-green-500',
  study: 'text-purple-500',
  germplasm: 'text-emerald-500',
  accession: 'text-amber-500',
  page: 'text-gray-500',
  report: 'text-indigo-500',
  division: 'text-green-600',
};

interface FavoritesPanelProps {
  className?: string;
  compact?: boolean;
  maxItems?: number;
}

export function FavoritesPanel({
  className,
  compact = false,
  maxItems,
}: FavoritesPanelProps) {
  const { favorites, removeFavorite, clearFavorites, count } = useFavorites();

  const displayItems = maxItems ? favorites.slice(0, maxItems) : favorites;

  if (count === 0) {
    return (
      <Card className={cn('', className)}>
        <CardContent className="p-6 text-center">
          <StarOff className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">No favorites yet</p>
          <p className="text-xs text-muted-foreground mt-1">
            Click the star icon on any item to add it here
          </p>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <div className={cn('space-y-1', className)}>
        {displayItems.map((item) => {
          const itemType = item.type as FavoriteType;
          const Icon = TYPE_ICONS[itemType] as React.ComponentType<{ className?: string }>;
          const iconColor = TYPE_COLORS[itemType];
          return (
            <Link
              key={`${item.type}-${item.id}`}
              to={item.route}
              className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent text-sm"
            >
              <Icon className={cn('h-4 w-4', iconColor)} />
              <span className="truncate">{item.name}</span>
            </Link>
          );
        })}
        {maxItems && count > maxItems && (
          <Link
            to="/favorites"
            className="block text-xs text-muted-foreground hover:text-foreground px-2 py-1"
          >
            +{count - maxItems} more...
          </Link>
        )}
      </div>
    );
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-500" />
            Favorites ({count})
          </CardTitle>
          {count > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFavorites}
              className="h-8 text-xs text-muted-foreground"
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-1">
          {displayItems.map((item) => {
            const itemType = item.type as FavoriteType;
            const Icon = TYPE_ICONS[itemType] as React.ComponentType<{ className?: string }>;
            const iconColor = TYPE_COLORS[itemType];
            return (
              <div
                key={`${item.type}-${item.id}`}
                className="flex items-center gap-2 group"
              >
                <Link
                  to={item.route}
                  className="flex-1 flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent"
                >
                  <Icon className={cn('h-4 w-4', iconColor)} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{item.name}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {item.type}
                    </p>
                  </div>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => removeFavorite(item.id, item.type)}
                >
                  <StarOff className="h-3 w-3" />
                </Button>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default FavoritesPanel;
