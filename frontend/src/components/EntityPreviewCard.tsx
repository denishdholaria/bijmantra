import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ExternalLink, Copy, Star, StarOff, MoreHorizontal, 
  Eye, Edit, Trash2, Share2, Download, Archive,
  Dna, FlaskConical, MapPin, Leaf, Users, Calendar
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from '@/components/ui/hover-card';
import { cn } from '@/lib/utils';

type EntityType = 
  | 'germplasm' | 'trial' | 'study' | 'program' 
  | 'location' | 'person' | 'seedlot' | 'cross'
  | 'observation' | 'trait' | 'sample';

interface EntityPreviewCardProps {
  id: string;
  type: EntityType;
  name: string;
  subtitle?: string;
  description?: string;
  status?: string;
  statusVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  metadata?: { label: string; value: string }[];
  tags?: string[];
  imageUrl?: string;
  isFavorite?: boolean;
  onFavoriteToggle?: (id: string) => void;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onShare?: (id: string) => void;
  onExport?: (id: string) => void;
  href?: string;
  compact?: boolean;
  showActions?: boolean;
  className?: string;
}

const ENTITY_CONFIG: Record<EntityType, { icon: React.ReactNode; color: string; route: string }> = {
  germplasm: { icon: <Dna className="h-4 w-4" />, color: 'text-green-500', route: '/germplasm' },
  trial: { icon: <FlaskConical className="h-4 w-4" />, color: 'text-blue-500', route: '/trials' },
  study: { icon: <FlaskConical className="h-4 w-4" />, color: 'text-purple-500', route: '/studies' },
  program: { icon: <Leaf className="h-4 w-4" />, color: 'text-emerald-500', route: '/programs' },
  location: { icon: <MapPin className="h-4 w-4" />, color: 'text-red-500', route: '/locations' },
  person: { icon: <Users className="h-4 w-4" />, color: 'text-orange-500', route: '/people' },
  seedlot: { icon: <Leaf className="h-4 w-4" />, color: 'text-amber-500', route: '/seedlots' },
  cross: { icon: <Dna className="h-4 w-4" />, color: 'text-pink-500', route: '/crosses' },
  observation: { icon: <Eye className="h-4 w-4" />, color: 'text-cyan-500', route: '/observations' },
  trait: { icon: <FlaskConical className="h-4 w-4" />, color: 'text-indigo-500', route: '/traits' },
  sample: { icon: <FlaskConical className="h-4 w-4" />, color: 'text-teal-500', route: '/samples' },
};

export function EntityPreviewCard({
  id,
  type,
  name,
  subtitle,
  description,
  status,
  statusVariant = 'secondary',
  metadata = [],
  tags = [],
  imageUrl,
  isFavorite = false,
  onFavoriteToggle,
  onView,
  onEdit,
  onDelete,
  onShare,
  onExport,
  href,
  compact = false,
  showActions = true,
  className,
}: EntityPreviewCardProps) {
  const navigate = useNavigate();
  const config = ENTITY_CONFIG[type];
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    if (onView) {
      onView(id);
    } else if (href) {
      navigate(href);
    } else {
      navigate(`${config.route}/${id}`);
    }
  };

  const copyId = async () => {
    await navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (compact) {
    return (
      <div
        onClick={handleClick}
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg border cursor-pointer',
          'hover:bg-muted/50 transition-colors',
          className
        )}
      >
        <div className={cn('p-2 rounded-lg bg-muted', config.color)}>
          {config.icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{name}</p>
          {subtitle && <p className="text-sm text-muted-foreground truncate">{subtitle}</p>}
        </div>
        {status && <Badge variant={statusVariant}>{status}</Badge>}
        <ExternalLink className="h-4 w-4 text-muted-foreground" />
      </div>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          {/* Avatar/Icon */}
          {imageUrl ? (
            <Avatar className="h-12 w-12">
              <img src={imageUrl} alt={name} className="object-cover" />
              <AvatarFallback>{getInitials(name)}</AvatarFallback>
            </Avatar>
          ) : (
            <div className={cn('p-3 rounded-lg bg-muted', config.color)}>
              {config.icon}
            </div>
          )}

          {/* Title & Subtitle */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 
                className="font-semibold truncate cursor-pointer hover:text-primary"
                onClick={handleClick}
              >
                {name}
              </h3>
              {status && <Badge variant={statusVariant}>{status}</Badge>}
            </div>
            {subtitle && (
              <p className="text-sm text-muted-foreground truncate">{subtitle}</p>
            )}
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="text-xs capitalize">
                {type}
              </Badge>
              <HoverCard>
                <HoverCardTrigger asChild>
                  <button 
                    className="text-xs text-muted-foreground hover:text-foreground font-mono"
                    onClick={(e) => { e.stopPropagation(); copyId(); }}
                  >
                    {copied ? 'Copied!' : id.slice(0, 8)}...
                  </button>
                </HoverCardTrigger>
                <HoverCardContent className="w-auto">
                  <p className="text-xs font-mono">{id}</p>
                  <Button size="sm" variant="ghost" className="mt-2 w-full" onClick={copyId}>
                    <Copy className="h-3 w-3 mr-2" />
                    Copy ID
                  </Button>
                </HoverCardContent>
              </HoverCard>
            </div>
          </div>

          {/* Actions */}
          {showActions && (
            <div className="flex items-center gap-1">
              {onFavoriteToggle && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => { e.stopPropagation(); onFavoriteToggle(id); }}
                  aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                  {isFavorite ? (
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ) : (
                    <StarOff className="h-4 w-4" />
                  )}
                </Button>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" aria-label="More actions">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleClick}>
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </DropdownMenuItem>
                  {onEdit && (
                    <DropdownMenuItem onClick={() => onEdit(id)}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                  )}
                  {onShare && (
                    <DropdownMenuItem onClick={() => onShare(id)}>
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </DropdownMenuItem>
                  )}
                  {onExport && (
                    <DropdownMenuItem onClick={() => onExport(id)}>
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </DropdownMenuItem>
                  )}
                  {onDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        onClick={() => onDelete(id)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0 space-y-3">
        {/* Description */}
        {description && (
          <p className="text-sm text-muted-foreground line-clamp-2">{description}</p>
        )}

        {/* Metadata */}
        {metadata.length > 0 && (
          <div className="grid grid-cols-2 gap-2">
            {metadata.slice(0, 4).map((item, i) => (
              <div key={i} className="text-sm">
                <span className="text-muted-foreground">{item.label}: </span>
                <span className="font-medium">{item.value}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tags.slice(0, 5).map((tag, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {tags.length > 5 && (
              <Badge variant="outline" className="text-xs">
                +{tags.length - 5}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Quick preview on hover
export function EntityPreviewHover({
  children,
  entity,
}: {
  children: React.ReactNode;
  entity: EntityPreviewCardProps;
}) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>{children}</HoverCardTrigger>
      <HoverCardContent className="w-80 p-0">
        <EntityPreviewCard {...entity} showActions={false} />
      </HoverCardContent>
    </HoverCard>
  );
}
