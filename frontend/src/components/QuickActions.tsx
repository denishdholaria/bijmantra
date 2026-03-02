/**
 * Quick Actions Component
 * Provides quick access to common actions
 */
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface QuickAction {
  label: string
  icon: string
  path: string
  description?: string
  color?: string
}

interface QuickActionsProps {
  title?: string
  actions: QuickAction[]
  columns?: 2 | 3 | 4 | 6
}

export function QuickActions({ 
  title = 'Quick Actions', 
  actions,
  columns = 4 
}: QuickActionsProps) {
  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-4',
    6: 'grid-cols-3 md:grid-cols-6',
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Common tasks and shortcuts</CardDescription>
      </CardHeader>
      <CardContent>
        <div className={`grid ${gridCols[columns]} gap-3`}>
          {actions.map((action, index) => (
            <Button
              key={index}
              variant="outline"
              className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-primary/5"
              asChild
            >
              <Link to={action.path}>
                <span className="text-2xl">{action.icon}</span>
                <span className="text-sm font-medium">{action.label}</span>
                {action.description && (
                  <span className="text-xs text-muted-foreground">{action.description}</span>
                )}
              </Link>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Default quick actions for the dashboard
export const defaultQuickActions: QuickAction[] = [
  { label: 'New Program', icon: '🌾', path: '/programs/new', description: 'Create program' },
  { label: 'Add Germplasm', icon: '🌱', path: '/germplasm/new', description: 'Register entry' },
  { label: 'New Trial', icon: '🧪', path: '/trials/new', description: 'Start trial' },
  { label: 'New Study', icon: '📈', path: '/studies/new', description: 'Create study' },
  { label: 'Add Location', icon: '📍', path: '/locations/new', description: 'Add site' },
  { label: 'New Trait', icon: '🔬', path: '/traits/new', description: 'Define variable' },
  { label: 'Collect Data', icon: '📊', path: '/observations/collect', description: 'Enter data' },
  { label: 'Import Data', icon: '📥', path: '/import-export', description: 'Bulk import' },
  { label: 'New Sample', icon: '🧫', path: '/samples/new', description: 'Register sample' },
  { label: 'Plan Cross', icon: '🔀', path: '/plannedcrosses', description: 'Schedule cross' },
  { label: 'View Reports', icon: '📊', path: '/reports', description: 'Analytics' },
  { label: 'Search', icon: '🔍', path: '/search', description: 'Find anything' },
]

// Genotyping-specific quick actions
export const genotypingQuickActions: QuickAction[] = [
  { label: 'New Sample', icon: '🧫', path: '/samples/new', description: 'Register sample' },
  { label: 'View Variants', icon: '🔀', path: '/variants', description: 'Browse SNPs' },
  { label: 'Allele Matrix', icon: '📐', path: '/allelematrix', description: 'View matrix' },
  { label: 'Manage Plates', icon: '🧪', path: '/plates', description: 'Sample plates' },
  { label: 'Genome Maps', icon: '🗺️', path: '/genomemaps', description: 'View maps' },
  { label: 'Vendor Orders', icon: '📦', path: '/vendororders', description: 'Track orders' },
]

// Breeding-specific quick actions
export const breedingQuickActions: QuickAction[] = [
  { label: 'New Cross', icon: '🧬', path: '/crosses/new', description: 'Make cross' },
  { label: 'Plan Crosses', icon: '📋', path: '/plannedcrosses', description: 'Schedule' },
  { label: 'Projects', icon: '🔀', path: '/crossingprojects', description: 'View projects' },
  { label: 'Seed Lots', icon: '📦', path: '/seedlots', description: 'Inventory' },
  { label: 'Pedigrees', icon: '🌳', path: '/germplasm', description: 'View ancestry' },
  { label: 'Progeny', icon: '🌱', path: '/germplasm', description: 'Track offspring' },
]
