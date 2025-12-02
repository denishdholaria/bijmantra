import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  BookOpen,
  Search,
  Database,
  Table,
  Key,
  Link,
  FileText,
  Download,
  Filter,
  ChevronRight,
  Hash,
  Type,
  Calendar,
  ToggleLeft
} from 'lucide-react'

interface DataField {
  name: string
  type: string
  description: string
  required: boolean
  example: string
  brapiField?: string
}

interface DataEntity {
  name: string
  description: string
  fields: DataField[]
  relationships: string[]
}

export function DataDictionary() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEntity, setSelectedEntity] = useState('germplasm')

  const entities: Record<string, DataEntity> = {
    germplasm: {
      name: 'Germplasm',
      description: 'Genetic material used in breeding programs',
      fields: [
        { name: 'germplasmDbId', type: 'string', description: 'Unique identifier for germplasm', required: true, example: 'GERM001', brapiField: 'germplasmDbId' },
        { name: 'germplasmName', type: 'string', description: 'Human readable name', required: true, example: 'IR64', brapiField: 'germplasmName' },
        { name: 'accessionNumber', type: 'string', description: 'Accession number from genebank', required: false, example: 'ACC-2024-001', brapiField: 'accessionNumber' },
        { name: 'pedigree', type: 'string', description: 'Pedigree string', required: false, example: 'IR5657/IR2061', brapiField: 'pedigree' },
        { name: 'seedSource', type: 'string', description: 'Source of seed material', required: false, example: 'IRRI Genebank', brapiField: 'seedSource' },
        { name: 'biologicalStatusOfAccessionCode', type: 'integer', description: 'MCPD biological status code', required: false, example: '300', brapiField: 'biologicalStatusOfAccessionCode' },
        { name: 'countryOfOriginCode', type: 'string', description: 'ISO 3166-1 alpha-3 country code', required: false, example: 'PHL', brapiField: 'countryOfOriginCode' }
      ],
      relationships: ['Crosses', 'Observations', 'SeedLots', 'Pedigree']
    },
    trial: {
      name: 'Trial',
      description: 'A breeding trial or experiment',
      fields: [
        { name: 'trialDbId', type: 'string', description: 'Unique identifier for trial', required: true, example: 'TRIAL001', brapiField: 'trialDbId' },
        { name: 'trialName', type: 'string', description: 'Human readable name', required: true, example: 'Yield Trial 2024', brapiField: 'trialName' },
        { name: 'programDbId', type: 'string', description: 'Associated breeding program', required: false, example: 'PROG001', brapiField: 'programDbId' },
        { name: 'startDate', type: 'date', description: 'Trial start date', required: false, example: '2024-01-15', brapiField: 'startDate' },
        { name: 'endDate', type: 'date', description: 'Trial end date', required: false, example: '2024-06-30', brapiField: 'endDate' },
        { name: 'active', type: 'boolean', description: 'Whether trial is active', required: false, example: 'true', brapiField: 'active' }
      ],
      relationships: ['Studies', 'Programs', 'Contacts']
    },
    observation: {
      name: 'Observation',
      description: 'A single data point measurement',
      fields: [
        { name: 'observationDbId', type: 'string', description: 'Unique identifier', required: true, example: 'OBS001', brapiField: 'observationDbId' },
        { name: 'observationUnitDbId', type: 'string', description: 'Associated observation unit', required: true, example: 'OU001', brapiField: 'observationUnitDbId' },
        { name: 'observationVariableDbId', type: 'string', description: 'Variable being measured', required: true, example: 'VAR001', brapiField: 'observationVariableDbId' },
        { name: 'value', type: 'string', description: 'Measured value', required: true, example: '5.2', brapiField: 'value' },
        { name: 'observationTimeStamp', type: 'datetime', description: 'When observation was made', required: false, example: '2024-03-15T10:30:00Z', brapiField: 'observationTimeStamp' }
      ],
      relationships: ['ObservationUnits', 'ObservationVariables', 'Studies']
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'string': return <Type className="h-4 w-4 text-blue-500" />
      case 'integer': case 'number': return <Hash className="h-4 w-4 text-green-500" />
      case 'date': case 'datetime': return <Calendar className="h-4 w-4 text-purple-500" />
      case 'boolean': return <ToggleLeft className="h-4 w-4 text-orange-500" />
      default: return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const entityList = Object.keys(entities)
  const currentEntity = entities[selectedEntity]

  const filteredFields = currentEntity?.fields.filter(f =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.description.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

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
        <Button variant="outline"><Download className="h-4 w-4 mr-2" />Export Documentation</Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg"><Database className="h-5 w-5 text-blue-600" /></div>
              <div>
                <div className="text-2xl font-bold">{entityList.length}</div>
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
                <div className="text-2xl font-bold">{Object.values(entities).reduce((sum, e) => sum + e.fields.length, 0)}</div>
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
                <div className="text-2xl font-bold">{Object.values(entities).reduce((sum, e) => sum + e.relationships.length, 0)}</div>
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
                {entityList.map((key) => (
                  <div key={key} className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${selectedEntity === key ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`} onClick={() => setSelectedEntity(key)}>
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      <span className="font-medium capitalize">{key}</span>
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
                <CardTitle className="capitalize">{currentEntity?.name}</CardTitle>
                <CardDescription>{currentEntity?.description}</CardDescription>
              </div>
              <div className="flex gap-2">
                {currentEntity?.relationships.map((rel, i) => (
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
                  {filteredFields.map((field, i) => (
                    <tr key={i} className="border-t hover:bg-muted/50">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-muted px-2 py-1 rounded">{field.name}</code>
                          {field.brapiField && <Badge variant="secondary" className="text-xs">BrAPI</Badge>}
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
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
