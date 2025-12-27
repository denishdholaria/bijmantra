/**
 * Study Detail Page
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function StudyDetail() {
  const { studyDbId } = useParams<{ studyDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['study', studyDbId],
    queryFn: () => apiClient.getStudy(studyDbId!),
    enabled: !!studyDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteStudy(studyDbId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      navigate('/studies')
    },
  })

  const study = data?.result

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !study) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold mb-2">Study Not Found</h2>
            <p className="text-muted-foreground mb-6">
              {error instanceof Error ? error.message : 'The study does not exist.'}
            </p>
            <Button asChild><Link to="/studies">← Back to Studies</Link></Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/studies">←</Link>
          </Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{study.studyName}</h1>
            <div className="flex gap-2 mt-1">
              {study.active !== false && <Badge className="bg-green-500">Active</Badge>}
              {study.studyType && <Badge variant="secondary">{study.studyType}</Badge>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild><Link to={`/studies/${studyDbId}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>🗑️ Delete</Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="observations">Observations</TabsTrigger>
          <TabsTrigger value="germplasm">Germplasm</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {study.studyDescription && (
                <Card>
                  <CardHeader><CardTitle>📝 Description</CardTitle></CardHeader>
                  <CardContent>
                    <p className="whitespace-pre-wrap">{study.studyDescription}</p>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader><CardTitle>📅 Timeline</CardTitle></CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Start Date</dt>
                      <dd className="mt-1">{study.startDate || 'Not set'}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">End Date</dt>
                      <dd className="mt-1">{study.endDate || 'Not set'}</dd>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader><CardTitle>Study Info</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <dt className="text-sm font-semibold text-muted-foreground">Study ID</dt>
                    <dd className="font-mono text-sm bg-muted px-2 py-1 rounded mt-1">{study.studyDbId}</dd>
                  </div>
                  {study.trialDbId && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Trial</dt>
                      <dd className="mt-1">
                        <Link to={`/trials/${study.trialDbId}`} className="text-primary hover:underline">
                          {study.trialName || study.trialDbId}
                        </Link>
                      </dd>
                    </div>
                  )}
                  {study.locationDbId && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Location</dt>
                      <dd className="mt-1">
                        <Link to={`/locations/${study.locationDbId}`} className="text-primary hover:underline">
                          {study.locationName || study.locationDbId}
                        </Link>
                      </dd>
                    </div>
                  )}
                  {study.seasons?.length > 0 && (
                    <div>
                      <dt className="text-sm font-semibold text-muted-foreground">Seasons</dt>
                      <dd className="mt-1">{study.seasons.join(', ')}</dd>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle>Quick Actions</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <Button variant="outline" className="w-full">📊 Record Observations</Button>
                  <Button variant="outline" className="w-full">📥 Export Data</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="observations" className="mt-6">
          <Card>
            <CardContent className="p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-2">No Observations Yet</h3>
              <p className="text-muted-foreground mb-4">Start recording phenotypic observations for this study</p>
              <Button>➕ Add Observation</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="germplasm" className="mt-6">
          <Card>
            <CardContent className="p-12 text-center">
              <div className="text-6xl mb-4">🌱</div>
              <h3 className="text-xl font-bold mb-2">No Germplasm Assigned</h3>
              <p className="text-muted-foreground mb-4">Assign germplasm entries to this study</p>
              <Button>➕ Add Germplasm</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Study"
        message={`Are you sure you want to delete "${study.studyName}"?`}
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
