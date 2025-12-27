/**
 * Pedigree Tree Component
 * Visual representation of germplasm ancestry
 */

import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface PedigreeTreeProps {
  germplasmDbId: string
  depth?: number
}

export function PedigreeTree({ germplasmDbId, depth: _depth = 2 }: PedigreeTreeProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pedigree', germplasmDbId],
    queryFn: () => apiClient.getPedigree(germplasmDbId),
    enabled: !!germplasmDbId,
  })

  const pedigree = data?.result

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <div className="flex gap-4">
          <Skeleton className="h-20 w-1/2" />
          <Skeleton className="h-20 w-1/2" />
        </div>
      </div>
    )
  }

  if (error || !pedigree) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <div className="text-4xl mb-2">🌳</div>
        <p>Pedigree information not available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Current Germplasm */}
      <div className="flex justify-center">
        <GermplasmNode 
          germplasmDbId={germplasmDbId}
          germplasmName={pedigree.germplasmName || 'Current'}
          isRoot
        />
      </div>

      {/* Parents */}
      {(pedigree.parent1DbId || pedigree.parent2DbId) && (
        <>
          <div className="flex justify-center">
            <div className="w-px h-8 bg-border" />
          </div>
          <div className="flex justify-center gap-8">
            {pedigree.parent1DbId && (
              <div className="flex flex-col items-center">
                <div className="w-px h-4 bg-border" />
                <GermplasmNode 
                  germplasmDbId={pedigree.parent1DbId}
                  germplasmName={pedigree.parent1Name || 'Parent 1'}
                  parentType="female"
                />
              </div>
            )}
            {pedigree.parent2DbId && (
              <div className="flex flex-col items-center">
                <div className="w-px h-4 bg-border" />
                <GermplasmNode 
                  germplasmDbId={pedigree.parent2DbId}
                  germplasmName={pedigree.parent2Name || 'Parent 2'}
                  parentType="male"
                />
              </div>
            )}
          </div>
        </>
      )}

      {/* Pedigree String */}
      {pedigree.pedigree && (
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground mb-1">Pedigree String</p>
          <p className="font-mono text-sm">{pedigree.pedigree}</p>
        </div>
      )}
    </div>
  )
}

function GermplasmNode({ 
  germplasmDbId, 
  germplasmName, 
  isRoot = false,
  parentType 
}: { 
  germplasmDbId: string
  germplasmName: string
  isRoot?: boolean
  parentType?: 'female' | 'male'
}) {
  return (
    <Link to={`/germplasm/${germplasmDbId}`}>
      <Card className={`w-48 hover:shadow-md transition-shadow cursor-pointer ${
        isRoot ? 'border-primary border-2' : 
        parentType === 'female' ? 'border-pink-300 bg-pink-50/50' :
        parentType === 'male' ? 'border-blue-300 bg-blue-50/50' : ''
      }`}>
        <CardContent className="p-3 text-center">
          <div className="flex items-center justify-center gap-2 mb-1">
            {parentType === 'female' && <span className="text-pink-500">♀</span>}
            {parentType === 'male' && <span className="text-blue-500">♂</span>}
            <span className="text-lg">🌱</span>
          </div>
          <p className="font-medium text-sm truncate">{germplasmName}</p>
          <p className="text-xs text-muted-foreground font-mono truncate">{germplasmDbId}</p>
        </CardContent>
      </Card>
    </Link>
  )
}

export function SimplePedigreeDisplay({ pedigreeString }: { pedigreeString?: string }) {
  if (!pedigreeString) {
    return <span className="text-muted-foreground">No pedigree information</span>
  }

  return (
    <div className="font-mono text-sm bg-muted p-2 rounded">
      {pedigreeString}
    </div>
  )
}
