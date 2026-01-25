/**
 * Program Detail Page
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
import { toast } from 'sonner'

export function ProgramDetail() {
  const { programDbId } = useParams<{ programDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['program', programDbId],
    queryFn: () => apiClient.getProgram(programDbId!),
    enabled: !!programDbId,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteProgram(programDbId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['programs'] })
      navigate('/programs')
    },
  })

  const handleDelete = () => {
    deleteMutation.mutate()
  }

  const program = data?.result

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-64 w-full" />
          </div>
          <div className="space-y-6">
            <Skeleton className="h-48 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !program) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-gray-100 dark:border-slate-700 p-12 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Program Not Found</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {error instanceof Error ? error.message : 'The program you are looking for does not exist.'}
          </p>
          <Link
            to="/programs"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 font-semibold shadow-lg transition-all"
          >
            ← Back to Programs
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild aria-label="Back to programs">
            <Link to="/programs" title="Back to Programs">
              <span className="text-xl">←</span>
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-gray-100">{program.programName}</h1>
            {program.abbreviation && (
              <Badge variant="secondary" className="mt-1">
                {program.abbreviation}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="default" asChild>
            <Link to={`/programs/${programDbId}/edit`}>
              ✏️ Edit
            </Link>
          </Button>
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            🗑️ Delete
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Details Card */}
        <div className="lg:col-span-2 space-y-6">
          {/* Objective */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span>🎯</span>
                Objective
              </CardTitle>
            </CardHeader>
            <CardContent>
              {program.objective ? (
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{program.objective}</p>
              ) : (
                <p className="text-muted-foreground italic">No objective specified</p>
              )}
            </CardContent>
          </Card>

          {/* Additional Info */}
          {program.additionalInfo && Object.keys(program.additionalInfo).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>ℹ️</span>
                  Additional Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-3">
                  {Object.entries(program.additionalInfo).map(([key, value]) => (
                    <div key={key} className="flex flex-col">
                      <dt className="text-sm font-semibold text-muted-foreground">{key}</dt>
                      <dd className="text-gray-900 dark:text-gray-100 mt-1">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Program Info</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-semibold text-muted-foreground">Program ID</dt>
                  <dd className="text-sm text-gray-900 dark:text-gray-100 font-mono mt-1 bg-muted px-2 py-1 rounded">
                    {program.programDbId}
                  </dd>
                </div>
                {program.abbreviation && (
                  <div>
                    <dt className="text-sm font-semibold text-muted-foreground">Abbreviation</dt>
                    <dd className="text-gray-900 dark:text-gray-100 mt-1">{program.abbreviation}</dd>
                  </div>
                )}
                {program.leadPersonDbId && (
                  <div>
                    <dt className="text-sm font-semibold text-muted-foreground">Lead Person</dt>
                    <dd className="text-gray-900 dark:text-gray-100 mt-1">{program.leadPersonDbId}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full" asChild>
                <Link to={`/trials/new?programId=${programDbId}`}>
                  🧪 Create Trial
                </Link>
              </Button>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  const exportData = {
                    program: {
                      id: program.programDbId,
                      name: program.programName,
                      abbreviation: program.abbreviation,
                      objective: program.objective,
                      leadPerson: program.leadPersonName,
                      fundingSource: program.fundingSource,
                      documentationURL: program.documentationURL,
                    },
                    exportDate: new Date().toISOString(),
                    format: 'BrAPI v2.1',
                  };
                  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `program_${program.programDbId}_export.json`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                  toast.success('Program data exported');
                }}
              >
                📥 Export Data
              </Button>
            </CardContent>
          </Card>

          {/* Stats */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Trials</span>
                <span className="text-2xl font-bold text-green-600">0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Studies</span>
                <span className="text-2xl font-bold text-blue-600">0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Observations</span>
                <span className="text-2xl font-bold text-purple-600">0</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="Delete Program"
        message={`Are you sure you want to delete "${program.programName}"? This action cannot be undone.`}
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
