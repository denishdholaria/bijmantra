/**
 * List Detail Page
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

export function ListDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDelete, setShowDelete] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['list', id],
    queryFn: () => apiClient.getList(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteList(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] })
      toast.success('List deleted')
      navigate('/lists')
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : 'Delete failed'),
  })

  const list = data?.result

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error || !list) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2">List Not Found</h2>
        <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Could not load list'}</p>
        <Button asChild><Link to="/lists">← Back to Lists</Link></Button>
      </div>
    )
  }

  const listTypeColors: Record<string, string> = {
    germplasm: 'bg-green-100 text-green-800',
    studies: 'bg-blue-100 text-blue-800',
    programs: 'bg-purple-100 text-purple-800',
    trials: 'bg-orange-100 text-orange-800',
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild><Link to="/lists">←</Link></Button>
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold">{list.listName}</h1>
            <p className="text-muted-foreground">List</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild><Link to={`/lists/${id}/edit`}>✏️ Edit</Link></Button>
          <Button variant="destructive" onClick={() => setShowDelete(true)}>🗑️ Delete</Button>
        </div>
      </div>

      {/* List Info */}
      <div className="flex items-center gap-4">
        <Badge className={listTypeColors[list.listType] || 'bg-gray-100 text-gray-800'}>
          {list.listType}
        </Badge>
        <span className="text-muted-foreground">{list.listSize || 0} items</span>
        {list.dateCreated && (
          <span className="text-muted-foreground">Created: {list.dateCreated.split('T')[0]}</span>
        )}
      </div>

      {list.listDescription && (
        <Card>
          <CardContent className="p-4">
            <p>{list.listDescription}</p>
          </CardContent>
        </Card>
      )}

      {/* List Items */}
      <Card>
        <CardHeader>
          <CardTitle>List Items</CardTitle>
          <CardDescription>Items in this list</CardDescription>
        </CardHeader>
        <CardContent>
          {list.data && list.data.length > 0 ? (
            <div className="space-y-2">
              {list.data.map((item: string, index: number) => (
                <div key={index} className="p-3 bg-muted rounded-lg flex items-center justify-between">
                  <span className="font-mono text-sm">{item}</span>
                  <Button variant="ghost" size="sm">View</Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              <div className="text-4xl mb-2">📋</div>
              <p>This list is empty</p>
              <Button variant="outline" className="mt-4">+ Add Items</Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button variant="outline">📥 Import Items</Button>
          <Button variant="outline">📤 Export List</Button>
          <Button variant="outline">🔗 Share</Button>
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete List"
        message="Are you sure you want to delete this list? This action cannot be undone."
        confirmText="Delete"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
