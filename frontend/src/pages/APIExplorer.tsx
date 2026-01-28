import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Play, Copy } from 'lucide-react'

interface Endpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string
  description: string
  category: string
}

export function APIExplorer() {
  const [_activeTab, _setActiveTab] = useState('endpoints')
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null)
  const [response, setResponse] = useState<string | null>(null)

  const endpoints: Endpoint[] = [
    { method: 'GET', path: '/brapi/v2/germplasm', description: 'List all germplasm', category: 'Germplasm' },
    { method: 'GET', path: '/brapi/v2/trials', description: 'List all trials', category: 'Core' },
    { method: 'GET', path: '/brapi/v2/studies', description: 'List all studies', category: 'Core' },
    { method: 'GET', path: '/brapi/v2/observations', description: 'List observations', category: 'Phenotyping' },
    { method: 'GET', path: '/brapi/v2/variants', description: 'List variants', category: 'Genotyping' },
    { method: 'POST', path: '/brapi/v2/germplasm', description: 'Create germplasm', category: 'Germplasm' },
  ]

  const getMethodColor = (method: string) => {
    const colors: Record<string, string> = { GET: 'bg-green-100 text-green-800', POST: 'bg-blue-100 text-blue-800', PUT: 'bg-yellow-100 text-yellow-800', DELETE: 'bg-red-100 text-red-800' }
    return colors[method] || 'bg-gray-100 text-gray-800'
  }

  const handleTest = () => {
    setResponse(JSON.stringify({ status: 'success', data: { count: 42 } }, null, 2))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Explorer</h1>
          <p className="text-muted-foreground">Test and explore BrAPI endpoints</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader><CardTitle>Endpoints</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="divide-y max-h-[500px] overflow-auto">
              {endpoints.map((ep, idx) => (
                <div key={idx} className={`p-3 cursor-pointer hover:bg-accent ${selectedEndpoint === ep ? 'bg-accent' : ''}`} onClick={() => setSelectedEndpoint(ep)}>
                  <div className="flex items-center gap-2">
                    <Badge className={getMethodColor(ep.method)}>{ep.method}</Badge>
                    <code className="text-sm">{ep.path}</code>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{ep.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Request</CardTitle>
            {selectedEndpoint && (
              <div className="flex items-center gap-2">
                <Badge className={getMethodColor(selectedEndpoint.method)}>{selectedEndpoint.method}</Badge>
                <code>{selectedEndpoint.path}</code>
              </div>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input placeholder="Base URL" defaultValue="https://api.example.com" className="flex-1" />
              <Button onClick={handleTest}><Play className="mr-2 h-4 w-4" />Send</Button>
            </div>
            {response && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Response</span>
                  <Button variant="ghost" size="sm"><Copy className="mr-1 h-3 w-3" />Copy</Button>
                </div>
                <pre className="p-4 bg-accent rounded-lg text-sm overflow-auto max-h-64">{response}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
