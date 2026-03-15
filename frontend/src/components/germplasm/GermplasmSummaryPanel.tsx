import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, Sprout, Network, Image as ImageIcon } from 'lucide-react'

interface GermplasmSummaryPanelProps {
  germplasm: any
  stats?: {
    trialsCount?: number
    observationsCount?: number
    pedigreeDepth?: number
    imagesCount?: number
  }
}

export function GermplasmSummaryPanel({ germplasm, stats }: GermplasmSummaryPanelProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
          <Sprout className="h-8 w-8 text-green-500" />
          <div className="text-2xl font-bold">{stats?.trialsCount ?? '-'}</div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Trials</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
          <Activity className="h-8 w-8 text-blue-500" />
          <div className="text-2xl font-bold">{stats?.observationsCount ?? '-'}</div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Observations</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
          <Network className="h-8 w-8 text-purple-500" />
          <div className="text-2xl font-bold">{stats?.pedigreeDepth ?? '-'}</div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Pedigree Depth</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6 flex flex-col items-center justify-center text-center space-y-2">
          <ImageIcon className="h-8 w-8 text-orange-500" />
          <div className="text-2xl font-bold">{stats?.imagesCount ?? '-'}</div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Images</p>
        </CardContent>
      </Card>
    </div>
  )
}
