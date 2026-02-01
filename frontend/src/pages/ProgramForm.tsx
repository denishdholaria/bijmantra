/**
 * Program Create/Edit Form
 */

import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface ProgramFormData {
  programName: string
  abbreviation: string
  objective: string
}

export function ProgramForm() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProgramFormData>()

  const createMutation = useMutation({
    mutationFn: (data: ProgramFormData) => apiClient.programService.createProgram(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['programs'] })
      navigate('/programs')
    },
  })

  const onSubmit = (data: ProgramFormData) => {
    createMutation.mutate(data)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <CardTitle>Create New Program</CardTitle>
          <CardDescription>Add a new breeding program to your organization</CardDescription>
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
              <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
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
          {createMutation.isError && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg animate-slide-in">
              <p className="text-sm text-red-800 font-medium flex items-center gap-2">
                <span>❌</span>
                {createMutation.error instanceof Error
                  ? createMutation.error.message
                  : 'Failed to create program'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1"
            >
              {createMutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Creating Program...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <span>✓</span>
                  Create Program
                </span>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/programs')}
            >
              Cancel
            </Button>
          </div>
        </form>
        </CardContent>
      </Card>
    </div>
  )
}
