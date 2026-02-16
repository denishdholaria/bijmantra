import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import {
  BookOpen,
  Search,
  Database,
  Table,
  Key,
  Link,
  FileText,
  Download,
  ChevronRight,
  Hash,
  Type,
  Calendar,
  ToggleLeft
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

export function DataDictionary() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEntity, setSelectedEntity] = useState('germplasm')

  // Fetch entities list
  const { data: entitiesData } = useQuery({
    queryKey: ['data-dictionary-entities'],
    queryFn: () => apiClient.dataDictionaryService.getEntities(),
  })

  // Fetch selected entity details
  const { data: entityData, isLoading: entityLoading } = useQuery({
    queryKey: ['data-dictionary-entity', selectedEntity],
    queryFn: () => apiClient.dataDictionaryService.getEntity(selectedEntity),
    enabled: !!selectedEntity,
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['data-dictionary-stats'],
    queryFn: () => apiClient.dataDictionaryService.getStats(),
  })

  const entities = entitiesData?.data || []
  const currentEntity = entityData?.data
  const stats = statsData?.data || { total_entities: 0, total_fields: 0, total_relationships: 0 }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'string': return <Type className="h-4 w-4 text-blue-500" />
      case 'integer': case 'number': return <Hash className="h-4 w-4 text-green-500" />
      case 'date': case 'datetime': return <Calendar className="h-4 w-4 text-purple-500" />
      case 'boolean': return <ToggleLeft className="h-4 w-4 text-orange-500" />
      default: return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const filteredFields = currentEntity?.fields?.filter((f: any) =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const handleExport = async () => {
    try {
      const response = await apiClient.dataDictionaryService.exportDictionary('json')
      const data = response.data
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'data-dictionary.json'
      a.click()
      toast.success('Dictionary exported')
    } catch {
      toast.error('Export failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BookOpen className="h-8 w-8 text-primary" />
            Data Dictionary
          </h1>
          <p className="text-muted-foreground mt-1">Complete reference for all data entities and fields</p>
        </div>
        <Button variant="outline" onClick={handleExport}><Download className="h-4 w-4 mr-2" />Export Documentation</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Database className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_entities}</div>
                <div className="text-sm text-muted-foreground">Entities</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg"><Table className="h-5 w-5 text-green-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_fields}</div>
                <div className="text-sm text-muted-foreground">Fields</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg"><Link className="h-5 w-5 text-purple-600" /></div>
              <div>
                <div className="text-2xl font-bold">{stats.total_relationships}</div>
                <div className="text-sm text-muted-foreground">Relationships</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg"><Key className="h-5 w-5 text-yellow-600" /></div>
              <div>
                <div className="text-2xl font-bold">BrAPI 2.1</div>
                <div className="text-sm text-muted-foreground">Compliant</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Entity List */}
        <Card>
          <CardHeader>
            <CardTitle>Entities</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[500px]">
              <div className="space-y-1 p-2">
                {entities.map((entity: any) => (
                  <div key={entity.id} className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${selectedEntity === entity.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`} onClick={() => setSelectedEntity(entity.id)}>
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      <span className="font-medium">{entity.name}</span>
                    </div>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Entity Details */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{currentEntity?.name || 'Select an entity'}</CardTitle>
                <CardDescription>{currentEntity?.description}</CardDescription>
              </div>
              <div className="flex gap-2">
                {currentEntity?.relationships?.map((rel: string, i: number) => (
                  <Badge key={i} variant="outline" className="cursor-pointer hover:bg-primary hover:text-primary-foreground">{rel}</Badge>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search fields..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
            </div>

            {entityLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="text-left p-3">Field Name</th>
                      <th className="text-left p-3">Type</th>
                      <th className="text-left p-3">Description</th>
                      <th className="text-left p-3">Required</th>
                      <th className="text-left p-3">Example</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFields.map((field: any, i: number) => (
                      <tr key={i} className="border-t hover:bg-muted/50">
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <code className="text-sm bg-muted px-2 py-1 rounded">{field.name}</code>
                            {field.brapi_field && <Badge variant="secondary" className="text-xs">BrAPI</Badge>}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(field.type)}
                            <span>{field.type}</span>
                          </div>
                        </td>
                        <td className="p-3 text-muted-foreground">{field.description}</td>
                        <td className="p-3">
                          {field.required ? <Badge variant="destructive">Required</Badge> : <Badge variant="outline">Optional</Badge>}
                        </td>
                        <td className="p-3">
                          <code className="text-xs bg-muted px-2 py-1 rounded">{field.example}</code>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
