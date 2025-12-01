/**
 * Activity Feed Component
 * Shows recent activity across the system
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

interface ActivityItem {
  id: string
  type: 'program' | 'germplasm' | 'trial' | 'study' | 'observation' | 'cross'
  action: 'created' | 'updated' | 'deleted'
  name: string
  timestamp: string
  path: string
}

export function ActivityFeed() {
  // Fetch recent data from various endpoints
  const { data: programsData, isLoading: loadingPrograms } = useQuery({
    queryKey: ['programs-recent'],
    queryFn: () => apiClient.getPrograms(0, 5),
  })

  const { data: germplasmData, isLoading: loadingGermplasm } = useQuery({
    queryKey: ['germplasm-recent'],
    queryFn: () => apiClient.getGermplasm(0, 5),
  })

  const { data: trialsData, isLoading: loadingTrials } = useQuery({
    queryKey: ['trials-recent'],
    queryFn: () => apiClient.getTrials(0, 5),
  })

  const isLoading = loadingPrograms || loadingGermplasm || loadingTrials

  // Combine and sort activities
  const activities: ActivityItem[] = [
    ...(programsData?.result?.data || []).map((p: any) => ({
      id: p.programDbId,
      type: 'program' as const,
      action: 'created' as const,
      name: p.programName,
      timestamp: p.createdDate || new Date().toISOString(),
      path: `/programs/${p.programDbId}`,
    })),
    ...(germplasmData?.result?.data || []).map((g: any) => ({
      id: g.germplasmDbId,
      type: 'germplasm' as const,
      action: 'created' as const,
      name: g.germplasmName,
      timestamp: g.acquisitionDate || new Date().toISOString(),
      path: `/germplasm/${g.germplasmDbId}`,
    })),
    ...(trialsData?.result?.data || []).map((t: any) => ({
      id: t.trialDbId,
      type: 'trial' as const,
      action: 'created' as const,
      name: t.trialName,
      timestamp: t.startDate || new Date().toISOString(),
      path: `/trials/${t.trialDbId}`,
    })),
  ].slice(0, 10)

  const typeIcons: Record<string, string> = {
    program: '🌾',
    germplasm: '🌱',
    trial: '🧪',
    study: '📈',
    observation: '📋',
    cross: '🧬',
  }

  const typeColors: Record<string, string> = {
    program: 'bg-purple-100 text-purple-800',
    germplasm: 'bg-green-100 text-green-800',
    trial: 'bg-blue-100 text-blue-800',
    study: 'bg-orange-100 text-orange-800',
    observation: 'bg-pink-100 text-pink-800',
    cross: 'bg-cyan-100 text-cyan-800',
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <div className="text-4xl mb-2">📋</div>
            <p>No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <Link
                key={`${activity.type}-${activity.id}`}
                to={activity.path}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <span className="text-2xl">{typeIcons[activity.type]}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{activity.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {activity.timestamp?.split('T')[0] || 'Recently'}
                  </p>
                </div>
                <Badge className={typeColors[activity.type]}>
                  {activity.type}
                </Badge>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function CompactActivityFeed({ limit = 5 }: { limit?: number }) {
  const { data: programsData } = useQuery({
    queryKey: ['programs-compact'],
    queryFn: () => apiClient.getPrograms(0, limit),
  })

  const programs = programsData?.result?.data || []

  return (
    <div className="space-y-2">
      {programs.slice(0, limit).map((p: any) => (
        <Link
          key={p.programDbId}
          to={`/programs/${p.programDbId}`}
          className="flex items-center gap-2 p-2 rounded hover:bg-muted/50 text-sm"
        >
          <span>🌾</span>
          <span className="truncate">{p.programName}</span>
        </Link>
      ))}
    </div>
  )
}
