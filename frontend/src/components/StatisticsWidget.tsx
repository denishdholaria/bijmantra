/**
 * Statistics Widget Component
 * Reusable statistics display for dashboards
 */
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface StatItem {
  label: string
  value: number | string
  change?: number
  changeLabel?: string
  icon?: string
  color?: 'default' | 'success' | 'warning' | 'danger'
}

interface StatisticsWidgetProps {
  title: string
  description?: string
  stats: StatItem[]
  isLoading?: boolean
  columns?: 2 | 3 | 4
}

export function StatisticsWidget({ 
  title, 
  description, 
  stats, 
  isLoading = false,
  columns = 4 
}: StatisticsWidgetProps) {
  const getColorClass = (color?: string) => {
    const colors: Record<string, string> = {
      success: 'text-green-600',
      warning: 'text-yellow-600',
      danger: 'text-red-600',
      default: 'text-primary',
    }
    return colors[color || 'default']
  }

  const getChangeColor = (change?: number) => {
    if (!change) return 'text-muted-foreground'
    return change > 0 ? 'text-green-600' : 'text-red-600'
  }

  const gridCols = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-4',
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent>
          <div className={`grid ${gridCols[columns]} gap-4`}>
            {Array.from({ length: columns }).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className={`grid ${gridCols[columns]} gap-4`}>
          {stats.map((stat, index) => (
            <div key={index} className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                {stat.icon && <span className="text-xl">{stat.icon}</span>}
                <span className="text-sm text-muted-foreground">{stat.label}</span>
              </div>
              <div className={`text-2xl font-bold ${getColorClass(stat.color)}`}>
                {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
              </div>
              {stat.change !== undefined && (
                <div className={`text-xs mt-1 ${getChangeColor(stat.change)}`}>
                  {stat.change > 0 ? '↑' : '↓'} {Math.abs(stat.change)}%
                  {stat.changeLabel && ` ${stat.changeLabel}`}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Compact version for inline use
export function StatCard({ 
  label, 
  value, 
  icon, 
  change,
  onClick 
}: StatItem & { onClick?: () => void }) {
  return (
    <Card 
      className={`${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            {change !== undefined && (
              <p className={`text-xs ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {change > 0 ? '+' : ''}{change}%
              </p>
            )}
          </div>
          {icon && <span className="text-3xl opacity-50">{icon}</span>}
        </div>
      </CardContent>
    </Card>
  )
}
