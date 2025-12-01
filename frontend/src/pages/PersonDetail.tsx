/**
 * Person Detail Page
 * BrAPI v2.1 Core Module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'

export function PersonDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['person', id],
    queryFn: () => apiClient.getPerson(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deletePerson(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] })
      toast.success('Person deleted')
      navigate('/people')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const person = data?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !person) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">Person Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load person'}</p>
        <Button asChild><Link to="/people">← Back to People</Link></Button>
      </div>
    )
  }

  const fullName = [person.firstName, person.middleName, person.lastName].filter(Boolean).join(' ')

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild><Link to="/people">←</Link></Button>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-3xl">
              {person.firstName?.[0] || person.lastName?.[0] || '👤'}
            </div>
            <div>
              <h1 className="text-2xl lg:text-3xl font-bold">{fullName || 'Unknown'}</h1>
              <p className="text-muted-foreground">{person.userType || 'Contact'}</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/people/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Contact Info */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {person.emailAddress && (
              <div className="flex items-center gap-3">
                <span className="text-xl">📧</span>
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <a href={`mailto:${person.emailAddress}`} className="text-primary hover:underline">{person.emailAddress}</a>
                </div>
              </div>
            )}
            {person.phoneNumber && (
              <div className="flex items-center gap-3">
                <span className="text-xl">📞</span>
                <div>
                  <p className="text-sm text-muted-foreground">Phone</p>
                  <a href={`tel:${person.phoneNumber}`} className="text-primary hover:underline">{person.phoneNumber}</a>
                </div>
              </div>
            )}
            {person.mailingAddress && (
              <div className="flex items-center gap-3">
                <span className="text-xl">📍</span>
                <div>
                  <p className="text-sm text-muted-foreground">Address</p>
                  <p>{person.mailingAddress}</p>
                </div>
              </div>
            )}
            {!person.emailAddress && !person.phoneNumber && !person.mailingAddress && (
              <p className="text-muted-foreground text-center py-4">No contact information available</p>
            )}
          </CardContent>
        </Card>

        {/* Professional Info */}
        <Card>
          <CardHeader>
            <CardTitle>Professional Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {person.userType && (
              <div>
                <p className="text-sm text-muted-foreground">Role</p>
                <Badge variant="outline" className="mt-1">{person.userType}</Badge>
              </div>
            )}
            {person.instituteName && (
              <div>
                <p className="text-sm text-muted-foreground">Institution</p>
                <p className="font-medium">{person.instituteName}</p>
              </div>
            )}
            {person.orcid && (
              <div>
                <p className="text-sm text-muted-foreground">ORCID</p>
                <a href={`https://orcid.org/${person.orcid}`} target="_blank" rel="noopener" className="text-primary hover:underline font-mono">
                  {person.orcid}
                </a>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {person.description && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{person.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Associated Data */}
      <Card>
        <CardHeader>
          <CardTitle>Associated Data</CardTitle>
          <CardDescription>Programs, studies, and observations linked to this person</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-8 text-center text-muted-foreground">
            <div className="text-4xl mb-2">🔗</div>
            <p>Data associations coming soon</p>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Person"
        message="Are you sure you want to delete this person? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
