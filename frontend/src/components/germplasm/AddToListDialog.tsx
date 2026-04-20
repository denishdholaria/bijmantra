import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { Loader2, PlusCircle } from 'lucide-react'

interface AddToListDialogProps {
  germplasmDbId: string
  germplasmName: string
  trigger?: React.ReactNode
}

export function AddToListDialog({ germplasmDbId, germplasmName, trigger }: AddToListDialogProps) {
  const [selectedListId, setSelectedListId] = useState<string>('')
  const [open, setOpen] = useState(false)

  const { data: listsData, isLoading: isLoadingLists } = useQuery({
    queryKey: ['lists'],
    queryFn: () => apiClient.listService.getLists(0, 100)
  })

  const addMutation = useMutation({
    mutationFn: async () => {
       const listResponse = await apiClient.listService.getList(selectedListId)
       const list = listResponse.result

       if (!list) throw new Error('List not found')

       if (list.data && list.data.includes(germplasmDbId)) {
         throw new Error('Germplasm already in this list')
       }

       const updatedData = [...(list.data || []), germplasmDbId]

       return apiClient.listService.updateList(selectedListId, {
         ...list,
         data: updatedData
       })
    },
    onSuccess: () => {
      toast.success(`Added ${germplasmName} to list`)
      setOpen(false)
      setSelectedListId('')
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : 'Failed to add to list')
    }
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
            <Button variant="outline" size="sm">
                <PlusCircle className="mr-2 h-4 w-4" />
                Add to List
            </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add to List</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Select List</Label>
            <Select value={selectedListId} onValueChange={setSelectedListId}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a list..." />
              </SelectTrigger>
              <SelectContent>
                {isLoadingLists ? (
                  <div className="flex items-center justify-center p-2"><Loader2 className="animate-spin h-4 w-4" /></div>
                ) : listsData?.result?.data && listsData.result.data.length > 0 ? (
                  listsData.result.data.map((list: any) => (
                    <SelectItem key={list.listDbId} value={list.listDbId}>
                      {list.listName}
                    </SelectItem>
                  ))
                ) : (
                  <div className="p-2 text-sm text-muted-foreground text-center">No lists found</div>
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={() => addMutation.mutate()} disabled={!selectedListId || addMutation.isPending}>
            {addMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Add to List
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
