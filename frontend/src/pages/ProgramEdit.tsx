/**
 * Program Edit Page
 */

import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'

interface ProgramFormData {
  programName: string
  abbreviation: string
  objective: string
}

export function ProgramEdit() {
  const { programDbId } = useParams<{ programDbId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch existing program data
  const { data, isLoading: isLoadingProgram } = useQuery({
    queryKey: ['program', programDbId],
    queryFn: () => apiClient.getProgram(programDbId!),
    enabled: !!programDbId,
  })

  const program = data?.result

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProgramFormData>({
    values: program
      ? {
          programName: program.programName || '',
          abbreviation: program.abbreviation || '',
          objective: program.objective || '',
        }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (data: ProgramFormData) => apiClient.updateProgram(programDbId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['programs'] })
      queryClient.invalidateQueries({ queryKey: ['program', programDbId] })
      navigate(`/programs/${programDbId}`)
    },
  })

  const onSubmit = (data: ProgramFormData) => {
    updateMutation.mutate(data)
  }

  if (isLoadingProgram) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!program) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Program Not Found</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">The program you are trying to edit does not exist.</p>
            <Button asChild>
              <Link to="/programs">← Back to Programs</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild aria-label="Back to program">
              <Link to={`/programs/${programDbId}`} title="Back to Program">
                <span className="text-xl">←</span>
              </Link>
            </Button>
            <div>
              <CardTitle>Edit Program</CardTitle>
              <CardDescription>Update program information</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Program Name */}
          <div className="space-y-2">
            <Label htmlFor="programName">
              Program Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="programName"
              type="text"
              {...register('programName', { required: 'Program name is required' })}
              placeholder="e.g., Wheat Improvement Program"
            />
            {errors.programName && (
              <p className="text-sm text-red-600 flex items-center gap-1">
                <span>⚠️</span>
                {errors.programName.message}
              </p>
            )}
          </div>

          {/* Abbreviation */}
          <div className="space-y-2">
            <Label htmlFor="abbreviation">Abbreviation</Label>
            <Input
              id="abbreviation"
              type="text"
              {...register('abbreviation')}
              placeholder="e.g., WIP"
              maxLength={10}
            />
            <p className="text-xs text-muted-foreground">Short code for quick reference (max 10 characters)</p>
          </div>

          {/* Objective */}
          <div className="space-y-2">
            <Label htmlFor="objective">Objective</Label>
            <Textarea
              id="objective"
              {...register('objective')}
              rows={5}
              placeholder="Describe the program's objectives, goals, and expected outcomes..."
            />
            <p className="text-xs text-muted-foreground">Detailed description of what this program aims to achieve</p>
          </div>

          {/* Error Message */}
          {updateMutation.isError && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
              <p className="text-sm text-red-800 font-medium flex items-center gap-2">
                <span>❌</span>
                {updateMutation.error instanceof Error
                  ? updateMutation.error.message
                  : 'Failed to update program'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={updateMutation.isPending}
              className="flex-1"
            >
              {updateMutation.isPending ? '💾 Saving...' : '💾 Save Changes'}
            </Button>
            <Button variant="outline" asChild>
              <Link to={`/programs/${programDbId}`}>
                Cancel
              </Link>
            </Button>
          </div>
        </form>
        </CardContent>
      </Card>
    </div>
  )
}
