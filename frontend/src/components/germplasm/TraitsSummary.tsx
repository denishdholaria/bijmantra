import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Trait {
  traitName: string
  value: string | number
  unit?: string
  date?: string
}

interface TraitsSummaryProps {
  traits: Trait[]
  isLoading?: boolean
}

export function TraitsSummary({ traits, isLoading }: TraitsSummaryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Top Traits</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4 animate-pulse">
             <div className="h-10 bg-muted rounded" />
             <div className="h-10 bg-muted rounded" />
             <div className="h-10 bg-muted rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!traits?.length) {
    return (
      <Card>
        <CardHeader><CardTitle>Top Traits</CardTitle></CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">No trait data available.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle>Top Traits</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {traits.slice(0, 5).map((trait, i) => (
            <div key={i} className="flex items-center justify-between border-b last:border-0 pb-2 last:pb-0">
              <div>
                <p className="font-medium text-sm">{trait.traitName}</p>
                {trait.date && <p className="text-xs text-muted-foreground">{trait.date}</p>}
              </div>
              <div className="text-right">
                <span className="font-bold">{trait.value}</span>
                {trait.unit && <span className="text-xs text-muted-foreground ml-1">{trait.unit}</span>}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
