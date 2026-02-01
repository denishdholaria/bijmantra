/**
 * Images Page - Image Management
 * BrAPI v2.1 Phenotyping Module
 */

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { toast } from 'sonner'
import { RefreshCw, Upload, Loader2 } from 'lucide-react'

export function Images() {
  const [page, setPage] = useState(0)
  const [showUpload, setShowUpload] = useState(false)
  const [newImageName, setNewImageName] = useState('')
  const [newImageDesc, setNewImageDesc] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)

  const queryClient = useQueryClient()
  const pageSize = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['images', page],
    queryFn: () => apiClient.imagesService.getImages(page, pageSize),
  })

  const images = data?.result?.data || []
  const totalCount = data?.metadata?.pagination?.totalCount || 0
  const totalPages = Math.ceil(totalCount / pageSize)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      // Auto-fill name if empty
      if (!newImageName) {
        setNewImageName(e.target.files[0].name.split('.')[0])
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !newImageName) {
      toast.error('Please select a file and provide a name')
      return
    }

    try {
      setIsUploading(true)

      // 1. Upload file
      const uploadResp = await apiClient.imagesService.uploadImageFile(selectedFile)
      const imageURL = uploadResp.result.imageURL

      // 2. Create BrAPI Image record
      await apiClient.imagesService.createImage({
        imageName: newImageName,
        description: newImageDesc,
        imageURL: imageURL,
        imageFileName: selectedFile.name,
        imageFileSize: selectedFile.size,
        mimeType: selectedFile.type,
        imageTimeStamp: new Date().toISOString()
      })

      toast.success('Image uploaded successfully')
      setShowUpload(false)
      setNewImageName('')
      setNewImageDesc('')
      setSelectedFile(null)
      queryClient.invalidateQueries({ queryKey: ['images'] })
    } catch (err) {
      console.error(err)
      toast.error('Failed to upload image')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-4 lg:space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold">Images</h1>
          <p className="text-muted-foreground mt-1">Photos and visual documentation</p>
        </div>
        <Dialog open={showUpload} onOpenChange={setShowUpload}>
          <DialogTrigger asChild>
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload Image
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload Image</DialogTitle>
              <DialogDescription>Add a photo to your breeding records</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="imageName">Image Name</Label>
                <Input
                  id="imageName"
                  value={newImageName}
                  onChange={(e) => setNewImageName(e.target.value)}
                  placeholder="e.g., Plot A1 - Week 4"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imageFile">Select Image</Label>
                <Input
                  id="imageFile"
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imageDesc">Description</Label>
                <Textarea
                  id="imageDesc"
                  value={newImageDesc}
                  onChange={(e) => setNewImageDesc(e.target.value)}
                  rows={2}
                  placeholder="Notes about this image..."
                />
              </div>
              <Button
                className="w-full"
                onClick={handleUpload}
                disabled={isUploading || !selectedFile || !newImageName}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
                  </>
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{totalCount}</div>
            <div className="text-sm text-muted-foreground">Total Images</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">-</div>
            <div className="text-sm text-muted-foreground">This Month</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">-</div>
            <div className="text-sm text-muted-foreground">Tagged</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">-</div>
            <div className="text-sm text-muted-foreground">Storage Used</div>
          </CardContent>
        </Card>
      </div>

      {/* Images Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Image Gallery</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              <Skeleton className="aspect-square w-full" />
              <Skeleton className="aspect-square w-full" />
              <Skeleton className="aspect-square w-full" />
              <Skeleton className="aspect-square w-full" />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-red-600 mb-2">Error Loading Images</h3>
              <p className="text-muted-foreground mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
              <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['images'] })}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          ) : images.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-6xl mb-4">📷</div>
              <h3 className="text-xl font-bold mb-2">No Images Yet</h3>
              <p className="text-muted-foreground mb-6">Upload photos to document your breeding activities</p>
              <Button onClick={() => setShowUpload(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload First Image
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {images.map((image: any) => (
                <Card key={image.imageDbId} className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer">
                  <div className="aspect-square bg-muted flex items-center justify-center relative group">
                    {image.imageURL ? (
                      <img src={image.imageURL} alt={image.imageName} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-4xl">📷</span>
                    )}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <Button variant="secondary" size="sm" onClick={() => window.open(image.imageURL, '_blank')}>View</Button>
                    </div>
                  </div>
                  <CardContent className="p-3">
                    <p className="font-medium text-sm truncate" title={image.imageName}>{image.imageName || 'Untitled'}</p>
                    <p className="text-xs text-muted-foreground">{image.imageTimeStamp?.split('T')[0] || '-'}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-muted-foreground">Page {page + 1} of {totalPages}</div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>Previous</Button>
                <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>Next</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
